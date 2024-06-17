from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

# Create your models here.

# Modelo para los estados del evento
class Status(models.Model):
    status_name = models.CharField(max_length=50)
    icon = models.CharField(max_length=30, blank=True)
    active = models.BooleanField(default=True)
    color = models.CharField(max_length=30, default="white")
    
    def __str__(self):
        return self.status_name

# Modelo para los proyectos    
class Project(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    important = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(null=True, blank=True)  # Agregar blank=True para permitir que el campo sea opcional en formularios
    done = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')  # Asegúrate de que esta línea esté presente
    project = models.ForeignKey('Project', on_delete=models.CASCADE)  # Usa comillas si Project está definido más abajo en el mismo archivo

    def __str__(self):
        return f"{self.title} - {self.project.name}"

# Modelo para registrar los estados por los que pasa cada evento
class EventState(models.Model):
    event = models.ForeignKey('Event', on_delete=models.CASCADE)
    status = models.ForeignKey('Status', on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Si es un nuevo estado, establecer la hora de inicio
        if not self.id:
            self.start_time = timezone.now()
        # Si se está finalizando un estado, establecer la hora de finalización
        else:
            self.end_time = timezone.now()
        super(EventState, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.status.status_name} ({self.start_time} - {self.end_time})"
    
# Modelo para registrar las ediciones realizadas en los campos del evento
class EventHistory(models.Model):
    event = models.ForeignKey('Event', on_delete=models.CASCADE)
    edited_at = models.DateTimeField(auto_now_add=True)
    editor = models.ForeignKey(User, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.event.title} - {self.field_name} editado por {self.editor.username}"

class Tag(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

# Modelo principal del evento
class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    event_status = models.ForeignKey(Status, on_delete=models.CASCADE)
    venue = models.CharField(max_length=200)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_events')
    event_category = models.CharField(max_length=50)
    max_attendees = models.IntegerField(default=0)
    ticket_price = models.DecimalField(default=0, max_digits=6, decimal_places=2)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_events') 
    attendees = models.ManyToManyField(User, through='EventAttendee', related_name='collaborating_events') 
    tags = models.ManyToManyField(Tag, blank=True)
    links = models.ManyToManyField('self', blank=True, symmetrical=False)
    
    def change_status(self, new_status_id):
        # Obtener el nuevo estado
        new_status = Status.objects.get(id=new_status_id)
    
        # Finalizar el estado actual
        current_state = self.eventstate_set.filter(end_time__isnull=True).last()
        if current_state:
            current_state.end_time = timezone.now()
            current_state.save()
    
        # Crear un nuevo estado con el nuevo estado proporcionado
        EventState.objects.create(event=self, status=new_status)
    
        # Actualizar el estado del evento
        self.event_status = new_status
        self.updated_at = timezone.now()
        self.save()




    def record_edit(self, editor, field_name, old_value, new_value):
        # Registrar la edición en el historial
        EventHistory.objects.create(
            event=self,
            editor=editor,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value
        )

    def save(self, *args, **kwargs):
        # Registrar automáticamente los cambios en los campos editables
        if self.pk:
            original_event = Event.objects.get(pk=self.pk)
            fields_to_check = ['title', 'description', 'venue', 'host', 'event_category', 'max_attendees', 'ticket_price']
            for field in fields_to_check:
                original_value = getattr(original_event, field)
                new_value = getattr(self, field)
                if original_value != new_value:
                    self.record_edit(
                        editor=self.editor,  # Asegúrate de asignar el editor actual
                        field_name=field,
                        old_value=original_value,
                        new_value=new_value
                    )
        else:
            # Si es un nuevo evento, inicializar con el estado 'Creado'
            super(Event, self).save(*args, **kwargs)  # Guardar el evento antes de crear el EventState
            created_status = Status.objects.get_or_create(status_name='Creado')[0]
            EventState.objects.create(event=self, status=created_status)
        super(Event, self).save(*args, **kwargs)

    def __str__(self):
        return self.title + " - " + self.event_status.status_name

# Modelo para registrar los asistentes al evento
class EventAttendee(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    registration_time = models.DateTimeField(auto_now_add=True)
    has_paid = models.BooleanField(default=False)  # Campo nuevo para el pago
    notes = models.TextField(blank=True, null=True)  # Campo nuevo para notas adicionales

## modelos para el perfil del usuario

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    linkedin_url = models.URLField(blank=True)
    ROLE_CHOICES = [
        ('SU', 'Supervisor'),
        ('GE', 'Gestor de Eventos'),
        ('AD', 'Administrador'),
        ('US', 'Usuario Estándar'),
    ]
    role = models.CharField(max_length=2, choices=ROLE_CHOICES, default='US')
    
    def __str__(self):
        return self.user.username

class Experience(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='experiences')
    job_title = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField()

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"

class Education(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='education')
    institution_name = models.CharField(max_length=100)
    degree = models.CharField(max_length=100)
    field_of_study = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.degree} in {self.field_of_study} from {self.institution_name}"

class Skill(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='skills')
    skill_name = models.CharField(max_length=100)
    proficiency_level = models.CharField(max_length=50)  # Ejemplo: Principiante, Intermedio, Experto

    def __str__(self):
        return self.skill_name
