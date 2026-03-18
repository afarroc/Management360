# sim/engine.py
"""
Motor de generación histórica.
Orquesta los 3 generadores de canal, persiste en BD y registra el SimRun.
"""
import time
import logging
from datetime import datetime, timedelta, date

from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)

# Lazy imports para evitar circular en tests
def _get_models():
    from sim.models import SimAccount, SimAgent, Interaction, SimRun
    return SimAccount, SimAgent, Interaction, SimRun

def _get_generators():
    from sim.generators import inbound, outbound, digital
    return inbound, outbound, digital

from sim.generators.base import generate_agent_pool


class HistoricalEngine:
    """
    Genera N días de interacciones para una SimAccount.

    Uso:
        engine = HistoricalEngine(account, user)
        run = engine.generate(date_from, date_to, canales=['inbound','outbound'])
    """

    BATCH_SIZE = 2000   # bulk_create batch

    def __init__(self, account, user):
        self.account = account
        self.user    = user

    def generate(self, date_from: date, date_to: date,
                  canales: list = None) -> 'SimRun':
        """
        Genera todas las interacciones del rango de fechas.
        Crea o reutiliza agentes existentes.
        Returns: SimRun con resultado.
        """
        _, SimAgent, Interaction, SimRun = _get_models()
        inbound_gen, outbound_gen, digital_gen = _get_generators()

        canal   = self.account.canal
        canales = canales or self._default_canales(canal)

        run = SimRun.objects.create(
            account      = self.account,
            date_from    = date_from,
            date_to      = date_to,
            canales      = canales,
            status       = 'running',
            triggered_by = self.user,
        )

        t0 = time.time()
        total_interactions = 0
        cfg = self.account.config

        try:
            # ── Crear / recuperar pool de agentes ─────────────────────────
            agent_objs = list(SimAgent.objects.filter(account=self.account, is_active=True))

            if not agent_objs:
                agent_objs = self._create_agents(cfg, canales)

            # Convertir a dicts para los generadores (evita queries por agente)
            agent_pool = [
                {
                    'codigo':          a.codigo,
                    'turno':           a.turno,
                    'antiguedad':      a.antiguedad,
                    'sph_base':        a.sph_base,
                    'adherencia_base': a.adherencia_base,
                    'tmo_factor':      a.tmo_factor,
                }
                for a in agent_objs
            ]

            # Mapa codigo → SimAgent pk para FK lookup
            agent_pk_map = {a.codigo: a for a in agent_objs}

            # ── Generar día a día ─────────────────────────────────────────
            current = date_from
            lead_offset = Interaction.objects.filter(account=self.account).count()

            buffer = []

            while current <= date_to:
                dt = datetime.combine(current, datetime.min.time())
                day_interactions = []

                if 'inbound' in canales:
                    day_interactions += inbound_gen.generate_day(
                        dt, agent_pool,
                        cfg.get('inbound', {}),
                        lead_offset
                    )
                if 'outbound' in canales:
                    day_interactions += outbound_gen.generate_day(
                        dt, agent_pool,
                        cfg.get('outbound', {}),
                        lead_offset + len(day_interactions)
                    )
                if 'digital' in canales:
                    day_interactions += digital_gen.generate_day(
                        dt, agent_pool,
                        cfg.get('digital', {}),
                        lead_offset + len(day_interactions)
                    )

                # Convertir dicts → Interaction objects
                for row in day_interactions:
                    agent_codigo = row.pop('agent_codigo', None)
                    agent_obj    = agent_pk_map.get(agent_codigo) if agent_codigo else None
                    buffer.append(Interaction(
                        account   = self.account,
                        agent     = agent_obj,
                        **row
                    ))

                lead_offset += len(day_interactions)
                total_interactions += len(day_interactions)

                # Flush buffer
                if len(buffer) >= self.BATCH_SIZE:
                    Interaction.objects.bulk_create(buffer, ignore_conflicts=True)
                    buffer = []
                    logger.info("sim engine: flushed batch at %s — total=%d", current, total_interactions)

                current += timedelta(days=1)

            # Flush final
            if buffer:
                Interaction.objects.bulk_create(buffer, ignore_conflicts=True)

            # ── Actualizar SimRun ─────────────────────────────────────────
            run.status                 = 'done'
            run.interactions_generated = total_interactions
            run.agents_generated       = len(agent_objs)
            run.duration_s             = round(time.time() - t0, 2)
            run.finished_at            = timezone.now()
            run.save()

            logger.info(
                "sim engine: DONE account=%s | %s→%s | %d interactions | %.1fs",
                self.account.name, date_from, date_to, total_interactions, run.duration_s
            )

        except Exception as exc:
            run.status    = 'error'
            run.error_msg = str(exc)
            run.duration_s = round(time.time() - t0, 2)
            run.finished_at = timezone.now()
            run.save()
            logger.error("sim engine ERROR: %s", exc, exc_info=True)

        return run

    def _default_canales(self, canal: str) -> list:
        return {
            'inbound':  ['inbound'],
            'outbound': ['outbound'],
            'digital':  ['digital'],
            'mixed':    ['inbound', 'outbound', 'digital'],
        }.get(canal, ['inbound'])

    def _create_agents(self, cfg: dict, canales: list) -> list:
        """Genera el pool de agentes según el preset del canal."""
        SimAgent = _get_models()[1]

        # Determinar parámetros según canal dominante
        if 'outbound' in canales:
            out_cfg    = cfg.get('outbound', {})
            n_agents   = out_cfg.get('agents', 50)
            sph_base   = out_cfg.get('sph_base', 0.128)
            adh_base   = 0.931
            turnos     = out_cfg.get('turnos', ['MANANA', 'TARDE'])
        else:
            in_cfg   = cfg.get('inbound', {})
            n_agents = in_cfg.get('agents', 22)
            sph_base = 0.087
            adh_base = 0.931
            turnos   = ['MANANA']

        profiles = generate_agent_pool(n_agents, turnos, sph_base, adh_base)

        agent_objs = [
            SimAgent(
                account         = self.account,
                **{k: v for k, v in p.items() if k != 'turno'},
                turno           = p['turno'],
            )
            for p in profiles
        ]
        SimAgent.objects.bulk_create(agent_objs)
        return list(SimAgent.objects.filter(account=self.account, is_active=True))


def get_account_kpis(account) -> dict:
    """KPIs resumidos de una cuenta — para el panel."""
    from sim.models import Interaction
    from django.db.models import Count, Avg, Sum

    qs = Interaction.objects.filter(account=account)
    total = qs.count()
    if total == 0:
        return {'total': 0}

    by_canal  = dict(qs.values_list('canal').annotate(n=Count('id')).values_list('canal', 'n'))
    by_status = dict(qs.values_list('status').annotate(n=Count('id')).values_list('status', 'n'))
    tmo_avg   = qs.filter(duracion_s__gt=0).aggregate(avg=Avg('duracion_s'))['avg'] or 0

    atendidas = by_status.get('atendida', 0) + by_status.get('venta', 0) + by_status.get('agenda', 0)
    return {
        'total':         total,
        'by_canal':      by_canal,
        'by_status':     by_status,
        'atendidas':     atendidas,
        'abandonadas':   by_status.get('abandonada', 0),
        'no_contacto':   by_status.get('no_contacto', 0),
        'ventas':        by_status.get('venta', 0),
        'tmo_avg_s':     round(tmo_avg),
        'abandon_rate':  round(by_status.get('abandonada', 0) / max(atendidas + by_status.get('abandonada', 0), 1), 4),
    }
