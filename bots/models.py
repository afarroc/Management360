"""
Modelos para el sistema multi-bot FTE
Incluye usuarios genéricos, instancias de bots, coordinación y gestión de leads
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import uuid
import json

class GenericUser(models.Model):
    """Usuario genérico para bots - permite que múltiples bots compartan identidad"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='generic_user_profile')
    is_bot_user = models.BooleanField(default=False, help_text="Indica si este usuario es para un bot")
    role_description = models.CharField(max_length=200, blank=True, help_text="Descripción del rol del usuario")
    is_available = models.BooleanField(default=True, help_text="Si el usuario está disponible")
    allowed_operations = models.JSONField(default=list, help_text="Operaciones permitidas para este usuario")

    # Estadísticas
    tasks_completed = models.IntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} ({'Bot' if self.is_bot_user else 'Human'})"

    class Meta:
        verbose_name = "Usuario Genérico"
        verbose_name_plural = "Usuarios Genéricos"

class BotCoordinator(models.Model):
    """Coordinador principal del sistema multi-bot"""
    name = models.CharField(max_length=200, default="Main Bot Coordinator")
    is_active = models.BooleanField(default=True)

    # Configuración de escalado
    min_bots = models.IntegerField(default=1, help_text="Número mínimo de bots")
    max_bots = models.IntegerField(default=10, help_text="Número máximo de bots")
    scale_up_threshold = models.FloatField(default=0.8, help_text="Umbral para escalar hacia arriba (0-1)")
    scale_down_threshold = models.FloatField(default=0.2, help_text="Umbral para escalar hacia abajo (0-1)")
    auto_scaling_enabled = models.BooleanField(default=False, help_text="Habilitar auto-escalado")

    # Estado del sistema
    active_bots_count = models.IntegerField(default=0)
    system_load = models.FloatField(default=0.0, help_text="Carga actual del sistema (0-1)")
    last_health_check = models.DateTimeField(auto_now=True)

    def get_system_load(self):
        """Calcula la carga actual del sistema"""
        if self.active_bots_count == 0:
            return 0.0

        # Calcular basado en tareas activas vs capacidad
        active_tasks = BotTaskAssignment.objects.filter(
            status__in=['assigned', 'in_progress']
        ).count()

        # Capacidad aproximada: 5 tareas por bot
        total_capacity = self.active_bots_count * 5
        if total_capacity == 0:
            return 1.0

        load = min(active_tasks / total_capacity, 1.0)
        self.system_load = load
        self.save(update_fields=['system_load'])
        return load

    def should_scale_up(self):
        """Determina si el sistema debe escalar hacia arriba"""
        return (self.auto_scaling_enabled and
                self.system_load > self.scale_up_threshold and
                self.active_bots_count < self.max_bots)

    def should_scale_down(self):
        """Determina si el sistema debe escalar hacia abajo"""
        return (self.auto_scaling_enabled and
                self.system_load < self.scale_down_threshold and
                self.active_bots_count > self.min_bots)

    def __str__(self):
        return f"{self.name} (Load: {self.system_load:.1f})"

    class Meta:
        verbose_name = "Coordinador de Bots"
        verbose_name_plural = "Coordinadores de Bots"

class BotInstance(models.Model):
    """Instancia individual de bot"""
    name = models.CharField(max_length=100, unique=True)
    generic_user = models.ForeignKey(GenericUser, on_delete=models.CASCADE, related_name='bot_instances')

    # Configuración
    specialization = models.CharField(max_length=50, choices=[
        ('gtd_processor', 'Procesador GTD'),
        ('project_manager', 'Gestor de Proyectos'),
        ('task_executor', 'Ejecutor de Tareas'),
        ('calendar_optimizer', 'Optimizador de Calendario'),
        ('communication_handler', 'Manejador de Comunicación'),
        ('general_assistant', 'Asistente General')
    ], default='general_assistant')

    priority_level = models.IntegerField(default=1, help_text="Nivel de prioridad (1-10, mayor = más prioritario)")

    # Estado operativo
    is_active = models.BooleanField(default=True)
    current_status = models.CharField(max_length=20, choices=[
        ('idle', 'Inactivo'),
        ('working', 'Trabajando'),
        ('paused', 'Pausado'),
        ('error', 'Error'),
        ('maintenance', 'Mantenimiento')
    ], default='idle')

    status_message = models.CharField(max_length=200, blank=True)
    last_heartbeat = models.DateTimeField(auto_now=True)

    # Estadísticas de rendimiento
    tasks_completed_today = models.IntegerField(default=0)
    tasks_completed_total = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    average_task_time = models.FloatField(default=0.0, help_text="Tiempo promedio por tarea en segundos")

    # Configuración de horario
    working_hours_start = models.TimeField(default='09:00')
    working_hours_end = models.TimeField(default='18:00')
    timezone = models.CharField(max_length=50, default='UTC')

    # Configuración avanzada
    max_concurrent_tasks = models.IntegerField(default=1)
    capabilities = models.JSONField(default=dict, help_text="Capacidades específicas del bot")
    configuration = models.JSONField(default=dict, help_text="Configuración personalizada")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_working_hours(self):
        """Verifica si el bot está en horario laboral"""
        now = timezone.now().time()
        return self.working_hours_start <= now <= self.working_hours_end

    def can_take_task(self, task_type, priority=1):
        """Verifica si el bot puede tomar una tarea específica"""
        if not self.is_active or not self.is_working_hours():
            return False

        # Verificar límite de tareas concurrentes
        active_tasks = self.task_assignments.filter(status__in=['assigned', 'in_progress']).count()
        if active_tasks >= self.max_concurrent_tasks:
            return False

        # Verificar compatibilidad de especialización
        if self.specialization != 'general_assistant':
            compatible_tasks = self._get_compatible_tasks()
            if task_type not in compatible_tasks:
                return False

        return True

    def _get_compatible_tasks(self):
        """Retorna las tareas compatibles con la especialización del bot"""
        task_mapping = {
            'gtd_processor': ['process_inbox', 'create_task', 'organize_items'],
            'project_manager': ['create_project', 'update_project', 'manage_dependencies'],
            'task_executor': ['execute_task', 'update_task', 'complete_task'],
            'calendar_optimizer': ['schedule_task', 'optimize_calendar', 'create_event'],
            'communication_handler': ['send_notification', 'process_message', 'handle_communication'],
            'general_assistant': ['*']  # Todas las tareas
        }
        return task_mapping.get(self.specialization, [])

    def update_status(self, new_status, message=""):
        """Actualiza el estado del bot"""
        self.current_status = new_status
        self.status_message = message
        self.save(update_fields=['current_status', 'status_message', 'last_heartbeat'])

    def get_performance_metrics(self):
        """Retorna métricas de rendimiento del bot"""
        return {
            'tasks_completed_today': self.tasks_completed_today,
            'tasks_completed_total': self.tasks_completed_total,
            'error_rate': self.error_count / max(self.tasks_completed_total, 1),
            'average_task_time': self.average_task_time,
            'uptime_percentage': self._calculate_uptime()
        }

    def _calculate_uptime(self):
        """Calcula el porcentaje de uptime del bot"""
        # Lógica simplificada - en producción sería más compleja
        total_time = (timezone.now() - self.created_at).total_seconds()
        if total_time == 0:
            return 100.0

        # Estimar tiempo activo basado en heartbeats
        # Esto es una aproximación simplificada
        return 95.0  # Placeholder

    def __str__(self):
        return f"{self.name} ({self.specialization}) - {self.current_status}"

    class Meta:
        verbose_name = "Instancia de Bot"
        verbose_name_plural = "Instancias de Bots"
        ordering = ['-priority_level', 'name']

class BotTaskAssignment(models.Model):
    """Asignación de tareas a bots"""
    bot_instance = models.ForeignKey(BotInstance, on_delete=models.CASCADE, related_name='task_assignments')
    task_type = models.CharField(max_length=50)
    task_id = models.IntegerField()
    priority = models.IntegerField(default=1)

    # Estado
    status = models.CharField(max_length=20, choices=[
        ('assigned', 'Asignada'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('failed', 'Fallida'),
        ('cancelled', 'Cancelada')
    ], default='assigned')

    # Fechas
    assigned_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)

    # Resultados
    result_data = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)

    # Metadata
    assignment_reason = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)

    def start_task(self):
        """Marca la tarea como iniciada"""
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.save()

    def complete_task(self, result_data=None):
        """Completa la tarea exitosamente"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if result_data:
            self.result_data = result_data
        self.save()

        # Actualizar estadísticas del bot
        self.bot_instance.tasks_completed_total += 1
        self.bot_instance.tasks_completed_today += 1
        self.bot_instance.save()

    def fail_task(self, error_message):
        """Marca la tarea como fallida"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()

    def can_retry(self):
        """Verifica si la tarea puede reintentarse"""
        return self.retry_count < self.max_retries

    def __str__(self):
        return f"{self.bot_instance.name}: {self.task_type} ({self.status})"

    class Meta:
        verbose_name = "Asignación de Tarea"
        verbose_name_plural = "Asignaciones de Tareas"
        ordering = ['-assigned_at']

class ResourceLock(models.Model):
    """Sistema de bloqueos distribuidos para recursos"""
    resource_type = models.CharField(max_length=50)  # project, task, event, etc.
    resource_id = models.IntegerField()
    bot_instance = models.ForeignKey(BotInstance, on_delete=models.CASCADE, related_name='resource_locks')

    lock_type = models.CharField(max_length=20, choices=[
        ('exclusive', 'Exclusivo'),
        ('shared', 'Compartido')
    ], default='exclusive')

    # Estado del bloqueo
    is_active = models.BooleanField(default=True)
    acquired_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    # Metadata
    lock_reason = models.TextField(blank=True)

    @classmethod
    def acquire_lock(cls, resource_type, resource_id, bot_instance, lock_type='exclusive', timeout_minutes=5):
        """Intenta adquirir un bloqueo para un recurso"""
        from django.db import transaction

        expires_at = timezone.now() + timezone.timedelta(minutes=timeout_minutes)

        with transaction.atomic():
            # Verificar si ya existe un bloqueo exclusivo
            existing_lock = cls.objects.filter(
                resource_type=resource_type,
                resource_id=resource_id,
                is_active=True
            ).first()

            if existing_lock:
                if existing_lock.lock_type == 'exclusive':
                    return None  # Ya hay un bloqueo exclusivo
                elif lock_type == 'exclusive':
                    return None  # No se puede adquirir exclusivo sobre compartido

            # Crear el nuevo bloqueo
            lock = cls.objects.create(
                resource_type=resource_type,
                resource_id=resource_id,
                bot_instance=bot_instance,
                lock_type=lock_type,
                expires_at=expires_at
            )

            return lock

    def release(self):
        """Libera el bloqueo"""
        self.is_active = False
        self.save()

    def is_expired(self):
        """Verifica si el bloqueo ha expirado"""
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.resource_type}:{self.resource_id} ({self.lock_type}) - {self.bot_instance.name}"

    class Meta:
        verbose_name = "Bloqueo de Recurso"
        verbose_name_plural = "Bloqueos de Recursos"
        unique_together = ['resource_type', 'resource_id', 'bot_instance']

class BotCommunication(models.Model):
    """Sistema de comunicación entre bots"""
    sender = models.ForeignKey(BotInstance, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(BotInstance, on_delete=models.CASCADE, null=True, blank=True, related_name='received_messages')

    message_type = models.CharField(max_length=50, choices=[
        ('task_request', 'Solicitud de Tarea'),
        ('status_update', 'Actualización de Estado'),
        ('resource_request', 'Solicitud de Recurso'),
        ('coordination', 'Coordinación'),
        ('alert', 'Alerta'),
        ('broadcast', 'Difusión')
    ], default='coordination')

    subject = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente')
    ], default='medium')

    # Estado
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # Datos adicionales
    metadata = models.JSONField(default=dict)

    def mark_as_read(self):
        """Marca el mensaje como leído"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def __str__(self):
        recipient_name = self.recipient.name if self.recipient else "All"
        return f"{self.sender.name} → {recipient_name}: {self.subject}"

    class Meta:
        verbose_name = "Comunicación de Bot"
        verbose_name_plural = "Comunicaciones de Bots"
        ordering = ['-sent_at']

class BotLog(models.Model):
    """Sistema de logging distribuido para bots"""
    bot_instance = models.ForeignKey(BotInstance, on_delete=models.CASCADE, null=True, blank=True, related_name='logs')

    category = models.CharField(max_length=50, choices=[
        ('task', 'Tarea'),
        ('system', 'Sistema'),
        ('error', 'Error'),
        ('communication', 'Comunicación'),
        ('performance', 'Rendimiento'),
        ('lead', 'Lead'),
        ('coordination', 'Coordinación')
    ], default='system')

    level = models.CharField(max_length=20, choices=[
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical')
    ], default='info')

    message = models.TextField()
    details = models.JSONField(default=dict)

    # Relaciones opcionales
    task_assignment = models.ForeignKey(BotTaskAssignment, on_delete=models.SET_NULL, null=True, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)  # lead, task, project, etc.
    related_object_id = models.IntegerField(null=True, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        bot_name = self.bot_instance.name if self.bot_instance else "System"
        return f"[{self.level.upper()}] {bot_name}: {self.message[:50]}"

    class Meta:
        verbose_name = "Log de Bot"
        verbose_name_plural = "Logs de Bots"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['bot_instance', 'category', 'created_at']),
            models.Index(fields=['category', 'level', 'created_at']),
        ]

# =====================================================================================
# MODELOS PARA GESTIÓN DE LEADS
# =====================================================================================

class LeadCampaign(models.Model):
    """Campaña de leads para distribución automática"""
    name = models.CharField(max_length=200, help_text="Nombre de la campaña")
    description = models.TextField(blank=True, help_text="Descripción de la campaña")

    # Configuración de distribución
    auto_distribute = models.BooleanField(default=True, help_text="Distribuir automáticamente")
    distribution_strategy = models.CharField(max_length=50, choices=[
        ('round_robin', 'Round Robin - Rotativo'),
        ('equal_split', 'Igualdad - Repartir equitativamente'),
        ('priority_based', 'Por Prioridad - Según carga de trabajo'),
        ('skill_based', 'Por Habilidad - Según especialización del bot'),
        ('custom_rules', 'Reglas Personalizadas')
    ], default='equal_split')

    # Bots asignados a esta campaña
    assigned_bots = models.ManyToManyField('BotInstance', related_name='lead_campaigns', blank=True)

    # Límites y controles
    max_leads_per_bot = models.IntegerField(default=10, help_text="Máximo leads por bot")
    leads_per_batch = models.IntegerField(default=5, help_text="Leads por lote de distribución")

    # Estado
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Estadísticas
    total_leads = models.IntegerField(default=0)
    distributed_leads = models.IntegerField(default=0)
    converted_leads = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.distribution_strategy})"

    class Meta:
        verbose_name = "Campaña de Leads"
        verbose_name_plural = "Campañas de Leads"

class Lead(models.Model):
    """Lead/Prospect para ser procesado por bots"""
    # Información básica
    name = models.CharField(max_length=200, help_text="Nombre del lead")
    email = models.EmailField(blank=True, help_text="Email del lead")
    phone = models.CharField(max_length=20, blank=True, help_text="Teléfono del lead")
    company = models.CharField(max_length=200, blank=True, help_text="Empresa del lead")

    # Información adicional
    source = models.CharField(max_length=100, blank=True, help_text="Fuente del lead (CSV, manual, API, etc.)")
    notes = models.TextField(blank=True, help_text="Notas adicionales")

    # Datos personalizables en JSON
    custom_data = models.JSONField(default=dict, help_text="Datos adicionales en formato JSON")

    # Estado del lead
    status = models.CharField(max_length=50, choices=[
        ('new', 'Nuevo'),
        ('assigned', 'Asignado'),
        ('in_progress', 'En Progreso'),
        ('contacted', 'Contactado'),
        ('qualified', 'Calificado'),
        ('converted', 'Convertido'),
        ('rejected', 'Rechazado'),
        ('follow_up', 'Seguimiento')
    ], default='new')

    priority = models.CharField(max_length=20, choices=[
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente')
    ], default='medium')

    # Asignación
    campaign = models.ForeignKey(LeadCampaign, on_delete=models.CASCADE, related_name='leads')
    assigned_bot = models.ForeignKey('BotInstance', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_leads')
    assigned_at = models.DateTimeField(null=True, blank=True)

    # Seguimiento
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_contact = models.DateTimeField(null=True, blank=True)

    # Conversión
    converted_at = models.DateTimeField(null=True, blank=True)
    conversion_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def assign_to_bot(self, bot_instance):
        """Asignar lead a un bot específico"""
        self.assigned_bot = bot_instance
        self.assigned_at = timezone.now()
        self.status = 'assigned'
        self.save()

        # Crear InboxItem para que el bot lo procese
        self._create_inbox_item_for_bot()

    def _create_inbox_item_for_bot(self):
        """Crear InboxItem en el inbox del bot para procesamiento GTD"""
        from events.models import InboxItem

        inbox_item = InboxItem.objects.create(
            title=f"Lead: {self.name}",
            description=f"Procesar lead {self.name} ({self.company}) - {self.email}",
            host=self.assigned_bot.generic_user.user,
            priority=self.priority,
            context="lead_processing",
            custom_data={
                'lead_id': self.id,
                'lead_name': self.name,
                'lead_email': self.email,
                'lead_company': self.company,
                'campaign': self.campaign.name,
                'source': self.source
            }
        )

        # Log de la asignación
        BotLog.objects.create(
            bot_instance=self.assigned_bot,
            category='lead',
            message=f'Lead asignado: {self.name}',
            details={
                'lead_id': self.id,
                'inbox_item_id': inbox_item.id,
                'campaign': self.campaign.name
            },
            related_object_type='lead',
            related_object_id=self.id
        )

    def mark_converted(self, value=0):
        """Marcar lead como convertido"""
        self.status = 'converted'
        self.converted_at = timezone.now()
        self.conversion_value = value
        self.save()

        # Actualizar estadísticas de la campaña
        self.campaign.converted_leads += 1
        self.campaign.save()

    def __str__(self):
        return f"{self.name} ({self.company}) - {self.status}"

    class Meta:
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        ordering = ['-created_at']

class LeadDistributionRule(models.Model):
    """Reglas personalizadas para distribución de leads"""
    campaign = models.ForeignKey(LeadCampaign, on_delete=models.CASCADE, related_name='distribution_rules')

    # Condiciones de la regla
    condition_field = models.CharField(max_length=100, help_text="Campo a evaluar (ej: company, source, priority)")
    condition_operator = models.CharField(max_length=20, choices=[
        ('equals', 'Igual a'),
        ('contains', 'Contiene'),
        ('starts_with', 'Empieza con'),
        ('ends_with', 'Termina con'),
        ('greater_than', 'Mayor que'),
        ('less_than', 'Menor que')
    ], default='equals')
    condition_value = models.CharField(max_length=200, help_text="Valor a comparar")

    # Acción de la regla
    action_type = models.CharField(max_length=20, choices=[
        ('assign_to_bot', 'Asignar a Bot específico'),
        ('set_priority', 'Establecer Prioridad'),
        ('add_tag', 'Agregar Etiqueta'),
        ('skip_distribution', 'Omitir distribución')
    ], default='assign_to_bot')

    action_bot = models.ForeignKey('BotInstance', on_delete=models.CASCADE, null=True, blank=True)
    action_priority = models.CharField(max_length=20, choices=[
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente')
    ], null=True, blank=True)
    action_tag = models.CharField(max_length=100, blank=True)

    # Control de la regla
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1, help_text="Orden de evaluación (menor número = mayor prioridad)")

    created_at = models.DateTimeField(auto_now_add=True)

    def evaluate(self, lead):
        """Evaluar si la regla aplica a un lead"""
        field_value = getattr(lead, self.condition_field, None)
        if field_value is None:
            # Intentar en custom_data
            field_value = lead.custom_data.get(self.condition_field)

        if field_value is None:
            return False

        # Convertir a string para comparación
        field_value = str(field_value).lower()
        condition_value = str(self.condition_value).lower()

        # Aplicar operador
        if self.condition_operator == 'equals':
            return field_value == condition_value
        elif self.condition_operator == 'contains':
            return condition_value in field_value
        elif self.condition_operator == 'starts_with':
            return field_value.startswith(condition_value)
        elif self.condition_operator == 'ends_with':
            return field_value.endswith(condition_value)
        elif self.condition_operator == 'greater_than':
            try:
                return float(field_value) > float(condition_value)
            except ValueError:
                return False
        elif self.condition_operator == 'less_than':
            try:
                return float(field_value) < float(condition_value)
            except ValueError:
                return False

        return False

    def apply(self, lead):
        """Aplicar la acción de la regla al lead"""
        if self.action_type == 'assign_to_bot' and self.action_bot:
            lead.assign_to_bot(self.action_bot)
        elif self.action_type == 'set_priority' and self.action_priority:
            lead.priority = self.action_priority
            lead.save()
        elif self.action_type == 'add_tag' and self.action_tag:
            # Agregar tag al custom_data
            tags = lead.custom_data.get('tags', [])
            if self.action_tag not in tags:
                tags.append(self.action_tag)
                lead.custom_data['tags'] = tags
                lead.save()
        elif self.action_type == 'skip_distribution':
            lead.status = 'skipped'
            lead.save()

    def __str__(self):
        return f"Regla: {self.condition_field} {self.condition_operator} '{self.condition_value}' → {self.action_type}"

    class Meta:
        verbose_name = "Regla de Distribución"
        verbose_name_plural = "Reglas de Distribución"
        ordering = ['priority', 'created_at']
