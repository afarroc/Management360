import os
from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User
from django.utils import timezone

# Modelo para los estados del evento
class Status(models.Model):
    status_name = models.CharField(max_length=50)
    icon = models.CharField(max_length=30, blank=True, null=True)
    active = models.BooleanField(default=True)
    color = models.CharField(max_length=30, default="white")
    
    def __str__(self):
        return self.status_name

class ProjectStatus(models.Model):
    status_name = models.CharField(max_length=50)
    icon = models.CharField(max_length=30, blank=True, null=True)
    active = models.BooleanField(default=True)
    color = models.CharField(max_length=30, default="white")
    
    def __str__(self):
        return self.status_name

class TaskStatus(models.Model):
    status_name = models.CharField(max_length=50)
    icon = models.CharField(max_length=30, blank=True, null=True)
    active = models.BooleanField(default=True)
    color = models.CharField(max_length=30, default="white")
    
    def __str__(self):
        return self.status_name

# Classificationes
class Classification(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre

# Modelo para registrar los estados por los que pasa cada proyecto
class ProjectState(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE)
    status = models.ForeignKey('ProjectStatus', on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Si es un nuevo estado, establecer la hora de inicio
        if not self.id:
            self.start_time = timezone.now()
        # Si se está finalizando un estado, establecer la hora de finalización
        else:
            self.end_time = timezone.now()
        super(ProjectState, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.status.status_name} ({self.start_time} - {self.end_time})"
    
# Modelo para registrar las ediciones realizadas en los campos del proyecto
class ProjectHistory(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE)
    edited_at = models.DateTimeField(auto_now_add=True)
    editor = models.ForeignKey(User, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.project.id} - {self.field_name} - {self.editor.username} : - ({self.old_value} - {self.new_value})"

# Modelo para los proyectos    
class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    done = models.BooleanField(default=False)
    event = models.ForeignKey('Event', on_delete=models.CASCADE, null=True, blank=True)
    project_status = models.ForeignKey(ProjectStatus, on_delete=models.CASCADE)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_projects')
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_projets') 
    attendees = models.ManyToManyField(User, through='ProjectAttendee', related_name='collaborating_projects',blank=True) 
    ticket_price = models.DecimalField(default=0, max_digits=6, decimal_places=2)

    def change_status(self, new_status_id):
        # Obtener el nuevo estado
        new_status = ProjectStatus.objects.get(id=new_status_id)
        
        # Finalizar el estado actual
        current_state = self.projectstate_set.filter(end_time__isnull=True).last()
        if current_state:
            current_state.end_time = timezone.now()
            current_state.save()
        
        # Crear un nuevo estado con el nuevo estado proporcionado
        ProjectState.objects.create(project=self, status=new_status)
        
        # Actualizar el estado del proyecto
        self.project_status = new_status
        self.updated_at = timezone.now()
        self.save()

    def record_edit(self, editor, field_name, old_value, new_value):
        # Registrar la edición en el historial
        project_history = ProjectHistory.objects.create(
            project=self,
            editor=editor,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value
        )
        print(f"Registro de edición creado: {project_history}")
        
        # Si el campo editado es 'projects_status', ejecutar change_status
        if field_name == 'project_status':
            new_status = ProjectStatus.objects.get(status_name=new_value)
            self.change_status(new_status.id)
   
    def __str__(self):
        return f"{self.title} - {self.event}"

# Modelo para registrar los asistentes al Proyecto
class ProjectAttendee(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    registration_time = models.DateTimeField(auto_now_add=True)
    has_paid = models.BooleanField(default=False)  # Campo nuevo para el pago
    notes = models.TextField(blank=True, null=True)  # Campo nuevo para notas adicionales

# Modelo para registrar los estados por los que pasa cada tarea
class TaskState(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE)
    status = models.ForeignKey('TaskStatus', on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Si es un nuevo estado, establecer la hora de inicio
        if not self.id:
            self.start_time = timezone.now()
        # Si se está finalizando un estado, establecer la hora de finalización
        else:
            self.end_time = timezone.now()
        super(TaskState, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.status.status_name} ({self.start_time} - {self.end_time})"
    
# Modelo para registrar las ediciones realizadas en los campos de la tarea
class TaskHistory(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE)
    edited_at = models.DateTimeField(auto_now_add=True)
    editor = models.ForeignKey(User, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.task.id} - {self.field_name} - {self.editor.username} : - ({self.old_value} - {self.new_value})"

# Modelo para las tareas
class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    important = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Agregar blank=True para permitir que el campo sea opcional en formularios
    done = models.BooleanField(default=False)
    project = models.ForeignKey('Project', on_delete=models.CASCADE)  # Usa comillas si Project está definido más abajo en el mismo archivo
    event = models.ForeignKey('Event', on_delete=models.CASCADE, blank=True, null=True)
    task_status = models.ForeignKey(TaskStatus, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_tasks') 
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_tasks')  # Asegúrate de que esta línea esté presente
    ticket_price = models.DecimalField(default=0, max_digits=6, decimal_places=2)


    def change_status(self, new_status_id):
        # Obtener el nuevo estado
        new_status = TaskStatus.objects.get(id=new_status_id)
        
        # Finalizar el estado actual
        current_state = self.taskstate_set.filter(end_time__isnull=True).last()
        if current_state:
            current_state.end_time = timezone.now()
            current_state.save()
        
        # Crear un nuevo estado con el nuevo estado proporcionado
        TaskState.objects.create(task=self, status=new_status)
        
        # Actualizar el estado del evento
        self.task_status = new_status
        self.updated_at = timezone.now()
        self.save()

    def record_edit(self, editor, field_name, old_value, new_value):
        # Registrar la edición en el historial
        task_history = TaskHistory.objects.create(
            task=self,
            editor=editor,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value
        )
        print(f"Registro de edición creado: {task_history}")
        
        # Si el campo editado es 'task_status', ejecutar change_status
        if field_name == 'task_status':
            new_status = TaskStatus.objects.get(status_name=new_value)
            self.change_status(new_status.id)

    def __str__(self):
        return f"{self.title} - {self.event}"

from django.core.exceptions import ValidationError

class TaskProgram(models.Model):
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_programs')
    task = models.ForeignKey('Task', on_delete=models.CASCADE)

    def clean(self):
        # Ensure end_time is after start_time
        if self.start_time >= self.end_time:
            raise ValidationError('End time must be after start time')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Task Program"
        verbose_name_plural = "Task Programs"

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
        return f"{self.event.id} - {self.field_name} - {self.editor.username} : - ({self.old_value} - {self.new_value})"

# Modelo para las etiquetas
class Tag(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

# Modelo principal del evento
class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    event_status = models.ForeignKey(Status, on_delete=models.CASCADE)
    venue = models.CharField(max_length=200)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_events')
    event_category = models.CharField(max_length=50)
    max_attendees = models.IntegerField(default=0)
    ticket_price = models.DecimalField(default=0, max_digits=6, decimal_places=2)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_events') 
    attendees = models.ManyToManyField(User, through='EventAttendee', related_name='collaborating_events', blank=True) 
    tags = models.ManyToManyField(Tag, blank=True)
    links = models.ManyToManyField('self', blank=True, symmetrical=False)
    classification = models.ForeignKey(Classification, on_delete=models.SET_NULL, null=True, blank=True)

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
        event_history = EventHistory.objects.create(
            event=self,
            editor=editor,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value
        )
        print(f"Registro de edición creado: {event_history}")
    
        # Si el campo editado es 'event_status', ejecutar change_status
        if field_name == 'event_status':
            new_status = Status.objects.get(status_name=new_value)
            self.change_status(new_status.id)
            
    def __str__(self):
        return f"{self.title}"

# Modelo para registrar los asistentes al evento
class EventAttendee(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    registration_time = models.DateTimeField(auto_now_add=True)
    has_paid = models.BooleanField(default=False)  # Campo nuevo para el pago
    notes = models.TextField(blank=True, null=True)  # Campo nuevo para notas adicionales



from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class CreditAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"{self.user.username} - {self.balance} créditos"

    def add_credits(self, amount):
        if not isinstance(amount, Decimal):
            amount = Decimal(amount)
        self.balance += amount
        self.save()

    def subtract_credits(self, amount):
        if not isinstance(amount, Decimal):
            amount = Decimal(amount)
        if amount > self.balance:
            raise ValueError("No hay suficientes créditos")
        self.balance -= amount
        self.save()


class Room(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

