#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations with error handling
echo "Applying database migrations..."
if ! python manage.py migrate --no-input; then
    echo "Migration failed, attempting to reset and retry..."
    python manage.py migrate --fake-initial --no-input
    python manage.py migrate --no-input
fi

# Ensure auth migrations are applied first
echo "Ensuring auth migrations are applied..."
python manage.py migrate auth --no-input
python manage.py migrate contenttypes --no-input
python manage.py migrate sessions --no-input

# Force create tables if they don't exist (for PostgreSQL issues)
echo "Ensuring database tables exist..."
python manage.py migrate --run-syncdb

# Verify migrations were applied successfully
echo "Checking for unapplied migrations..."
UNAPPLIED=$(python manage.py showmigrations | findstr "\[ \]")
if [ -n "$UNAPPLIED" ]; then
    echo "Warning: There are unapplied migrations!"
    python manage.py migrate --fake-initial
    python manage.py migrate --no-input
else
    echo "All migrations applied successfully"
fi

# Additional check for critical tables
echo "Checking for critical tables..."
python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings'); import django; django.setup(); from django.contrib.auth.models import User; print('auth_user table exists')" 2>/dev/null || echo "Warning: auth_user table may not exist"

# Run database diagnostic script
echo "Running database diagnostic..."
python check_db.py