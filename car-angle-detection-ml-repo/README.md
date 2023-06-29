# Car Angle Detection using MRCNN 

The car angle detection project delivers a deep learning application that can detect the angle of a car in a given image. We train and deploy a MRCNN model to detect the position of different car parts. The detected  positions are then post processed to determine the angle of the car in the image. 

## Description

A MRCNN model is trained on the Car Parts Segmenation dataset provided in the repo: [dataset](https://github.com/dsmlr/Car-Parts-Segmentation.git). We modify the annotations of the dataset such that each wheel has a unique bounding box and a unique mask. Training is done using Sagemaker by utlizing the Dockerfile.train. The trained model is deployed on a container running the Dockerfile.serve file. Finally, A post processing logic transforms the position of the detected car parts into an angle-view pair.  

## Dependencies

* Make sure to have an AWS account with access to the following services: Amazon SageMaker, Amazon ECR and Amazon S3

## Execution

1. Run `chmod u+x deploy.sh`
2. Run `./deploy.sh <ENTER_BUCKET_NAME>`

The script executes the following: 
* It builds and pushes the two docker images needed for training and inference: Dockerfile.train and Dockerfile.serve
* It clones the [dataset](https://github.com/dsmlr/Car-Parts-Segmentation.git) and replace the annotation files for training and test by new files where each wheel has its own mask and its own bounding box.
* It uploads the training and validatio data to the given S3 bucket under the following Prefix: car_position
* It creates a Python virtual environment and install the necessary requirments and use it to run the car_angle_train.py file. 
