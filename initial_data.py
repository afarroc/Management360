import random
import string
from django.contrib.auth.models import User

def generate_random_username():
    return 'user_' + ''.join(random.choices(string.ascii_letters + string.digits, k=6))

def generate_random_password(length=12):
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(chars, k=length))

DOMAIN_BASE = 'example.com'

def create_default_users():
    user_data = []

    su_username = 'su'
    su_email = f'{su_username}@{DOMAIN_BASE}'
    su_password = generate_random_password()

    if not User.objects.filter(username=su_username).exists():
        User.objects.create_superuser(su_username, su_email, su_password)
        user_data.append({
            'username': su_username,
            'email': su_email,
            'password': su_password,
        })

    user_username = generate_random_username()
    user_email = f'{user_username}@{DOMAIN_BASE}'
    user_password = generate_random_password()

    if not User.objects.filter(username=user_username).exists():
        User.objects.create_user(user_username, user_email, user_password)
        user_data.append({
            'username': user_username,
            'email': user_email,
            'password': user_password,
        })

    return user_data
