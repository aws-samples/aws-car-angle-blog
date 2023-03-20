# Car positioning application

# Description

Some user applications can have specific requirements on the angle at which a  product is placed on, in an image. A scalable , user friendly solution is provided in a ready to deploy fashion, to detect the car's angle relative to the camera , using AWS services. 

## Architecture

Users upload the image to be processed on the front end, constructed with AWS Amplify. The application recieves the request via a API gateway. The Request triggers a corresponding Lambda function to complete the processing. The final result of the evaluation is stored in S3. The Dockerfiles deployed using Lambda are stored in ECR.  

![Alt text](solution_architecture.png?raw=true "Title")

More information on the services can be found here

AWS Rekognition : https://aws.amazon.com/rekognition/
AWS Amplify: https://aws.amazon.com/amplify/
Amazon Sagemaker : https://aws.amazon.com/sagemaker/ 
AWS API Gateway: https://aws.amazon.com/api-gateway/
AWS Lambda : https://aws.amazon.com/lambda/  


## Structure of the repo

The repo includes the following directories

car-angle-detection-ml-repo : contains the necessary scripts to train the 'Detectron' Mask RCNN Model that detects different car parts and subsequently compute the car angle. 

car-angle-detection-website-repo:  contains the HTML code for the front end , that receives the user input.

car-angle-detection: contains the CDK stack that deploys the entire application 

Lambda: contains the  individual Lamba Functions to trigger the Sagemaker endpoints , Rekognition API 


# Getting Started

## Dependencies

The following pre requisities are essential to setup the application 

1. An aws account 
2. EC2 Instance 
3. Appropriate IAM Roles 


## Execution

This app creates a stack (`car-angle-detection`) which contains an AWS Amplify static website project leverging an AWS CodeCommit repository, a Amazon S3 bucket, an AWS CodeCommit repository that is integrated into an AWS CodePipeline which enables CI/CD driven machine learning (ML) training, this ML training is done in Amazon SageMaker and will automatically deploy an endpoint, this endpoint is used in an AWS Lambda function behind an Amazon API Gateway. This comes together with another AWS Lambda function behind an Amazon API Gateway which can both be connected to the static frontend.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project. First we will need to create a virtuelenv,
stored under a .venv directory.  To create the virtualenv it assumes that there is a `python3` executable
in your path with access to the `venv` package. But before, let's install AWS CDK.

Step 0: Install the AWS CDK usin `npm`:

```
npm install -g aws-cdk
```

Step 1: Create a virtualenv on MacOS / Linux:

```
$ python3 -m venv .venv
```

Step 2: After the init process is complete and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are on a Windows platform,  activate the virtualenv with:

```
% .venv\Scripts\activate.bat
```

Step 3:Once the virtualenv is activated, install the required dependencies.

```
$ pip install -r requirements.txt
```

Step 4: At this point you can now synthesize the CloudFormation template for this code. 
**Before you do so, edit your app.py and provide the appropriate AWS account and region.**

```
$ cdk synth
```

Step 5: Also make sure that your account is bootstraped:

```
$ cdk bootstrap
```

Step 6:  you can now deploy the CloudFormation template for this code.

```
$ cdk deploy
```

You can explore the source code, contained in the app directory.
Further unit tests are included and can be run through:
**Before you do so, edit your car_positioning/tests/unit/car_angle_stack_test.py and provide the appropriate AWS account and region.**

```
$ pytest
```

To add additional dependencies, for example other CDK libraries, append them to
the requirements.txt file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!


## Authors

Contributors names and contact info

* [Aamna Najmi] (anajmi@amazon.de)
* [Ahmed Mansour] (amnsour@amazon.de)   
* [David Sauerwein] (dsauerwe@amazon.ch)
* [Michael Wallner] (wallnm@amazon.de)
* [Srikrishna Chaitanya Konduru] (srikrik@amazon.ch)


## License

This project is licensed under the MIT-0 License.


Security
---------------

See https://github.com/aws-samples/car-angle-detection-with-rekognition-and-sagemaker/blob/main/CONTRIBUTING.md#security-issue-notifications for more information.


Licensing
---------
This code is licensed under the MIT-0 License. It is copyright 2022 Amazon.com, Inc. or its affiliates.
