"""
Sistema de distribución automática de leads entre bots
Implementa diferentes estrategias de distribución y reglas personalizadas
"""

from django.utils import timezone
from django.db import transaction
from .models import Lead, LeadCampaign, LeadDistributionRule, BotInstance, BotLog
from .utils import get_bot_coordinator
import logging
import random
from collections import defaultdict

logger = logging.getLogger(__name__)

class LeadDistributor:
    """Distribuidor automático de leads según estrategias configurables"""

    def __init__(self, campaign):
        self.campaign = campaign
        self.coordinator = get_bot_coordinator()

    def distribute_leads(self, leads_queryset=None, batch_size=None):
        """
        Distribuir leads automáticamente según la estrategia de la campaña

        Args:
            leads_queryset: Queryset de leads a distribuir (opcional)
            batch_size: Tamaño del lote (opcional, usa configuración de campaña)

        Returns:
            dict: Resultado de la distribución
        """
        if not self.campaign.is_active:
            return {'success': False, 'error': 'Campaña inactiva'}

        if not self.campaign.auto_distribute:
            return {'success': False, 'error': 'Distribución automática desactivada'}

        # Obtener leads a distribuir
        if leads_queryset is None:
            leads_queryset = self.campaign.leads.filter(
                status='new',
                assigned_bot__isnull=True
            )

        leads = list(leads_queryset[:batch_size or self.campaign.leads_per_batch])

        if not leads:
            return {'success': True, 'distributed': 0, 'message': 'No hay leads para distribuir'}

        # Aplicar reglas personalizadas primero
        leads = self._apply_custom_rules(leads)

        # Filtrar leads que ya fueron asignados por reglas
        unassigned_leads = [lead for lead in leads if lead.assigned_bot is None]

        if not unassigned_leads:
            return {'success': True, 'distributed': len(leads), 'message': 'Todos los leads asignados por reglas'}

        # Distribuir leads restantes según estrategia
        distributed_count = 0

        if self.campaign.distribution_strategy == 'round_robin':
            distributed_count = self._distribute_round_robin(unassigned_leads)
        elif self.campaign.distribution_strategy == 'equal_split':
            distributed_count = self._distribute_equal_split(unassigned_leads)
        elif self.campaign.distribution_strategy == 'priority_based':
            distributed_count = self._distribute_priority_based(unassigned_leads)
        elif self.campaign.distribution_strategy == 'skill_based':
            distributed_count = self._distribute_skill_based(unassigned_leads)
        else:
            return {'success': False, 'error': f'Estrategia no implementada: {self.campaign.distribution_strategy}'}

        # Actualizar estadísticas de la campaña
        self.campaign.distributed_leads += distributed_count
        self.campaign.save()

        # Log de la distribución
        BotLog.objects.create(
            bot_instance=None,  # Sistema
            category='lead_distribution',
            message=f'Distribuidos {distributed_count} leads en campaña {self.campaign.name}',
            details={
                'campaign_id': self.campaign.id,
                'strategy': self.campaign.distribution_strategy,
                'distributed_count': distributed_count,
                'total_leads': len(leads)
            },
            related_object_type='campaign',
            related_object_id=self.campaign.id
        )

        return {
            'success': True,
            'distributed': distributed_count,
            'total_processed': len(leads),
            'strategy': self.campaign.distribution_strategy
        }

    def _apply_custom_rules(self, leads):
        """Aplicar reglas personalizadas de distribución"""
        rules = self.campaign.distribution_rules.filter(is_active=True).order_by('priority')

        for lead in leads:
            for rule in rules:
                if rule.evaluate(lead):
                    rule.apply(lead)
                    break  # Solo aplicar la primera regla que coincida

        return leads

    def _distribute_round_robin(self, leads):
        """Distribuir leads en round-robin entre bots disponibles"""
        available_bots = list(self._get_available_bots())

        if not available_bots:
            logger.warning(f"No hay bots disponibles para campaña {self.campaign.name}")
            return 0

        distributed = 0
        bot_index = 0

        for lead in leads:
            # Encontrar siguiente bot disponible
            attempts = 0
            while attempts < len(available_bots):
                bot = available_bots[bot_index % len(available_bots)]

                if self._can_assign_lead_to_bot(lead, bot):
                    lead.assign_to_bot(bot)
                    distributed += 1
                    break

                bot_index += 1
                attempts += 1

            if attempts >= len(available_bots):
                logger.warning(f"No se pudo asignar lead {lead.id} - ningún bot disponible")

        return distributed

    def _distribute_equal_split(self, leads):
        """Distribuir leads equitativamente entre todos los bots"""
        available_bots = self._get_available_bots()

        if not available_bots:
            return 0

        # Calcular cuántos leads por bot
        leads_per_bot = len(leads) // len(available_bots)
        extra_leads = len(leads) % len(available_bots)

        distributed = 0
        bot_index = 0

        for i, bot in enumerate(available_bots):
            # Calcular cuántos leads asignar a este bot
            bot_leads = leads_per_bot + (1 if i < extra_leads else 0)

            # Asignar leads a este bot
            assigned_to_bot = 0
            while assigned_to_bot < bot_leads and distributed < len(leads):
                lead = leads[distributed]
                if self._can_assign_lead_to_bot(lead, bot):
                    lead.assign_to_bot(bot)
                    assigned_to_bot += 1
                distributed += 1

        return distributed

    def _distribute_priority_based(self, leads):
        """Distribuir leads basado en la carga actual de trabajo de los bots"""
        available_bots = self._get_available_bots()

        if not available_bots:
            return 0

        # Calcular carga actual de cada bot
        bot_workloads = {}
        for bot in available_bots:
            current_tasks = bot.assigned_leads.filter(status__in=['assigned', 'in_progress']).count()
            bot_workloads[bot.id] = current_tasks

        distributed = 0

        for lead in leads:
            # Encontrar bot con menor carga
            min_load_bot = min(bot_workloads.items(), key=lambda x: x[1])

            if self._can_assign_lead_to_bot(lead, BotInstance.objects.get(id=min_load_bot[0])):
                lead.assign_to_bot(BotInstance.objects.get(id=min_load_bot[0]))
                bot_workloads[min_load_bot[0]] += 1
                distributed += 1

        return distributed

    def _distribute_skill_based(self, leads):
        """Distribuir leads basado en la especialización de los bots"""
        available_bots = self._get_available_bots()

        if not available_bots:
            return 0

        distributed = 0

        for lead in leads:
            # Determinar el tipo de lead basado en datos
            lead_type = self._classify_lead_type(lead)

            # Encontrar bot más adecuado para este tipo
            best_bot = self._find_best_bot_for_lead_type(lead_type, available_bots)

            if best_bot and self._can_assign_lead_to_bot(lead, best_bot):
                lead.assign_to_bot(best_bot)
                distributed += 1

        return distributed

    def _classify_lead_type(self, lead):
        """Clasificar el tipo de lead basado en sus datos"""
        # Lógica simple de clasificación
        if lead.company and 'tech' in lead.company.lower():
            return 'technology'
        elif lead.custom_data.get('industry') == 'finance':
            return 'finance'
        elif lead.priority == 'urgent':
            return 'urgent'
        else:
            return 'general'

    def _find_best_bot_for_lead_type(self, lead_type, available_bots):
        """Encontrar el bot más adecuado para un tipo de lead"""
        # Mapeo de tipos de lead a especializaciones de bot
        type_mapping = {
            'technology': ['gtd_processor', 'task_executor'],
            'finance': ['project_manager', 'task_executor'],
            'urgent': ['gtd_processor'],  # Procesadores GTD son más rápidos
            'general': ['general_assistant', 'task_executor']
        }

        preferred_specializations = type_mapping.get(lead_type, ['general_assistant'])

        # Buscar bot con especialización preferida
        for bot in available_bots:
            if bot.specialization in preferred_specializations:
                return bot

        # Si no hay bot preferido, devolver el primero disponible
        return available_bots[0] if available_bots else None

    def _get_available_bots(self):
        """Obtener bots disponibles para esta campaña"""
        if self.campaign.assigned_bots.exists():
            # Usar bots asignados específicamente a la campaña
            bots = self.campaign.assigned_bots.filter(is_active=True)
        else:
            # Usar todos los bots activos
            bots = BotInstance.objects.filter(is_active=True)

        # Filtrar bots que están en horario laboral y tienen capacidad
        available_bots = []
        for bot in bots:
            if (bot.is_working_hours() and
                bot.assigned_leads.filter(status__in=['assigned', 'in_progress']).count() < self.campaign.max_leads_per_bot):
                available_bots.append(bot)

        return available_bots

    def _can_assign_lead_to_bot(self, lead, bot):
        """Verificar si un lead puede asignarse a un bot específico"""
        # Verificar límite de leads por bot
        current_leads = bot.assigned_leads.filter(status__in=['assigned', 'in_progress']).count()
        if current_leads >= self.campaign.max_leads_per_bot:
            return False

        # Verificar que el bot esté activo y en horario
        if not bot.is_active or not bot.is_working_hours():
            return False

        return True

class BulkLeadImporter:
    """Importador masivo de leads desde diferentes fuentes"""

    def __init__(self, campaign):
        self.campaign = campaign

    def import_from_csv(self, csv_file):
        """
        Importar leads desde archivo CSV

        Args:
            csv_file: Archivo CSV con columnas: name,email,phone,company,notes

        Returns:
            dict: Resultado de la importación
        """
        import csv
        from io import StringIO

        try:
            # Leer archivo CSV
            csv_content = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(StringIO(csv_content))

            imported_count = 0
            errors = []

            for row_num, row in enumerate(csv_reader, start=2):  # +2 porque header es línea 1
                try:
                    lead = Lead.objects.create(
                        name=row.get('name', '').strip(),
                        email=row.get('email', '').strip(),
                        phone=row.get('phone', '').strip(),
                        company=row.get('company', '').strip(),
                        notes=row.get('notes', '').strip(),
                        source='CSV Import',
                        campaign=self.campaign,
                        custom_data=row  # Guardar todos los datos originales
                    )
                    imported_count += 1

                except Exception as e:
                    errors.append(f"Fila {row_num}: {str(e)}")

            # Actualizar estadísticas de la campaña
            self.campaign.total_leads += imported_count
            self.campaign.save()

            return {
                'success': True,
                'imported': imported_count,
                'errors': errors,
                'total_rows': imported_count + len(errors)
            }

        except Exception as e:
            return {'success': False, 'error': f'Error procesando CSV: {str(e)}'}

    def import_from_json(self, json_data):
        """
        Importar leads desde datos JSON

        Args:
            json_data: Lista de diccionarios con datos de leads

        Returns:
            dict: Resultado de la importación
        """
        try:
            imported_count = 0
            errors = []

            for item in json_data:
                try:
                    lead = Lead.objects.create(
                        name=item.get('name', ''),
                        email=item.get('email', ''),
                        phone=item.get('phone', ''),
                        company=item.get('company', ''),
                        notes=item.get('notes', ''),
                        source='JSON Import',
                        campaign=self.campaign,
                        custom_data=item
                    )
                    imported_count += 1

                except Exception as e:
                    errors.append(f"Item {item.get('name', 'Unknown')}: {str(e)}")

            # Actualizar estadísticas
            self.campaign.total_leads += imported_count
            self.campaign.save()

            return {
                'success': True,
                'imported': imported_count,
                'errors': errors
            }

        except Exception as e:
            return {'success': False, 'error': f'Error procesando JSON: {str(e)}'}

def get_lead_distributor(campaign):
    """Factory function para obtener distribuidor de leads"""
    return LeadDistributor(campaign)

def get_bulk_importer(campaign):
    """Factory function para obtener importador masivo"""
    return BulkLeadImporter(campaign)