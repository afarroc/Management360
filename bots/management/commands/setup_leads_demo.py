"""
Comando para configurar una demostración del sistema de leads
Crea campañas, reglas y leads de ejemplo
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from bots.models import LeadCampaign, Lead, LeadDistributionRule, BotInstance
from bots.lead_distributor import get_lead_distributor


class Command(BaseCommand):
    help = 'Configura una demostración del sistema de leads con campañas, reglas y datos de ejemplo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--leads-count',
            type=int,
            default=30,
            help='Número de leads a crear para la demostración'
        )
        parser.add_argument(
            '--campaign-name',
            type=str,
            default='Campaña Demo FTE',
            help='Nombre de la campaña de demostración'
        )

    def handle(self, *args, **options):
        self.stdout.write('Configurando demostracion del sistema de leads...\n')

        # Verificar que existan bots
        bots = BotInstance.objects.filter(is_active=True)
        if not bots.exists():
            self.stdout.write(
                self.style.ERROR('No hay bots activos. Ejecuta primero: python manage.py setup_bots')
            )
            return

        self.stdout.write(f'Encontrados {bots.count()} bots activos')

        # Crear campaña de demostración
        campaign = self._create_demo_campaign(options['campaign_name'], bots)
        self.stdout.write(f'Campana creada: {campaign.name}')

        # Crear reglas de distribución
        rules = self._create_distribution_rules(campaign, bots)
        self.stdout.write(f'Creadas {len(rules)} reglas de distribucion')

        # Crear leads de ejemplo
        leads = self._create_demo_leads(campaign, options['leads_count'])
        self.stdout.write(f'Creados {len(leads)} leads de ejemplo')

        # Distribuir leads automáticamente
        self.stdout.write('Distribuyendo leads entre bots...')
        distributor = get_lead_distributor(campaign)
        result = distributor.distribute_leads()

        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Distribucion completada: {result["distributed"]} leads asignados'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Error en distribucion: {result.get("error", "Error desconocido")}')
            )

        # Mostrar resumen
        self._show_summary(campaign)

        self.stdout.write(
            self.style.SUCCESS('\nDemostracion del sistema de leads configurada exitosamente!')
        )
        self.stdout.write('Accede al panel en: /bots/campaigns/')

    def _create_demo_campaign(self, name, bots):
        """Crear campaña de demostración"""
        campaign = LeadCampaign.objects.create(
            name=name,
            description='Campaña de demostración del sistema FTE de distribución automática de leads',
            distribution_strategy='custom_rules',  # Usar reglas personalizadas
            max_leads_per_bot=10,
            leads_per_batch=5,
            auto_distribute=True
        )

        # Asignar todos los bots disponibles
        campaign.assigned_bots.set(bots)

        return campaign

    def _create_distribution_rules(self, campaign, bots):
        """Crear reglas de distribución de ejemplo"""
        rules = []

        # Regla 1: Leads de empresas grandes van al bot más experimentado
        experienced_bot = bots.order_by('-tasks_completed_total').first()
        if experienced_bot:
            rule1 = LeadDistributionRule.objects.create(
                campaign=campaign,
                condition_field='company',
                condition_operator='contains',
                condition_value='Corp',
                action_type='assign_to_bot',
                action_bot=experienced_bot,
                priority=1
            )
            rules.append(rule1)

        # Regla 2: Leads urgentes van al bot de alta prioridad
        high_priority_bot = bots.filter(priority_level__gte=3).first()
        if high_priority_bot:
            rule2 = LeadDistributionRule.objects.create(
                campaign=campaign,
                condition_field='priority',
                condition_operator='equals',
                condition_value='urgent',
                action_type='assign_to_bot',
                action_bot=high_priority_bot,
                priority=2
            )
            rules.append(rule2)

        # Regla 3: Leads de tecnología tienen prioridad alta
        rule3 = LeadDistributionRule.objects.create(
            campaign=campaign,
            condition_field='company',
            condition_operator='contains',
            condition_value='Tech',
            action_type='set_priority',
            action_priority='high',
            priority=3
        )
        rules.append(rule3)

        # Regla 4: Agregar tag a leads de finanzas
        rule4 = LeadDistributionRule.objects.create(
            campaign=campaign,
            condition_field='company',
            condition_operator='contains',
            condition_value='Finance',
            action_type='add_tag',
            action_tag='finance',
            priority=4
        )
        rules.append(rule4)

        return rules

    def _create_demo_leads(self, campaign, count):
        """Crear leads de ejemplo"""
        companies = [
            'TechCorp Solutions', 'FinancePlus Inc', 'Global Industries Corp',
            'InnovateTech LLC', 'Capital Finance Group', 'MegaCorp Enterprises',
            'StartUp Tech', 'Traditional Industries Ltd', 'Modern Solutions Inc',
            'Legacy Systems Corp', 'NextGen Technologies', 'Classic Finance Co'
        ]

        priorities = ['low', 'medium', 'high', 'urgent']
        sources = ['Website', 'LinkedIn', 'Referral', 'Cold Call', 'Trade Show']

        leads = []
        for i in range(count):
            # Generar datos variados
            company = companies[i % len(companies)]
            priority = priorities[i % len(priorities)] if i % 7 == 0 else 'medium'  # Algunos urgentes
            source = sources[i % len(sources)]

            lead = Lead.objects.create(
                name=f'Lead Demo {i+1:03d}',
                email=f'lead{i+1:03d}@example.com',
                phone=f'+1-555-{1000+i:04d}',
                company=company,
                source=source,
                priority=priority,
                notes=f'Lead generado automáticamente para demostración - {company}',
                campaign=campaign,
                custom_data={
                    'demo': True,
                    'generated_at': timezone.now().isoformat(),
                    'sequence': i + 1
                }
            )
            leads.append(lead)

        return leads

    def _show_summary(self, campaign):
        """Mostrar resumen de la configuración"""
        self.stdout.write('\nResumen de la Configuracion:')
        self.stdout.write(f'   Campaña: {campaign.name}')
        self.stdout.write(f'   Estrategia: {campaign.get_distribution_strategy_display()}')
        self.stdout.write(f'   Bots asignados: {campaign.assigned_bots.count()}')
        self.stdout.write(f'   Reglas activas: {campaign.distribution_rules.filter(is_active=True).count()}')
        self.stdout.write(f'   Leads totales: {campaign.leads.count()}')

        # Estadísticas de distribución
        assigned = campaign.leads.filter(status='assigned').count()
        self.stdout.write(f'   Leads asignados: {assigned}')

        # Distribución por bot
        bot_distribution = campaign.leads.filter(
            assigned_bot__isnull=False
        ).values('assigned_bot__name').annotate(
            count=Lead.objects.filter(
                campaign=campaign,
                assigned_bot__name=models.F('assigned_bot__name')
            ).count()
        )

        if bot_distribution:
            self.stdout.write('   Distribución por bot:')
            for dist in bot_distribution:
                self.stdout.write(f'     - {dist["assigned_bot__name"]}: {dist["count"]} leads')