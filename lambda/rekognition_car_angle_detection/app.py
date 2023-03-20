import json
from typing import List

import boto3
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from itertools import combinations

import numpy as np
from itertools import combinations
import math

rek = boto3.client('rekognition')

#font_file = '/opt/ml/arial.ttf'

def get_wheels_and_cars_default(response):
    """
    Filter out bounding boxes of wheels and cars
    from response of the default Rekognition model
    """
    car_bbs, wheel_bbs = [], []
    for detections in response["Labels"]:
        boxes = [instance["BoundingBox"] for instance in detections["Instances"]]
        if detections["Name"] == "Car":
            car_bbs.extend(boxes)
        if detections["Name"] == "Wheel":
            wheel_bbs.extend(boxes)
    return car_bbs, wheel_bbs

def get_wheels_and_cars_custom(response):
    """
    Filter out bounding boxes of wheels and cars
    from response of a custom Rekognition model
    """
    car_bbs, wheel_bbs = [], []
    for detection in response["CustomLabels"]:
        box = detection["Geometry"]["BoundingBox"]
        if detection["Name"] == "vehicle":
            car_bbs.append(box)
        if detection["Name"] == "vehicle_wheel":
            wheel_bbs.append(box)
    return car_bbs, wheel_bbs


def _extract_bb_coords(box, img):
    """
    Take bounding boxes of one object and return
    pixel coordinates within the image
    """
    imgWidth, imgHeight = img.size
    left = imgWidth * box['Left']
    top = imgHeight * box['Top']
    width = imgWidth * box['Width']
    height = imgHeight * box['Height']
    points = [
        (left,top),
        (left + width, top),
        (left + width, top + height),
        (left , top + height),
        (left, top)
    ]
    return points


def car_angle_from_wheels(wheel_instances, img):
    """
    Takes a list of bounding boxes of wheel bounding boxes (as returned by Rekognition)
    Returns the angle between a horizontal line and a reference vector between
    the front and rear wheel of the car (aka reference vector).
    
    Most part of this function deals with finding this vector.
    
    Parameters
    ----------
    wheel_instances: List[dict]
        Bounding boxes of wheels of the form
        {'Width': ...,'Height': .., 'Left': ..., 'Top': ...}
    img:
        PIL image object

    Returns
    -------
    float, list
        Car angle and a the wheel centers for plotting.
    """
    n_wheels = len(wheel_instances)

    # Get a list of the centre of all wheel bounding boxes
    wheel_centers = [np.array(_extract_bb_coords(wheel, img)).mean(axis=0) for wheel in wheel_instances]
    
    # Get all possible vectors between wheel bounding boxes and sort them by their length
    wheel_center_comb = list(combinations(wheel_centers, 2))
    # Note: We enumerate these vectors to later still have information on which wheels belong to which vector (need that for plotting)
    vecs = [(k, pair[0] - pair[1]) for k,pair in enumerate(wheel_center_comb)]
    vecs = sorted(vecs, key = lambda vec: np.linalg.norm(vec[1]))
    
    # If we have 3 vectors (normally the case if we have 2 front wheels and 1 rear wheel)
    # we want to take the 2nd longest as reference to get the angle.
    vec_rel = vecs[1] if n_wheels == 3 else vecs[0]
    angle = math.degrees(math.atan(vec_rel[1][1]/vec_rel[1][0]))
    
    wheel_centers_rel = [tuple(wheel.tolist()) for wheel in wheel_center_comb[vec_rel[0]]]
    return np.abs(angle), wheel_centers_rel


def label_image(img_string, response):
    """
    Takes an image and a Rekognition response with detections for this image.
    Plots relevant information on the image.
    
    img: PIL image
    
    response:
    """
    
    img = Image.open(BytesIO(img_string)).convert('RGB')
    imgWidth, imgHeight = img.size
    
    car_bbs, wheel_bbs = get_wheels_and_cars_default(response)
    
    draw = ImageDraw.Draw(img)
    #fnt = ImageFont.truetype(font=font_file, size=30)
    fnt = ImageFont.load_default()
    
    # If there is more than 1 car in the image we don't get the angle
    if len(car_bbs) > 1:
        text = "Too many cars"
        print(text)
        draw.text((imgWidth * 0.1, imgHeight * 0.1), text, font=fnt, fill="#CC0000")
        return None, img

    # If there are less than 2 or more than 3 wheels, something is odd and we don't return an angle
    if len(wheel_bbs) not in [2,3]:
        text = "Too many or too few wheels detected"
        print(text)
        draw.text((imgWidth * 0.1, imgHeight * 0.1), text, font=fnt, fill="#CC0000")
        return None, img
    
    # If there are 2 or 3 wheels, get the angle and plot the reference vector
    angle, wheel_centers_rel = car_angle_from_wheels(wheel_bbs, img) 
    draw.text((imgWidth * 0.5, imgHeight * 0.7), f"Angle: {angle:.2f}°", font=fnt, fill="#CC0000")
    draw.line(wheel_centers_rel, fill='#3333FF', width=5)
    return angle, img


def lambda_handler(event, context):
    body_bytes = json.loads(event["body"])["image"].split(",")[-1]
    body_bytes = base64.b64decode(body_bytes)

    response = rek.detect_labels(Image={'Bytes': body_bytes}, MinConfidence=80)
    
    angle, img = label_image(img_string=body_bytes, response=response)

    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_str = "data:image/jpeg;base64," + base64.b64encode(buffered.getvalue()).decode('utf-8')

    return {
        'statusCode': 200,
        "headers": {
            "Access-Control-Allow-Origin": event["headers"]["origin"],
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
        'body': json.dumps({
            "image": img_str,
            "angle": angle
        })
    }
