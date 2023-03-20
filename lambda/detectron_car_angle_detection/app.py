import os
import json

import boto3
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from position_detection import car_angle_from_bbs

runtime = boto3.Session().client(service_name="runtime.sagemaker")

def label_image(img_string, wheel_centers_rel):
    img = Image.open(BytesIO(img_string)).convert('RGB')
    
    draw = ImageDraw.Draw(img)
    imgWidth, imgHeight = img.size
    if not wheel_centers_rel:
        draw.text((imgWidth * 0.1, imgHeight * 0.1), "Segmentation not sufficient for position detection.", font=ImageFont.load_default(), fill="#CC0000")
    else:
        draw.line(wheel_centers_rel, fill='#3333FF', width=5)
    return img

def lambda_handler(event, context):
    body_bytes = json.loads(event["body"])["image"].split(",")[-1]
    body_bytes = base64.b64decode(body_bytes)
    
    response = runtime.invoke_endpoint(
                    EndpointName=os.environ["ENDPOINT_NAME"], ContentType="application/x-image", Body=body_bytes
                )
    result = response["Body"].read()
    result = json.loads(result)

    view, angle, wheel_centers_rel = car_angle_from_bbs(result)
    
    img = label_image(img_string=body_bytes, wheel_centers_rel=wheel_centers_rel)

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
            "view": None if view is None else view.value,
            "angle": angle
        })
    }
