FROM python:3.11-slim-buster

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_VERSION=1.5.0

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
ENV ENV=PROD

RUN pip install poetry==${POETRY_VERSION} && \
    poetry config virtualenvs.path --unset && \
    poetry config virtualenvs.in-project true

COPY . /usr/src/app/

RUN poetry install --no-root

CMD poetry run flask db upgrade && \
    poetry run gunicorn app:app \
    --workers 1 \
    --timeout 0 \
    --bind 0.0.0.0:${PORT} \
    --log-level=info \
    --access-logfile '-'
