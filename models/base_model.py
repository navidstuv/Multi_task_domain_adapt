import os
import time
import itertools

import numpy as np
from PIL import Image
from tqdm import tqdm

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import torch.backends.cudnn as cudnn
from torch.optim.lr_scheduler import _LRScheduler

# custom modules
from schedulers import get_scheduler

from optimizers import get_optimizer
from models.model import get_model
from utils.metrics import AverageMeter
from utils.utils import to_device, make_inf_dl

# summary
from tensorboardX import SummaryWriter

class LinearRampdown(_LRScheduler):
    def __init__(self, opt, rampdown_from=1000, rampdown_till=1200, last_epoch=-1):
        self.rampdown_from = rampdown_from
        self.rampdown_till = rampdown_till
        super(LinearRampdown, self).__init__(opt, last_epoch)

    def ramp(self, e):
        if e > self.rampdown_from:
            f = (e-self.rampdown_from)/(self.rampdown_till-self.rampdown_from)
            return 1 - f
        else:
            return 1.0

    def get_lr(self):
        factor = self.ramp(self.last_epoch)
        return [base_lr * factor for base_lr in self.base_lrs]

class AuxModel:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.writer = SummaryWriter(config.log_dir)
        cudnn.enabled = True

        # set up model
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = get_model(config)
        self.model = self.model.to(self.device)

        if config.mode == 'train':
            # set up optimizer, lr scheduler and loss functions

            lr = config.lr
            self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr, betas=(.5, .999))
            self.scheduler = LinearRampdown(self.optimizer , rampdown_from=1000, rampdown_till=1200)

            self.class_loss_func = nn.CrossEntropyLoss()

            self.start_iter = 0

            # resume
            if config.training_resume:
                self.load(config.model_dir + '/' + config.training_resume)

            cudnn.benchmark = True

        elif config.mode == 'val':
            self.load(os.path.join(config.model_dir, config.validation_model))
        else:
            self.load(os.path.join(config.model_dir, config.testing_model))

    def entropy_loss(self, x):
        return torch.sum(-F.softmax(x, 1) * F.log_softmax(x, 1), 1).mean()

    def train(self, src_loader, tar_loader, val_loader, test_loader):

        num_batches = len(src_loader)
        print_freq = max(num_batches // self.config.training_num_print_epoch, 1)
        i_iter = self.start_iter
        start_epoch = i_iter // num_batches
        num_epochs = self.config.num_epochs
        best_acc = 0
        for epoch in range(start_epoch, num_epochs):
            self.model.train()
            batch_time = AverageMeter()
            losses = AverageMeter()

            # adjust learning rate
            self.scheduler.step()

            for it, src_batch in enumerate(src_loader):
                t = time.time()

                self.optimizer.zero_grad()
                src = src_batch
                src = to_device(src, self.device)
                src_imgs, src_cls_lbls, src_aux_imgs, src_aux_lbls = src


                self.optimizer.zero_grad()

                src_main_logits = self.model(src_imgs,'main_task')
                src_main_loss = self.class_loss_func(src_main_logits, src_cls_lbls)
                loss = src_main_loss* self.config.loss_weight['main_task']


                loss.backward()
                self.optimizer.step()

                losses.update(loss.item(), src_imgs.size(0))

                # measure elapsed time
                batch_time.update(time.time() - t)

                i_iter += 1


                print_string = 'Epoch {:>2} | iter {:>4} | loss:{:.3f}| src_main: {:.3f} |' +  '|{:4.2f} s/it'

                self.logger.info(print_string.format(epoch, i_iter,
                    losses.avg,
                    src_main_loss.item(),
                    batch_time.avg))
                self.writer.add_scalar('losses/all_loss', losses.avg, i_iter)
                self.writer.add_scalar('losses/src_main_loss', src_main_loss, i_iter)
            # del loss, src_class_loss, src_aux_loss, tar_aux_loss, tar_entropy_loss
            # del src_aux_logits, src_class_logits
            # del tar_aux_logits, tar_class_logits

            # validation
            self.save(self.config.model_dir, i_iter)

            if val_loader is not None:
                self.logger.info('validating...')
                class_acc = self.test(val_loader)
                # self.writer.add_scalar('val/aux_acc', class_acc, i_iter)
                self.writer.add_scalar('val/class_acc', class_acc, i_iter)
                if class_acc > best_acc:
                    best_acc = class_acc
                    self.save(self.config.best_model_dir, i_iter)
                    # todo copy current model to best model
                self.logger.info('Best testing accuracy: {:.2f} %'.format(best_acc))

            if test_loader is not None:
                self.logger.info('testing...')
                class_acc = self.test(test_loader)
                # self.writer.add_scalar('test/aux_acc', class_acc, i_iter)
                self.writer.add_scalar('test/class_acc', class_acc, i_iter)
                if class_acc > best_acc:
                    best_acc = class_acc
                    # todo copy current model to best model
                self.logger.info('Best testing accuracy: {:.2f} %'.format(best_acc))

        self.logger.info('Best testing accuracy: {:.2f} %'.format(best_acc))
        self.logger.info('Finished Training.')

    def save(self, path, i_iter):
        state = {"iter": i_iter + 1,
                "model_state": self.model.state_dict(),
                "optimizer_state": self.optimizer.state_dict(),
                "scheduler_state": self.scheduler.state_dict(),
                }
        save_path = os.path.join(path, 'model_{:06d}.pth'.format(i_iter))
        self.logger.info('Saving model to %s' % save_path)
        torch.save(state, save_path)

    def load(self, path):
        checkpoint = torch.load(path)
        self.model.load_state_dict(checkpoint['model_state'])
        self.logger.info('Loaded model from: ' + path)

        if self.config.mode == 'train':
            self.model.load_state_dict(checkpoint['model_state'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state'])
            self.scheduler.load_state_dict(checkpoint['scheduler_state'])
            self.start_iter = checkpoint['iter']
            self.logger.info('Start iter: %d ' % self.start_iter)

    def test(self, val_loader):
        val_loader_iterator = iter(val_loader)
        num_val_iters = len(val_loader)
        tt = tqdm(range(num_val_iters), total=num_val_iters, desc="Validating")

        aux_correct = 0
        class_correct = 0
        total = 0
        soft_labels = np.zeros((1, 2))
        true_labels = []

        self.model.eval()
        with torch.no_grad():
            for cur_it in tt:

                data = next(val_loader_iterator)
                data = to_device(data, self.device)
                imgs, cls_lbls, _, _ = data
                # Get the inputs

                logits = self.model(imgs, 'main_task')

                if self.config.save_output==True:
                    smax = nn.Softmax(dim=1)
                    smax_out = smax(logits)
                    soft_labels = np.concatenate((soft_labels, smax_out.cpu().numpy()), axis=0)
                    true_labels = np.append(true_labels, cls_lbls.cpu().numpy())

                _, cls_pred = logits.max(dim=1)
                # _, aux_pred = aux_logits.max(dim=1)

                class_correct += torch.sum(cls_pred == cls_lbls)
                # aux_correct += torch.sum(aux_pred == aux_lbls.data)
                total += imgs.size(0)

            tt.close()
        if self.config.save_output==True:
            soft_labels = soft_labels[1:, :]
            np.save('pred_cam1.npy', soft_labels)
            np.save('true_cam1.npy', true_labels)

        # aux_acc = 100 * float(aux_correct) / total
        class_acc = 100 * float(class_correct) / total
        self.logger.info('class_acc: {:.2f} %'.format( class_acc))
        return class_acc