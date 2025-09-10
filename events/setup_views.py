from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.urls import reverse
from django.core.exceptions import ValidationError
from cv.models import Curriculum as Profile
from .utils import create_user_profile
from .initial_data import generate_random_name, generate_random_username, create_initial_statuses  # Añadir import aquí
from .models import Status, ProjectStatus, TaskStatus
import random
import string

DOMAIN_BASE = 'localhost'

def generate_random_password(length=12):
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(chars, k=length))

class SetupView(View):
    template_name = 'setup/setup.html'

    def get(self, request):
        print("=== GET REQUEST RECIBIDO EN SetupView ===")
        print(f"Request method: {request.method}")
        print(f"Request path: {request.path}")
        print(f"GET params: {dict(request.GET)}")
        print(f"User: {request.user} (authenticated: {request.user.is_authenticated})")

        if not request.user.is_authenticated:
            step = request.GET.get('step', '1')
        elif request.user.is_superuser:
            step = request.GET.get('step', '5')
        else:
            step = 'login'

        completed_steps = []

        # Check if superuser exists (handle missing table)
        try:
            if User.objects.filter(username='su').exists():
                completed_steps.append('1')
        except Exception as e:
            # Table might not exist yet, skip this check
            pass

        # Check if user profile exists
        try:
            if request.user.is_authenticated and Profile.objects.filter(user=request.user).exists():
                completed_steps.append('2')
        except Exception as e:
            # Table might not exist yet, skip this check
            pass

        # Get all groups and users (handle missing tables)
        try:
            all_groups = Group.objects.all()
        except Exception as e:
            all_groups = []

        try:
            all_users = User.objects.all()
        except Exception as e:
            all_users = []

        # Check if statuses exist
        try:
            if Status.objects.exists() and ProjectStatus.objects.exists() and TaskStatus.objects.exists():
                completed_steps.append('3')
        except Exception as e:
            # Tables might not exist yet, skip this check
            pass

        return render(request, self.template_name, {
            'page_title': 'Setup',
            'step': step,
            'completed_steps': completed_steps,
            'all_groups': all_groups,
            'all_users': all_users,
        })

    def post(self, request):
        print("=== POST REQUEST RECIBIDO EN SetupView ===")
        print(f"Request method: {request.method}")
        print(f"Request path: {request.path}")
        print(f"POST data keys: {list(request.POST.keys())}")
        print(f"FILES data keys: {list(request.FILES.keys()) if request.FILES else None}")
        print(f"User: {request.user} (authenticated: {request.user.is_authenticated})")

        # Check for superuser creation request - multiple detection methods for robustness
        create_su_triggered = (
            'create_su' in request.POST or
            'create_su_btn' in request.POST or
            request.POST.get('create_su') == 'Create Superuser' or
            request.POST.get('create_su_btn') == 'Create Superuser'
        )

        if create_su_triggered:
            print("=== INICIO PROCESO CREACIÓN SUPERUSUARIO ===")
            print("PASO 1: Verificando POST data - 'create_su' en request.POST:", 'create_su' in request.POST)
            print("PASO 1: Valor de 'create_su':", repr(request.POST.get('create_su', 'NOT FOUND')))
            print("PASO 1: Verificando 'create_su_btn' en request.POST:", 'create_su_btn' in request.POST)
            print("PASO 1: Valor de 'create_su_btn':", repr(request.POST.get('create_su_btn', 'NOT FOUND')))
            print("PASO 1: ¿Se activó creación de superusuario?:", create_su_triggered)
            print("PASO 1: ✓ Botón 'create_su' detectado en POST request")
            try:
                print("PASO 2: Verificando existencia del superusuario 'su'")
                superuser_exists = User.objects.filter(username='su').exists()
                print(f"PASO 2: Superusuario 'su' existe: {superuser_exists}")

                if not superuser_exists:
                    print("PASO 2: ✓ Superusuario no existe, procediendo con creación")

                    print("PASO 3: Datos preparados - Username: su, Email: su@localhost")
                    username = 'su'
                    first_name = 'Superusuario'
                    last_name = ''  # Empty last name for PostgreSQL compatibility
                    email = f'{username}@{DOMAIN_BASE}'

                    print("PASO 4: Generando contraseña aleatoria")
                    password = generate_random_password()
                    print(f"PASO 4: ✓ Contraseña generada (longitud: {len(password)})")

                    print("PASO 5: Importando módulos para SQL raw")
                    from django.db import connection
                    from django.contrib.auth.hashers import make_password
                    print("PASO 5: ✓ Módulos importados correctamente")

                    print("PASO 6: Hasheando contraseña")
                    hashed_password = make_password(password)
                    print(f"PASO 6: ✓ Contraseña hasheada (tipo: {type(hashed_password)})")

                    print("PASO 7: Ejecutando SQL raw para insertar usuario")
                    sql_params = [username, first_name, last_name, email, hashed_password, True, True, True]
                    print(f"PASO 7: Parámetros SQL: {sql_params}")

                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO auth_user (
                                username, first_name, last_name, email, password,
                                is_staff, is_active, is_superuser,
                                date_joined, last_login
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        """, sql_params)

                    print("PASO 7: ✓ SQL ejecutado exitosamente")

                    print("PASO 8: Verificando creación del usuario en base de datos")
                    superuser = User.objects.get(username='su')
                    print(f"PASO 8: ✓ Usuario encontrado en BD - Username: {superuser.username}")
                    print(f"PASO 8:   - Is superuser: {superuser.is_superuser}")
                    print(f"PASO 8:   - Is staff: {superuser.is_staff}")
                    print(f"PASO 8:   - Is active: {superuser.is_active}")

                    print("PASO 9: ✓ Mensaje de éxito enviado: Superusuario creado: su, contraseña: [REDACTED]")
                    messages.success(request, f'Superusuario creado: su, contraseña: {password}')

                    print("PASO 10: Autenticando usuario con credenciales")
                    user = authenticate(username='su', password=password)
                    print(f"PASO 10: Resultado autenticación: {user is not None}")

                    if user is not None:
                        print("PASO 10: ✓ Autenticación exitosa")

                        print("PASO 11: Ejecutando login del usuario")
                        login(request, user)
                        print("PASO 11: ✓ Login completado")

                        print("PASO 12: Configurando variable de sesión")
                        request.session['first_session'] = True
                        print("PASO 12: ✓ Sesión configurada")

                        print("PASO 13: Redirigiendo a: /events/setup/?step=2")
                        print("=== PROCESO CREACIÓN SUPERUSUARIO COMPLETADO EXITOSAMENTE ===")
                        return redirect(reverse('setup') + '?step=2')
                    else:
                        print("PASO 10: ❌ Error en autenticación")
                        messages.error(request, 'Error al autenticar el superusuario creado.')

                else:
                    print("PASO 2: ✓ Superusuario ya existe")
                    messages.info(request, 'El superusuario ya existe. Por favor, inicie sesión.')
                    return redirect(reverse('setup') + '?step=login')

            except Exception as e:
                print(f"ERROR: Exception in superuser creation: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()

                error_message = f'Error al crear superusuario: {str(e)}. Las migraciones pueden no haberse ejecutado aún.'

                # Try to add error message, but don't fail if messages middleware is not available
                try:
                    messages.error(request, error_message)
                except Exception as msg_error:
                    print(f"WARNING: Could not add error message: {msg_error}")

                # Always return a redirect to prevent button from getting stuck
                try:
                    return redirect(reverse('setup'))
                except Exception as redirect_error:
                    print(f"ERROR: Could not redirect: {redirect_error}")
                    # Fallback: return a basic HttpResponse
                    from django.http import HttpResponse
                    return HttpResponse("Error occurred. Please refresh the page.", status=500)

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
                # Create or update profile with essential fields only
                profile, created = Profile.objects.get_or_create(
                    user=su,
                    defaults={
                        'full_name': request.POST.get('full_name', ''),
                        'profession': request.POST.get('profession', ''),
                        'role': request.POST.get('role', 'US'),
                    }
                )

                if not created:
                    profile.full_name = request.POST.get('full_name', '')
                    profile.profession = request.POST.get('profession', '')
                    profile.role = request.POST.get('role', 'US')

                # Handle profile picture if provided
                if 'profile_picture' in request.FILES:
                    profile.profile_picture = request.FILES['profile_picture']

                profile.save()
                messages.success(request, 'Profile created successfully!')
                return redirect(reverse('setup') + '?step=3')

            except User.DoesNotExist:
                messages.error(request, 'Superuser does not exist. Please create one first.')
            except Exception as e:
                messages.error(request, f'Error creating profile: {str(e)}. Las tablas pueden no existir aún.')
            return redirect(reverse('setup') + '?step=2')

        elif 'create_random_users' in request.POST:
            try:
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
            except Exception as e:
                messages.error(request, f'Error al crear usuarios: {str(e)}. Las tablas pueden no existir aún.')
                return redirect(reverse('setup'))

        elif 'create_group' in request.POST:
            try:
                group_name = request.POST['group_name']
                usernames = request.POST.getlist('usernames')
                group, created = Group.objects.get_or_create(name=group_name)
                for username in usernames:
                    user = User.objects.get(username=username)
                    user.groups.add(group)
                messages.success(request, f'Grupo {group_name} creado y usuarios asignados.')
                completed_steps = ['1', '2', '3', '4']
                return redirect(reverse('setup') + '?step=5')
            except Exception as e:
                messages.error(request, f'Error al crear grupo: {str(e)}. Las tablas pueden no existir aún.')
                return redirect(reverse('setup'))

        elif 'create_another_su' in request.POST:
            try:
                su_username = request.POST['su_username']
                su_email = request.POST['su_email']
                su_password = generate_random_password()
                if not User.objects.filter(username=su_username).exists():
                    superuser = User.objects.create_superuser(su_username, su_email, su_password)
                    superuser.save()
                    messages.success(request, f'Superusuario creado: {su_username}, contraseña: {su_password}')
                else:
                    messages.error(request, 'El nombre de usuario ya existe.')
            except Exception as e:
                messages.error(request, f'Error al crear superusuario: {str(e)}. Las tablas pueden no existir aún.')

        elif 'create_initial_statuses' in request.POST:
            created_statuses = create_initial_statuses()
            if created_statuses:
                messages.success(request, 'Initial statuses created successfully:')
                for status in created_statuses:
                    messages.info(request, f'- {status}')
            else:
                messages.info(request, 'All initial statuses already exist.')
            return redirect(reverse('setup') + '?step=4')

        # Fallback: if no specific action was handled, redirect back to setup
        print("DEBUG: No specific POST action handled, redirecting to setup")
        return redirect(reverse('setup'))