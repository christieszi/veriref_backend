# Dockerfile

# python base image
FROM python:3.10-alpine

WORKDIR /app

COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY . .

# collecting static
CMD ["python3", "app.py"]
