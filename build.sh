#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

#!/bin/bash
echo "=== DJANGO BUILD PROCESS ==="

# Set Django settings
export DJANGO_SETTINGS_MODULE=panel.settings

# Install Python dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --no-input --verbosity=1

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input --verbosity=1

# Build process complete
echo "[SUCCESS] Build completed successfully!"
echo "Database migrations applied and static files collected."
echo "=== BUILD COMPLETE ==="
