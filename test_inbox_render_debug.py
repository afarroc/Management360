#!/usr/bin/env python
"""
Test script to check inbox item detail admin view rendering and logs
"""
import os
import sys
import django
from django.test import Client
from django.contrib.auth.models import User

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

def test_inbox_detail_rendering():
    """Test the inbox item detail admin view rendering"""
    client = Client()

    # Login as admin user
    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            print("ERROR: No superuser found")
            return

        client.force_login(admin_user)
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
            if '<title>' in content:
                print("✓ HTML title found")
            else:
                print("✗ HTML title missing")

            # Check for item data
            if f'Item #{item_id}' in content:
                print(f"✓ Item {item_id} reference found")
            else:
                print(f"✗ Item {item_id} reference missing")

            # Check for specific data that should be rendered
            if 'created_by' in content:
                print("✓ Created by field found")
            else:
                print("✗ Created by field missing")

            # Look for any error messages
            if 'error' in content.lower():
                print("⚠ Warning: 'error' found in response")

            # Check for empty fields that might indicate missing data
            if 'None' in content and 'Asignado a:' in content:
                print("⚠ Warning: 'None' found in assigned to section")

            # Print a sample of the content to see what's being rendered
            print("\n--- Sample of rendered content ---")
            # Find the main content area
            start = content.find('<div class="card-body">')
            if start != -1:
                end = content.find('</div>', start + 100)
                if end != -1:
                    sample = content[start:end+6]
                    print(sample[:500] + "..." if len(sample) > 500 else sample)

        else:
            print(f"ERROR: Failed to load page. Status: {response.status_code}")
            print(f"Response content: {response.content.decode('utf-8')[:500]}...")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_inbox_detail_rendering()