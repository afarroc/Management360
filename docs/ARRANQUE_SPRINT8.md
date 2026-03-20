# Arranque — Sesión Dev · Sprint 8 · App `bots`
> 2026-03-19 · Antes de abrir Claude

---

## 1. Termux — dos terminales

**Terminal 1 — engine simcity** (si vas a tocar `events` o necesitas el sistema completo)
```bash
engine
# alias: ubuntu run "source /root/micropolis/venv/bin/activate && cd /root/micropolis/simcity_web && python manage.py runserver 0.0.0.0:8001"
```
Si solo trabajas en `bots`, puedes saltarte este paso. `bots` no depende del engine.

**Terminal 2 — M360**
```bash
m360
# alias: cd ~/projects/Management360 && source venv/bin/activate && python manage.py runserver
```

---

## 2. Git — estado antes de tocar nada

```bash
cd ~/projects/Management360
git status --short          # no debe haber nada sin commitear del sprint anterior
git log --oneline -5        # confirmar en qué commit estás
git push origin main        # si hay commits locales sin pushear (hay 15+ pendientes)
```

---

## 3. Verificar que la app `bots` arranca

```bash
python manage.py check bots          # sin errores de configuración
python manage.py showmigrations bots # debe mostrar [X] 0001_initial
```

---

## 4. Subir a Claude — en este orden

```
1. BOTS_DEV_REFERENCE.md    ← contexto técnico completo (lo más importante)
2. BOTS_DESIGN.md           ← roadmap y notas para Claude
3. PROJECT_DEV_REFERENCE.md ← convenciones globales
4. bots/models.py
5. bots/views.py
6. bots/utils.py
7. bots/lead_distributor.py
8. bots/gtd_processor.py
9. bots/management/commands/setup_bots.py
10. bots/management/commands/run_bots.py
```

---

## 5. Prompt para Claude

```
Eres dev de Management360 trabajando en la app `bots`.

Lee BOTS_DEV_REFERENCE.md como referencia técnica completa.
Lee BOTS_DESIGN.md para el roadmap y orden de trabajo.

Tarea: Sprint 8 — Fase 0 (fixes críticos) + BOT-1

Empieza por los fixes de Fase 0 en este orden:
1. BOT-BUG-13: setup_bots.py — eliminar campos fantasma
2. BOT-BUG-16: models.py — cerrar pipeline Lead→GTD en _create_inbox_item_for_bot()
3. BOT-BUG-03: views.py — @login_required en APIs
4. BOT-BUG-05: models.py — transaction.atomic() en assign_to_bot()
5. BOT-BUG-18: utils.py — doble incremento tasks_completed_today
6. BOT-BUG-20: utils.py — can_take_task('any') en BotTaskQueue
7. BOT-BUG-01/02/14: models.py choices + gtd_processor._log_error() + makemigrations

Para cada fix: muestra solo el fragmento modificado con contexto suficiente.
Al terminar Fase 0: verifica con los comandos de prueba indicados.
Luego continuar con BOT-1.
```

---

## 6. Verificar cada fix de Fase 0 en Termux

Después de aplicar los cambios de Claude, verificar en esta secuencia:

```bash
# Fix BOT-BUG-13 (setup_bots)
python manage.py setup_bots --bots-count 3
# Esperado: "Sistema multi-bot inicializado correctamente!"

# Fix BOT-BUG-01/02 (choices + migración)
python manage.py makemigrations bots
python manage.py migrate bots
# Esperado: migración 0002 aplicada sin errores

# Fix BOT-BUG-16 + general (pipeline completo en dry-run)
python manage.py run_bots --once --dry-run
# Esperado: ciclo completo sin excepciones, log de bots procesando

# Smoke test del servidor
python manage.py runserver
# Ir a /bots/campaigns/ — debe cargar con 200
```

---

## 7. Workflow de commit para Sprint 8

Un commit por fix crítico, luego commits por feature:

```bash
git add bots/management/commands/setup_bots.py
git commit -m "bots: BOT-BUG-13 — remove nonexistent fields from BotInstance get_or_create"

git add bots/models.py
git commit -m "bots: BOT-BUG-16+05 — close Lead→GTD pipeline, atomic assign_to_bot"

git add bots/views.py
git commit -m "bots: BOT-BUG-03 — add @login_required to API endpoints"

git add bots/utils.py
git commit -m "bots: BOT-BUG-18+20 — fix double counter increment, fix BotTaskQueue specialization"

git add bots/models.py bots/gtd_processor.py bots/migrations/0002_*.py
git commit -m "bots: BOT-BUG-01+02+14 — fix Lead/BotLog choices, fix log_level kwarg, migration 0002"

# Luego por feature:
git commit -m "bots: BOT-1 — improve lead assignment engine"
git commit -m "bots: BOT-4 — bot performance dashboard"
# etc.
```
