import os
class DefaultConfigs(object):


    mode = 'train'
    encoder_name = 'Disc128'
    pretrained = False
    gan_latent_dim = 100
    exp_name = ' cam-oscc'
    task_names = ['main_task', 'magnification']
    aux_task_names = ['magnification']
    tasks = {'magnification': {'type': 'classification', 'n_classes': 3}, 'main_task': {'type': 'classification', 'n_classes': 2} }
    loss_weight = {'magnification': 0.2, 'main_task': 1}

    log_dir = 'E:\Back_up\experiments_log\domain_adoptation\GAN\logs'
    cache_dir = 'E:\Back_up\experiments_log\domain_adoptation\GAN\cache'
    model_dir = 'E:\Back_up\experiments_log\domain_adoptation\\GAN\model'
    best_model_dir = 'E:\Back_up\experiments_log\domain_adoptation\GAN\\best_model'
    training_resume = 'model_033922.pth'
    training_num_print_epoch = 1


    #source domain
    src_batch_size = 32
    base_data_path = 'G:\\512allcamelyon'
    pickle_path = 'E:\Back_up\git-files\Multi_task_domain_adapt\pickle_files\\training_cam.pickle'
    budget = 'training_cam1'

    #target domain
    tar_batch_size = 32
    base_data_path_unlabel = 'G:\\512all'
    pickle_path_unlabel= 'E:\Back_up\git-files\Multi_task_domain_adapt\pickle_files\\training.pickle'
    budget_unlabel = 'training1'



    #validation
    pickle_path_valid = 'E:\Back_up\git-files\Multi_task_domain_adapt\pickle_files\\validation.pickle'
    budget_valid = 'validation1'
    validation_model = 'model_002120.pth'


    #test
    pickle_path_test = 'E:\Back_up\git-files\Multi_task_domain_adapt\pickle_files\\test.pickle'
    budget_test = 'test1'
    testing_model ='model_033922.pth'

    save_output = True
    eval_batch_size = 128
    test_batch_size = 128



    random_seed = 22
    num_epochs = 100

    optimizer = 'sgd'
    lr =  0.0003
    weight_decay= 0.0005
    momentum= 0.9
    nesterov= True

    lr_scheduler= {'name': 'step', 'step_size': 24}

    gpus = '1'
config = DefaultConfigs()