#!/bin/sh

set -e

/srv/env/bin/python /srv/app/manage.py migrate
/srv/env/bin/python /srv/app/manage.py create_admin

exec "$@"
