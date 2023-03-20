
# Some basic setup:
# Setup detectron2 logger
from detectron2.utils.logger import setup_logger
setup_logger()

# import some common libraries
import os
import sys
import argparse
import yaml

# import some common detectron2 utilities
from detectron2 import model_zoo
from detectron2.engine import DefaultTrainer
from detectron2.config import get_cfg
from detectron2.data.datasets import register_coco_instances
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))


def train(args):
    logger.info('train_dir')
    logger.info(args.train_data_dir)
    register_coco_instances("train_dataset", {}, f"{args.train_data_dir}/annotations.json",
                            f"{args.train_data_dir}")
    register_coco_instances("valid_dataset", {}, f"{args.val_data_dir}/annotations.json",
                            f"{args.val_data_dir}")

    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file(args.coco_config_file))
    cfg.DATASETS.TRAIN = ("train_dataset",)
    cfg.DATASETS.TEST = ()
    cfg.MODEL.DEVICE = args.model_device
    cfg.DATALOADER.NUM_WORKERS = args.num_workers
    cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url(args.coco_model_checkpoint)
    cfg.SOLVER.IMS_PER_BATCH = args.imgs_per_batch
    cfg.SOLVER.BASE_LR = args.base_lr
    cfg.SOLVER.MAX_ITER = args.max_iter
    cfg.SOLVER.STEPS = args.steps
    cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = args.batch_size_per_img
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = args.num_classes
    cfg.OUTPUT_DIR = '/opt/ml/model'
    trainer = DefaultTrainer(cfg)
    trainer.resume_or_load(resume=False)
    trainer.train()
    config_dict = yaml.safe_load(cfg.dump())
    # save the config file needed to load the trained model during inference
    with open(f'{cfg.OUTPUT_DIR}/config.yaml', 'w') as file:
        documents = yaml.dump(config_dict, file)
    logger.info(f'Model trained successfully and artefacts stored at {cfg.OUTPUT_DIR}.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-data-dir", type=str,
                        default=os.environ["SM_CHANNEL_TRAINING"])
    parser.add_argument("--val-data-dir", type=str,
                        default=os.environ["SM_CHANNEL_VALIDATION"])
    parser.add_argument("--model-device", type=str,
                        default="cuda")
    parser.add_argument("--num-workers", type=int,
                        default=4)
    parser.add_argument("--imgs-per-batch", type=int,
                        default=2)
    parser.add_argument("--base-lr", type=float,
                        default=0.00025)
    parser.add_argument("--max-iter", type=int,
                        default=3000)
    parser.add_argument("--batch-size-per-img", type=int,
                        default=512)
    parser.add_argument("--num-classes", type=int,
                        default=19)
    parser.add_argument("--steps", type=list,
                        default=[])
    parser.add_argument("--coco-config-file", type=str,
                        default="COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml")
    parser.add_argument("--coco-model-checkpoint", type=str,
                        default="COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml")
    train(parser.parse_args())
