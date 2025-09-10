#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Comprehensive migration deployment with error handling
echo "=== COMPREHENSIVE MIGRATION DEPLOYMENT ==="

# Set Django settings module
export DJANGO_SETTINGS_MODULE=panel.settings

# Function to check if migrations were successful
check_migration_success() {
    echo "Checking migration success..."
    python -c "
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
sys.path.append('.')
django.setup()

try:
    from django.contrib.auth.models import User
    from django.db import connection
    cursor = connection.cursor()

    # Check if auth_user table exists
    cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='auth_user';\")
    if cursor.fetchone():
        print('[SUCCESS] auth_user table exists')
    else:
        print('[ERROR] auth_user table missing')
        sys.exit(1)

    # Check if we can create a test user
    if User.objects.filter(username='test_migration').exists():
        User.objects.filter(username='test_migration').delete()

    test_user = User.objects.create_user('test_migration', 'test@example.com', 'testpass123')
    test_user.save()
    test_user.delete()
    print('[SUCCESS] Database operations working correctly')

except Exception as e:
    print(f'[ERROR] Migration verification failed: {e}')
    sys.exit(1)
" 2>/dev/null

    if [ $? -eq 0 ]; then
        echo "[SUCCESS] All migrations applied successfully!"
        return 0
    else
        echo "[ERROR] Migration verification failed!"
        return 1
    fi
}

# Step 1: Create database tables if they don't exist
echo "Step 1: Ensuring database tables exist..."
python manage.py migrate --run-syncdb --no-input --verbosity=1
if [ $? -ne 0 ]; then
    echo "[WARNING] migrate --run-syncdb failed, continuing..."
fi

# Step 2: Apply Django core migrations first (most critical)
echo "Step 2: Applying Django core migrations..."
python manage.py migrate auth --no-input --verbosity=1
python manage.py migrate contenttypes --no-input --verbosity=1
python manage.py migrate sessions --no-input --verbosity=1
python manage.py migrate admin --no-input --verbosity=1

# Step 3: Apply events migration (critical for signup)
echo "Step 3: Applying events migration (critical for signup)..."
python manage.py migrate events --no-input --verbosity=1

# Step 4: Apply all remaining migrations
echo "Step 4: Applying all remaining migrations..."
python manage.py migrate --no-input --verbosity=1

# Step 5: Force sync one more time to ensure everything is created
echo "Step 5: Final database sync..."
python manage.py migrate --run-syncdb --no-input --verbosity=1

# Step 6: Verify migrations were successful
echo "Step 6: Verifying migration success..."
if check_migration_success; then
    echo "[SUCCESS] Database is ready for production!"
else
    echo "[ERROR] Database migration verification failed!"
    exit 1
fi

# Step 7: Create a migration check script for runtime
echo "Step 7: Creating runtime migration check..."
cat > check_migrations.py << 'EOF'
#!/usr/bin/env python
import os
import sys
import django

# Add current directory to path
sys.path.append('.')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

def check_and_run_migrations():
    """Check if migrations are needed and run them if necessary"""
    try:
        from django.core.management import execute_from_command_line
        from django.db import connection

        # Check if auth_user table exists
        cursor = connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_name = 'auth_user'
        """)

        if cursor.fetchone()[0] == 0:
            print("auth_user table missing, running migrations...")
            execute_from_command_line(['manage.py', 'migrate', '--no-input'])
            print("Migrations completed successfully!")
        else:
            print("Database tables exist, skipping migrations")

    except Exception as e:
        print(f"Error checking migrations: {e}")
        # Try to run migrations anyway
        try:
            execute_from_command_line(['manage.py', 'migrate', '--no-input'])
        except Exception as e2:
            print(f"Error running migrations: {e2}")

if __name__ == '__main__':
    check_and_run_migrations()
EOF

chmod +x check_migrations.py

echo "=== DEPLOYMENT COMPLETE ==="
echo "Database is ready for production!"
echo "Use 'python check_migrations.py' if you need to run migrations at runtime"
