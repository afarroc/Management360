from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from cv.models import Curriculum, RoleChoices

class Command(BaseCommand):
    help = 'Asigna rol de administrador a un usuario'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nombre de usuario')
        parser.add_argument(
            '--role',
            type=str,
            choices=['SU', 'AD', 'GE', 'US'],
            default='AD',
            help='Rol a asignar (SU=Supervisor, AD=Administrador, GE=Gestor de Eventos, US=Usuario Estándar)'
        )

    def handle(self, *args, **options):
        username = options['username']
        role = options['role']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f'Usuario "{username}" no encontrado.')
            )
            return

        # Crear o actualizar el perfil CV
        cv, created = Curriculum.objects.get_or_create(
            user=user,
            defaults={
                'full_name': user.get_full_name() or user.username,
                'profession': 'Administrador',
                'bio': f'Perfil administrativo para {user.username}',
                'role': role,
                'location': '',
                'country': '',
                'address': '',
                'phone': '',
                'email': user.email or '',
                'linkedin_url': '',
                'github_url': '',
                'twitter_url': '',
                'facebook_url': '',
                'instagram_url': '',
                'company': 'Management360',
                'job_title': 'Administrador del Sistema',
            }
        )

        if not created:
            cv.role = role
            cv.save()

        role_display = dict(RoleChoices.choices)[role]
        self.stdout.write(
            self.style.SUCCESS(
                f'Rol "{role_display}" asignado exitosamente a {username}'
            )
        )