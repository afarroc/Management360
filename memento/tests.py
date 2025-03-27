from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from datetime import date, timedelta
from .models import MementoConfig
from .views import memento, calculate_memento_data
from .forms import MementoConfigForm

class MementoModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.birth_date = date(1990, 1, 1)
        self.death_date = date(2070, 1, 1)
        
    def test_memento_config_creation(self):
        config = MementoConfig.objects.create(
            user=self.user,
            birth_date=self.birth_date,
            death_date=self.death_date,
            preferred_frequency='monthly'
        )
        self.assertEqual(config.__str__(), f"Memento Config for {self.user.username}")

class MementoViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.birth_date = date(1990, 1, 1)
        self.death_date = date(2070, 1, 1)
        
    def test_calculate_memento_data(self):
        data = calculate_memento_data(self.birth_date, self.death_date)
        self.assertIn('total_days', data)
        self.assertIn('passed_days', data)
        self.assertIn('left_days', data)
        self.assertTrue(data['total_days'] > 0)
        
    def test_memento_view_without_params(self):
        request = self.factory.get('/memento/')
        request.user = self.user
        response = memento(request)
        self.assertEqual(response.status_code, 200)
        
    def test_memento_view_with_params(self):
        request = self.factory.get(f'/memento/monthly/{self.birth_date}/{self.death_date}/')
        request.user = self.user
        response = memento(request, 'monthly', str(self.birth_date), str(self.death_date))
        self.assertEqual(response.status_code, 200)

class MementoFormTest(TestCase):
    def test_valid_form(self):
        form_data = {
            'frequency': 'monthly',
            'birth_date': '1990-01-01',
            'death_date': '2070-01-01'
        }
        form = MementoConfigForm(data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_invalid_dates(self):
        form_data = {
            'frequency': 'monthly',
            'birth_date': '2070-01-01',
            'death_date': '1990-01-01'
        }
        form = MementoConfigForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('death_date', form.errors)