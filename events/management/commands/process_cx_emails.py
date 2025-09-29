import re
from datetime import datetime, timedelta
import logging

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

from events.models import InboxItem, InboxItemAuthorization

try:
    from imap_tools import MailBox, AND
except ImportError:
    raise CommandError("imap-tools is required. Install with: pip install imap-tools")

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process CX emails and create InboxItem entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually creating items',
        )
        parser.add_argument(
            '--max-emails',
            type=int,
            default=50,
            help='Maximum number of emails to process in one run',
        )

    def handle(self, *args, **options):
        if not settings.EMAIL_RECEPTION_ENABLED:
            self.stdout.write(
                self.style.WARNING('Email reception is disabled in settings. Skipping...')
            )
            return

        dry_run = options['dry_run']
        max_emails = options['max_emails']

        self.stdout.write(f'Starting CX email processing (dry_run={dry_run}, max_emails={max_emails})')

        try:
            # Conectar al servidor IMAP usando imap-tools
            with MailBox(settings.EMAIL_IMAP_HOST).login(
                settings.EMAIL_IMAP_USER,
                settings.EMAIL_IMAP_PASSWORD
            ) as mailbox:

                # Seleccionar carpeta CX o INBOX
                try:
                    mailbox.folder.set(settings.EMAIL_CX_FOLDER)
                    self.stdout.write(f'Using CX folder: {settings.EMAIL_CX_FOLDER}')
                except:
                    mailbox.folder.set('INBOX')
                    self.stdout.write('CX folder not found, using INBOX')

                # Buscar correos no leídos
                messages = list(mailbox.fetch(AND(seen=False), limit=max_emails))
                self.stdout.write(f'Found {len(messages)} unread emails')

                processed_count = 0

                for msg in messages:
                    try:
                        # Procesar el correo
                        inbox_item_data = self._process_cx_email(msg)

                        if inbox_item_data:
                            if dry_run:
                                self.stdout.write(
                                    self.style.SUCCESS(f'[DRY RUN] Would create: {inbox_item_data["title"]}')
                                )
                            else:
                                # Crear InboxItem
                                inbox_item = self._create_inbox_item_from_email(inbox_item_data)
                                self.stdout.write(
                                    self.style.SUCCESS(f'Created InboxItem: {inbox_item.title}')
                                )

                            processed_count += 1

                        # Marcar como leído (opcional)
                        # mailbox.flag(msg.uid, '\\Seen', True)

                    except Exception as e:
                        logger.error(f'Error processing email {msg.uid}: {str(e)}')
                        self.stdout.write(
                            self.style.ERROR(f'Error processing email {msg.uid}: {str(e)}')
                        )

                self.stdout.write(
                    self.style.SUCCESS(f'Processed {processed_count} CX emails successfully')
                )

        except Exception as e:
            raise CommandError(f'Email processing failed: {str(e)}')

    def _process_cx_email(self, msg):
        """
        Procesa un correo electrónico CX y extrae la información relevante
        """
        try:
            # Extraer información básica usando imap-tools
            subject = msg.subject or 'Sin asunto'
            sender = msg.from_ or ''
            date = msg.date

            # Extraer cuerpo del mensaje
            body = self._get_email_body(msg)

            # Verificar si es un correo CX válido
            if not self._is_cx_email(subject, body, sender):
                return None

            # Extraer ID de cliente si existe
            customer_id = self._extract_customer_id(subject, body, sender)

            # Determinar prioridad basada en contenido
            priority = self._determine_priority(subject, body)

            # Crear título para InboxItem
            title = f"CX: {subject[:100]}"

            # Crear descripción
            description = f"De: {sender}\nCliente: {customer_id or 'No identificado'}\n\n{body[:500]}..."

            return {
                'title': title,
                'description': description,
                'subject': subject,
                'sender': sender,
                'body': body,
                'customer_id': customer_id,
                'priority': priority,
                'received_at': date,
            }

        except Exception as e:
            logger.error(f'Error processing email content: {str(e)}')
            return None

    def _get_email_body(self, msg):
        """Extrae el cuerpo del email usando imap-tools"""
        try:
            # Intentar obtener texto plano primero
            if msg.text:
                return msg.text.strip()
            # Si no hay texto plano, usar HTML convertido a texto
            elif msg.html:
                # Simple conversión HTML a texto (puedes mejorar esto)
                import re
                html = msg.html
                # Remover tags HTML básicos
                clean = re.compile('<.*?>')
                text = re.sub(clean, '', html)
                # Decodificar entidades HTML comunes
                text = text.replace('&nbsp;', ' ').replace('&', '&').replace('<', '<').replace('>', '>')
                return text.strip()
            else:
                return "Sin contenido"
        except:
            return "Error al extraer contenido"

    def _is_cx_email(self, subject, body, sender):
        """Determina si un email es de CX"""
        text_to_check = f"{subject} {body}".lower()

        # Verificar dominios CX
        sender_domain = self._extract_domain(sender)
        if sender_domain and any(domain.strip('@') in sender_domain for domain in settings.CX_EMAIL_DOMAINS):
            return True

        # Verificar palabras clave CX
        for keyword in settings.CX_KEYWORDS:
            if keyword.lower().strip() in text_to_check:
                return True

        return False

    def _extract_customer_id(self, subject, body, sender):
        """Extrae ID de cliente del email"""
        # Patrones comunes para IDs de cliente
        patterns = [
            r'Cliente[:\s]+([A-Z0-9\-]+)',
            r'ID[:\s]+([A-Z0-9\-]+)',
            r'Cuenta[:\s]+([A-Z0-9\-]+)',
            r'Número[:\s]+([A-Z0-9\-]+)',
        ]

        text = f"{subject} {body}"

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        # Extraer de email si tiene formato cliente@dominio
        local_part = sender.split('@')[0] if '@' in sender else sender
        if re.match(r'^[A-Z0-9\-]+$', local_part, re.IGNORECASE):
            return local_part

        return None

    def _determine_priority(self, subject, body):
        """Determina la prioridad del email CX"""
        text = f"{subject} {body}".lower()

        # Palabras clave de alta prioridad
        high_priority_keywords = ['urgente', 'inmediato', 'crítico', 'emergencia', 'queja', 'reclamo']

        for keyword in high_priority_keywords:
            if keyword in text:
                return 'alta'

        # Palabras clave de media prioridad
        medium_priority_keywords = ['cambio', 'modificar', 'actualizar', 'solicitud']

        for keyword in medium_priority_keywords:
            if keyword in text:
                return 'media'

        return 'media'  # Default


    def _extract_domain(self, email_address):
        """Extrae el dominio de una dirección de email"""
        if '@' in email_address:
            return email_address.split('@')[1].lower()
        return None

    def _create_inbox_item_from_email(self, email_data):
        """
        Crea un InboxItem desde los datos del email procesado
        """
        # Obtener usuario sistema o bot apropiado
        system_user = self._get_system_user()

        # Crear InboxItem
        inbox_item = InboxItem.objects.create(
            title=email_data['title'],
            description=email_data['description'],
            created_by=system_user,
            gtd_category='accionable',
            action_type='delegar',  # Delegar a bot/usuario apropiado
            priority=email_data['priority'],
            context='cliente',
            user_context={
                'source': 'cx_email',
                'customer_id': email_data.get('customer_id'),
                'email_subject': email_data['subject'],
                'email_sender': email_data['sender'],
                'email_body': email_data['body'],
                'received_at': email_data['received_at'].isoformat(),
                'processed_at': timezone.now().isoformat(),
            }
        )

        # Determinar y asignar usuario/bot apropiado
        assigned_user = self._determine_assigned_user(email_data)
        if assigned_user:
            InboxItemAuthorization.objects.create(
                inbox_item=inbox_item,
                user=assigned_user,
                granted_by=system_user,
                permission_level='edit'
            )

        return inbox_item

    def _get_system_user(self):
        """Obtiene el usuario sistema para crear InboxItem"""
        try:
            return User.objects.get(username='system')
        except User.DoesNotExist:
            # Crear usuario sistema si no existe
            system_user = User.objects.create_user(
                username='system',
                email='system@local',
                first_name='Sistema',
                last_name='CX',
                is_staff=False,
                is_active=False  # Usuario no interactivo
            )
            return system_user

    def _determine_assigned_user(self, email_data):
        """
        Determina qué usuario/bot debe procesar este email CX
        """
        # Lógica simple: asignar basado en tipo de solicitud
        subject = email_data['subject'].lower()
        body = email_data['body'].lower()

        # Buscar bots disponibles para CX
        try:
            from bots.models import BotInstance

            # Buscar bot de CX
            cx_bot = BotInstance.objects.filter(
                name__icontains='cx',
                is_active=True
            ).first()

            if cx_bot:
                return cx_bot.user

            # Buscar cualquier bot activo
            active_bot = BotInstance.objects.filter(is_active=True).first()
            if active_bot:
                return active_bot.user

        except:
            pass

        # Fallback: asignar a usuario administrador
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            return admin_user
        except:
            return None