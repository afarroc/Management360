# initial_data.py
from faker import Faker
import random
import string
from django.contrib.auth.models import User

fake_en = Faker()
fake_es = Faker('es_ES')

def generate_random_username():
    """Genera un nombre de usuario aleatorio."""
    return 'setup_user_' + ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def generate_random_name(language, format='full'):
    """Genera un nombre aleatorio en el idioma especificado."""
    if language == 'english':
        fake = fake_en
    elif language == 'spanish':
        fake = fake_es
    else:
        raise ValueError('Idioma no soportado')

    if format == 'full':
        return fake.name()
    elif format == 'first_last':
        return f"{fake.first_name()} {fake.last_name()}"
    else:
        raise ValueError('Formato no soportado')


def generate_random_password(length=12):
    """Genera una contraseña aleatoria con la longitud especificada."""
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(chars, k=length))

DOMAIN_BASE = 'localhost'

def create_default_users():
    """Crea usuarios predeterminados."""
    user_data = []

    su_username = 'su'
    su_first_name = 'Superusuario'
    su_email = f'{su_username}@{DOMAIN_BASE}'
    su_password = generate_random_password()

    if not User.objects.filter(username=su_username).exists():
        User.objects.create_superuser(su_username, su_email, su_password)
        user_data.append({
        'username': su_username,
        'email': su_email,
        'password': su_password,
        'first_name': su_first_name,
        })

    user_username = generate_random_username()
    user_first_name = generate_random_name('spanish', format='first_last').split()[0]
    user_last_name = generate_random_name('spanish', format='first_last').split()[1]
    user_email = f'{user_username}@{DOMAIN_BASE}'
    user_password = generate_random_password()

    if not User.objects.filter(username=user_username).exists():
        User.objects.create_user(user_username, user_email, user_password)
        user_data.append({
        'username': user_username,
        'first_name': user_first_name,
        'last_name': user_last_name,
        'email': user_email,
        'password': user_password,
        })

        return user_data