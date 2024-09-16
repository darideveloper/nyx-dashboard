#!/bin/sh
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py apps_loaddata
gunicorn djcrm.wsgi --bind=0.0.0.0:80