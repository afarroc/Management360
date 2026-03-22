# sim/models.py
import uuid
from django.db import models
from django.conf import settings  # IMPORTANTE: añadir esta línea

CANAL_CHOICES = [
    ('inbound',  'Inbound Voz'),
    ('outbound', 'Outbound Discador'),
    ('digital',  'Digital (Chat/Mail/App)'),
    ('mixed',    'Mixto'),
]

ACCOUNT_TYPE_CHOICES = [
    ('banking', 'Banca'),
    ('telco',   'Telecomunicaciones'),
    ('retail',  'Retail'),
    ('generic', 'Genérico'),
]

TURNO_CHOICES = [
    ('MANANA', 'Mañana'),
    ('TARDE',  'Tarde'),
    ('NOCHE',  'Noche'),
]

ANTIGUEDAD_CHOICES = [
    ('junior', 'Junior (< 3 meses)'),
    ('senior', 'Senior (> 3 meses)'),
]

STATUS_CHOICES = [
    ('atendida',    'Atendida'),
    ('abandonada',  'Abandonada'),
    ('no_contacto', 'No Contacto'),
    ('venta',       'Venta'),
    ('agenda',      'Agenda / Callback'),
    ('rechazo',     'Rechazo'),
]


class SimAccount(models.Model):
    """
    Cuenta o campaña simulada. Contiene la configuración completa
    para generar interacciones realistas por canal.

    config JSONField por canal:

    inbound: {
        weekday_vol, weekend_vol, tmo_s, acw_s, agents, abandon_rate,
        sl_s, schedule_start, schedule_end,
        intraday: {9: 0.123, 10: 0.135, ...},
        skills: {
            "PLD": {weight: 0.657, tipificaciones: {"CUOTA MENSUAL": 0.473, ...}},
            ...
        }
    }

    outbound: {
        daily_marcaciones, contact_rate, conv_rate, agenda_rate,
        agents, absence_rate, sph_base, arpu,
        turnos: ["MANANA", "TARDE"],
        no_contact: {"no_contesta": 0.524, "buzon": 0.328, ...},
        tipificaciones_contacto: {"Venta": 0.0084, "Agenda (Usuario)": 0.076, ...},
        producto: {"PORTABILIDAD": 0.92, "LINEA NUEVA": 0.08}
    }

    digital: {
        daily_vol, channels: {"bxi": 0.849, "app": 0.151},
        duration_s,
        tipificaciones: {"BXI_ACTIVACION USUARIO NUEVO": 0.634, ...}
    }
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name         = models.CharField(max_length=200, verbose_name='Nombre')
    canal        = models.CharField(max_length=20, choices=CANAL_CHOICES)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='generic')
    preset       = models.CharField(max_length=50, blank=True,
                                    help_text='Preset usado: banking_inbound / telco_outbound / banking_digital')
    config       = models.JSONField(default=dict)
    is_active    = models.BooleanField(default=True)
    created_by   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sim_accounts')

    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Cuenta simulada'
        verbose_name_plural = 'Cuentas simuladas'
        ordering            = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.get_canal_display()})"

    @property
    def interaction_count(self):
        return self.interactions.count()


class SimAgent(models.Model):
    """
    Agente simulado con perfil de rendimiento individual.
    SPH y adherencia tienen varianza gaussiana respecto al promedio del preset.
    """
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account         = models.ForeignKey(SimAccount, on_delete=models.CASCADE, related_name='agents')
    codigo          = models.CharField(max_length=20)   # AGT-001, AGT-002...
    turno           = models.CharField(max_length=10, choices=TURNO_CHOICES, default='MANANA')
    antiguedad      = models.CharField(max_length=10, choices=ANTIGUEDAD_CHOICES, default='senior')
    sph_base        = models.FloatField(default=0.128,
                                        help_text='Sales/ventas por hora base del agente')
    adherencia_base = models.FloatField(default=0.931,
                                        help_text='Adherencia base 0.0-1.0')
    tmo_factor      = models.FloatField(default=1.0,
                                        help_text='Factor sobre TMO base (1.0 = promedio)')
    is_active       = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Agente simulado'
        verbose_name_plural = 'Agentes simulados'
        unique_together     = [('account', 'codigo')]
        ordering            = ['codigo']

    def __str__(self):
        return f"{self.codigo} [{self.get_turno_display()} / {self.get_antiguedad_display()}]"


class Interaction(models.Model):
    """
    Cada contacto generado por el simulador.
    is_simulated=True siempre — permite coexistir con datos reales en el futuro.
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account      = models.ForeignKey(SimAccount, on_delete=models.CASCADE, related_name='interactions')
    agent        = models.ForeignKey(SimAgent, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='interactions')

    # Canal y producto
    canal        = models.CharField(max_length=20, choices=CANAL_CHOICES)
    skill        = models.CharField(max_length=100, blank=True)    # PLD / CONVENIOS / etc.
    sub_canal    = models.CharField(max_length=50, blank=True)     # bxi / app / porta / chip

    # Tiempo
    fecha        = models.DateField()
    hora_inicio  = models.DateTimeField()
    hora_fin     = models.DateTimeField()
    duracion_s   = models.IntegerField(default=0)
    acw_s        = models.IntegerField(default=0)

    # Resultado
    tipificacion = models.CharField(max_length=200, blank=True)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES)
    lead_id      = models.CharField(max_length=50, blank=True)     # ID sintético

    # Outbound específico
    intento_num  = models.IntegerField(default=1)                  # nro. de intento al lead

    # Meta
    is_simulated = models.BooleanField(default=True, editable=False)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Interacción simulada'
        verbose_name_plural = 'Interacciones simuladas'
        ordering            = ['hora_inicio']
        indexes             = [
            models.Index(fields=['account', 'fecha']),
            models.Index(fields=['account', 'canal', 'fecha']),
            models.Index(fields=['agent', 'fecha']),
        ]

    def __str__(self):
        return f"{self.canal} | {self.fecha} {self.hora_inicio:%H:%M} | {self.status}"

    @property
    def tmo_total_s(self):
        return self.duracion_s + self.acw_s


class SimRun(models.Model):
    """
    Registro de cada ejecución del generador histórico.
    Permite saber cuándo se generó, cuánto tardó y cuántas interacciones produjo.
    """
    STATUS = [
        ('running', 'Ejecutando'),
        ('done',    'Completado'),
        ('error',   'Error'),
    ]
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account      = models.ForeignKey(SimAccount, on_delete=models.CASCADE, related_name='runs')
    date_from    = models.DateField()
    date_to      = models.DateField()
    canales      = models.JSONField(default=list)       # ["inbound","outbound","digital"]
    status       = models.CharField(max_length=10, choices=STATUS, default='running')
    interactions_generated = models.IntegerField(default=0)
    agents_generated       = models.IntegerField(default=0)
    duration_s   = models.FloatField(default=0.0)
    error_msg    = models.TextField(blank=True)
    triggered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sim_runs')
    started_at   = models.DateTimeField(auto_now_add=True)
    finished_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name        = 'Ejecución de simulación'
        verbose_name_plural = 'Ejecuciones de simulación'
        ordering            = ['-started_at']

    def __str__(self):
        return f"{self.account.name} | {self.date_from}→{self.date_to} | {self.status}"

# ─────────────────────────────────────────────────────────────────────────────
# SIM-5 — Training Mode
# ─────────────────────────────────────────────────────────────────────────────

class TrainingScenario(models.Model):
    """
    Escenario de training reutilizable y reproducible.

    events = [
        {
            "at_sim_min": 30,
            "type":       "volume_spike",
            "params":     {"pct": 30},
            "hint":       "Pico de volumen +30% — ¿qué harías?",
            "auto":       true
        },
    ]

    expected_actions = [
        {
            "after_event_idx": 0,
            "within_min":      10,
            "description":     "Escalar a supervisor o solicitar refuerzo"
        }
    ]
    """
    DIFFICULTY = [
        ('easy',   'Básico'),
        ('medium', 'Intermedio'),
        ('hard',   'Avanzado'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=200, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    canal       = models.CharField(max_length=20, choices=CANAL_CHOICES, default='inbound')
    difficulty  = models.CharField(max_length=10, choices=DIFFICULTY, default='medium')
    account     = models.ForeignKey(
        SimAccount, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='training_scenarios',
        verbose_name='Cuenta simulada',
    )
    clock_speed      = models.IntegerField(default=15)
    thresholds       = models.JSONField(default=dict)
    events           = models.JSONField(default=list)
    expected_actions = models.JSONField(default=list)
    is_public        = models.BooleanField(default=False)    
    created_by       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='training_scenarios')
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Escenario de training'
        verbose_name_plural = 'Escenarios de training'
        ordering            = ['-updated_at']

    def __str__(self):
        return f"{self.name} [{self.get_difficulty_display()}] — {self.get_canal_display()}"

    @property
    def event_count(self):
        return len(self.events)

    @property
    def session_count(self):
        return self.sessions.count()


class TrainingSession(models.Model):
    """
    Ejecución de un TrainingScenario por un analista.

    actions_log = [
        {
            "sim_time":  "10:45",
            "real_ts":   "2026-03-17T20:31:00",
            "action":    "Solicité refuerzo de 3 agentes",
            "event_ref": 0
        }
    ]

    score_detail = {
        "base": 100, "sl_alerts": -20, "abandon_alerts": -10,
        "events_responded": 15, "final_sl_bonus": 10, "total": 95
    }
    """
    STATUS = [
        ('active',    'En curso'),
        ('completed', 'Completada'),
        ('abandoned', 'Abandonada'),
    ]

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scenario         = models.ForeignKey(TrainingScenario, on_delete=models.CASCADE, related_name='sessions')
    trainee          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='training_sessions')    
    sim_date         = models.DateField(null=True, blank=True)
    status           = models.CharField(max_length=15, choices=STATUS, default='active')
    score            = models.IntegerField(default=0)
    score_detail     = models.JSONField(default=dict)
    alerts_count     = models.IntegerField(default=0)
    events_responded = models.IntegerField(default=0)
    actions_log      = models.JSONField(default=list)
    final_kpis       = models.JSONField(default=dict)
    trainer_notes    = models.TextField(blank=True)
    started_at       = models.DateTimeField(auto_now_add=True)
    finished_at      = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name        = 'Sesión de training'
        verbose_name_plural = 'Sesiones de training'
        ordering            = ['-started_at']

    def __str__(self):
        return (f"{self.scenario.name} | {self.trainee.username} | "
                f"{self.get_status_display()} | score:{self.score}")

# ─────────────────────────────────────────────────────────────────────────────
# SIM-6a — SimAgentProfile
# Perfil conductual reutilizable para agentes simulados.
# ─────────────────────────────────────────────────────────────────────────────

class SimAgentProfile(models.Model):
    """
    Perfil conductual de agente simulado.
    Define comportamiento realista en llamadas: velocidad, hold, cortes,
    conversión, ausencias y multi-skill.

    Presets del sistema (is_preset=True):
        top:   aht×0.85 · conv 2.5% · hold 2% · corte 1% · available 92%
        alto:  aht×0.95 · conv 1.5% · hold 5% · corte 3% · available 87%
        medio: aht×1.05 · conv 0.8% · hold 10%· corte 8% · available 80%
        bajo:  aht×1.30 · conv 0.3% · hold 18%· corte 15%· available 70%
    """
    TIER = [
        ('top',   'Top'),
        ('alto',  'Alto'),
        ('medio', 'Medio'),
        ('bajo',  'Bajo'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=200, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    tier        = models.CharField(max_length=10, choices=TIER, default='medio',
                                   verbose_name='Nivel')
    canal       = models.CharField(max_length=20, choices=CANAL_CHOICES, default='inbound',
                                   verbose_name='Canal')

    # ── Velocidad ─────────────────────────────────────────────────────────────
    aht_factor      = models.FloatField(default=1.0,
        help_text='Multiplicador sobre AHT base del preset (0.85 = 15% más rápido)')
    acw_factor      = models.FloatField(default=1.0,
        help_text='Multiplicador sobre ACW base')
    available_pct   = models.FloatField(default=0.85,
        help_text='Fracción de tiempo logueado en estado Available')

    # ── Comportamiento en llamada ──────────────────────────────────────────────
    answer_rate     = models.FloatField(default=0.95,
        help_text='Fracción de llamadas que atiende (vs rechaza/deja ring)')
    hold_rate       = models.FloatField(default=0.05,
        help_text='Fracción de llamadas que pone en hold')
    hold_dur_s      = models.IntegerField(default=30,
        help_text='Duración media del hold en segundos')
    transfer_rate   = models.FloatField(default=0.04,
        help_text='Fracción de llamadas que transfiere')
    corte_rate      = models.FloatField(default=0.05,
        help_text='Fracción de llamadas donde corta antes de finalizar ACW')

    # ── Resultados comerciales ─────────────────────────────────────────────────
    conv_rate       = models.FloatField(default=0.008,
        help_text='Tasa de conversión a venta sobre contactos')
    agenda_rate     = models.FloatField(default=0.128,
        help_text='Tasa de agendamiento sobre contactos')

    # ── Ausencias y shrinkage ──────────────────────────────────────────────────
    break_freq      = models.FloatField(default=1.0,
        help_text='Breaks no programados por hora')
    break_dur_s     = models.IntegerField(default=300,
        help_text='Duración media del break no programado en segundos')
    shrinkage       = models.FloatField(default=0.10,
        help_text='Fracción de tiempo improductivo total (0.10 = 10%)')

    # ── Multi-skill ────────────────────────────────────────────────────────────
    skills          = models.JSONField(default=list,
        help_text='Skills que puede atender ["PORTABILIDAD", "LINEA NUEVA"]')
    skill_priority  = models.JSONField(default=dict,
        help_text='Prioridad por skill {"PORTABILIDAD": 1, "LINEA NUEVA": 2}')

    # ── Meta ──────────────────────────────────────────────────────────────────
    # BOT-2: Si is_preset=True y bot_specialization != '', este perfil se asigna
    # automáticamente al registrar un BotInstance con esa specialization en ACD.
    bot_specialization = models.CharField(
        max_length=50, blank=True,
        help_text=(
            'Especialización de BotInstance compatible. '
            'Valores: gtd_processor | project_manager | task_executor | '
            'calendar_optimizer | communication_handler | general_assistant. '
            'Vacío = perfil de uso general.'
        ),
    )
    is_preset   = models.BooleanField(
        default=False,
        help_text='True = preset del sistema (no editable por usuarios)',
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sim_agent_profiles')    
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Perfil de agente simulado'
        verbose_name_plural = 'Perfiles de agente simulado'
        ordering            = ['tier', 'name']

    def __str__(self):
        return f"{self.name} [{self.get_tier_display()}] — {self.get_canal_display()}"

# ─────────────────────────────────────────────────────────────────────────────
# SIM-7a — ACD Simulator
# Sesión multi-agente con enrutamiento real/simulado.
# ─────────────────────────────────────────────────────────────────────────────

ACD_DIALING_MODE = [
    ('predictive',  'Predictivo'),
    ('progressive', 'Progresivo'),
    ('manual',      'Manual'),
]

ACD_SESSION_STATUS = [
    ('config',    'Configurando'),
    ('active',    'Activa'),
    ('paused',    'Pausada'),
    ('finished',  'Finalizada'),
]

ACD_AGENT_TYPE = [
    ('real',      'OJT Real'),
    ('simulated', 'Simulado'),
    ('bot',       'Bot FTE'),        # BOT-2
]

ACD_AGENT_STATUS = [
    ('offline',   'Offline'),
    ('available', 'Disponible'),
    ('ringing',   'Timbrando'),
    ('on_call',   'En Llamada'),
    ('acw',       'Post-llamada'),
    ('break',     'Break'),
    ('absent',    'Ausente'),
]

ACD_AGENT_LEVEL = [
    ('basic',        'Básico'),
    ('intermediate', 'Intermedio'),
    ('advanced',     'Avanzado'),
]

ACD_INTERACTION_STATUS = [
    ('queued',    'En cola'),
    ('ringing',   'Timbrando'),
    ('on_call',   'En llamada'),
    ('acw',       'Post-llamada'),
    ('completed', 'Completada'),
    ('abandoned', 'Abandonada'),
    ('rejected',  'Rechazada'),
]

ACD_ACTION_TYPE = [
    ('answer',    'Atender'),
    ('reject',    'Rechazar'),
    ('hold',      'Hold'),
    ('unhold',    'Retomar'),
    ('transfer',  'Transferir'),
    ('tipify',    'Tipificar'),
    ('end_acw',   'Finalizar ACW'),
    ('break',     'Ir a Break'),
    ('return',    'Volver de Break'),
    ('note',      'Nota'),
]


class ACDSession(models.Model):
    """
    Sesión ACD multi-agente.
    Coordina N ACDAgentSlots (reales OJT + simulados) sobre un motor GTR.

    dialing_mode:
      predictive  → motor lanza N llamadas por ocupación del equipo
      progressive → una llamada por agente libre, motor espera liberación
      manual      → el agente decide cuándo marcar (solo outbound)

    gtr_session_id → Redis key del GTR subyacente (clock, interacciones)
    """
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name           = models.CharField(max_length=200, verbose_name='Nombre')
    account        = models.ForeignKey(
        SimAccount, on_delete=models.CASCADE, related_name='acd_sessions',
        verbose_name='Cuenta simulada',
    )
    dialing_mode   = models.CharField(
        max_length=15, choices=ACD_DIALING_MODE, default='progressive',
        verbose_name='Modo de discado',
    )
    canal          = models.CharField(max_length=20, choices=CANAL_CHOICES, default='inbound')
    clock_speed    = models.IntegerField(default=15)
    sim_date       = models.DateField(null=True, blank=True)
    status         = models.CharField(max_length=10, choices=ACD_SESSION_STATUS, default='config')
    gtr_session_id = models.CharField(max_length=100, blank=True,
                                      verbose_name='ID sesión GTR (Redis)')
    thresholds     = models.JSONField(default=dict, verbose_name='Umbrales de alerta')
    config         = models.JSONField(default=dict, verbose_name='Configuración adicional')
    # config puede incluir:
    # {'agents_target': 10, 'max_queue_time': 30, 'routing': 'skill_based'|'round_robin'}

    created_by     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='acd_sessions')    
    started_at     = models.DateTimeField(auto_now_add=True)
    finished_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name        = 'Sesión ACD'
        verbose_name_plural = 'Sesiones ACD'
        ordering            = ['-started_at']

    def __str__(self):
        return f"{self.name} | {self.get_dialing_mode_display()} | {self.get_status_display()}"

    @property
    def slot_count(self):
        return self.slots.count()

    @property
    def active_agents(self):
        return self.slots.exclude(status__in=['offline', 'absent']).count()


class ACDAgentSlot(models.Model):
    """
    Slot de agente dentro de una ACDSession.

    Puede ser:
      - real OJT: user FK → recibe llamadas en su pantalla
      - simulated: profile FK → el motor resuelve automáticamente según perfil

    stats JSONField:
    {
        'atendidas': int, 'rechazadas': int, 'ventas': int,
        'agenda': int, 'no_contacto': int,
        'tmo_sum_s': int, 'tmo_count': int,
        'hold_count': int, 'transfer_count': int
    }
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session      = models.ForeignKey(ACDSession, on_delete=models.CASCADE, related_name='slots')
    slot_number  = models.IntegerField(default=1, verbose_name='Nro. slot')

    agent_type   = models.CharField(max_length=10, choices=ACD_AGENT_TYPE, default='simulated')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True, blank=True,
        on_delete=models.SET_NULL, 
        related_name='acd_slots',
        verbose_name='Usuario OJT',
    )    
    profile      = models.ForeignKey(
        SimAgentProfile, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='acd_slots',
        verbose_name='Perfil simulado',
    )
    display_name = models.CharField(max_length=100, blank=True,
                                    verbose_name='Nombre para display')
    skill        = models.CharField(max_length=100, blank=True,
                                    verbose_name='Skill activo')
    status       = models.CharField(max_length=12, choices=ACD_AGENT_STATUS, default='offline')
    level        = models.CharField(max_length=15, choices=ACD_AGENT_LEVEL, default='basic',
                                    verbose_name='Nivel OJT (solo real)')

    stats        = models.JSONField(default=dict, verbose_name='Métricas acumuladas')

    class Meta:
        verbose_name        = 'Slot de agente ACD'
        verbose_name_plural = 'Slots de agente ACD'
        ordering            = ['session', 'slot_number']
        unique_together     = [('session', 'slot_number')]

    def __str__(self):
        label = self.display_name or (
            self.user.username if self.user else
            str(self.profile) if self.profile else f"Slot-{self.slot_number}"
        )
        return f"{self.session.name} | {label} [{self.get_status_display()}]"

    @property
    def name(self):
        if self.display_name:
            return self.display_name
        if self.agent_type == 'real' and self.user:
            return self.user.get_full_name() or self.user.username
        if self.profile:
            return self.profile.name
        return f"Agente {self.slot_number}"

    @property
    def aht_s(self):
        s = self.stats
        if s.get('tmo_count', 0) == 0:
            return 0
        return int(s.get('tmo_sum_s', 0) / s['tmo_count'])


class ACDInteraction(models.Model):
    """
    Interacción asignada a un slot en una sesión ACD.

    Ciclo de vida:
      queued → ringing → on_call → acw → completed
                       ↘ abandoned (sin respuesta)
                       ↘ rejected  (agente rechaza)

    Para agentes reales (OJT): el agente ve esta interacción y actúa.
    Para agentes simulados: el motor resuelve automáticamente según el perfil.
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session      = models.ForeignKey(ACDSession, on_delete=models.CASCADE,
                                     related_name='acd_interactions')
    slot         = models.ForeignKey(ACDAgentSlot, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='acd_interactions')

    canal        = models.CharField(max_length=20, choices=CANAL_CHOICES)
    skill        = models.CharField(max_length=100, blank=True)
    lead_id      = models.CharField(max_length=50, blank=True)
    status       = models.CharField(max_length=12, choices=ACD_INTERACTION_STATUS,
                                    default='queued')

    # Timestamps del ciclo de vida
    queued_at    = models.DateTimeField(auto_now_add=True)
    assigned_at  = models.DateTimeField(null=True, blank=True)
    answered_at  = models.DateTimeField(null=True, blank=True)
    ended_at     = models.DateTimeField(null=True, blank=True)

    # KPIs calculados al cerrar
    duration_s   = models.IntegerField(default=0)
    acw_s        = models.IntegerField(default=0)
    hold_s       = models.IntegerField(default=0)

    # Tipificación del agente
    tipificacion     = models.CharField(max_length=200, blank=True)
    sub_tipificacion = models.CharField(max_length=200, blank=True)
    notes            = models.TextField(blank=True)

    is_simulated = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Interacción ACD'
        verbose_name_plural = 'Interacciones ACD'
        ordering            = ['-queued_at']
        indexes             = [
            models.Index(fields=['session', 'status']),
            models.Index(fields=['slot', 'queued_at']),
        ]

    def __str__(self):
        return f"{self.session.name} | {self.canal} | {self.lead_id} | {self.get_status_display()}"

    @property
    def wait_s(self):
        if self.answered_at and self.queued_at:
            return int((self.answered_at - self.queued_at).total_seconds())
        return 0


class ACDAgentAction(models.Model):
    """
    Acción registrada por un agente OJT durante una interacción.

    action_type:
      answer    → el agente atiende la llamada
      reject    → el agente rechaza
      hold      → pone en espera
      unhold    → retoma
      transfer  → transfiere (params: {to_slot_id, to_skill, reason})
      tipify    → tipifica (params: {tipificacion, sub, notes})
      end_acw   → finaliza el ACW y se marca disponible
      break     → solicita break (params: {reason})
      return    → vuelve de break
      note      → nota libre (params: {text})

    Registradas en tiempo real para evaluación del trainer.
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    interaction  = models.ForeignKey(ACDInteraction, on_delete=models.CASCADE,
                                     related_name='agent_actions')
    slot         = models.ForeignKey(ACDAgentSlot, on_delete=models.CASCADE,
                                     related_name='agent_actions')
    action_type  = models.CharField(max_length=15, choices=ACD_ACTION_TYPE)
    params       = models.JSONField(default=dict)
    sim_time     = models.CharField(max_length=5, blank=True)   # "10:45"
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Acción de agente ACD'
        verbose_name_plural = 'Acciones de agente ACD'
        ordering            = ['created_at']

    def __str__(self):
        return (f"{self.slot.name} | {self.get_action_type_display()} | "
                f"{self.sim_time} | {self.created_at:%H:%M:%S}")
