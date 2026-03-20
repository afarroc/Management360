# events/views/ai_assistant.py
"""
Asistente IA para el módulo GTD (Inbox / Events).

Endpoints:
  GET  /events/inbox/ai/summary/  → análisis automático del estado GTD del usuario
  POST /events/inbox/ai/chat/     → chat HTMX con el asistente

Integra con Ollama a través de chat.ollama_api.generate_response.
Si Ollama no está disponible, devuelve análisis estático basado en los datos.

Convención del proyecto:
  - @login_required en todas las vistas
  - JsonResponse({'success': True/False, ...})
  - Sin @csrf_exempt — usa cookie csrftoken desde JS
"""

from __future__ import annotations

import json
import logging
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from events.models import (
    InboxItem,
    Task,
    Project,
    Event,
)

logger = logging.getLogger(__name__)


# ─── Ollama helper ────────────────────────────────────────────────────────────

def _call_ollama(prompt: str) -> str | None:
    """
    Llama a Ollama via chat.ollama_api.generate_response.
    Devuelve None si no está disponible (sin crash).
    """
    try:
        from chat.ollama_api import generate_response
        response = generate_response(prompt)
        # generate_response puede devolver str o dict según implementación
        if isinstance(response, dict):
            return response.get("response") or response.get("content") or str(response)
        return str(response) if response else None
    except ImportError:
        logger.warning("ai_assistant: chat.ollama_api no disponible")
        return None
    except Exception as exc:
        logger.error("ai_assistant: Ollama error — %s", exc)
        return None


# ─── Context builder ─────────────────────────────────────────────────────────

def _build_gtd_context(user) -> dict:
    """
    Construye un snapshot GTD del usuario consultando la DB directamente.
    Devuelve un dict estructurado y un string resumen para el prompt de Ollama.
    """
    now = timezone.now()
    today = now.date()

    # ── Inbox ──────────────────────────────────────────────────────────────────
    inbox_qs = InboxItem.objects.filter(
        Q(created_by=user) | Q(assigned_to=user)
    ).distinct()

    inbox_unprocessed = inbox_qs.filter(is_processed=False)
    inbox_processed   = inbox_qs.filter(is_processed=True)

    inbox_by_category = (
        inbox_unprocessed
        .values("gtd_category")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    inbox_by_action = (
        inbox_unprocessed
        .exclude(action_type="")
        .values("action_type")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    inbox_today = inbox_qs.filter(created_at__date=today).count()

    # ── Tasks ──────────────────────────────────────────────────────────────────
    tasks_qs = Task.objects.filter(
        Q(host=user) | Q(assigned_to=user)
    ).distinct().select_related("task_status")

    tasks_total    = tasks_qs.count()
    tasks_overdue  = tasks_qs.filter(
        due_date__lt=now, is_processed=False
    ).count() if hasattr(Task, 'due_date') else 0

    # Intentar obtener overdue de forma segura
    try:
        tasks_overdue = tasks_qs.filter(due_date__lt=now).count()
    except Exception:
        tasks_overdue = 0

    tasks_important = 0
    try:
        tasks_important = tasks_qs.filter(important=True).count()
    except Exception:
        pass

    tasks_by_status = (
        tasks_qs.values("task_status__status_name")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    # ── Projects ───────────────────────────────────────────────────────────────
    projects_qs = Project.objects.filter(
        Q(host=user) | Q(assigned_to=user) | Q(attendees=user)
    ).distinct().select_related("project_status")

    projects_total = projects_qs.count()
    projects_by_status = (
        projects_qs.values("project_status__status_name")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    # ── Events próximos ────────────────────────────────────────────────────────
    upcoming_events = (
        Event.objects.filter(
            Q(host=user) | Q(assigned_to=user) | Q(eventattendee__user=user)
        )
        .distinct()
        .select_related("event_status")
        .order_by("start_date")[:5]
    ) if hasattr(Event, 'start_date') else []

    # ── Estructurar contexto ───────────────────────────────────────────────────
    context_data = {
        "fecha": today.isoformat(),
        "usuario": user.get_full_name() or user.username,
        "inbox": {
            "total": inbox_qs.count(),
            "sin_procesar": inbox_unprocessed.count(),
            "procesados": inbox_processed.count(),
            "creados_hoy": inbox_today,
            "por_categoria": list(inbox_by_category),
            "por_accion": list(inbox_by_action),
        },
        "tasks": {
            "total": tasks_total,
            "vencidas": tasks_overdue,
            "importantes": tasks_important,
            "por_estado": [
                {
                    "estado": r["task_status__status_name"] or "sin estado",
                    "total": r["total"],
                }
                for r in tasks_by_status
            ],
        },
        "projects": {
            "total": projects_total,
            "por_estado": [
                {
                    "estado": r["project_status__status_name"] or "sin estado",
                    "total": r["total"],
                }
                for r in projects_by_status
            ],
        },
        "eventos_proximos": [
            {
                "titulo": e.title,
                "fecha": str(getattr(e, "start_date", "?")),
                "estado": getattr(e.event_status, "status_name", "?") if e.event_status else "?",
            }
            for e in upcoming_events
        ],
    }

    return context_data


def _context_to_summary_text(ctx: dict) -> str:
    """Convierte el context dict en texto plano legible para el prompt."""
    inbox  = ctx["inbox"]
    tasks  = ctx["tasks"]
    proj   = ctx["projects"]

    lines = [
        f"Fecha: {ctx['fecha']}  |  Usuario: {ctx['usuario']}",
        "",
        "=== INBOX GTD ===",
        f"Total items: {inbox['total']}",
        f"Sin procesar: {inbox['sin_procesar']}  |  Procesados: {inbox['procesados']}",
        f"Creados hoy: {inbox['creados_hoy']}",
    ]

    if inbox["por_categoria"]:
        lines.append("Por categoría GTD:")
        for row in inbox["por_categoria"]:
            lines.append(f"  - {row.get('gtd_category','?')}: {row['total']}")

    if inbox["por_accion"]:
        lines.append("Por tipo de acción:")
        for row in inbox["por_accion"]:
            lines.append(f"  - {row.get('action_type','?')}: {row['total']}")

    lines += [
        "",
        "=== TAREAS ===",
        f"Total: {tasks['total']}  |  Vencidas: {tasks['vencidas']}  |  Importantes: {tasks['importantes']}",
    ]
    if tasks["por_estado"]:
        lines.append("Por estado:")
        for row in tasks["por_estado"]:
            lines.append(f"  - {row['estado']}: {row['total']}")

    lines += [
        "",
        "=== PROYECTOS ===",
        f"Total: {proj['total']}",
    ]
    if proj["por_estado"]:
        lines.append("Por estado:")
        for row in proj["por_estado"]:
            lines.append(f"  - {row['estado']}: {row['total']}")

    if ctx["eventos_proximos"]:
        lines += ["", "=== PRÓXIMOS EVENTOS ==="]
        for ev in ctx["eventos_proximos"]:
            lines.append(f"  - {ev['titulo']} ({ev['fecha']}) — {ev['estado']}")

    return "\n".join(lines)


def _static_analysis(ctx: dict) -> str:
    """
    Análisis estático cuando Ollama no está disponible.
    Devuelve texto con insights basados en los datos.
    """
    inbox  = ctx["inbox"]
    tasks  = ctx["tasks"]
    proj   = ctx["projects"]

    insights = []

    # Inbox
    total_in = inbox["sin_procesar"]
    if total_in == 0:
        insights.append("✅ Tu inbox está vacío — excelente captura y procesamiento GTD.")
    elif total_in <= 5:
        insights.append(f"🟢 Tienes {total_in} item(s) sin procesar. Buena gestión.")
    elif total_in <= 20:
        insights.append(f"⚠️ {total_in} items sin procesar en inbox. Considera una sesión de procesamiento.")
    else:
        insights.append(f"🔴 {total_in} items acumulados en inbox. Es urgente una sesión GTD de vaciado.")

    # Inbox por acción
    hacer = next((r["total"] for r in inbox["por_accion"] if r.get("action_type") == "hacer"), 0)
    if hacer > 0:
        insights.append(f"📌 Tienes {hacer} item(s) marcados como 'hacer' — acciones directas pendientes.")

    delegar = next((r["total"] for r in inbox["por_accion"] if r.get("action_type") == "delegar"), 0)
    if delegar > 0:
        insights.append(f"🤝 {delegar} item(s) para delegar — revisa a quién asignarlos.")

    # Tasks vencidas
    venc = tasks["vencidas"]
    if venc == 0:
        insights.append("✅ Sin tareas vencidas — al día con los plazos.")
    elif venc <= 3:
        insights.append(f"⚠️ {venc} tarea(s) vencida(s). Revísalas pronto.")
    else:
        insights.append(f"🔴 {venc} tareas vencidas. Esto afecta la productividad — prioriza resolverlas.")

    # Tasks importantes
    imp = tasks["importantes"]
    if imp > 0:
        insights.append(f"⭐ {imp} tarea(s) marcadas como importantes están pendientes.")

    # Proyectos
    total_proj = proj["total"]
    if total_proj > 0:
        insights.append(f"📁 Tienes {total_proj} proyecto(s) activos.")

    # Eventos próximos
    if ctx["eventos_proximos"]:
        prox = ctx["eventos_proximos"][0]
        insights.append(f"📅 Próximo evento: '{prox['titulo']}' el {prox['fecha']}.")

    return "\n".join(insights)


# ═══════════════════════════════════════════════════════════════════════════════
# Views
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
@require_GET
def inbox_ai_summary(request):
    """
    GET /events/inbox/ai/summary/

    Genera un análisis automático del estado GTD del usuario.
    Intenta usar Ollama; si no está disponible, devuelve análisis estático.

    Response:
      {
        "success": true,
        "analysis": "<texto del análisis>",
        "context": { ...snapshot GTD... },
        "source": "ollama" | "static"
      }
    """
    try:
        ctx = _build_gtd_context(request.user)
        summary_text = _context_to_summary_text(ctx)

        system_prompt = (
            "Eres un asistente de productividad personal especializado en GTD "
            "(Getting Things Done). Analiza el estado de trabajo del usuario y "
            "proporciona un diagnóstico claro, prioridades concretas y hasta 3 "
            "acciones recomendadas para hoy. Responde en español, de forma concisa "
            "(máximo 200 palabras). Usa listas cortas, no párrafos largos."
        )
        full_prompt = f"{system_prompt}\n\nDATO ACTUAL DEL USUARIO:\n{summary_text}"

        ollama_response = _call_ollama(full_prompt)

        if ollama_response:
            analysis = ollama_response
            source = "ollama"
        else:
            analysis = _static_analysis(ctx)
            source = "static"

        return JsonResponse({
            "success": True,
            "analysis": analysis,
            "context": ctx,
            "source": source,
        })

    except Exception as exc:
        logger.error("inbox_ai_summary error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@login_required
@require_POST
def inbox_ai_chat(request):
    """
    POST /events/inbox/ai/chat/

    Chat HTMX con el asistente GTD.
    Body: {"message": "¿Qué debería hacer primero hoy?"}

    Response:
      {
        "success": true,
        "reply": "<respuesta del asistente>",
        "source": "ollama" | "static"
      }
    """
    try:
        body    = json.loads(request.body)
        message = (body.get("message") or "").strip()

        if not message:
            return JsonResponse({"success": False, "error": "Mensaje vacío."}, status=400)

        # Construir contexto GTD compacto para el chat
        ctx = _build_gtd_context(request.user)
        summary_text = _context_to_summary_text(ctx)

        system_prompt = (
            "Eres un asistente de productividad GTD integrado en la aplicación "
            "Management360. Tienes acceso al estado actual del usuario. "
            "Responde en español, de forma concisa y útil (máximo 150 palabras). "
            "Prioriza acciones concretas."
        )
        full_prompt = (
            f"{system_prompt}\n\n"
            f"ESTADO ACTUAL:\n{summary_text}\n\n"
            f"PREGUNTA DEL USUARIO: {message}"
        )

        ollama_response = _call_ollama(full_prompt)

        if ollama_response:
            reply  = ollama_response
            source = "ollama"
        else:
            # Fallback: respuesta estática contextualizada
            reply = (
                f"[Ollama no disponible] Basado en tus datos:\n"
                f"{_static_analysis(ctx)}"
            )
            source = "static"

        return JsonResponse({
            "success": True,
            "reply": reply,
            "source": source,
        })

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido."}, status=400)
    except Exception as exc:
        logger.error("inbox_ai_chat error: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)
