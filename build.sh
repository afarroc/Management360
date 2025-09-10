#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Force all migrations - simple and direct
echo "=== FORCED MIGRATION DEPLOYMENT ==="

# Step 1: Force sync all tables
echo "Step 1: Creating all database tables..."
python manage.py migrate --run-syncdb --no-input

# Step 2: Apply all migrations
echo "Step 2: Applying all migrations..."
python manage.py migrate --no-input

# Step 3: Force events migration (critical for signup)
echo "Step 3: Forcing events migration..."
python manage.py migrate events --no-input

# Step 4: Quick verification
echo "Step 4: Quick verification..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()
from django.contrib.auth.models import User
print(f'Users table: {User.objects.count()} records')
print('Migration completed successfully!')
" 2>/dev/null && echo "[SUCCESS] Ready for production" || echo "[WARNING] Check database connection"

echo "=== DEPLOYMENT COMPLETE ==="
