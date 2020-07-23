import os
class DefaultConfigs(object):

    mode = 'train'
    encoder_name = 'resnet50'
    pretrained = False
    stain_normalized = True
    augmentation = True
    training_num_print_epoch = 20
    save_output = True
    eval_batch_size = 128
    test_batch_size = 128
    random_seed = 33
    num_epochs = 100
    gpus = [1]
    lr =  0.001
    weight_decay = 10e-3
    src_batch_size = 64
    tar_batch_size = 64
    exp_name = ' cam-oscc'
    # for resumin training
    training_resume = ''

    task_names = ['main_task', 'rot']#['main_task', 'magnification', 'jigsaw', 'domain_classifier', hematoxylin, 'rot']
    aux_task_names =task_names[1:]
    tasks = {'magnification': {'type': 'classification_self', 'n_classes': 3},
             'main_task': {'type': 'classification_main', 'n_classes': 2},
             'jigsaw': {'type': 'classification_self', 'n_classes': 12},
             'domain_classifier': {'type': 'classification_adapt', 'n_classes': 2},
             'hematoxylin': {'type': 'pixel_self', 'n_classes': 1},
             'flip': {'type': 'classification_self', 'n_classes': 2},
             'rot': {'type': 'classification_self', 'n_classes': 4},
             'auto': {'type': 'pixel_self', 'n_classes': 3}
             }
    loss_weight = {'magnification': 1, 'domain_classifier': 1,
                   'main_task': 1, 'jigsaw': 1, 'hematoxylin': 1,
                   'flip': 1, 'rot':1, 'auto': 1}
    annotation_budget = 0.01
    log_dir = './exp/'
    cache_dir = './exp/'
    model_dir = './exp/'
    best_model_dir = './exp/'
    for task_name in task_names:
        log_dir = log_dir +'_' +task_name[:3]
        cache_dir = cache_dir +'_' +task_name[:3]
        model_dir = model_dir +'_' +task_name[:3]
        best_model_dir = best_model_dir +'_' +task_name[:3]
    log_dir = log_dir + str(annotation_budget)+'/logs'
    cache_dir = cache_dir + str(annotation_budget)+'/cache'
    model_dir = model_dir + str(annotation_budget)+'/model'
    best_model_dir = best_model_dir + str(annotation_budget)+'/best_model'



    #source domain path
    # base_data_path = '/media/navid/SeagateBackupPlusDrive/512allcamelyon'
    base_data_path = '/media/navid/SeagateBackupPlusDrive/512all'
    pickle_path = 'pickle_files/training_balanced.pickle'
    budget = 'training' + str(annotation_budget)

    #target domain path
    # base_data_path_unlabel = '/media/navid/SeagateBackupPlusDrive/512all'
    base_data_path_unlabel = '/media/navid/SeagateBackupPlusDrive/512all'
    pickle_path_unlabel= 'pickle_files/training_balanced.pickle'
    budget_unlabel = 'training1'

    # validation path
    pickle_path_valid = './pickle_files/validation_balanced.pickle'
    budget_valid = 'validation1'

    # test path
    # base_data_path_unlabel_new = 'G://test_camelyon'
    pickle_path_test = './pickle_files/test_balanced.pickle'
    budget_test = 'test1'
    testing_model ='./exp/_mai_mag_jig_hem0.01/best_model/model_best_acc.pth'

config = DefaultConfigs()