#!/bin/sh

set -e

sleep 1
/srv/env/bin/python /srv/app/manage.py migrate
/srv/env/bin/python /srv/app/manage.py create_admin
/srv/env/bin/python /srv/app/manage.py create_resource

exec "$@"
