# signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from ..models import CreditAccount
import logging

logger = logging.getLogger(__name__)

def _create_credit_account_later(user):
    """Helper function to create CreditAccount later if initial creation fails"""
    try:
        if not CreditAccount.objects.filter(user=user).exists():
            CreditAccount.objects.create(user=user)
            logger.info(f"CreditAccount created later for user: {user.username}")
    except Exception as e:
        logger.error(f"Failed to create CreditAccount later for user {user.username}: {str(e)}")

@receiver(post_save, sender=User)
def create_credit_account(sender, instance, created, **kwargs):
    if created:
        try:
            # Add a small delay to ensure database is ready
            import time
            time.sleep(0.1)

            # Check if CreditAccount already exists to avoid duplicates
            if not CreditAccount.objects.filter(user=instance).exists():
                credit_account = CreditAccount.objects.create(user=instance)
                logger.info(f"CreditAccount created for user: {instance.username}")
            else:
                logger.info(f"CreditAccount already exists for user: {instance.username}")
        except Exception as e:
            logger.error(f"Error creating CreditAccount for user {instance.username}: {str(e)}")
            # Don't raise exception to avoid breaking user creation
            # Try to create it later if possible
            try:
                # Schedule creation for later (this won't block the response)
                from django.db import transaction
                transaction.on_commit(lambda: _create_credit_account_later(instance))
            except:
                pass

@receiver(post_save, sender=User)
def save_credit_account(sender, instance, **kwargs):
    try:
        # Only save if the credit account exists and we're not in creation
        if hasattr(instance, 'creditaccount') and not kwargs.get('created', False):
            instance.creditaccount.save()
            logger.info(f"CreditAccount saved for user: {instance.username}")
    except Exception as e:
        logger.error(f"Error saving CreditAccount for user {instance.username}: {str(e)}")
        # Don't raise exception to avoid breaking user operations
