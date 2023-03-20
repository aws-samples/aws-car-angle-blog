#!/usr/bin/env python3

import aws_cdk as _cdk
import cdk_nag as _nag

from car_angle_detection.car_angle_detection_stack import CarAngleDetectionStack

account='Enter your AWS Account ID'
bucket_name = f'detectron-blog-test-run-{account}'
region='Enter your AWS Account Region'
app = _cdk.App()
CarAngleDetectionStack(app, "car-angle-detection", account=account, bucket_name=bucket_name, aws_region=region)

# Uncomment if needed!
# _cdk.Aspects.of(app).add(_nag.AwsSolutionsChecks())

app.synth()
