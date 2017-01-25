FROM ubuntu:16.04

MAINTAINER 3Blades <contact@3blades.io>

RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -yq --no-install-recommends \
    build-essential \
    git \
    libffi-dev \
    libpq-dev \
    libssl-dev \
    python3.5 \
    python3.5-dev \
    libmagic-dev \
    virtualenv && \
    apt-get clean && \
    apt-get autoclean && \
    apt-get autoremove

RUN mkdir -p /srv/
WORKDIR /srv/
RUN virtualenv env --python=/usr/bin/python3.5
RUN . env/bin/activate; pip install --upgrade setuptools pip wheel

WORKDIR /srv/app/

ADD requirements/ /srv/app/requirements

# install requirements to run hub server
RUN . ../env/bin/activate; pip install -r requirements/dev.txt

ADD . /srv/app

EXPOSE 80
