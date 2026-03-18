# sim/views/docs.py
"""
Sirve los tres archivos .md de documentación como HTML renderizado.

Endpoints:
  GET  sim/docs/context/     → SIM_CONTEXT.md
  GET  sim/docs/reference/   → SIM_DEV_REFERENCE.md
  GET  sim/docs/design/      → SIM_DESIGN.md
"""

import os
import logging
import markdown

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import Http404

logger = logging.getLogger(__name__)

# Docs viven en la raíz de la app sim/
_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_DOCS = {
    'context':   ('SIM_CONTEXT.md',        'Mapa de Contexto — Sim'),
    'reference': ('SIM_DEV_REFERENCE.md',  'Referencia de Desarrollo — Sim'),
    'design':    ('SIM_DESIGN.md',          'Diseño y Estado — Simulador'),
}


@login_required
def docs_view(request, doc_key):
    """Renderiza un archivo markdown de documentación como HTML."""
    if doc_key not in _DOCS:
        raise Http404

    filename, title = _DOCS[doc_key]
    filepath = os.path.join(_APP_DIR, filename)

    if not os.path.exists(filepath):
        logger.warning("Sim doc not found: %s", filepath)
        raise Http404

    try:
        with open(filepath, encoding='utf-8') as f:
            raw = f.read()
        content_html = markdown.markdown(
            raw,
            extensions=['tables', 'fenced_code', 'toc', 'nl2br'],
        )
    except Exception as exc:
        logger.error("Error rendering sim doc %s: %s", filename, exc)
        content_html = f'<p class="text-danger">Error al renderizar: {exc}</p>'

    return render(request, 'sim/docs.html', {
        'title':        title,
        'content_html': content_html,
        'doc_key':      doc_key,
        'docs':         {k: v[1] for k, v in _DOCS.items()},
    })
