from constructs import Construct
from aws_cdk import (
    Stack,
    Duration,
    aws_s3 as _s3,
    aws_ec2 as _ec2,
    aws_iam as _iam,
    aws_lambda as _lambda,
    aws_codecommit as _codecommit,
    aws_codebuild as _codebuild,
    aws_codepipeline as _pipeline,
    aws_amplify_alpha as _amplify,
    aws_codepipeline_actions as _actions,
    aws_apigateway as _apigateway,
    aws_kms as kms
)



class CarAngleDetectionStack(Stack):

    def __init__(self, scope: Construct, id: str, account: str, bucket_name: str, aws_region: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        key_policy_document=_iam.PolicyDocument(
                statements=[_iam.PolicyStatement(
                    actions=["kms:*"
                    ],
                    principals=[_iam.AccountRootPrincipal()],
                    resources=["*"]
                )]
            )


        key_1 = kms.Key(
                    self,
                    "pipeline-key",
                    alias="alias/codepipeline",
                    enable_key_rotation=True,
                    policy=key_policy_document,
                )
        
        artifact_bucket_name = 'artifact-' + bucket_name
        artifact_bucket = _s3.Bucket(self, 'artifact_bucket', bucket_name=artifact_bucket_name, 
                                     encryption=_s3.BucketEncryption.KMS, encryption_key=key_1,       
                                     access_control=_s3.BucketAccessControl.BUCKET_OWNER_FULL_CONTROL)

        key_2 = kms.Key(
                    self,
                    "data-key",
                    alias="alias/datakey",
                    enable_key_rotation=True,
                    policy=key_policy_document,
                )
        bucket = _s3.Bucket(self, id, bucket_name=bucket_name, encryption=_s3.BucketEncryption.KMS, 
                            encryption_key=key_2)
        website_repository = _codecommit.Repository(
            self,
            "car-angle-detection-website-repo",
            repository_name="car-angle-detection-website-repo",
            description="This repository serves as your entry point for AWS Amplify to host your website.",
            code=_codecommit.Code.from_directory("car-angle-detection-website-repo", "master"))

        ml_repository = _codecommit.Repository(
            self,
            "car-angle-detection-ml-repo",
            repository_name="car-angle-detection-ml-repo",
            description="This repository serves as your entry point for the ML code and deployment.",
            code=_codecommit.Code.from_directory("car-angle-detection-ml-repo", "master"))

        ml_codebuild = _codebuild.Project(
            self,
            'car-angle-detection-ml-build',
            source=_codebuild.Source.code_commit(repository=ml_repository),
            environment=_codebuild.BuildEnvironment(
                build_image=_codebuild.LinuxBuildImage.STANDARD_1_0,
                compute_type=_codebuild.ComputeType.LARGE,
                privileged=True
            ),
            environment_variables={
                "S3_BUCKET": _codebuild.BuildEnvironmentVariable(
                    value=bucket_name),
                "AWS_REGION": _codebuild.BuildEnvironmentVariable(
                    value=aws_region),
            },
            build_spec=_codebuild.BuildSpec.from_object({
                "version": "0.2",
                "env": {
                    "shell": "bash"
                },
                "phases": {
                    "build": {
                        "commands": [
                        "chmod +x deploy.sh",
                        "bash deploy.sh $S3_BUCKET $AWS_REGION"
                      ]
                    }
                  }
                }))

        ml_codebuild.add_to_role_policy(_iam.PolicyStatement(
            resources=["*"],
            actions= ["sagemaker:CreateEndpoint",
                "sagemaker:CreateEndpointConfig",
                "sagemaker:CreateTrainingJob",
                "sagemaker:DescribeEndpoint",
                "sagemaker:DescribeTrainingJob",
                "sagemaker:CreateModel",
                "s3:ListBucket",
                "ecr:GetAuthorizationToken",
                "ecr:CreateRepository",
                "ecr:DescribeImages",
                "ecr:DescribeRepositories",
                "ecr:BatchGetImage",
                "ecr:GetDownloadUrlForLayer"
            ],
            effect=_iam.Effect.ALLOW
        ))

        ml_codebuild.add_to_role_policy(_iam.PolicyStatement(
            resources=[f"arn:aws:iam::{account}:role/car-angle-detection-carangledetectionmlbuildRole*"],
            actions= ["iam:GetRole",
                "iam:PassRole"
            ],
            effect=_iam.Effect.ALLOW
        ))

        key_2.grant(ml_codebuild, *["kms:Decrypt", "kms:DescribeKey", "kms:Encrypt",
                "kms:ReEncrypt*", "kms:GenerateDataKey*"])

        ml_codebuild.add_to_role_policy(_iam.PolicyStatement(
            resources=[
                f"arn:aws:ecr:{aws_region}:{account}:repository/sagemaker-d2-car-position-train",
                f"arn:aws:ecr:{aws_region}:{account}:repository/sagemaker-d2-car-position-serve"
            ],
            actions=["ecr:BatchCheckLayerAvailability",
                "ecr:BatchGetImage",
                "ecr:CompleteLayerUpload",
                "ecr:InitiateLayerUpload",
                "ecr:PutImage",
                "ecr:UploadLayerPart"
            ],
            effect=_iam.Effect.ALLOW
        ))

        ml_codebuild.add_to_role_policy(_iam.PolicyStatement(
            resources=[
                f"arn:aws:s3:::{bucket_name}",
                f"arn:aws:s3:::{bucket_name}/*",
                f"arn:aws:s3:::{artifact_bucket_name}",
                f"arn:aws:s3:::{artifact_bucket_name}/*",
                f"arn:aws:s3:::sagemaker-{aws_region}-{account}",
                f"arn:aws:s3:::sagemaker-{aws_region}-{account}/*"
            ],
            actions=["s3:GetObject*",
                "s3:GetBucket*",
                "s3:List*",
                "s3:DeleteObject*",
                "s3:PutObject",
                "s3:PutObjectLegalHold",
                "s3:PutObjectRetention",
                "s3:PutObjectTagging",
                "s3:PutObjectVersionTagging",
                "s3:Abort*"
            ],
            effect=_iam.Effect.ALLOW
        ))

        ml_codebuild.add_to_role_policy(_iam.PolicyStatement(
            resources=[
                f"arn:aws:logs:{aws_region}:{account}:log-group:/aws/codebuild/carangledetectionmlbuild*",
                f"arn:aws:logs:{aws_region}:{account}:log-group:/aws/sagemaker/TrainingJobs*"
            ],
            actions=["logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:DescribeLogStreams",
                "logs:GetLogEvents",
                "logs:PutLogEvents"
            ],
            effect=_iam.Effect.ALLOW
        ))

        ml_codebuild.role.assume_role_policy.add_statements(
            _iam.PolicyStatement(
                actions=["sts:AssumeRole"],
                effect=_iam.Effect.ALLOW,
                principals=[_iam.ServicePrincipal("sagemaker.amazonaws.com")]))

        source_artifact = _pipeline.Artifact()

        pipeline = _pipeline.Pipeline(
            self,
            "Pipeline",
            pipeline_name="car-angle-detection-ml-pipeline",
            artifact_bucket=artifact_bucket)

        source_action = _actions.CodeCommitSourceAction(
            action_name="Source",
            output=source_artifact,
            repository=ml_repository,
            code_build_clone_output=True)

        build_action = _actions.CodeBuildAction(
            action_name="Deploy",
            project=ml_codebuild,
            input=source_artifact,
            outputs=[_pipeline.Artifact()])

        pipeline.add_stage(
            stage_name="Source",
            actions=[source_action])
        pipeline.add_stage(
            stage_name="Deploy",
            actions=[build_action])

        amplify_app = _amplify.App(
            self,
            "car-angle-detection-website",
            source_code_provider=_amplify.CodeCommitSourceCodeProvider(
                repository=website_repository))

        master_branch = amplify_app.add_branch("master")

        # Defines an AWS Lambda resource
        rekognition_lambda = _lambda.DockerImageFunction(
            self, 'RekognitionLambda',
            code=_lambda.DockerImageCode.from_image_asset("lambda/rekognition_car_angle_detection/"),
            environment={
                'BUCKET': bucket.bucket_name,
            },
            timeout=Duration.seconds(60),
        )

        detect_rekognition_policy = _iam.PolicyStatement(
            actions=["rekognition:DetectLabels"],
            resources=["arn:aws:lambda:::*"])

        rekognition_lambda.add_to_role_policy(
            statement=detect_rekognition_policy)

        # Defines an AWS Lambda resource
        detectron_lambda = _lambda.DockerImageFunction(
            self, 'DetectronLambda',
            code=_lambda.DockerImageCode.from_image_asset("lambda/detectron_car_angle_detection/"),
            environment={
                'BUCKET': bucket.bucket_name,
                # ENDPOINT_NAME has to be the same as in car-angle-detection-ml-repo/car_angle_train.py
                'ENDPOINT_NAME': "detectron-endpoint"
            },
            timeout=Duration.seconds(60),
        )

        detect_detectron_policy = _iam.PolicyStatement(
            actions=["sagemaker:InvokeEndpoint"],
            resources=["arn:aws:lambda:::*"])

        detectron_lambda.add_to_role_policy(
            statement=detect_detectron_policy)

        api_rekognition = _apigateway.RestApi(self, "rekognition-api",
                  rest_api_name="Car Angle Rekognition Service",
                  description="This service serves predictions.")
        get_rekognition_integration = _apigateway.LambdaIntegration(rekognition_lambda,
                request_templates={"application/json": '{ "statusCode": "200" }'})
        api_rekognition.root.add_method("POST", get_rekognition_integration)

        api_detectron = _apigateway.RestApi(self, "detectron-api",
                  rest_api_name="Car Angle detectron Service",
                  description="This service serves predictions.")
        get_detectron_integration = _apigateway.LambdaIntegration(detectron_lambda,
                request_templates={"application/json": '{ "statusCode": "200" }'})
        api_detectron.root.add_method("POST", get_detectron_integration)
