#!/usr/bin/env python
"""
Test script to check inbox item detail admin view with authentication
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

def test_inbox_detail_with_auth():
    """Test the inbox item detail admin view with authentication"""
    client = Client()

    # Login as admin user
    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            print("ERROR: No superuser found")
            return

        # Login
        login_success = client.login(username=admin_user.username, password='admin123')  # Try common password
        if not login_success:
            # Try alternative login method
            client.force_login(admin_user)
            print(f"Forced login as: {admin_user.username}")
        else:
            print(f"Logged in as: {admin_user.username}")

        # Test item 99 (the one we know exists)
        item_id = 99
        url = f'/events/inbox/admin/{item_id}/'

        print(f"Testing URL: {url}")

        response = client.get(url)

        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            print("SUCCESS: Page loaded successfully")

            # Check if key content is present
            content = response.content.decode('utf-8')

            # Check for basic HTML structure
            if 'Inbox Item Details' in content:
                print("✓ Page title found")
            else:
                print("✗ Page title not found")

            # Check for item data
            if f'Item #{item_id}' in content:
                print(f"✓ Item {item_id} reference found")
            else:
                print(f"✗ Item {item_id} reference missing")

            # Check for specific data that should be rendered
            if 'system' in content:
                print("✓ Created by 'system' found")
            else:
                print("✗ Created by 'system' not found")

            # Check for email content
            if 'arturo.farro@outlook.com' in content:
                print("✓ Email content found")
            else:
                print("✗ Email content missing")

            # Check for available users
            if 'available_users' in content or 'delegateModal' in content:
                print("✓ Delegation modal found")
            else:
                print("✗ Delegation modal missing")

            # Look for any error messages
            if 'error' in content.lower():
                print("⚠ Warning: 'error' found in response")

            print("\n--- Sample of key content ---")
            # Extract key sections
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'Item #99' in line:
                    print(f"Line {i}: {line.strip()}")
                elif 'created_by' in line and 'system' in line:
                    print(f"Line {i}: {line.strip()}")
                elif 'arturo.farro@outlook.com' in line:
                    print(f"Line {i}: {line.strip()}")

        else:
            print(f"ERROR: Failed to load page. Status: {response.status_code}")
            print(f"Response content: {response.content.decode('utf-8')[:500]}...")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_inbox_detail_with_auth()