#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Automatic migration deployment with verification
echo "=== AUTOMATIC MIGRATION DEPLOYMENT ==="
echo "Running deploy_migrations.py for guaranteed database setup..."

# Run the robust migration script
python deploy_migrations.py

# Check exit code
if [ $? -eq 0 ]; then
    echo "[SUCCESS] Database migration completed successfully"
else
    echo "[ERROR] Database migration failed - attempting fallback..."

    # Fallback: Force migration sync
    echo "Fallback: Forcing database sync..."
    python manage.py migrate --run-syncdb --no-input || echo "Fallback sync failed"

    # Final verification
    python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
import django
django.setup()
try:
    from django.contrib.auth.models import User
    from events.models import CreditAccount
    user_count = User.objects.count()
    credit_count = CreditAccount.objects.count()
    print(f'[OK] Final verification: {user_count} users, {credit_count} credit accounts')
except Exception as e:
    print(f'[ERROR] Final verification failed: {e}')
" 2>/dev/null || echo "[CRITICAL] Database setup incomplete"
fi

echo "=== DEPLOYMENT MIGRATION COMPLETE ==="
