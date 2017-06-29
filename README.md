[![Build Status](https://travis-ci.org/3Blades/app-backend.svg?branch=master)](https://travis-ci.org/3Blades/app-backend)
[![Docker Hub](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com/r/3blades/app-backend/)
[![codecov](https://codecov.io/gh/3Blades/app-backend/branch/master/graph/badge.svg)](https://codecov.io/gh/3Blades/app-backend)
[![Code Climate](https://codeclimate.com/github/3Blades/app-backend/badges/gpa.svg)](https://codeclimate.com/github/3Blades/app-backend)
[![Code Health](https://landscape.io/github/3Blades/app-backend/master/landscape.svg?style=flat)](https://landscape.io/github/3Blades/app-backend/master)
[![Requirements Status](https://requires.io/github/3Blades/app-backend/requirements.svg?branch=master)](https://requires.io/github/3Blades/app-backend/requirements/?branch=master)
[![slack in](https://slack.3blades.io/badge.svg)](https://slack.3blades.io)

# 3Blades Backend Server

Application server backend based on [Django](https://www.djangoproject.com/).

Refer to [docs repo](https://github.com/3blades/docs) for full stack installation instructions.

## Dev Setup with Docker

### Requirements

> Newest version of docker-compose conflicts with docker-py. Install latest version of docker-py with `pip install docker` or remove it entirely from your system.

We recommend using Ubuntu Xenial (16.04), although these instructions should also work with other Linux distributions and Mac OSX. Requirements are:

- [Python 3.6](https://www.python.org/downloads/release/python-360/)
- [Docker](https://docs.docker.com/engine/installation/)
- [Docker Compose](https://docs.docker.com/compose/install/)

We recommend using installation scripts supported by Docker.

Docker Engine:

    curl -sSL https://get.docker.com | sh

Docker Compose:

    curl -L https://github.com/docker/compose/releases/download/1.13.0/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose

Apply executable permissions to docker-compose binary:

    sudo chmod +x /usr/local/bin/docker-compose

> Due Docker's accelerated release cycles, most O/S package managers have outdated versions of Docker Engine and Docker Compose.

We support the **latest** stable releases of docker engine and docker compose, unless noted otherwise.

If using Debian or Ubuntu Linux distributions, you may have to install dependencies to support SSH using your operating system's package manager:

    sudo apt-get install -y libpq-dev libssl-dev

We maintain an `docker-compose.yml` file to launch our working `app-backend` stack. Launching the full stack may be necessary to support integration testing, such as creating new user servers. Services include (in alphabetical order):

- [API](https://hub.docker.com/r/3blades/app-backend)
- [Celery](https://hub.docker.com/r/3blades/app-backend)
- [Elasticsearch](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html)
- [Notificaitons Server](https://hub.docker.com/r/3blades/notifications-server)
- [OpenResty](https://hub.docker.com/r/3blades/)
- [Postgres](https://hub.docker.com/_/postgres/)
- [Redis](https://hub.docker.com/_/redis/)
- [RabbitMQ](https://hub.docker.com/_/rabbitmq/)



> `docker-compose up -d` should check for latest image and pull newer image if one exists, but it may be necessary to pull images explicitly using `docker pull <3blades/image-name`.

> Please refer to `https://github.com/3blades/onpremise` for full stack setup, which includes `react-frontend`.

### Systemd

Newer Linux distributions including Ubuntu Xenial (16.04) use `systemd` as an init system and system manager. `Systemd` provides commands to obtain service status, start services, stop services, among others.

To view docker service status, type:

    systemctl status docker

The resulting output should confirm the service file used by the docker deamon and its general settings:

```
docker.service - Docker Application Container Engine
   Loaded: loaded (/lib/systemd/system/docker.service; enabled; vendor preset: enabled)
   Active: active (running) since Sun 2017-03-19 15:56:44 UTC; 3 days ago
     Docs: https://docs.docker.com
 Main PID: 3897 (dockerd)
    Tasks: 155
   Memory: 358.8M
      CPU: 4min 27.718s
   CGroup: /system.slice/docker.service
           ├─ 3897 /usr/bin/dockerd -H fd://
```

Edit the docker service file to add connections to docker daemon using tcp:

    nano /lib/systemd/system/docker.service

Add `-H tcp://0.0.0.0:2375` after `-H fd://`

Restart docker service and confirm that setting is in place for CGroup:

    sudo systemctl restart docker
    systemctl status docker

### Environment Variables

Modify environment variables located in `env` file with your local settings. You can also export env vars like so:

```
    AWS_ACCESS_KEY_ID=
    AWS_SECRET_ACCESS_KEY=
    AWS_STORAGE_BUCKET_NAME=
    C_ROOT=1
    DATABASE_URL=postgres://postgres:@db:5432/postgres/
    DEBUG=True
    DJANGO_SETTINGS_MODULE=appdj.settings.prod
    DOCKER_DOMAIN=172.17.0.1:2375
    DOCKER_HOST=tcp://172.17.0.1:2375/
    ELASTICSEARCH_URL=http://search:9200/
    EMAIL_HOST=
    EMAIL_PORT=
    EMAIL_HOST_USER=
    EMAIL_HOST_PASSWORD=
    EMAIL_USE_SSL=
    EMAIL_USE_TLS=
    ENABLE_BILLING=True
    GITHUB_CLIENT_ID=
    GITHUB_CLIENT_SECRET=
    GOOGLE_CLIENT_ID=
    GOOGLE_CLIENT_SECRET=
    RABBITMQ_URL=amqp://broker/
    REDIS_URL=redis://cache:6379/0
    RESOURCE_DIR=
    SERVER_RESOURCE_DIR=
    SECRET_KEY=
    SLACK_KEY=
    SLACK_SECRET=
    STRIPE_SECRET_KEY=
    TBS_HOST=
```

> Obtain internal virtual machine IPv4 address with `ifconfig`. Usually enp0s3 or eth0 will be the IP address you need to configure for DOCKER_HOST env var. If you switch setup to use production configuration (`DJANGO_SETTINGS_MODULE='appdj.settings.prod`) make sure to set debug to false (`DEBUG=False`). By default, app-backend allows connections from `staging.3blades.io` and `localhost`. Additional host names or IP addresses can be added to the `TBS_HOST`.

> When launching stack with `dev` environment, `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` will always print emails to the console, regardless of what values are set.

A volume mount is used to persist files used by docker containers. By default, `docker-compose.yml` uses the `/workspaces` directory. You can either add that directory or change `docker-compose.yml` to use another one.

### Launch Stack

Use the following command to launch the full stack with docker compose (-d for detached mode):

    sudo docker-compose up -d

Verify docker containers with `docker ps`:

```
CONTAINER ID        IMAGE                                 COMMAND                  CREATED             STATUS              PORTS                                                   NAMES
3f52405452d9        3blades/openresty:latest              "/usr/local/openre..."   55 minutes ago      Up 55 minutes       443/tcp, 0.0.0.0:5000->80/tcp                           vagrant_server_1
d27b923375c1        dev_celery                        "/srv/app/docker-e..."   55 minutes ago      Up 53 minutes       80/tcp                                                  vagrant_celery_1
3034d8539114        dev_api                           "/srv/app/docker-e..."   55 minutes ago      Up 53 minutes       80/tcp                                                  vagrant_api_1
3b2e36ca71f2        postgres:alpine                       "docker-entrypoint..."   55 minutes ago      Up 55 minutes       0.0.0.0:5432->5432/tcp                                  vagrant_db_1
94cf97bb0bc6        rabbitmq:alpine                       "docker-entrypoint..."   55 minutes ago      Up 55 minutes       4369/tcp, 5671/tcp, 25672/tcp, 0.0.0.0:5672->5672/tcp   vagrant_broker_1
bd8179fd15b8        3blades/notifications-server:latest   "npm start"              55 minutes ago      Up 55 minutes       0.0.0.0:3000->3000/tcp                                  vagrant_notifications-server_1
3ef5ab52176b        redis:alpine                          "docker-entrypoint..."   55 minutes ago      Up 55 minutes       0.0.0.0:6379->6379/tcp                                  vagrant_cache_1
c06b9d4c73ae        gliderlabs/logspout                   "/bin/logspout"          55 minutes ago      Up 55 minutes       80/tcp                                                  vagrant_logspout_1
```

Create admin (superuser) user:

    sudo docker-compose exec api /srv/env/bin/python manage.py createsuperuser

Collect static files:

    sudo docker-compose exec api /srv/env/bin/python manage.py collectstatic

Access API docs page and login:

    http://localhost:5000/swagger/

> You may have to explicitly pull images, even though they are using the latest tag.

### Re Launch Stack after Code Update

Code updates are frequent and may require you to re launch stack. These steps should allow you to relaunch a development stack using updated code base:

1. Navigate into repo and pull latest commit:

    cd app-backend
    git pull origin master

2. Stop all running containers:

    docker-compose stop

3. Verify docker service settings:

    systemctl status docker

If `-H fd:// -H tcp://0.0.0.0:2375` appears, skip step for and move to step 7. Otherwise go to step 4.

4. Edit `docker.service` file:

    sudo nano /lib/systemd/system/docker.service

 Add -H tcp://0.0.0.0:2375 **after** -H fd://

5. Reload daemon service:

    sudo systemctl daemon-reload

6. Restart docker deamon:

    sudo systemctl restart docker

7. Re build images:

    docker-compose build

8. Launch docker stack:

    docker-compose up -d

If you remove all containders with `docker-compose down` or `docker rm -f $(docker ps -a -q)`, then
you will need to recreate your super user and fetch static assets:

    sudo docker-compose exec api /srv/env/bin/python manage.py createsuperuser
    sudo docker-compose exec api /srv/env/bin/python manage.py collectstatic

> It may be necessary to pull new version of an image not managed by app-backend repo, such
as `3blades/openresty`. In that case, make sure you have the latest versions of your images by pulling
them with latest tag, such as `docker pull image 3blades/openresty:latest`.

### Additional Configurations for MAC OSX Users

You may have to add an additional IP address to your `lo0` interface:

    sudo ifconfig lo0 alias 10.200.10.1/24

Make sure your service is listening on `0.0.0.0` (not 127.0.0.1) and change `DOCKER_HOST`
env var to use this IP Address.

## Dev Setup with Django on Host

> Sometimes you may not need to run and test the full stack. Under these circumstances some developers may find that running the Django backend server directly on the host improves development/test cycles, particularly when used with an IDE such as PyCharm.

At a minimum, `app-backend` requires Postgres and Redis.

To run services individually, use the docker run command. Run Postgres with docker:

    docker run --name my-postgres -p 5432:5432 -d postgres

Run Redis with docker:

    docker run --name my-redis -p 6379:6379 -d redis

> You could install Postgres and Redis directly on the host, but we feel that docker simplifies the setup process.

Verify with `docker ps`:

```
CONTAINER ID        IMAGE                                 COMMAND                  CREATED             STATUS              PORTS                                                   NAMES
3b2e36ca71f2        postgres:alpine                       "docker-entrypoint..."   55 minutes ago      Up 55 minutes       0.0.0.0:5432->5432/tcp                                  vagrant_db_1
3ef5ab52176b        redis:alpine                          "docker-entrypoint..."   55 minutes ago      Up 55 minutes       0.0.0.0:6379->6379/tcp                                  vagrant_cache_1
```

Run database migrations:

    python manage.py migrate

Create admin (superuser) user:

    python manage.py createsuperuser

Run application:

    python manage.py runserver 0.0.0.0:8000

Access API docs page and login:

    http://localhost:8000/swagger/

### Run Tests

Update Django settings so that it uses `test` module:

    export DJANGO_SETTINGS_MODULE=appdj.settings.test

Run tests:

    python manage.py test


### Swagger JSON file

http://127.0.0.1:8000/swagger/?format=openapi

## Dev Setup with Vagrant

### Note for Users with Windows

If you have Docker installed on Windows and wish to use Virtualbox as your Vagrant provider (enabled by default), then you will not be able to run both Docker and Vagrant at the same time as they both require Hyper-V. We have found the following work around the simplest to implement:

Log into Vagrant terminal with `vagrant ssh` and manage docker directly from the VM. If you want to access ports published by docker containers, you must have the right ports forwarded in your Vagrantfile. Edits need a `vagrant reload` for the changes to take effect.

Requirements:

- Vagrant may be used with several VM solutions. We recommend [VirtualBox](https://www.virtualbox.org/wiki/Downloads).
- [Vagrant](https://www.vagrantup.com/downloads.html)

> If using Windows 10, we recommend setting up [Ubuntu based bash shell](https://msdn.microsoft.com/en-us/commandline/wsl/install_guide) and run setup natively as described [in next section](https://github.com/3Blades/app-backend#native-dev-setup-on-linux-and-mac-systems). If using previous versions of Windows, consider using VirtualBox with Ubuntu Xenial (16.04).

Setup virtualenv on your host with Python 2.7:

    virtualenv -p python2.7 venv
    source venv/bin/activate

Launch Vagrant environment:

    vagrant up

Login to vagrant:

    vagrant ssh

Activate virtualenv:

    cd /vagrant
    source venv3/bin/activate

Run migration:

    python manage.py migrate

Create super user:

    python manage.py createsuperuser

Run application:

    python manage.py runserver 0.0.0.0:8000

Connect:

    http://localhost:8000/swagger

> You can change the IP address and forwarded port by changing the settings in the `Vagrantfile`.

## Trouble Shooting

### Environment variables

If you are running app-backend without docker, then you need to make sure all environment variables are set correctly. Verify by checking them with the echo command, such as:

    echo $DATABASE_URL

You can also view all configured environment variables with the `printenv` command.

To avoid having to set environment variables every time you log into the terminal, add them to your `.profile` file. This will automatically export environment variables when launching new bash terminals.

### Launch clean stack

Sometimes it will be necessary to re launch a fresh version of app-backend or full stack. There are several options, depending on how you launched your development environment.

With Vagrant, running `vagrant provision` will re run Vagrantfile commands which will in turn re run dependencies and re launch services. The `vagrant reload` command will restart your virtual machine. Our default configuration uses VirtualBox, so the Vagrantfile will use the VirtualBox provider to restart the Vagrant virtual machine. If you would like to start from scratch, the `vagrant destroy` command will remove your VM so that you can run `vagrant up` as if it were a fresh machine.

If using Vagrant installation option, you can log into your Vagrant VM with `vagrant ssh` and then run `docker-compose down` and then `docker-compose up -d` manually from the home directory. This would re launch containers without having to rung `vagrant provision` which is more time consuming. With Vagrant setup, `docker-compose.yml` and `env` files are copied to the vagrant user's home directory.

If setting up with Docker on Linux distribution, then you can do a `docker-compose down` and a `docker-compose up -d` but from the repositories root folder.

## Contributing

This project enforces the [Contributor Covenant](./CODE_OF_CONDUCT.md). Be kind
and build a nice open source community with us.


## Copyright and license

Copyright © 2016-2017 3Blades, LLC. All rights reserved, except as follows. Code
is released under the BSD 3.0 license. The README.md file, and files in the
"docs" folder are licensed under the Creative Commons Attribution 4.0
International License under the terms and conditions set forth in the file
"LICENSE.docs". You may obtain a duplicate copy of the same license, titled
CC-BY-SA-4.0, at http://creativecommons.org/licenses/by/4.0/.
