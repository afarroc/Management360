# signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from ..models import CreditAccount

@receiver(post_save, sender=User)
def create_credit_account(sender, instance, created, **kwargs):
    if created:
        CreditAccount.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_credit_account(sender, instance, **kwargs):
    instance.creditaccount.save()
