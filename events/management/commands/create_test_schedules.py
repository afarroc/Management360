from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, time, timedelta
from events.models import Task, TaskSchedule, TaskStatus, Status
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create test task schedules using existing tasks'

    def handle(self, *args, **options):
        self.stdout.write('Creating test task schedules...\n')

        # Get user 1 (admin user) and test user
        try:
            admin_user = User.objects.get(id=1)
            self.stdout.write(f'Using admin user: {admin_user.username} (ID: 1)')
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING('User with ID 1 not found, creating test user instead'))
            admin_user = None

        # Get or create test user
        test_user, created = User.objects.get_or_create(
            username='test_scheduler',
            defaults={
                'email': 'scheduler@test.com',
                'first_name': 'Test',
                'last_name': 'Scheduler'
            }
        )
        if created:
            test_user.set_password('testpass123')
            test_user.save()
            self.stdout.write(f'Created test user: {test_user.username}')

        # Use admin user if available, otherwise test user
        users = [u for u in [admin_user, test_user] if u is not None]

        # Get or create required statuses
        task_status, _ = TaskStatus.objects.get_or_create(
            status_name='To Do',
            defaults={'active': True, 'color': 'blue'}
        )

        event_status, _ = Status.objects.get_or_create(
            status_name='Created',
            defaults={'active': True, 'color': 'green'}
        )

        # Create tasks for each user
        all_tasks = []
        for user in users:
            self.stdout.write(f'Creating fresh test tasks for schedules for user: {user.username}...\n')
            tasks = []
            import uuid
            for i in range(3):
                unique_id = str(uuid.uuid4())[:8]
                task = Task.objects.create(
                    title=f'Tarea Schedule {i+1} - {unique_id} ({user.username})',
                    description=f'Tarea de prueba creada específicamente para programaciones recurrentes {i+1} del usuario {user.username}',
                    host=user,
                    assigned_to=user,
                    task_status=task_status,
                    ticket_price=0.0
                )
                tasks.append(task)
                self.stdout.write(f'Created task: {task.title}')
            all_tasks.append((user, tasks))

        # Create test schedules for each user
        schedules_data = [
            {
                'recurrence_type': 'daily',
                'start_time': time(9, 0),
                'duration': timedelta(hours=1),
                'start_date': date.today() + timedelta(days=1),
                'end_date': date.today() + timedelta(days=30),
                'description': 'Reunión diaria de equipo'
            },
            {
                'recurrence_type': 'weekly',
                'monday': True,
                'wednesday': True,
                'friday': True,
                'start_time': time(14, 30),
                'duration': timedelta(hours=2),
                'start_date': date.today() + timedelta(days=1),
                'end_date': date.today() + timedelta(days=60),
                'description': 'Revisión de código semanal'
            },
            {
                'recurrence_type': 'weekly',
                'tuesday': True,
                'thursday': True,
                'start_time': time(10, 0),
                'duration': timedelta(hours=1, minutes=30),
                'start_date': date.today() + timedelta(days=2),
                'end_date': date.today() + timedelta(days=45),
                'description': 'Planificación de sprint'
            }
        ]

        created_schedules = []
        for user, tasks in all_tasks:
            self.stdout.write(f'Creating schedules for user: {user.username}\n')

            for i, schedule_data in enumerate(schedules_data):
                task = tasks[i % len(tasks)]  # Cycle through available tasks

                schedule, created = TaskSchedule.objects.get_or_create(
                    task=task,
                    host=user,
                    defaults={
                        'recurrence_type': schedule_data['recurrence_type'],
                        'start_time': schedule_data['start_time'],
                        'duration': schedule_data['duration'],
                        'start_date': schedule_data['start_date'],
                        'end_date': schedule_data['end_date'],
                        'is_active': True,
                        **{k: v for k, v in schedule_data.items()
                           if k in ['monday', 'tuesday', 'wednesday', 'thursday',
                                   'friday', 'saturday', 'sunday']}
                    }
                )

                if created:
                    created_schedules.append(schedule)
                    self.stdout.write(
                        f'[OK] Created schedule for {user.username}: {schedule.task.title} - {schedule.get_recurrence_type_display()}'
                    )

                    # Generate some occurrences
                    occurrences = schedule.generate_occurrences(limit=5)
                    self.stdout.write(f'  -> Generated {len(occurrences)} upcoming occurrences')

                    # Create TaskPrograms for the first few occurrences
                    programs = schedule.create_task_programs(occurrences[:3])
                    self.stdout.write(f'  -> Created {len(programs)} TaskPrograms')
                else:
                    self.stdout.write(
                        f'[SKIP] Schedule already exists for {user.username}: {schedule.task.title}'
                    )

        self.stdout.write(f'\n[SUCCESS] Created {len(created_schedules)} test schedules')
        self.stdout.write('\nSummary of created schedules:')

        for schedule in created_schedules:
            self.stdout.write(f'  - {schedule.task.title}')
            self.stdout.write(f'    Type: {schedule.get_recurrence_type_display()}')
            self.stdout.write(f'    Time: {schedule.start_time} ({schedule.duration})')
            self.stdout.write(f'    Days: {schedule.get_selected_days_display()}')
            self.stdout.write(f'    Period: {schedule.start_date} to {schedule.end_date}')
            self.stdout.write('')

        self.stdout.write('Test schedules creation completed!')