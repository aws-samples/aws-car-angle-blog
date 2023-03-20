import aws_cdk as core
import aws_cdk.assertions as assertions

from car_angle_detection.car_angle_detection_stack import CarAngleDetectionStack

# example tests. To run these tests, uncomment this file along with the example
# resource in experiment_dashboard/experiment_dashboard_stack.py

ACCOUNT="enter your AWS account"
REGION="enter your AWS region"
BUCKET=f'detectron-blog-unit-test-run-{ACCOUNT}-{REGION}'

def test_s3_bucket():
    app = core.App()
    stack = CarAngleDetectionStack(app, "car-angle-detection", account=ACCOUNT, bucket_name=BUCKET, aws_region=REGION)
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::S3::Bucket", 2)

def test_lambda_permission():
    app = core.App()
    stack = CarAngleDetectionStack(app, "car-angle-detection", account=ACCOUNT, bucket_name=BUCKET, aws_region=REGION)
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::Lambda::Permission", 4)

def test_lambda_function():
    app = core.App()
    stack = CarAngleDetectionStack(app, "car-angle-detection", account=ACCOUNT, bucket_name=BUCKET, aws_region=REGION)
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::Lambda::Function", 2)

def test_kms_key():
    app = core.App()
    stack = CarAngleDetectionStack(app, "car-angle-detection", account=ACCOUNT, bucket_name=BUCKET, aws_region=REGION)
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::KMS::Key", 2)

def test_iam_role():
    app = core.App()
    stack = CarAngleDetectionStack(app, "car-angle-detection", account=ACCOUNT, bucket_name=BUCKET, aws_region=REGION)
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::IAM::Role", 10)


def test_iam_policy():
    app = core.App()
    stack = CarAngleDetectionStack(app, "car-angle-detection", account=ACCOUNT, bucket_name=BUCKET, aws_region=REGION)
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::IAM::Policy", 8)


def test_events_rule():
    app = core.App()
    stack = CarAngleDetectionStack(app, "car-angle-detection", account=ACCOUNT, bucket_name=BUCKET, aws_region=REGION)
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::Events::Rule", 1)

def test_codecommit_repos():
    app = core.App()
    stack = CarAngleDetectionStack(app, "car-angle-detection", account=ACCOUNT, bucket_name=BUCKET, aws_region=REGION)
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::CodeCommit::Repository", 2)

def test_codebuild_projects():
    app = core.App()
    stack = CarAngleDetectionStack(app, "car-angle-detection", account=ACCOUNT, bucket_name=BUCKET, aws_region=REGION)
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::CodeBuild::Project", 1)

def test_amplify_app():
    app = core.App()
    stack = CarAngleDetectionStack(app, "car-angle-detection", account=ACCOUNT, bucket_name=BUCKET, aws_region=REGION)
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::Amplify::App", 1)
