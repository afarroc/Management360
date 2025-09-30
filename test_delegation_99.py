#!/usr/bin/env python3
"""
Test script for delegating inbox item 99 to another user
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
    print('=== Testing Delegation of Inbox Item 99 ===')

    # Create test client
    client = Client()

    # Use 'admin' user (superuser)
    admin_user = User.objects.get(username='admin')
    print(f'Using admin user: {admin_user.username}')

    # Login
    client.login(username='admin', password='admin123')
    print('Logged in successfully')

    # Check item 99
    item = InboxItem.objects.get(id=99)
    print(f'Item 99: {item.title}')
    print(f'Currently assigned to: {item.assigned_to.username if item.assigned_to else "None"}')

    # Get available users (exclude current assignee)
    available_users = User.objects.filter(is_active=True).exclude(
        id=item.assigned_to.id if item.assigned_to else None
    )
    print(f'Available users for delegation: {available_users.count()}')

    # Select target user (first available)
    target_user = available_users.first()
    print(f'Selected target user: {target_user.username} (ID: {target_user.id})')

    # Test 1: Access the detail page
    print('\n--- Test 1: Access Detail Page ---')
    url = reverse('inbox_item_detail_admin', kwargs={'item_id': 99})
    response = client.get(url)
    print(f'Detail page status: {response.status_code}')

    if response.status_code == 200:
        print('Detail page accessible')
    else:
        print(f'Error accessing detail page: {response.status_code}')
        return False

    # Test 2: Attempt delegation
    print('\n--- Test 2: Attempt Delegation ---')
    bulk_url = reverse('inbox_admin_bulk_action')
    post_data = {
        'action': 'delegate',
        'selected_items': ['99'],
        'delegate_user_id': str(target_user.id)
    }

    print(f'POST URL: {bulk_url}')
    print(f'POST data: {post_data}')

    response = client.post(bulk_url, post_data)

    print(f'Response status: {response.status_code}')

    if response.status_code == 200:
        try:
            import json
            data = json.loads(response.content.decode('utf-8'))
            print(f'Response data: {data}')

            if data.get('success'):
                print('SUCCESS: Delegation completed!')

                # Verify in database
                item.refresh_from_db()
                if item.assigned_to == target_user:
                    print('VERIFIED: Item reassigned in database')
                    print(f'New assignee: {item.assigned_to.username}')
                    return True
                else:
                    print(f'ERROR: Item still assigned to: {item.assigned_to.username if item.assigned_to else "None"}')
                    return False
            else:
                print(f'FAILED: {data.get("error", "Unknown error")}')
                return False

        except json.JSONDecodeError:
            print('Response is not JSON')
            print(response.content.decode('utf-8')[:500])
            return False
    else:
        print(f'HTTP Error: {response.status_code}')
        print(response.content.decode('utf-8')[:500])
        return False

if __name__ == '__main__':
    success = test_delegation()
    print(f'\nTest result: {"PASSED" if success else "FAILED"}')
    sys.exit(0 if success else 1)