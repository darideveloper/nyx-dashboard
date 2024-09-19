#!/bin/bash
set -e

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start the server
exec gunicorn --bind 0.0.0.0:80 nyx_dashboard.wsgi:application
