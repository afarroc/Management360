from django.db import models
from django.core.validators import MinValueValidator

class CallRecord(models.Model):  
    semana = models.IntegerField("Semana")  
    agente = models.CharField("Agente", max_length=100)  
    supervisor = models.CharField("Supervisor", max_length=100)  
    servicio = models.CharField("Servicio", max_length=50, choices=[("Reclamos", "Reclamos"), ("Consultas", "Consultas")])  
    canal = models.CharField("Canal", max_length=50, choices=[("Phone", "Phone"), ("Mail", "Mail"), ("Chat", "Chat")])  
    eventos = models.IntegerField("Eventos")  
    aht = models.FloatField("AHT")  
    evaluaciones = models.IntegerField("Evaluaciones")  
    satisfaccion = models.FloatField("Satisfacción")  
    
    def __str__(self):  
        return f"{self.agente} - Semana {self.semana}"
        
class ExchangeRate(models.Model):
    """
    Modelo mejorado para tasas de cambio con manejo adecuado de fechas
    """
    date = models.DateField(
        verbose_name="Fecha de referencia",
        help_text="Primer día del mes al que corresponde la tasa"
    )
    rate = models.DecimalField(
        verbose_name="Tasa de cambio",
        max_digits=10,
        decimal_places=6,
        validators=[MinValueValidator(0)],
        help_text="Tasa promedio PEN/USD - Compra interbancaria"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        verbose_name = "Tasa de Cambio"
        verbose_name_plural = "Tasas de Cambio"
        unique_together = ['date']

    def __str__(self):
        return f"{self.date.strftime('%b%y').lower()}: {self.rate} PEN/USD"
    
    @property
    def period(self):
        """Propiedad para mantener compatibilidad con formato MmmYY"""
        return self.date.strftime('%b%y').lower()
