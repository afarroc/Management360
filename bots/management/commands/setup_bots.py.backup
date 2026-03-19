"""
Comando para inicializar y configurar el sistema multi-bot
Crea usuarios genéricos, bots y configuraciones iniciales
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction, models
from bots.models import GenericUser, BotInstance, BotCoordinator
import uuid

class Command(BaseCommand):
    help = 'Inicializa el sistema multi-bot con usuarios y configuraciones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reinicia completamente el sistema de bots',
        )
        parser.add_argument(
            '--bots-count',
            type=int,
            default=3,
            help='Número de bots a crear (default: 3)',
        )

    def handle(self, *args, **options):
        reset = options['reset']
        bots_count = options['bots_count']

        try:
            with transaction.atomic():
                if reset:
                    self.stdout.write(self.style.WARNING('Reiniciando sistema de bots...'))
                    self._reset_system()
        
                self.stdout.write(self.style.SUCCESS('Inicializando sistema multi-bot...'))

                # Crear coordinador
                coordinator = self._create_coordinator()

                # Crear usuarios genéricos y bots
                for i in range(bots_count):
                    self._create_bot_user_and_instance(i + 1)

                # Mostrar resumen
                self._show_system_status()

                self.stdout.write(self.style.SUCCESS('Sistema multi-bot inicializado correctamente!'))
                self.stdout.write(self.style.SUCCESS('Ejecuta: python manage.py run_bots'))

        except Exception as e:
            raise CommandError(f'Error inicializando bots: {str(e)}')

    def _reset_system(self):
        """Reinicia completamente el sistema"""
        BotInstance.objects.all().delete()
        GenericUser.objects.all().delete()
        BotCoordinator.objects.all().delete()

        # Eliminar usuarios bot (opcional - solo si tienen un patrón específico)
        bot_users = User.objects.filter(username__startswith='bot_user_')
        for user in bot_users:
            user.delete()

        self.stdout.write('Sistema reiniciado')

    def _create_coordinator(self):
        """Crea o obtiene el coordinador principal"""
        coordinator, created = BotCoordinator.objects.get_or_create(
            defaults={'name': 'Main Bot Coordinator'}
        )

        if created:
            self.stdout.write('Coordinador creado')
        else:
            self.stdout.write('Coordinador existente actualizado')

        return coordinator

    def _create_bot_user_and_instance(self, bot_number):
        """Crea un usuario genérico y su bot correspondiente"""
        # Crear usuario Django
        username = f'bot_user_{bot_number}'
        user, user_created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'bot{bot_number}@system.local',
                'first_name': f'Bot',
                'last_name': f'FTE {bot_number}',
                'is_staff': False,
                'is_superuser': False,
            }
        )

        if user_created:
            # Establecer contraseña por defecto
            user.set_password('bot_password_123')
            user.save()
            self.stdout.write(f'Usuario {username} creado')

        # Crear GenericUser
        generic_user, gu_created = GenericUser.objects.get_or_create(
            user=user,
            defaults={
                'is_bot_user': True,
                'role_description': f'Bot FTE {bot_number} - Asistente GTD',
                'is_available': True,
                'allowed_operations': [
                    'create_task', 'update_task', 'create_project',
                    'process_inbox', 'send_notifications'
                ]
            }
        )

        if gu_created:
            self.stdout.write(f'GenericUser para {username} creado')

        # Crear BotInstance
        bot_name = f'Bot_FTE_{bot_number}'
        specialization = self._get_specialization_for_bot(bot_number)

        bot, bot_created = BotInstance.objects.get_or_create(
            name=bot_name,
            defaults={
                'generic_user': generic_user,
                'specialization': specialization,
                'processing_speed': 'balanced',
                'risk_tolerance': 60,
                'communication_style': 'professional',
                'max_concurrent_tasks': 3,
                'priority_level': bot_number,
                'gtd_expertise_level': 85,
                'auto_process_under_2min': True,
                'auto_delegate_when_overloaded': True,
                'auto_create_projects': True,
            }
        )

        if bot_created:
            self.stdout.write(f'Bot {bot_name} creado ({specialization})')
        else:
            self.stdout.write(f'Bot {bot_name} ya existe')

        return bot

    def _get_specialization_for_bot(self, bot_number):
        """Asigna especialización basada en el número del bot"""
        specializations = [
            'gtd_processor',      # Bot 1: Especialista en GTD
            'project_manager',    # Bot 2: Gestor de proyectos
            'task_executor',      # Bot 3: Ejecutor de tareas
            'calendar_optimizer', # Bot 4: Optimizador de calendario
            'communication_handler' # Bot 5: Manejador de comunicación
        ]

        # Repetir especializaciones si hay más bots que especializaciones
        index = (bot_number - 1) % len(specializations)
        return specializations[index]

    def _show_system_status(self):
        """Muestra el estado actual del sistema"""
        total_bots = BotInstance.objects.count()
        active_bots = BotInstance.objects.filter(is_active=True).count()
        generic_users = GenericUser.objects.count()

        self.stdout.write('\nEstado del Sistema Multi-Bot:')
        self.stdout.write(f'   Bots totales: {total_bots}')
        self.stdout.write(f'   Bots activos: {active_bots}')
        self.stdout.write(f'   Usuarios genéricos: {generic_users}')

        # Mostrar especializaciones
        specializations = BotInstance.objects.values('specialization').annotate(
            count=models.Count('id')
        ).order_by('specialization')

        self.stdout.write('\nEspecializaciones:')
        for spec in specializations:
            self.stdout.write(f'   • {spec["specialization"]}: {spec["count"]}')

        # Mostrar coordinador
        coordinator = BotCoordinator.objects.first()
        if coordinator:
            self.stdout.write(f'\nCoordinador: {coordinator.name}')
            self.stdout.write(f'   Carga del sistema: {coordinator.get_system_load():.1f}%')