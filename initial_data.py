# initial_data.py
from django.contrib.auth.models import User

def create_default_users():
    if not User.objects.filter(username='su').exists():
        User.objects.create_superuser('su', 'su@example.com', 'password_su')
    
    if not User.objects.filter(username='user').exists():
        User.objects.create_user('user', 'user@example.com', 'password_user')