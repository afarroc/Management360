#!/bin/bash
# Startup script for Django application with migration checks

echo "=== DJANGO APPLICATION STARTUP ==="

# Set Django settings
export DJANGO_SETTINGS_MODULE=panel.settings

# Function to check and run migrations if needed
check_migrations() {
    echo "Checking database migrations..."

    # Try to check if auth_user table exists
    python -c "
import os, sys, django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')

try:
    django.setup()
    from django.db import connection
    cursor = connection.cursor()

    # Check for auth_user table (works for both PostgreSQL and SQLite)
    if connection.vendor == 'postgresql':
        cursor.execute(\"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'auth_user');\")
    else:
        cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='auth_user';\")

    result = cursor.fetchone()
    table_exists = bool(result and result[0])

    if not table_exists:
        print('auth_user table missing, running migrations...')
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'migrate', '--no-input', '--verbosity=1'])
        print('Migrations completed successfully!')
    else:
        print('Database tables exist, proceeding with startup...')

except Exception as e:
    print(f'Error checking migrations: {e}')
    print('Attempting to run migrations anyway...')
    try:
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'migrate', '--no-input', '--verbosity=1'])
    except Exception as e2:
        print(f'Error running migrations: {e2}')
        print('Continuing with startup despite migration errors...')
}

# Run the migration check
check_migrations

echo "Starting Django application with Daphne..."
echo "=== APPLICATION READY ==="

# Start the application
exec daphne panel.asgi:application --port $PORT --bind 0.0.0.0