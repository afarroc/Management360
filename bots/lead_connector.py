# bots/lead_connector.py
"""
BOT-3b: Conectores de leads externos → sistema de bots M360.

Arquitectura:
  - process_webhook_payload(source, payload) es el punto de entrada único.
  - El endpoint HTTP /bots/webhook/<source>/ lo llama tras autenticar.
  - sim/views/acd.py lo llama directamente (sin HTTP) para coherencia.
  - Añadir un conector nuevo = subclasear BaseLeadConnector + registrar en CONNECTORS.

Schema normalizado (LeadData):
    {
        'source':        str,   # 'sim' | 'vicidial' | 'purecloud'
        'external_id':   str,   # ID único en el sistema origen
        'phone':         str,   # ANI / número marcado — clave de idempotencia
        'name':          str,   # Nombre del contacto
        'campaign_name': str,   # Nombre de la LeadCampaign destino
        'result':        str,   # Tipificación / disposición
        'duration_s':    int,   # Duración de la interacción en segundos
        'acw_s':         int,   # Post-llamada
        'agent_id':      str,   # ID del agente en el sistema origen
        'agent_name':    str,
        'skill':         str,
        'canal':         str,   # inbound | outbound | digital
        'metadata':      dict,  # Datos extra del origen
    }
"""

import logging
from django.db import transaction

from .models import LeadCampaign, Lead

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Schema vacío — evita KeyError en conectores que no tengan todos los campos
# ─────────────────────────────────────────────────────────────────────────────

EMPTY_LEAD_DATA = {
    'source':        '',
    'external_id':   '',
    'phone':         '',
    'name':          '',
    'campaign_name': '',
    'result':        '',
    'duration_s':    0,
    'acw_s':         0,
    'agent_id':      '',
    'agent_name':    '',
    'skill':         '',
    'canal':         'inbound',
    'metadata':      {},
}


# ─────────────────────────────────────────────────────────────────────────────
# Conectores
# ─────────────────────────────────────────────────────────────────────────────

class BaseLeadConnector:
    source = ''

    def normalize(self, payload: dict) -> dict:
        """Transforma el payload del origen al schema normalizado."""
        raise NotImplementedError


class SimConnector(BaseLeadConnector):
    """
    Conector para ACDInteractions completadas en sim.

    Payload emitido por sim/views/acd.py._emit_completed():
    {
        "source":        "sim",
        "external_id":   "uuid-ACDInteraction",
        "phone":         "INB-000123",          # lead_id sintético
        "name":          "Contacto INB-000123",
        "campaign_name": "Banca Telefónica Q1", # session.account.name
        "result":        "Venta",               # tipificacion
        "duration_s":    320,
        "acw_s":         18,
        "agent_id":      "uuid-ACDAgentSlot",
        "agent_name":    "Bot_FTE_1",
        "skill":         "PLD",
        "canal":         "inbound",
        "metadata": {
            "session_id":   "uuid-ACDSession",
            "slot_number":  3,
            "is_simulated": true,
            "hold_s":       0
        }
    }
    """
    source = 'sim'

    def normalize(self, payload: dict) -> dict:
        data = {**EMPTY_LEAD_DATA}
        data.update({
            'source':        'sim',
            'external_id':   payload.get('external_id', ''),
            'phone':         payload.get('phone', ''),
            'name':          payload.get('name', ''),
            'campaign_name': payload.get('campaign_name', 'Simulación ACD'),
            'result':        payload.get('result', ''),
            'duration_s':    int(payload.get('duration_s', 0)),
            'acw_s':         int(payload.get('acw_s', 0)),
            'agent_id':      payload.get('agent_id', ''),
            'agent_name':    payload.get('agent_name', ''),
            'skill':         payload.get('skill', ''),
            'canal':         payload.get('canal', 'inbound'),
            'metadata':      payload.get('metadata', {}),
        })
        return data


class VicidialConnector(BaseLeadConnector):
    """
    Conector para VICIdial agent_events.php.

    Payload típico (form-encoded o JSON según configuración):
    {
        "lead_id":       "4521",
        "phone_number":  "0991234567",
        "full_name":     "Juan Pérez",
        "status":        "SALE",
        "campaign_id":   "PORTABILIDAD",
        "user":          "agent01",
        "length_in_sec": "185",
        "call_date":     "2026-03-22 14:30:00",
        "comments":      "interesado portabilidad"
    }

    Referencia: VICIdial agent_events.php → custom_fields o AGI variables.
    Adaptar según la configuración específica de la instancia.
    """
    source = 'vicidial'

    # Mapa de disposiciones VICIdial → tipificación M360
    STATUS_MAP = {
        'SALE':      'Venta',
        'A':         'Agenda',
        'CB':        'Agenda',
        'N':         'No interesado',
        'NI':        'No interesado',
        'NA':        'No contesta',
        'B':         'Buzon de voz',
        'DC':        'Número inválido',
        'DROP':      'Corte',
    }

    def normalize(self, payload: dict) -> dict:
        raw_status = payload.get('status', '')
        result = self.STATUS_MAP.get(raw_status.upper(), raw_status)
        try:
            duration = int(payload.get('length_in_sec', 0))
        except (ValueError, TypeError):
            duration = 0

        data = {**EMPTY_LEAD_DATA}
        data.update({
            'source':        'vicidial',
            'external_id':   str(payload.get('lead_id', '')),
            'phone':         payload.get('phone_number', ''),
            'name':          payload.get('full_name', payload.get('phone_number', '')),
            'campaign_name': payload.get('campaign_id', 'VICIdial'),
            'result':        result,
            'duration_s':    duration,
            'acw_s':         0,   # VICIdial no reporta ACW separado
            'agent_id':      payload.get('user', ''),
            'agent_name':    payload.get('user', ''),
            'skill':         payload.get('campaign_id', ''),
            'canal':         'outbound',   # VICIdial es principalmente outbound
            'metadata': {
                'raw_status': raw_status,
                'call_date':  payload.get('call_date', ''),
                'comments':   payload.get('comments', ''),
            },
        })
        return data


class PureCloudConnector(BaseLeadConnector):
    """
    Conector para Genesys PureCloud / Cloud webhooks.

    Payload típico (conversationEnd event):
    {
        "id":                "conv-uuid",
        "conversationStart":  "2026-03-22T14:30:00Z",
        "conversationEnd":    "2026-03-22T14:35:20Z",
        "participants": [
            {
                "participantId": "part-uuid",
                "participantName": "Juan Pérez",
                "purpose": "customer",
                "ani": "0991234567",
                "wrapupCode": "VENTA",
                "wrapupNote": "interesado en portabilidad"
            },
            {
                "participantId": "agent-uuid",
                "participantName": "Agent Smith",
                "purpose": "agent",
                "queueName": "PORTABILIDAD"
            }
        ]
    }

    Referencia: Genesys Cloud Conversation End event schema.
    Adaptar campos según suscripción configurada en EventBridge/webhook.
    """
    source = 'purecloud'

    def normalize(self, payload: dict) -> dict:
        participants = payload.get('participants', [])

        customer  = next((p for p in participants if p.get('purpose') == 'customer'), {})
        agent     = next((p for p in participants if p.get('purpose') == 'agent'), {})

        # Duración desde timestamps ISO
        duration_s = 0
        try:
            from datetime import datetime, timezone as tz
            fmt = '%Y-%m-%dT%H:%M:%SZ'
            start = datetime.strptime(payload['conversationStart'], fmt).replace(tzinfo=tz.utc)
            end   = datetime.strptime(payload['conversationEnd'],   fmt).replace(tzinfo=tz.utc)
            duration_s = int((end - start).total_seconds())
        except Exception:
            pass

        data = {**EMPTY_LEAD_DATA}
        data.update({
            'source':        'purecloud',
            'external_id':   payload.get('id', ''),
            'phone':         customer.get('ani', ''),
            'name':          customer.get('participantName', customer.get('ani', '')),
            'campaign_name': agent.get('queueName', 'PureCloud'),
            'result':        customer.get('wrapupCode', ''),
            'duration_s':    duration_s,
            'acw_s':         0,
            'agent_id':      agent.get('participantId', ''),
            'agent_name':    agent.get('participantName', ''),
            'skill':         agent.get('queueName', ''),
            'canal':         'inbound',
            'metadata': {
                'conversation_start': payload.get('conversationStart', ''),
                'conversation_end':   payload.get('conversationEnd', ''),
                'wrapup_note':        customer.get('wrapupNote', ''),
                'raw_participants':   participants,
            },
        })
        return data


# ─────────────────────────────────────────────────────────────────────────────
# Registro de conectores — añadir aquí nuevos orígenes
# ─────────────────────────────────────────────────────────────────────────────

CONNECTORS = {
    'sim':        SimConnector(),
    'vicidial':   VicidialConnector(),
    'purecloud':  PureCloudConnector(),
}


# ─────────────────────────────────────────────────────────────────────────────
# Punto de entrada único
# ─────────────────────────────────────────────────────────────────────────────

def process_webhook_payload(source: str, payload: dict) -> dict:
    """
    Normaliza el payload del origen y upserta el Lead en M360.

    Llamado desde:
      - bots/views.webhook_receiver()     ← VICIdial, PureCloud (vía HTTP)
      - sim/views/acd._emit_completed()   ← sim (llamada directa, sin HTTP)

    Returns:
        {'success': bool, 'lead_id': int|None, 'created': bool, 'error': str}
    """
    connector = CONNECTORS.get(source)
    if not connector:
        return {'success': False, 'lead_id': None, 'created': False,
                'error': f'Conector desconocido: {source}'}

    try:
        lead_data = connector.normalize(payload)
    except Exception as e:
        logger.error('lead_connector normalize error [%s]: %s', source, e)
        return {'success': False, 'lead_id': None, 'created': False, 'error': str(e)}

    if not lead_data.get('phone'):
        return {'success': False, 'lead_id': None, 'created': False,
                'error': 'phone vacío — no se puede identificar el lead'}

    try:
        lead, created = _upsert_lead(lead_data)
        logger.info('lead_connector [%s] %s lead=%s phone=%s result=%s',
                    source, 'CREATED' if created else 'UPDATED',
                    lead.pk, lead_data['phone'], lead_data['result'])
        return {'success': True, 'lead_id': lead.pk, 'created': created, 'error': ''}
    except Exception as e:
        logger.error('lead_connector upsert error [%s]: %s', source, e, exc_info=True)
        return {'success': False, 'lead_id': None, 'created': False, 'error': str(e)}


def _upsert_lead(lead_data: dict):
    """Crea o actualiza Lead. Clave: phone + campaign."""
    with transaction.atomic():
        campaign, _ = LeadCampaign.objects.get_or_create(
            name=lead_data['campaign_name'],
            defaults={
                'description':           f'Auto-creada desde conector {lead_data["source"]}',
                'auto_distribute':       False,   # el trainer asigna bots manualmente
                'distribution_strategy': 'equal_split',
                'is_active':             True,
            },
        )

        lead, created = Lead.objects.update_or_create(
            phone=lead_data['phone'],
            campaign=campaign,
            defaults={
                'name':        lead_data['name'] or lead_data['phone'],
                'email':       '',
                'phone':       lead_data['phone'],
                'company':     lead_data['skill'] or lead_data['campaign_name'],
                'source':      lead_data['source'],
                'notes':       lead_data['result'],
                'custom_data': {
                    'external_id': lead_data['external_id'],
                    'result':      lead_data['result'],
                    'duration_s':  lead_data['duration_s'],
                    'acw_s':       lead_data['acw_s'],
                    'agent_id':    lead_data['agent_id'],
                    'agent_name':  lead_data['agent_name'],
                    'skill':       lead_data['skill'],
                    'canal':       lead_data['canal'],
                    **lead_data['metadata'],
                },
                # No tocar status si el lead ya tiene asignación activa
            },
        )

        # Solo actualizar stats de la campaña en creación
        if created:
            LeadCampaign.objects.filter(pk=campaign.pk).update(
                total_leads=campaign.leads.count()
            )

    return lead, created
