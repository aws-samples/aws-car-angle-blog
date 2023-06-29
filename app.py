#!/usr/bin/env python3

import aws_cdk as _cdk
import cdk_nag as _nag

from car_angle_detection.car_angle_detection_stack import CarAngleDetectionStack

bucket_name = f'Enter your bucket name'
app = _cdk.App()
CarAngleDetectionStack(app, "car-angle-detection", bucket_name=bucket_name)

# Uncomment if needed!
# _cdk.Aspects.of(app).add(_nag.AwsSolutionsChecks())

app.synth()
