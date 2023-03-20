from enum import Enum
from itertools import combinations
import math

import numpy as np

CLASS_TO_NUMBER = {"wheel": 18, "back_bumper": 1, "front_bumper": 7}


class View(Enum):
    '''
    Used to encode whether an image shows a car in back, front or side view.
    '''
    BACK = 0
    FRONT = 1
    SIDE = 2


def bbox_for_class(bbs, pred_classes, class_name):
    '''
    Select only bounding boxes for a specific class from
    a Detectron prediction and reformat it.
    '''
    # Select only bboxes for wheels
    bbs = np.compress(pred_classes == CLASS_TO_NUMBER[class_name], bbs, axis=0)

    bbs_reformated = []
    for bb in bbs:
        bb = np.array([[bb[0], bb[1]], [bb[2], bb[1]], [bb[0], bb[3]], [bb[2], bb[3]]])
        bbs_reformated.append(bb)
    return bbs_reformated


def car_angle_wheel_bbs(wheel_bbs):
    '''
    Calculate car position from wheel bounding boxes.

    Parameters
    ----------
    wheel_bbs: List[np.ndarray]
        Bounding boxes of car wheels

    Returns
    -------
    tuple:
        Car angle and relative positions of car wheels to each other.
    '''
    n_wheels = len(wheel_bbs)

    wheel_centers = [wheel_bb.mean(axis=0) for wheel_bb in wheel_bbs]
    # Get all possible vectors between wheel bounding boxes and sort them by their length
    wheel_center_comb = list(combinations(wheel_centers, 2))

    # Note: We enumerate these vectors to later still have information on which wheels belong to which vector (need that for plotting)
    vecs = [(k, pair[0] - pair[1]) for k, pair in enumerate(wheel_center_comb)]
    vecs = sorted(vecs, key=lambda vec: np.linalg.norm(vec[1]))

    # If we have 3 vectors (normally the case if we have 2 front wheels and 1 rear wheel)
    # we want to take the 2nd longest as reference to get the angle.
    vec_rel = vecs[1] if n_wheels == 3 else vecs[0]
    angle = math.degrees(math.atan(vec_rel[1][1]/vec_rel[1][0]))

    wheel_centers_rel = [tuple(wheel.tolist()) for wheel in wheel_center_comb[vec_rel[0]]]
    return np.abs(angle), wheel_centers_rel


def car_angle_from_bbs(outputs):
    '''
    Post-processing to infer car position and angle to image horizontal from Detectron Mask R-CNN prediction.

    Parameters
    ----------
    outputs : dict
        Prediction output of Detectron2 default predictor for one image

    Returns
    -------
    tuple
        A triple of:
            view : View
                The general view of the car (front, back, side) as defined in the View Enum.
            angle : float
                Angle of the car relative to the horizontal of the image
            wheel_centers_rel: list
                Positions of the wheels for plotting

    '''
    # Get all bboxes
    bbs = np.asarray(outputs["pred_boxes"])

    # Select only wheel objects
    pred_classes = np.asarray(outputs["pred_classes"])

    class_bbs = {class_name: bbox_for_class(bbs=bbs, pred_classes=pred_classes, class_name=class_name) for class_name in CLASS_TO_NUMBER.keys()}
    n_class = {class_name: len(class_bbs[class_name]) for class_name in class_bbs.keys()}

    # Check if front or back view

    if n_class["front_bumper"] == 1 and n_class["back_bumper"] == 0:
        view = View.FRONT

    elif n_class["front_bumper"] == 0 and n_class["back_bumper"] == 1:
        view = View.BACK

    elif n_class["front_bumper"] == 0 and n_class["back_bumper"] == 0:
        view = View.SIDE
    else:
<<<<<<< HEAD:src/position_detection.py
        raise Exception(f"Detected inconsistent number of {n_class['front_bumper']} front and {n_class['back_bumper']} back bumpers.")

=======
        print(f"Detected inconsistent number of {n_class['front_bumper']} front and {n_class['back_bumper']} back bumpers.")
        return [None] * 3
    
>>>>>>> c056655b5668a4cdc8bf16b5e1cd39a7d4bbde88:cdk-automation/lambda/detectron_car_angle_detection/position_detection.py
    # Get the angle
    if n_class["wheel"] == 0:
        # Angle is zero
        angle, wheel_centers_rel = 0, []

    elif n_class["wheel"] == 2 or n_class["wheel"] == 3:
        angle, wheel_centers_rel = car_angle_wheel_bbs(class_bbs["wheel"])

    else:
<<<<<<< HEAD:src/position_detection.py
        raise Exception(f"Nr. of detected wheels should be 0, 2 or 3 - detected {n_class['wheel']}.")

=======
        print(f"Nr. of detected wheels should be 0, 2 or 3 - detected {n_class['wheel']}.")
        return [None] * 3
        
>>>>>>> c056655b5668a4cdc8bf16b5e1cd39a7d4bbde88:cdk-automation/lambda/detectron_car_angle_detection/position_detection.py
    return view, angle, wheel_centers_rel
