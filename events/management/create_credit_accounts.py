# management/commands/create_credit_accounts.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()
from events.models import CreditAccount

class Command(BaseCommand):
    help = 'Create credit accounts for existing users'

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        for user in users:
            if not hasattr(user, 'creditaccount'):
                CreditAccount.objects.create(user=user)
                self.stdout.write(self.style.SUCCESS(f'Created credit account for {user.username}'))
