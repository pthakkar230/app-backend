[![Build Status](https://travis-ci.org/3Blades/app-backend.svg?branch=master)](https://travis-ci.org/3Blades/app-backend)
[![Docker Hub](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com/r/3blades/app-backend/)
[![codecov](https://codecov.io/gh/3Blades/app-backend/branch/master/graph/badge.svg)](https://codecov.io/gh/3Blades/app-backend)
[![Code Climate](https://codeclimate.com/github/3Blades/app-backend/badges/gpa.svg)](https://codeclimate.com/github/3Blades/app-backend)
[![Code Health](https://landscape.io/github/3Blades/app-backend/master/landscape.svg?style=flat)](https://landscape.io/github/3Blades/app-backend/master)
[![Requirements Status](https://requires.io/github/3Blades/app-backend/requirements.svg?branch=master)](https://requires.io/github/3Blades/app-backend/requirements/?branch=master)
[![slack in](https://slackin-pypmyuhqds.now.sh/badge.svg)](https://slackin-pypmyuhqds.now.sh/)

# app-backend
#

Application server backend. Replaces hubserver.

Refer to [docs repo](https://github.com/3blades/docs) for installation instructions.

This project enforces the [Contributor Covenant](./CODE_OF_CONDUCT.md). Be kind
and build a nice open source community with us.

## Dev Setup

- `pip install -r requirements.txt`
- create new database for django
- run your database and redis
- add env variables: `DATABASE_URL`, `REDIS_URL`, `DJANGO_SETTINGS_MODULE=appdj.settings.dev`
- add env variable for hubserver database `OLD_DATABASE_URL`
- run `python manage.py migrate`
- run `python manage.py migrate_data $OLD_DATABASE_URL`
- run `python manage.py runserver`
- go to [http://localhost:8000/swagger/](http://localhost:8000/swagger/)


## Copyright and license

Copyright © 2016-2017 3Blades, LLC. All rights reserved, except as follows. Code
is released under the BSD 3.0 license. The README.md file, and files in the
"docs" folder are licensed under the Creative Commons Attribution 4.0
International License under the terms and conditions set forth in the file
"LICENSE.docs". You may obtain a duplicate copy of the same license, titled
CC-BY-SA-4.0, at http://creativecommons.org/licenses/by/4.0/.
