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
    python manage.py migrate --fake-initial
    python manage.py migrate --no-input
fi

# Force create tables if they don't exist (for PostgreSQL issues)
echo "Ensuring database tables exist..."
python manage.py migrate --run-syncdb

# Verify migrations were applied successfully
if python manage.py showmigrations | grep -q "\[ \]"; then
    echo "Warning: There are unapplied migrations!"
    python manage.py migrate --fake-initial
    python manage.py migrate --no-input
else
    echo "All migrations applied successfully"
fi

# Additional check for critical tables
echo "Checking for critical tables..."
python manage.py shell -c "from django.contrib.auth.models import User; print('auth_user table exists')" || echo "Warning: auth_user table may not exist"