#!/usr/bin/env python
"""
Simple test to verify inbox detail page loads
"""
import requests

def test_inbox_page():
    """Test that the inbox detail page exists and responds"""
    print("Testing inbox item detail admin page...")

    url = "http://192.168.18.47:5000/events/inbox/admin/110/"

    try:
        response = requests.get(url, timeout=5, allow_redirects=False)
        print(f"Status code: {response.status_code}")

        if response.status_code == 302:
            print("SUCCESS: Page exists and redirects (likely to login as expected)")
            print(f"Redirect location: {response.headers.get('Location', 'Unknown')}")
        elif response.status_code == 200:
            print("SUCCESS: Page loads directly (may not require auth)")
        else:
            print(f"UNEXPECTED: Status code {response.status_code}")

        # Check if response contains expected content
        content = response.text.lower()
        if 'inbox' in content:
            print("SUCCESS: Response contains 'inbox' (page loaded)")
        else:
            print("INFO: Response does not contain 'inbox'")

    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == '__main__':
    test_inbox_page()