from django.urls import resolve, reverse
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from .views import signup_view
from .forms import SignUpForm

class SignUpFormTests(TestCase):
    """Comprehensive tests for SignUpForm validation"""
    
    def setUp(self):
        self.valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!'
        }

    def test_form_fields(self):
        """Test form contains expected fields"""
        form = SignUpForm()
        self.assertEqual(
            list(form.fields.keys()),
            ['username', 'email', 'password1', 'password2']
        )

    def test_email_required(self):
        """Test email is required"""
        data = self.valid_data.copy()
        data.pop('email')
        form = SignUpForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_password_validation(self):
        """Test password validation rules"""
        # Too short
        data = self.valid_data.copy()
        data.update({'password1': 'short', 'password2': 'short'})
        form = SignUpForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

        # Mismatch
        data.update({'password2': 'mismatch'})
        form = SignUpForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_username_validation(self):
        """Test username constraints"""
        # Too long
        data = self.valid_data.copy()
        data['username'] = 'a' * 151
        form = SignUpForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_email_format_validation(self):
        """Test email format validation"""
        data = self.valid_data.copy()
        data['email'] = 'invalid-email'
        form = SignUpForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_duplicate_email(self):
        """Test email uniqueness"""
        User.objects.create_user(
            username='existing',
            email=self.valid_data['email'],
            password='testpass123'
        )
        form = SignUpForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

class SignUpViewTests(TestCase):
    """End-to-end tests for signup view"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('signup')
        self.valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!'
        }
        self.home_url = reverse('index')

    def test_get_request_rendering(self):
        """Test GET request renders correctly"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/signup.html')
        self.assertIsInstance(response.context['form'], SignUpForm)
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_successful_signup_flow(self):
        """Test complete successful signup flow"""
        response = self.client.post(
            self.url, 
            self.valid_data,
            follow=True
        )
        
        # Check redirect
        self.assertRedirects(response, self.home_url)
        
        # Check user creation
        self.assertTrue(User.objects.filter(
            username=self.valid_data['username'],
            email=self.valid_data['email']
        ).exists())
        
        # Check auto-login
        self.assertTrue(response.context['user'].is_authenticated)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('success' in message.tags for message in messages))

    def test_invalid_signup_attempts(self):
        """Test various invalid submissions"""
        test_cases = [
            ({}, "empty form"),
            (self.valid_data | {'password2': 'mismatch'}, "password mismatch"),
            (self.valid_data | {'email': 'invalid'}, "invalid email"),
            (self.valid_data | {'username': 'a'*151}, "long username")
        ]
        
        for data, description in test_cases:
            with self.subTest(description):
                response = self.client.post(self.url, data)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['form'].errors)
                self.assertFalse(User.objects.filter(
                    username=data.get('username', '')
                ).exists())

    def test_duplicate_email_protection(self):
        """Test duplicate email prevention"""
        # Create first user
        User.objects.create_user(
            username=self.valid_data['username'],
            email=self.valid_data['email'],
            password=self.valid_data['password1']
        )
        
        # Attempt duplicate email
        data = self.valid_data.copy()
        data['username'] = 'differentuser'
        response = self.client.post(self.url, data)
        
        # Should not create new user
        self.assertEqual(User.objects.count(), 1)
        
        # Should show form with errors
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertIn('email', response.context['form'].errors)

    def test_case_sensitive_username(self):
        """Test username case sensitivity"""
        # Create first user
        User.objects.create_user(
            username=self.valid_data['username'],
            email=self.valid_data['email'],
            password=self.valid_data['password1']
        )
        
        # Attempt different case username
        data = self.valid_data.copy()
        data['username'] = self.valid_data['username'].upper()
        response = self.client.post(self.url, data)
        
        # Should not create new user
        self.assertEqual(User.objects.count(), 1)
        
        # Should show form with errors
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertIn('username', response.context['form'].errors)

class SecurityTests(TestCase):
    """Security-related test cases"""
    
    def test_csrf_protection(self):
        """Test CSRF protection is enabled"""
        response = self.client.get(reverse('signup'))
        self.assertContains(response, 'csrfmiddlewaretoken')
        
        # Attempt POST without CSRF
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse('signup'), {})
        self.assertEqual(response.status_code, 403)

    def test_password_not_in_response(self):
        """Test passwords don't leak in responses"""
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'test',
                'email': 'test@example.com',
                'password1': 'should_not_see_this',
                'password2': 'should_not_see_this'
            },
            follow=True
        )
        self.assertNotContains(response, 'should_not_see_this')