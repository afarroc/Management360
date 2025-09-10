#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "=== DJANGO BUILD PROCESS ==="

# Set Django settings
export DJANGO_SETTINGS_MODULE=panel.settings

# Install Python dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Apply database migrations in correct order
echo "Applying database migrations..."

# First, apply Django core migrations (auth, contenttypes, sessions)
echo "Applying Django core migrations..."
python manage.py migrate auth --verbosity=1
python manage.py migrate contenttypes --verbosity=1
python manage.py migrate sessions --verbosity=1

# Then apply all other migrations
echo "Applying remaining migrations..."
python manage.py migrate --no-input --verbosity=1

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input --verbosity=1

# Build process complete
echo "[SUCCESS] Build completed successfully!"
echo "Database migrations applied and static files collected."
echo "=== BUILD COMPLETE ==="
