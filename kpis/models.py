from django.db import models  

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