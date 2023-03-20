from typing import BinaryIO, Mapping
import json
import logging
import sys
from pathlib import Path

import numpy as np
import cv2
import torch

from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2 import model_zoo


logger = logging.Logger("InferenceScript", level=logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))
logger.addHandler(handler)

COCO_CONFIG_FILE = "COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml"
COCO_MODEL_CHECKPOINT = "COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml"
DEFAULT_SCORE_THRESHOLD = 0.5
TRAINED_SCORE_THRESHOLD = 0.7


def _get_pretraind_model():
    """Get Detectron2 default predictor"""
    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file(COCO_CONFIG_FILE))
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = DEFAULT_SCORE_THRESHOLD
    cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url(COCO_MODEL_CHECKPOINT)
    predictor = DefaultPredictor(cfg)
    return predictor


def _load_from_bytearray(request_body: BinaryIO) -> np.ndarray:
    npimg = np.frombuffer(request_body, np.uint8)
    return cv2.imdecode(npimg, cv2.IMREAD_COLOR)


def get_main_car_mask(seg_predictor, np_image):
    """Get the main mask of the car object in the given image

    Parameters
    ----------
    predictor : DefaultPredictor
        Detectron2 default predictor
    input_object : np.ndarray

    Returns
    -------
    np.ndarray
        A Boolean Numpy array that contains the mask of the main car. The function uses a MRCNN predictor 
        to segment the input image. It focusses on the ouput classes 2 and 7 which coresspond to Car and Truck.
        If the image conatins more than one object of this class, the object with the largest mask is selected,
        if no object is found, it returns None.
    """
    outputs = seg_predictor(np_image)
    pred_classes = outputs['instances'].pred_classes.cpu().numpy()
    pred_masks = outputs['instances'].pred_masks.cpu().numpy() 
    mask_size = 0
    mask_return = None
    for obj, mask in zip(pred_classes, pred_masks):
        if obj in [2, 7]:
            cur_size = mask.sum()
            if cur_size > mask_size:
                mask_return = mask
                mask_size = cur_size
        else:
            continue

    return mask_return


def model_fn(model_dir: str) -> DefaultPredictor:
    """Load trained model

    Parameters
    ----------
    model_dir : str
        S3 location of the model directory

    Returns
    -------
    DefaultPredictor
        PyTorch model created by using Detectron2 API
    """
    logger.info(f"Model dir {model_dir}")
    path_cfg, path_model = None, None
    for p_file in Path(model_dir).iterdir():
        if p_file.suffix == ".yaml":
            logger.info('Test')
            logger.info(p_file)

            path_cfg = p_file
        if p_file.suffix == ".pth":
            path_model = p_file

    logger.info(f"Using configuration specified in {path_cfg}")
    logger.info(f"Using model saved at {path_model}")

    if path_model is None:
        err_msg = "Missing model PTH file"
        logger.error(err_msg)
        raise RuntimeError(err_msg)
    if path_cfg is None:
        err_msg = "Missing configuration JSON file"
        logger.error(err_msg)
        raise RuntimeError(err_msg) 
    cfg = get_cfg()
    cfg.merge_from_file(path_cfg)
    cfg.MODEL.WEIGHTS = str(path_model)
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = TRAINED_SCORE_THRESHOLD
    cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

    return DefaultPredictor(cfg)


def input_fn(request_body: BinaryIO, request_content_type: str) -> np.ndarray:
    """Parse input data

    Parameters
    ----------
    request_body : BinaryIO
        encoded input image
    request_content_type : str
        type of content

    Returns
    -------
    np.ndarray
        input image

    Raises
    ------
    ValueError
        ValueError if the content type is not `application/x-image`
    """
    if request_content_type == "application/x-image":
        np_image = _load_from_bytearray(request_body)
    else:
        err_msg = f"Type [{request_content_type}] not support this type yet"
        logger.error(err_msg)
        raise ValueError(err_msg)
    return np_image


def predict_fn(input_object: np.ndarray, predictor: DefaultPredictor) -> Mapping:
    """Run Detectron2 prediction

    Parameters
    ----------
    input_object : np.ndarray
        input image
    predictor : DefaultPredictor
        Detectron2 default predictor (see Detectron2 documentation for details)

    Returns
    -------
    Mapping
        a dictionary that contains: the image shape (`image_height`, `image_width`), the predicted
        bounding boxes in format x1y1x2y2 (`pred_boxes`), the confidence scores (`scores`) and the
        labels associated with the bounding boxes (`pred_boxes`)
    """
    logger.info(f"Prediction on image of shape {input_object.shape}")
    pretrained_predictor = _get_pretraind_model()
    car_mask = get_main_car_mask(pretrained_predictor, input_object)
    outputs = predictor(input_object)
    logger.info(f"Car Mask {car_mask}")
    fmt_out = {
        "image_height": input_object.shape[0],
        "image_width": input_object.shape[1],
        "pred_boxes": outputs["instances"].pred_boxes.tensor.tolist(),
        "scores": outputs["instances"].scores.tolist(),
        "pred_classes": outputs["instances"].pred_classes.tolist(),
        "car_mask": car_mask.tolist()
    }
    logger.info(f"Number of detected boxes: {len(fmt_out['pred_boxes'])}")
    return fmt_out


def output_fn(predictions, response_content_type):
    r"""Serialize the prediction result into the desired response content type"""
    return json.dumps(predictions)
