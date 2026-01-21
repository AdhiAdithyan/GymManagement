#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Running Migrations..."
python manage.py migrate --no-input

echo "Creating Superuser..."
python create_superuser.py || echo "Superuser creation skipped or failed (might already exist)"

echo "Creating Demo Tenant..."
python manage.py create_demo_tenant || echo "Demo tenant creation skipped (might already exist)"

echo "Starting Gunicorn..."
gunicorn gym_management.wsgi
