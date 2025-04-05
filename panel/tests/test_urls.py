from django.test import TestCase
from django.urls import reverse, resolve
from django.test.utils import CaptureQueriesContext
from django.db import connection

class URLTests(TestCase):
    def test_admin_url(self):
        response = self.client.get('/admin/')
        self.assertIn(response.status_code, [200, 302])  # Accept redirection

    def test_app_urls(self):
        app_urls = [
            '/accounts/',
            '/chat/',
            '/cv/',
            '/events/',
            '/kpis/',  # Known 404
            '/memento/',
            '/passgen/',  # Known 404
            '/rooms/',
            '/tools/',  # Known 404
        ]
        for url in app_urls:
            response = self.client.get(url)
            if url in ['/kpis/', '/passgen/', '/tools/']:
                self.assertEqual(response.status_code, 404)  # Explicitly check for 404
                self.assertIn('Not Found', response.reason_phrase)  # Verify reason phrase
            else:
                self.assertIn(response.status_code, [200, 302])  # Accept success or redirection

    def test_api_urls(self):
        api_urls = [
            reverse('api-csrf'),
            reverse('api-login'),
            reverse('api-logout'),
            reverse('api-signup'),
            reverse('api-connection-token'),
            reverse('api-subscription-token'),
        ]
        for url in api_urls:
            with CaptureQueriesContext(connection) as queries:
                if url == reverse('api-login'):  # Test /api/login/ with required data
                    response = self.client.post(url, data={'username': 'test', 'password': 'test'})
                    self.assertIn(response.status_code, [200, 400, 401, 403])  # Expect success or auth errors
                    self.assertIn('application/json', response['Content-Type'])  # Ensure JSON response
                elif url in [reverse('api-connection-token'), reverse('api-subscription-token')]:
                    response = self.client.post(url)  # Test token endpoints
                    self.assertIn(response.status_code, [401, 403])  # Expect unauthorized or forbidden
                else:
                    response = self.client.post(url)  # Default POST request
                    self.assertIn(response.status_code, [200, 405, 400, 403])  # Accept method not allowed or bad request
                # Log the number of queries executed for debugging
                print(f"Queries executed for {url}: {len(queries)}")

# Run the tests
if __name__ == "__main__":
    import os
    os.system("python manage.py test panel.tests.test_urls")
