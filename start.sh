#!/bin/sh

set -e

echo "Running migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:80 nyx_dashboard.wsgi:application
