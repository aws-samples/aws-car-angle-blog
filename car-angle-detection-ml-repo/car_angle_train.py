import boto3
import sagemaker
import argparse

import json

from sagemaker.estimator import Estimator
from sagemaker.pytorch import PyTorchModel

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--s3-bucket", type=str, default="MY_S3_BUCKET_NAME")
    parser.add_argument("--ecr-image-training", type=str, default="MY_ECR_IMAGE")
    parser.add_argument("--ecr-image-serving", type=str, default="MY_ECR_IMAGE")
    args = parser.parse_args()
    
    s3_prefix = 'car_position'
    training_instance = "ml.g4dn.4xlarge"

    sm_session = sagemaker.Session()
    session_bucket = args.s3_bucket
    role = sagemaker.get_execution_role()

    training_channel = f"s3://{session_bucket}/{s3_prefix}/train/"
    validation_channel = f"s3://{session_bucket}/{s3_prefix}/test/"
    
    training_image_uri = args.ecr_image_training # "013349204568.dkr.ecr.eu-central-1.amazonaws.com/sagemaker-d2-car-position-train:latest"
    serve_image_uri = args.ecr_image_serving
    
    prefix_model = "detectron2/training_artefacts"
    
    d2_estimator = Estimator(
        image_uri=training_image_uri,
        role=role,
        sagemaker_session=sm_session,
        instance_count=1,
        instance_type=training_instance,
        output_path=f"s3://{session_bucket}/{prefix_model}",
        base_job_name=f"detectron2",
    )

    d2_estimator.fit(
        {
            "training": training_channel,
            "validation": validation_channel,

        },
        wait=True,
    )
    
    test_channel = f"s3://{session_bucket}/{s3_prefix}/inference/JPEGImages/"
    prefix_predictions = "detectron2/predictions"
    serve_container_name = "sagemaker-d2-serve"
    inference_output = f"s3://{session_bucket}/{prefix_predictions}/{serve_container_name}/inference_channel/detectron_latest"
    
    model = PyTorchModel(
        name="d2-sku110k-model",
        model_data=d2_estimator.model_data,
        role=role,
        sagemaker_session=sm_session,
        entry_point="predict.py",
        source_dir="src",
        image_uri=serve_image_uri,
        framework_version="1.6.0",
    )


    predictor = model.deploy(
        initial_instance_count=1,
        instance_type="ml.g4dn.xlarge",
        endpoint_name="detectron-endpoint",
        serializer=sagemaker.serializers.JSONSerializer(),
        deserializer=sagemaker.deserializers.JSONDeserializer(),
        wait=True
    )