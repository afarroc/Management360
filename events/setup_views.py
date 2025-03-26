from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.core.exceptions import ValidationError
from cv.models import Curriculum as Profile
from .utils import create_user_profile
from .initial_data import generate_random_name, generate_random_username
import random
import string

 # setup_views.py (fragmento completo corregido)
from cv.forms import CurriculumForm as ProfileForm  # Asegurar esta importación


DOMAIN_BASE = 'localhost'

def generate_random_password(length=12):
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(chars, k=length))

class SetupView(View):
    template_name = 'setup/setup.html'

    def get(self, request):
        if not request.user.is_authenticated:
            step = request.GET.get('step', '1')
        elif request.user.is_superuser:
            step = request.GET.get('step', '5')
        else:
            step = 'login'

        completed_steps = []

        if User.objects.filter(username='su').exists():
            completed_steps.append('1')

        if request.user.is_authenticated and Profile.objects.filter(user=request.user).exists():
            completed_steps.append('2')

        all_groups = Group.objects.all()
        all_users = User.objects.all()

        return render(request, self.template_name, {
            'page_title': 'Setup',
            'step': step,
            'completed_steps': completed_steps,
            'all_groups': all_groups,
            'all_users': all_users,
        })

    def post(self, request):
        if 'create_su' in request.POST:
            if not User.objects.filter(username='su').exists():
                username = 'su'
                first_name = 'Superusuario'
                email = f'{username}@{DOMAIN_BASE}'
                password = generate_random_password()
                superuser = User.objects.create_superuser(username, email, password, first_name=first_name)
                superuser.save()
                messages.success(request, f'Superusuario creado: su, contraseña: {password}')
                user = authenticate(username='su', password=password)
                if user is not None:
                    login(request, user)
                    request.session.setdefault('first_session', True)
                    return redirect(reverse('setup') + '?step=2')
            else:
                messages.info(request, 'El superusuario ya existe. Por favor, inicie sesión.')
                return redirect(reverse('setup') + '?step=login')

        elif 'login_su' in request.POST:
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect(reverse('setup') + '?step=2')
            else:
                messages.error(request, 'Credenciales incorrectas.')


        elif 'create_profile' in request.POST:
            try:
                su = User.objects.get(username='su')
                form = ProfileForm(
                    data=request.POST,
                    files=request.FILES,
                    instance=su.profile if hasattr(su, 'profile') else None
                )
                if form.is_valid():
                    profile = form.save(commit=False)
                    profile.user = su  # Asignar usuario solo si es nuevo
                    profile.save()
                    messages.success(request, 'Perfil actualizado con éxito.')
                    return redirect(reverse('setup') + '?step=3')
                else:
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(request, f"{field}: {error}")
            except User.DoesNotExist:
                messages.error(request, 'Superusuario no existe. Cree uno primero.')
            except Exception as e:
                messages.error(request, f'Error crítico: {str(e)}')
            return redirect(reverse('setup') + '?step=2')
        
        elif 'create_random_users' in request.POST:
            domain = request.POST['domain']
            num_users = int(request.POST['num_users'])
            group_name = request.POST.get('new_group_name')  # Nombre del nuevo grupo (si se proporciona)
            group_id = request.POST.get('group_id')  # Grupo seleccionado para asignar usuarios
            user_data = []

            if group_name:
                group, created = Group.objects.get_or_create(name=group_name)
            elif group_id:
                group = Group.objects.get(id=group_id)
            else:
                group = None

            for _ in range(num_users):
                username = generate_random_username()
                first_name = generate_random_name('spanish', format='first_last').split()[0]
                last_name = generate_random_name('spanish', format='first_last').split()[1]
                email = f'{username}@{domain}'
                password = generate_random_password()

                if not User.objects.filter(username=username).exists():
                    user = User.objects.create_user(username, email, password)
                    user.first_name = first_name
                    user.last_name = last_name
                    user.save()
                    user_data.append({
                        'username': username,
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': email,
                        'password': password,
                    })

                    # Asignar el usuario al grupo si se seleccionó uno
                    if group:
                        user.groups.add(group)

            messages.success(request, 'Usuarios creados con éxito.')
            completed_steps = ['1', '2', '3']
            all_groups = Group.objects.all()
            all_users = User.objects.all()
            return render(request, self.template_name, {
                'page_title': 'Crear Usuarios Aleatorios',
                'user_data': user_data,
                'step': '4',
                'completed_steps': completed_steps,
                'all_groups': all_groups,
                'all_users': all_users,
            })

        elif 'create_group' in request.POST:
            group_name = request.POST['group_name']
            usernames = request.POST.getlist('usernames')
            group, created = Group.objects.get_or_create(name=group_name)
            for username in usernames:
                user = User.objects.get(username=username)
                user.groups.add(group)
            messages.success(request, f'Grupo {group_name} creado y usuarios asignados.')
            completed_steps = ['1', '2', '3', '4']
            return redirect(reverse('setup') + '?step=5')

        elif 'create_another_su' in request.POST:
            su_username = request.POST['su_username']
            su_email = request.POST['su_email']
            su_password = generate_random_password()
            if not User.objects.filter(username=su_username).exists():
                superuser = User.objects.create_superuser(su_username, su_email, su_password)
                superuser.save()
                messages.success(request, f'Superusuario creado: {su_username}, contraseña: {su_password}')
            else:
                messages.error(request, 'El nombre de usuario ya existe.')

        return redirect(reverse('setup'))