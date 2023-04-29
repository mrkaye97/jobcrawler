FROM python:3.10.7-slim-buster

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN  apt-get update \
    && apt-get install -y wget gnupg2 curl \
    && rm -rf /var/lib/apt/lists/*

# Install Firefox, geckodriver, xvfb, and required dependencies
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

# Installing Unzip
RUN apt-get install -yqq unzip

# Download the Chrome Driver
RUN release=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) && wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/$release/chromedriver_linux64.zip

# Unzip the Chrome Driver into /usr/local/bin directory
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

# Set display port as an environment variable
ENV DISPLAY=:99

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

# copy project
COPY . /usr/src/app/

CMD flask db upgrade && \
    gunicorn app:app \
    --workers 2 \
    --timeout 180 \
    --bind 0.0.0.0:${PORT} \
    --log-level=info \
    --preload
