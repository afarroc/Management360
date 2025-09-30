#!/usr/bin/env python3
"""
Test script for delegating inbox item 99 using HTTP requests to the running server
"""

import requests
import json

def test_delegation_http():
    print('=== Testing Delegation of Inbox Item 99 via HTTP ===')

    base_url = 'http://192.168.18.47:5000'
    session = requests.Session()

    # Step 1: Get login page and CSRF token
    print('\n--- Step 1: Login ---')
    try:
        login_page_url = f'{base_url}/accounts/login/'
        response = session.get(login_page_url)

        if response.status_code != 200:
            print(f'Failed to get login page: {response.status_code}')
            return False

        # Extract CSRF token
        csrf_token = None
        if 'csrfmiddlewaretoken' in response.text:
            # Simple extraction - look for the token in the form
            import re
            match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text)
            if match:
                csrf_token = match.group(1)
                print(f'CSRF token obtained: {csrf_token[:10]}...')
            else:
                print('CSRF token not found in login page')
                return False
        else:
            print('No CSRF token found')
            return False

        # Try different admin users and passwords
        admin_credentials = [
            ('admin', 'admin123'),
            ('su', 'su123'),
            ('so', 'so123'),
            ('admin', 'admin'),
            ('su', 'su'),
        ]

        login_success = False
        for username, password in admin_credentials:
            print(f'Trying login with {username}...')
            login_data = {
                'username': username,
                'password': password,
                'csrfmiddlewaretoken': csrf_token
            }

            login_response = session.post(login_page_url, data=login_data)

            if login_response.url and 'login' not in login_response.url.lower():
                print(f'Login successful with {username}')
                login_success = True
                break
            else:
                print(f'Login failed for {username}')

        if not login_success:
            print('All login attempts failed')
            return False

        login_response = session.post(login_page_url, data=login_data)

        if login_response.status_code != 200:
            print(f'Login failed with status: {login_response.status_code}')
            print(f'Response: {login_response.text[:200]}')
            return False

        # Check if login was successful by looking for redirect or success indicators
        if 'login' in login_response.url.lower():
            print('Login failed - still on login page')
            return False

        print('Login successful')

    except Exception as e:
        print(f'Login error: {e}')
        return False

    # Step 2: Access the inbox item detail page
    print('\n--- Step 2: Access Detail Page ---')
    try:
        detail_url = f'{base_url}/events/inbox/admin/99/'
        response = session.get(detail_url)

        print(f'Detail page URL: {detail_url}')
        print(f'Status: {response.status_code}')

        if response.status_code == 200:
            print('Successfully accessed detail page')

            # Check for delegation elements
            if 'delegate_user' in response.text:
                print('Delegation form found')
            else:
                print('WARNING: Delegation form not found')

            if 'available_users' in response.text or 'select' in response.text:
                print('User selection elements found')
            else:
                print('WARNING: User selection elements not found')

        else:
            print(f'Failed to access detail page: {response.status_code}')
            print(f'Response: {response.text[:500]}')
            return False

    except Exception as e:
        print(f'Error accessing detail page: {e}')
        return False

    # Step 3: Attempt delegation
    print('\n--- Step 3: Attempt Delegation ---')
    try:
        # Get CSRF token from the detail page
        csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text)
        if csrf_match:
            csrf_token = csrf_match.group(1)
            print(f'CSRF token from detail page: {csrf_token[:10]}...')
        else:
            print('No CSRF token found in detail page')
            return False

        # Try delegation via bulk action
        bulk_url = f'{base_url}/events/inbox/admin/bulk-action/'
        print(f'Bulk action URL: {bulk_url}')

        # Prepare data as form-encoded string (like the JavaScript does)
        delegate_data = f'action=delegate&selected_items=99&delegate_user_id=1'

        print(f'Delegation data: {delegate_data}')

        response = session.post(bulk_url, data=delegate_data, headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrf_token
        })

        print(f'Delegation response status: {response.status_code}')

        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f'Response JSON: {response_data}')

                if response_data.get('success'):
                    print('SUCCESS: Delegation completed!')
                    print(f'Message: {response_data.get("message", "N/A")}')
                    print(f'Count: {response_data.get("count", "N/A")}')
                    print(f'Delegate user: {response_data.get("delegate_user", "N/A")}')
                    return True
                else:
                    print(f'FAILED: {response_data.get("error", "Unknown error")}')
                    return False

            except json.JSONDecodeError:
                print('Response is not JSON')
                print(f'Raw response: {response.text[:500]}')
                return False
        else:
            print(f'HTTP Error: {response.status_code}')
            print(f'Response: {response.text[:500]}')
            return False

    except Exception as e:
        print(f'Error during delegation: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_delegation_http()
    print(f'\nTest result: {"PASSED" if success else "FAILED"}')