from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone

class MementoConfig(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='memento_configs'
    )
    birth_date = models.DateField()
    death_date = models.DateField(
        validators=[MinValueValidator(limit_value=timezone.now().date())]
    )
    FREQUENCY_CHOICES = [
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
    ]
    preferred_frequency = models.CharField(
        max_length=10,
        choices=FREQUENCY_CHOICES,
        default='monthly'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración Memento"
        verbose_name_plural = "Configuraciones Memento"
        ordering = ['-updated_at']
        unique_together = ('user', 'birth_date', 'death_date')

    def __str__(self):
        return f"Configuración de {self.user.username} (Nacimiento: {self.birth_date})"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('memento', kwargs={
            'frequency': self.preferred_frequency,
            'birth_date': self.birth_date.strftime('%Y-%m-%d'),  # Cambiado de birth_date_str
            'death_date': self.death_date.strftime('%Y-%m-%d')   # Cambiado de death_date_str
        })