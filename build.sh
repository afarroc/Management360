#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

#!/bin/bash
echo "=== SIMPLE MIGRATION BUILD ==="

# Set Django settings
export DJANGO_SETTINGS_MODULE=panel.settings

# Simple and direct migration approach
echo "Running Django migrations..."
python manage.py migrate --no-input --verbosity=1

# Verify critical tables exist
echo "Verifying critical tables..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

try:
    from django.contrib.auth.models import User
    from django.apps import apps

    # Check if User model can be queried (implies table exists)
    user_count = User.objects.count()
    print(f'[SUCCESS] Database ready! Users table accessible. Current users: {user_count}')

except Exception as e:
    print(f'[ERROR] Database check failed: {e}')
    exit 1
" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "[SUCCESS] Build completed successfully!"
else
    echo "[ERROR] Build failed!"
    exit 1
fi

echo "=== BUILD COMPLETE ==="
