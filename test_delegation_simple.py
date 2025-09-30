#!/usr/bin/env python3
"""
Simple test for inbox item delegation
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from events.models import InboxItem

def test_delegation():
    print('=== Testing Inbox Item Delegation ===')

    # Create test client
    client = Client()

    # Get or create admin user
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        print('Created admin user')
    else:
        print(f'Using admin: {admin_user.username}')

    # Login
    client.login(username=admin_user.username, password='admin123')
    print(f'Logged in as: {admin_user.username}')

    # Check if item exists
    try:
        item = InboxItem.objects.get(id=99)
        print(f'✓ Item 99 exists: {item.title}')
        print(f'  Currently assigned to: {item.assigned_to.username if item.assigned_to else "None"}')
    except InboxItem.DoesNotExist:
        print('✗ Item 99 does not exist')
        return False

    # Get available users
    available_users = User.objects.filter(is_active=True).exclude(id=item.assigned_to.id if item.assigned_to else None)
    if not available_users.exists():
        print('✗ No available users for delegation')
        return False

    target_user = available_users.first()
    print(f'Selected target user: {target_user.username} (ID: {target_user.id})')

    # Attempt delegation via bulk action
    bulk_url = reverse('inbox_admin_bulk_action')
    post_data = {
        'action': 'delegate',
        'selected_items': ['99'],
        'delegate_user_id': str(target_user.id)
    }

    print(f'POST to: {bulk_url}')
    print(f'Data: {post_data}')

    response = client.post(bulk_url, post_data)

    print(f'Response status: {response.status_code}')

    if response.status_code == 200:
        try:
            import json
            data = json.loads(response.content.decode('utf-8'))
            print(f'Response: {data}')

            if data.get('success'):
                print('✓ Delegation successful!')

                # Verify in database
                item.refresh_from_db()
                if item.assigned_to == target_user:
                    print('✓ Database updated correctly')
                    return True
                else:
                    print(f'✗ Database not updated. Still assigned to: {item.assigned_to.username if item.assigned_to else "None"}')
                    return False
            else:
                print(f'✗ Delegation failed: {data.get("error")}')
                return False
        except:
            print('Response is not JSON')
            print(response.content.decode('utf-8')[:500])
            return False
    else:
        print(f'✗ HTTP Error: {response.status_code}')
        print(response.content.decode('utf-8')[:500])
        return False

if __name__ == '__main__':
    success = test_delegation()
    print(f'\nTest result: {"PASSED" if success else "FAILED"}')
    sys.exit(0 if success else 1)