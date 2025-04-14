# Dockerfile

# python base image
FROM python:3.10-alpine

WORKDIR /app

# Install dependencies: curl, wget, and libraries required for Firefox and Geckodriver
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ca-certificates \
    libx11-6 \
    libx11-dev \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libxt6 \
    libgdk-pixbuf2.0-0 \
    libnss3 \
    libasound2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxss1 \
    libgbm1 \
    && apt-get clean

# Install Firefox
RUN mkdir -p /opt && \
    curl -sSL https://download.mozilla.org/?product=firefox-latest&os=linux64&lang=en-US -o /tmp/firefox.tar.bz2 && \
    mkdir -p /opt/firefox && \
    tar -xjf /tmp/firefox.tar.bz2 -C /opt/firefox --strip-components=1 && \
    rm /tmp/firefox.tar.bz2

# Install Geckodriver (latest version)
RUN curl -sSL https://github.com/mozilla/geckodriver/releases/download/v0.31.0/geckodriver-v0.31.0-linux64.tar.gz -o /tmp/geckodriver.tar.gz && \
    tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin && \
    rm /tmp/geckodriver.tar.gz

# Set environment variables
ENV FIREFOX_BIN=/opt/firefox/firefox
ENV GECKODRIVER_BIN=/usr/local/bin/geckodriver

COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY . .

# collecting static
CMD ["python3", "app.py"]
