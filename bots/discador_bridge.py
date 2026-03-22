# bots/discador_bridge.py
"""
BOT-3: Bridge entre campaigns.DiscadorLoad y bots.LeadCampaign/Lead.

Servicio que transforma ContactRecords de una carga de discador
en Leads distribuibles a BotInstances.

Uso típico (desde la vista):
    bridge = DiscadorBridge()
    result = bridge.sync(discador_load_id=pk, bot_ids=[1,2,3],
                         strategy='equal_split', auto_distribute=True)
"""

import logging
from django.db import transaction

from campaigns.models import DiscadorLoad, ContactRecord
from .models import LeadCampaign, Lead, BotInstance
from .lead_distributor import LeadDistributor

logger = logging.getLogger(__name__)


def _priority_from_score(score: int) -> str:
    """Convierte propensity_score a prioridad de Lead."""
    if score >= 70:
        return 'high'
    if score >= 40:
        return 'medium'
    return 'low'


class DiscadorBridge:
    """
    Sincroniza una DiscadorLoad con el sistema de leads de bots.

    Flujo:
      1. Obtener DiscadorLoad + ProviderRawData
      2. Crear/actualizar LeadCampaign (1:1 con ProviderRawData)
      3. Asignar bots a la campaña (si se pasan bot_ids)
      4. Mapear ContactRecord → Lead via update_or_create(phone+campaign)
      5. Actualizar contadores en DiscadorLoad
      6. Opcional: disparar LeadDistributor
    """

    def sync(
        self,
        discador_load_id: int,
        bot_ids: list = None,
        strategy: str = 'equal_split',
        auto_distribute: bool = True,
    ) -> dict:
        """
        Sincroniza una DiscadorLoad con LeadCampaign+Lead.

        Args:
            discador_load_id: PK de DiscadorLoad (int AutoField).
            bot_ids: Lista de BotInstance PKs a asignar. None = no asignar.
            strategy: distribution_strategy para LeadCampaign.
            auto_distribute: Si True, lanza LeadDistributor al terminar.

        Returns:
            {
                'success': bool,
                'lead_campaign_id': int,
                'created': int,
                'updated': int,
                'skipped': int,
                'distributed': int,
                'errors': [str],
            }
        """
        result = {
            'success': False,
            'lead_campaign_id': None,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'distributed': 0,
            'errors': [],
        }

        # ── 1. Obtener carga ─────────────────────────────────────────────────
        try:
            discador = DiscadorLoad.objects.select_related('campaign').get(
                pk=discador_load_id
            )
        except DiscadorLoad.DoesNotExist:
            result['errors'].append(f'DiscadorLoad {discador_load_id} no encontrada.')
            return result

        provider = discador.campaign   # ProviderRawData

        # Marcar como cargando
        discador.status = 'loading'
        discador.save(update_fields=['status'])

        try:
            # ── 2. LeadCampaign ─────────────────────────────────────────────
            lead_campaign, _ = LeadCampaign.objects.update_or_create(
                name=provider.campaign_name,
                defaults={
                    'description': (
                        f'Importado desde discador: {provider.campaign_name} '
                        f'({provider.upload_date:%Y-%m-%d})'
                    ),
                    'distribution_strategy': strategy,
                    'auto_distribute':       auto_distribute,
                    'is_active':             True,
                },
            )
            result['lead_campaign_id'] = lead_campaign.pk

            # ── 3. Asignar bots ─────────────────────────────────────────────
            if bot_ids:
                bots = BotInstance.objects.filter(pk__in=bot_ids, is_active=True)
                lead_campaign.assigned_bots.set(bots)   # reemplaza — idempotente

            # ── 4. Mapear ContactRecords → Leads ────────────────────────────
            contacts = ContactRecord.objects.filter(campaign=provider)
            created = updated = skipped = 0

            for contact in contacts.iterator():
                try:
                    lead, is_new = self._upsert_lead(contact, lead_campaign)
                    if is_new:
                        created += 1
                    else:
                        updated += 1
                except Exception as e:
                    skipped += 1
                    logger.warning('BOT-3 skip contact %s: %s', contact.ani, e)
                    result['errors'].append(f'ani={contact.ani}: {e}')

            result['created'] = created
            result['updated'] = updated
            result['skipped'] = skipped

            # ── 5. Actualizar LeadCampaign.total_leads ──────────────────────
            total = lead_campaign.leads.count()
            lead_campaign.total_leads = total
            lead_campaign.save(update_fields=['total_leads'])

            # ── 6. Actualizar DiscadorLoad ───────────────────────────────────
            discador.records_loaded    = total
            discador.records_processed = created + updated
            discador.status            = 'loaded'
            discador.save(update_fields=['records_loaded', 'records_processed', 'status'])

            # ── 7. Distribución ──────────────────────────────────────────────
            distributed = 0
            if auto_distribute and lead_campaign.assigned_bots.exists():
                try:
                    distributor = LeadDistributor(lead_campaign)
                    assignments = distributor.distribute_leads()
                    distributed = len(assignments) if assignments else 0
                    result['distributed'] = distributed
                    discador.status = 'in_progress'
                    discador.save(update_fields=['status'])
                except Exception as e:
                    logger.error('BOT-3 distribución falló: %s', e)
                    result['errors'].append(f'Distribución: {e}')

            result['success'] = True
            logger.info(
                'BOT-3 sync OK — campaign=%s created=%d updated=%d distributed=%d',
                lead_campaign.name, created, updated, distributed,
            )

        except Exception as e:
            logger.error('BOT-3 sync error: %s', e, exc_info=True)
            result['errors'].append(str(e))
            # Revertir status si algo catastrófico
            try:
                discador.status = 'pending'
                discador.save(update_fields=['status'])
            except Exception:
                pass

        return result

    @staticmethod
    def _upsert_lead(contact: ContactRecord, lead_campaign: LeadCampaign):
        """
        Crea o actualiza un Lead desde un ContactRecord.
        Clave de idempotencia: phone + campaign.
        """
        custom_data = {
            'ani':             contact.ani,
            'dni':             contact.dni or '',
            'current_product': contact.current_product,
            'offered_product': contact.offered_product,
            'segment':         contact.segment or '',
            'propensity_score':contact.propensity_score,
            'contact_type':    contact.contact_type,
        }

        lead, is_new = Lead.objects.update_or_create(
            phone=contact.ani,
            campaign=lead_campaign,
            defaults={
                'name':        contact.full_name,
                'email':       '',                          # ContactRecord no tiene email
                'phone':       contact.ani,
                'company':     contact.offered_product,    # mejor campo disponible
                'source':      'discador',
                'priority':    _priority_from_score(contact.propensity_score),
                'custom_data': custom_data,
                # Solo resetear a 'new' si está en estados terminales — no pisar asignaciones activas
                # update_or_create toca 'status' solo vía defaults; si el lead ya está
                # assigned/in_progress, el campo se actualiza al mismo valor: no hay problema
                # porque la vista sólo llama sync en discador recién cargados.
            },
        )
        return lead, is_new
