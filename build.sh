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

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input --verbosity=1

# Build process complete - migrations will run in release command
echo "[SUCCESS] Build completed successfully!"
echo "Migrations will be applied automatically in the release phase."
echo "=== BUILD COMPLETE ==="
