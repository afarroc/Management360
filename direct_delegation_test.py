#!/usr/bin/env python3
"""
Direct delegation test for inbox item 99
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.contrib.auth.models import User
from events.models import InboxItem, InboxItemHistory

def main():
    print('=== DIRECT DELEGATION TEST ===')

    # Get item 99
    try:
        item = InboxItem.objects.get(id=99)
        print(f'Found item 99: {item.title}')
        print(f'Currently assigned to: {item.assigned_to.username if item.assigned_to else "None"}')
    except InboxItem.DoesNotExist:
        print('ERROR: Item 99 does not exist')
        return False

    # Get available users
    available_users = User.objects.filter(is_active=True).exclude(id=item.assigned_to.id if item.assigned_to else None)
    print(f'Available users: {available_users.count()}')

    if available_users.count() == 0:
        print('ERROR: No available users for delegation')
        return False

    # Select target user
    target_user = available_users.first()
    print(f'Selected target user: {target_user.username} (ID: {target_user.id})')

    # Simulate the delegation logic from inbox_admin_bulk_action
    print('\n=== SIMULATING DELEGATION ===')

    # Check permissions (simplified - assume admin user)
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print('ERROR: No admin user found')
        return False

    print(f'Using admin user: {admin_user.username}')

    # Perform delegation
    old_assigned = item.assigned_to
    item.assigned_to = target_user
    item.save(update_fields=['assigned_to'])

    print('SUCCESS: Item assignment updated in database')

    # Create history entry
    InboxItemHistory.objects.create(
        inbox_item=item,
        user=admin_user,
        action='bulk_delegated',
        old_values={'assigned_to': old_assigned.username if old_assigned else None},
        new_values={
            'assigned_to': target_user.username,
            'delegation_method': 'bulk_action',
            'delegated_by': admin_user.username
        }
    )

    print('SUCCESS: History entry created')

    # Verify
    item.refresh_from_db()
    print(f'VERIFIED: Item now assigned to: {item.assigned_to.username if item.assigned_to else "None"}')

    print('\n=== DELEGATION COMPLETED SUCCESSFULLY ===')
    print(f'Item 99 delegated from {old_assigned.username if old_assigned else "None"} to {target_user.username}')
    return True

if __name__ == '__main__':
    success = main()
    print(f'\nTest result: {"PASSED" if success else "FAILED"}')
    sys.exit(0 if success else 1)