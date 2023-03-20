FROM public.ecr.aws/lambda/python:3.9

COPY position_detection.py app.py requirements.txt ./
COPY arial.ttf /opt/ml/arial.ttf

RUN python3.9 -m pip install -r requirements.txt -t .

CMD ["app.lambda_handler"]
