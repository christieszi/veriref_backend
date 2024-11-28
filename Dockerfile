# Dockerfile

# python base image
FROM python:3.10-alpine

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBUG 1

COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY . .

# collecting static
RUN python3 app.py

