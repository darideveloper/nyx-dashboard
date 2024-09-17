#!/bin/sh
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py apps_loaddata
gunicorn nyx_dashboard.wsgi --bind=0.0.0.0:80