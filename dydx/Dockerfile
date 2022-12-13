FROM python:3.8

WORKDIR /app
ARG requirements=requirements/production.txt

ADD . /app

RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install --no-cache-dir -e .
RUN pip install --no-cache-dir -r $requirements
