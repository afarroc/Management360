# signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from ..models import CreditAccount
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def create_credit_account(sender, instance, created, **kwargs):
    if created:
        try:
            # Check if CreditAccount already exists to avoid duplicates
            if not CreditAccount.objects.filter(user=instance).exists():
                CreditAccount.objects.create(user=instance)
                logger.info(f"CreditAccount created for user: {instance.username}")
            else:
                logger.info(f"CreditAccount already exists for user: {instance.username}")
        except Exception as e:
            logger.error(f"Error creating CreditAccount for user {instance.username}: {str(e)}")
            # Don't raise exception to avoid breaking user creation

@receiver(post_save, sender=User)
def save_credit_account(sender, instance, **kwargs):
    try:
        # Only save if the credit account exists
        if hasattr(instance, 'creditaccount'):
            instance.creditaccount.save()
            logger.info(f"CreditAccount saved for user: {instance.username}")
    except Exception as e:
        logger.error(f"Error saving CreditAccount for user {instance.username}: {str(e)}")
        # Don't raise exception to avoid breaking user operations
