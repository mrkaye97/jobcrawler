FROM python:3.10.7-slim-buster

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install Firefox, geckodriver, xvfb, and required dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    firefox-esr \
    wget \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libx11-xcb1 \
    xvfb

# Download and install geckodriver
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux64.tar.gz && \
    tar -xzf geckodriver-v0.30.0-linux64.tar.gz && \
    rm geckodriver-v0.30.0-linux64.tar.gz && \
    mv geckodriver /usr/local/bin

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

# copy project
COPY . /usr/src/app/

CMD xvfb-run --server-args="-screen 0 1024x768x24" flask db upgrade && \
    xvfb-run --server-args="-screen 0 1024x768x24" gunicorn src:app \
    --workers 2 \
    --bind 0.0.0.0:${PORT} \
    --log-level=debug \
    --preload
