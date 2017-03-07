FROM python:alpine

MAINTAINER 3Blades <contact@3blades.io>

RUN apk update \
 && apk upgrade \
 && apk add --no-cache \
    build-base \
    postgresql-dev \
    libffi-dev

RUN pip install virtualenv

RUN mkdir -p /srv/
WORKDIR /srv/
RUN virtualenv env --python=python3
RUN . env/bin/activate; pip --no-cache-dir install --upgrade setuptools pip wheel

WORKDIR /srv/app/

ADD requirements/ /srv/app/requirements

# install requirements to run app
RUN . ../env/bin/activate; pip --no-cache-dir install -r requirements/dev.txt

ADD . /srv/app

ENTRYPOINT ["/srv/app/docker-entrypoint.sh"]

EXPOSE 80
