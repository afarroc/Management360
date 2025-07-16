# campaigns/models.py
from django.db import models
from django.utils import timezone
import uuid

class ProviderRawData(models.Model):
    CAMPAIGN_STATUS = (
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('loaded', 'Cargada'),
        ('completed', 'Completada'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign_name = models.CharField(max_length=255, verbose_name="Nombre Campaña")
    upload_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=CAMPAIGN_STATUS, default='pending')
    source_file = models.FileField(upload_to='campaigns/raw_data/', blank=True, null=True)
    records_count = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.campaign_name} - {self.upload_date.strftime('%Y-%m-%d')}"

class ContactRecord(models.Model):
    CONTACT_TYPE = (
        ('mobile', 'Móvil'),
        ('landline', 'Fijo'),
        ('whatsapp', 'WhatsApp'),
    )
    
    campaign = models.ForeignKey(ProviderRawData, on_delete=models.CASCADE, related_name='contacts')
    ani = models.CharField(max_length=20, verbose_name="Número Teléfono")
    dni = models.CharField(max_length=20, verbose_name="Documento Identidad", blank=True, null=True)
    full_name = models.CharField(max_length=255, verbose_name="Nombre Completo")
    current_product = models.CharField(max_length=100, verbose_name="Producto Actual")
    offered_product = models.CharField(max_length=100, verbose_name="Producto Ofrecido")
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPE, default='mobile')
    segment = models.CharField(max_length=50, verbose_name="Segmento", blank=True, null=True)
    propensity_score = models.IntegerField(default=0, verbose_name="Score Propensión")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['ani']),
            models.Index(fields=['dni']),
            models.Index(fields=['campaign']),
        ]
    
    def __str__(self):
        return f"{self.full_name} - {self.ani}"

class DiscadorLoad(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('loading', 'Cargando'),
        ('loaded', 'Cargado'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
    )
    
    campaign = models.OneToOneField(ProviderRawData, on_delete=models.CASCADE, related_name='discador_load')
    load_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    records_loaded = models.IntegerField(default=0)
    records_processed = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0.0)
    export_file = models.FileField(upload_to='campaigns/discador_exports/', blank=True, null=True)
    
    def __str__(self):
        return f"Carga para {self.campaign.campaign_name} - {self.load_date}"