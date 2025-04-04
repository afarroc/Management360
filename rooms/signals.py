# signals.py (nuevo archivo)
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PlayerProfile
import requests  # Para llamadas a API del CRM

@receiver(post_save, sender=PlayerProfile)
def sync_with_crm(sender, instance, **kwargs):
    if kwargs.get('created') or kwargs.get('update_fields'):
        data = {
            'user_id': instance.user.id,
            'state': instance.state,
            'productivity': instance.productivity
        }
        requests.post('https://crm-api.example.com/update_player', json=data)