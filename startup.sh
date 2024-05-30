#!/bin/bash
python manage.py migrate
python manage.py collectstatic --noinput
uwsgi --ini webapp.ini