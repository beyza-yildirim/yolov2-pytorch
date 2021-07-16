import torch
import torch.nn as nn
from data import *
import argparse
from utils.vocapi_evaluator import VOCAPIEvaluator
from utils.cocoapi_evaluator import COCOAPIEvaluator


parser = argparse.ArgumentParser(description='YOLO Detector Evaluation')
parser.add_argument('-v', '--version', default='yolo_v2',
                    help='yolov2_d19, yolov2_r50, yolov2_slim, yolov3, yolov3_spp, yolov3_tiny, yolov4')
parser.add_argument('-d', '--dataset', default='voc',
                    help='voc, coco-val, coco-test.')
parser.add_argument('--trained_model', type=str,
                    default='weights_yolo_v2/yolo_v2_72.2.pth', 
                    help='Trained state_dict file path to open')
parser.add_argument('-size', '--input_size', default=416, type=int,
                    help='input_size')
parser.add_argument('--cuda', action='store_true', default=False,
                    help='Use cuda')

args = parser.parse_args()



def voc_test(model, device, input_size):
    evaluator = VOCAPIEvaluator(data_root=VOC_ROOT,
                                img_size=input_size,
                                device=device,
                                transform=BaseTransform(input_size),
                                labelmap=VOC_CLASSES,
                                display=True
                                )

    # VOC evaluation
    evaluator.evaluate(model)


def coco_test(model, device, input_size, test=False):
    if test:
        # test-dev
        print('test on test-dev 2017')
        evaluator = COCOAPIEvaluator(
                        data_dir=coco_root,
                        img_size=input_size,
                        device=device,
                        testset=True,
                        transform=BaseTransform(input_size)
                        )

    else:
        # eval
        evaluator = COCOAPIEvaluator(
                        data_dir=coco_root,
                        img_size=input_size,
                        device=device,
                        testset=False,
                        transform=BaseTransform(input_size)
                        )

    # COCO evaluation
    evaluator.evaluate(model)


if __name__ == '__main__':
    # dataset
    if args.dataset == 'voc':
        print('eval on voc ...')
        num_classes = 20
    elif args.dataset == 'coco-val':
        print('eval on coco-val ...')
        num_classes = 80
    elif args.dataset == 'coco-test':
        print('eval on coco-test-dev ...')
        num_classes = 80
    else:
        print('unknow dataset !! we only support voc, coco-val, coco-test !!!')
        exit(0)

    # cuda
    if args.cuda:
        print('use cuda')
        torch.backends.cudnn.benchmark = True
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")


    # model
    model_name = args.version
    print('Model: ', model_name)

    # load model and config file
    if model_name == 'yolov2_d19':
        from models.yolov2_d19 import YOLOv2D19 as yolo_net
        cfg = config.yolov2_d19_cfg

    else:
        print('Unknown model name...')
        exit(0)

    # input size
    input_size = args.input_size

    # build model
    anchor_size = cfg['anchor_size_voc'] if args.dataset == 'voc' else cfg['anchor_size_coco']
    net = yolo_net(device=device, 
                   input_size=input_size, 
                   num_classes=num_classes, 
                   trainable=False, 
                   anchor_size=anchor_size)

    # load net
    net.load_state_dict(torch.load(args.trained_model, map_location='cuda'))
    net.eval()
    print('Finished loading model!')
    net = net.to(device)
    
    # evaluation
    with torch.no_grad():
        if args.dataset == 'voc':
            voc_test(net, device, input_size)
        elif args.dataset == 'coco-val':
            coco_test(net, device, input_size, test=False)
        elif args.dataset == 'coco-test':
            coco_test(net, device, input_size, test=True)
