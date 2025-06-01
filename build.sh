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
    python manage.py migrate
fi

# Verify migrations were applied successfully
if python manage.py showmigrations | grep -q "\[ \]"; then
    echo "Warning: There are unapplied migrations!"
    python manage.py migrate --fake-initial
else
    echo "All migrations applied successfully"
fi