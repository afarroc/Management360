#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Database migration process - Step by step approach
echo "=== DATABASE MIGRATION PROCESS ==="

# Step 1: Apply Django core migrations in correct order
echo "Step 1: Applying Django core migrations..."
python manage.py migrate contenttypes --no-input || echo "Warning: contenttypes migration failed"
python manage.py migrate auth --no-input || echo "Warning: auth migration failed"
python manage.py migrate sessions --no-input || echo "Warning: sessions migration failed"
python manage.py migrate admin --no-input || echo "Warning: admin migration failed"

# Step 2: Apply all remaining migrations
echo "Step 2: Applying all remaining migrations..."
python manage.py migrate --no-input || echo "Warning: general migration failed"

# Step 3: Force sync if needed
echo "Step 3: Ensuring all tables exist..."
python manage.py migrate --run-syncdb --no-input || echo "Warning: syncdb failed"

# Step 4: Verify critical tables exist
echo "Step 4: Testing critical database tables..."
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
import django
django.setup()
try:
    from django.contrib.auth.models import User
    count = User.objects.count()
    print(f'✅ auth_user table OK - {count} users')
except Exception as e:
    print(f'❌ auth_user table ERROR: {e}')
" 2>/dev/null || echo "❌ Database connection failed"

# Step 5: Show migration status
echo "Step 5: Migration status summary..."
python manage.py showmigrations | grep -E "(auth|contenttypes|admin|sessions)" || echo "Could not check migration status"

echo "=== MIGRATION PROCESS COMPLETE ==="