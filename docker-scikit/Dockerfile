FROM public.ecr.aws/lambda/python:3.7

COPY requirements.txt ./tmp/requirements.txt
RUN pip install -r ./tmp/requirements.txt

COPY model/pickle_model.pkl ./tmp/pickle_model.pkl

COPY app.py   ./
CMD ["app.handler"]