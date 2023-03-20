#!/usr/bin/env bash

S3_BUCKET=$1  # name of the bucket where the new data should be stored
AWS_REGION=$2

# Log in to SageMaker repo to get pytorch container
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin 763104351884.dkr.ecr.$AWS_REGION.amazonaws.com

account=$(aws sts get-caller-identity --query Account --output text)
region=$AWS_REGION

prefix=sagemaker-d2-car-position
train_image=${prefix}-train
serve_image=${prefix}-serve
tag=latest
dockerfile_train=Dockerfile.train
dockerfile_serve=Dockerfile.serve

train_ecr=${account}.dkr.ecr.${region}.amazonaws.com/${train_image}:${tag}
serve_ecr=${account}.dkr.ecr.${region}.amazonaws.com/${serve_image}:${tag}

aws ecr describe-repositories --repository-names "${train_image}" > /dev/null 2>&1

if [ $? -ne 0 ]
then
    aws ecr create-repository --repository-name "${train_image}" > /dev/null
fi

aws ecr describe-repositories --repository-names "${serve_image}" > /dev/null 2>&1

if [ $? -ne 0 ]
then
    aws ecr create-repository --repository-name "${serve_image}" > /dev/null
fi

docker build -t ${train_image}:${tag} . -f ${dockerfile_train}
docker tag ${train_image} ${train_ecr}
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin ${account}.dkr.ecr.$AWS_REGION.amazonaws.com
docker push ${train_ecr}

aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin 763104351884.dkr.ecr.$AWS_REGION.amazonaws.com

docker build -t ${serve_image}:${tag} . -f ${dockerfile_serve}
docker tag ${serve_image} ${serve_ecr}
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin ${account}.dkr.ecr.$AWS_REGION.amazonaws.com
docker push ${serve_ecr}

git clone https://github.com/dsmlr/Car-Parts-Segmentation.git
rm Car-Parts-Segmentation/trainingset/annotations.json
cp data/annotations-train.json Car-Parts-Segmentation/trainingset/
mv Car-Parts-Segmentation/trainingset/annotations-train.json Car-Parts-Segmentation/trainingset/annotations.json
rm Car-Parts-Segmentation/testset/annotations.json
cp data/annotations-test.json Car-Parts-Segmentation/testset/
mv Car-Parts-Segmentation/testset/annotations-test.json Car-Parts-Segmentation/testset/annotations.json

aws s3 cp Car-Parts-Segmentation/trainingset s3://$S3_BUCKET/car_position/train --recursive
aws s3 cp Car-Parts-Segmentation/testset s3://$S3_BUCKET/car_position/test --recursive

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 car_angle_train.py --s3-bucket $S3_BUCKET --ecr-image-training $train_ecr --ecr-image-serving $serve_ecr