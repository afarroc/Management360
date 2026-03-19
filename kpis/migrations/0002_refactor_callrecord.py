# kpis/migrations/0002_refactor_callrecord.py
"""
Sprint 7 — KPI-1: Refactor CallRecord + ExchangeRate.
MySQL-safe: usa RunSQL con IF NOT EXISTS para evitar errores en columnas existentes.
"""
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('kpis', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [

        # ── CallRecord: agregar columnas nuevas (IF NOT EXISTS — MySQL safe) ──

        migrations.RunSQL(
            sql="""
                ALTER TABLE kpis_callrecord
                    ADD COLUMN IF NOT EXISTS uuid          CHAR(32)     NULL,
                    ADD COLUMN IF NOT EXISTS fecha         DATE         NULL,
                    ADD COLUMN IF NOT EXISTS created_by_id INT          NULL,
                    ADD COLUMN IF NOT EXISTS created_at    DATETIME(6)  NULL;
            """,
            reverse_sql="""
                ALTER TABLE kpis_callrecord
                    DROP COLUMN IF EXISTS uuid,
                    DROP COLUMN IF EXISTS fecha,
                    DROP COLUMN IF EXISTS created_by_id,
                    DROP COLUMN IF EXISTS created_at;
            """,
        ),

        # Rellenar fecha desde semana (aproximación: semana 1 = primer lunes del año actual)
        migrations.RunSQL(
            sql="""
                UPDATE kpis_callrecord
                SET fecha = DATE_ADD(
                    STR_TO_DATE(CONCAT(YEAR(NOW()), ' ', semana, ' 1'), '%X %V %w'),
                    INTERVAL 0 DAY
                )
                WHERE fecha IS NULL AND semana IS NOT NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        # ── Índices (IF NOT EXISTS via RunSQL) ────────────────────────────────

        migrations.RunSQL(
            sql="""
                ALTER TABLE kpis_callrecord
                    MODIFY COLUMN agente     VARCHAR(100) NOT NULL,
                    MODIFY COLUMN supervisor VARCHAR(100) NOT NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS kpis_cr_fecha_serv   ON kpis_callrecord (fecha, servicio);
                CREATE INDEX IF NOT EXISTS kpis_cr_fecha_canal  ON kpis_callrecord (fecha, canal);
                CREATE INDEX IF NOT EXISTS kpis_cr_fecha_agente ON kpis_callrecord (fecha, agente(50));
                CREATE INDEX IF NOT EXISTS kpis_cr_fecha_sup    ON kpis_callrecord (fecha, supervisor(50));
                CREATE INDEX IF NOT EXISTS kpis_cr_sem_serv     ON kpis_callrecord (semana, servicio);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS kpis_cr_fecha_serv   ON kpis_callrecord;
                DROP INDEX IF EXISTS kpis_cr_fecha_canal  ON kpis_callrecord;
                DROP INDEX IF EXISTS kpis_cr_fecha_agente ON kpis_callrecord;
                DROP INDEX IF EXISTS kpis_cr_fecha_sup    ON kpis_callrecord;
                DROP INDEX IF EXISTS kpis_cr_sem_serv     ON kpis_callrecord;
            """,
        ),

        # ── ExchangeRate: agregar UUID (IF NOT EXISTS) ────────────────────────

        migrations.RunSQL(
            sql="""
                ALTER TABLE kpis_exchangerate
                    ADD COLUMN IF NOT EXISTS uuid CHAR(32) NULL;
            """,
            reverse_sql="""
                ALTER TABLE kpis_exchangerate
                    DROP COLUMN IF EXISTS uuid;
            """,
        ),

        # Eliminar unique_together antiguo si existe
        migrations.RunSQL(
            sql="""
                SET @idx = (
                    SELECT CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS
                    WHERE TABLE_NAME = 'kpis_exchangerate'
                    AND CONSTRAINT_TYPE = 'UNIQUE'
                    AND TABLE_SCHEMA = DATABASE()
                    AND CONSTRAINT_NAME != 'PRIMARY'
                    LIMIT 1
                );
                SET @sql = IF(@idx IS NOT NULL,
                    CONCAT('ALTER TABLE kpis_exchangerate DROP INDEX `', @idx, '`'),
                    'SELECT 1'
                );
                PREPARE stmt FROM @sql;
                EXECUTE stmt;
                DEALLOCATE PREPARE stmt;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        # Agregar unique en date (si no existe)
        migrations.RunSQL(
            sql="""
                CREATE UNIQUE INDEX IF NOT EXISTS kpis_er_date_unique ON kpis_exchangerate (date);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS kpis_er_date_unique ON kpis_exchangerate;
            """,
        ),

        # ── Estado Django (para que el ORM sepa que los campos existen) ───────

        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name='callrecord',
                    name='uuid',
                    field=models.UUIDField(default=uuid.uuid4, editable=False, null=True),
                ),
                migrations.AddField(
                    model_name='callrecord',
                    name='fecha',
                    field=models.DateField(verbose_name='Fecha', null=True, blank=True, db_index=True),
                ),
                migrations.AddField(
                    model_name='callrecord',
                    name='created_by',
                    field=models.ForeignKey(
                        null=True, blank=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='call_records',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='Creado por',
                    ),
                ),
                migrations.AddField(
                    model_name='callrecord',
                    name='created_at',
                    field=models.DateTimeField(auto_now_add=True, null=True),
                ),
                migrations.AlterField(
                    model_name='callrecord',
                    name='agente',
                    field=models.CharField('Agente', max_length=100, db_index=True),
                ),
                migrations.AlterField(
                    model_name='callrecord',
                    name='supervisor',
                    field=models.CharField('Supervisor', max_length=100, db_index=True),
                ),
                migrations.AlterField(
                    model_name='callrecord',
                    name='semana',
                    field=models.IntegerField('Semana', db_index=True),
                ),
                migrations.AlterField(
                    model_name='callrecord',
                    name='servicio',
                    field=models.CharField(
                        verbose_name='Servicio', max_length=50, db_index=True,
                        choices=[('Reclamos','Reclamos'),('Consultas','Consultas'),
                                 ('Ventas','Ventas'),('Soporte','Soporte'),('Cobranzas','Cobranzas')],
                    ),
                ),
                migrations.AlterField(
                    model_name='callrecord',
                    name='canal',
                    field=models.CharField(
                        verbose_name='Canal', max_length=50, db_index=True,
                        choices=[('Phone','Teléfono'),('Mail','Email'),('Chat','Chat'),
                                 ('WhatsApp','WhatsApp'),('Social Media','Redes Sociales')],
                    ),
                ),
                migrations.AlterModelOptions(
                    name='callrecord',
                    options={
                        'verbose_name': 'Registro de llamadas',
                        'verbose_name_plural': 'Registros de llamadas',
                        'ordering': ['-fecha', 'agente'],
                    },
                ),
                migrations.AddIndex(
                    model_name='callrecord',
                    index=models.Index(fields=['fecha', 'servicio'],   name='kpis_cr_fecha_serv'),
                ),
                migrations.AddIndex(
                    model_name='callrecord',
                    index=models.Index(fields=['fecha', 'canal'],      name='kpis_cr_fecha_canal'),
                ),
                migrations.AddIndex(
                    model_name='callrecord',
                    index=models.Index(fields=['fecha', 'agente'],     name='kpis_cr_fecha_agente'),
                ),
                migrations.AddIndex(
                    model_name='callrecord',
                    index=models.Index(fields=['fecha', 'supervisor'], name='kpis_cr_fecha_sup'),
                ),
                migrations.AddIndex(
                    model_name='callrecord',
                    index=models.Index(fields=['semana', 'servicio'],  name='kpis_cr_sem_serv'),
                ),
                migrations.AddField(
                    model_name='exchangerate',
                    name='uuid',
                    field=models.UUIDField(default=uuid.uuid4, editable=False, null=True),
                ),
                migrations.AlterUniqueTogether(
                    name='exchangerate',
                    unique_together=set(),
                ),
                migrations.AlterField(
                    model_name='exchangerate',
                    name='date',
                    field=models.DateField(
                        verbose_name='Fecha de referencia',
                        help_text='Primer día del mes al que corresponde la tasa',
                        unique=True, db_index=True,
                    ),
                ),
            ],
        ),
    ]
