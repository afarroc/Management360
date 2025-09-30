#!/usr/bin/env python3
"""
Django TestCase for inbox item delegation
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from events.models import InboxItem

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

class InboxDelegationTest(TestCase):
    def setUp(self):
        # Create test users
        self.admin_user = User.objects.create_superuser(
            username='test_admin',
            email='admin@test.com',
            password='test123'
        )

        self.target_user = User.objects.create_user(
            username='target_user',
            email='target@test.com',
            password='target123'
        )

        # Get or create inbox item 99
        self.item, created = InboxItem.objects.get_or_create(
            id=99,
            defaults={
                'title': 'Test Item for Delegation',
                'description': 'Test description',
                'created_by': self.admin_user,
                'gtd_category': 'pendiente',
                'priority': 'media'
            }
        )

        if created:
            print(f'Created test item 99: {self.item.title}')
        else:
            print(f'Using existing item 99: {self.item.title}')

        self.client = Client()

    def test_delegation_workflow(self):
        """Test the complete delegation workflow"""
        print('\n=== Testing Delegation Workflow ===')

        # Login
        login_success = self.client.login(username='test_admin', password='test123')
        self.assertTrue(login_success, "Login should succeed")
        print('✓ Login successful')

        # Access detail page
        url = reverse('inbox_item_detail_admin', kwargs={'item_id': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "Detail page should be accessible")
        print('✓ Detail page accessible')

        # Check that delegation form is present
        self.assertIn('delegate_user', response.content.decode(), "Delegation form should be present")
        print('✓ Delegation form found')

        # Attempt delegation
        bulk_url = reverse('inbox_admin_bulk_action')
        post_data = {
            'action': 'delegate',
            'selected_items': ['99'],
            'delegate_user_id': str(self.target_user.id)
        }

        response = self.client.post(bulk_url, post_data)

        print(f'Delegation response status: {response.status_code}')

        # Check response
        if response.status_code == 200:
            try:
                import json
                data = json.loads(response.content.decode('utf-8'))
                print(f'Response data: {data}')

                self.assertTrue(data.get('success'), f"Delegation should succeed: {data.get('error', 'Unknown error')}")
                print('✓ Delegation API call successful')

                # Verify in database
                self.item.refresh_from_db()
                self.assertEqual(self.item.assigned_to, self.target_user, "Item should be assigned to target user")
                print('✓ Database assignment verified')

                print(f'SUCCESS: Item 99 delegated from {self.admin_user.username} to {self.target_user.username}')

            except json.JSONDecodeError:
                self.fail(f"Response should be JSON, got: {response.content.decode('utf-8')[:500]}")
        else:
            self.fail(f"Delegation request failed with status {response.status_code}: {response.content.decode('utf-8')[:500]}")

if __name__ == '__main__':
    import unittest

    # Run the test
    suite = unittest.TestLoader().loadTestsFromTestCase(InboxDelegationTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        print('\n🎉 ALL TESTS PASSED!')
        sys.exit(0)
    else:
        print(f'\n❌ {len(result.failures)} test(s) failed')
        sys.exit(1)