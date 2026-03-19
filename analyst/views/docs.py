# analyst/views/docs.py
"""
Serves the three .md documentation files as rendered HTML.

Endpoints:
  GET  analyst/docs/context/     → ANALYST_CONTEXT.md
  GET  analyst/docs/reference/   → ANALYST_DEV_REFERENCE.md
  GET  analyst/docs/design/      → ANALYST_PLATFORM_DESIGN.md
"""

import os
import logging
import markdown

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import Http404

logger = logging.getLogger(__name__)

# Docs live in the analyst app root directory
_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_DOCS = {
    'context':   ('ANALYST_CONTEXT.md',        'Mapa de Contexto — Analyst'),
    'reference': ('ANALYST_DEV_REFERENCE.md',  'Referencia de Desarrollo — Analyst'),
    'design':    ('ANALYST_PLATFORM_DESIGN.md','Diseño y Estado — Plataforma Analyst'),
}


@login_required
def docs_view(request, doc_key):
    """Render a markdown doc file as HTML."""
    if doc_key not in _DOCS:
        raise Http404

    filename, title = _DOCS[doc_key]
    filepath = os.path.join(_APP_DIR, filename)

    if not os.path.exists(filepath):
        logger.warning("Analyst doc not found: %s", filepath)
        raise Http404

    try:
        with open(filepath, encoding='utf-8') as f:
            raw = f.read()
        content_html = markdown.markdown(
            raw,
            extensions=['tables', 'fenced_code', 'toc', 'nl2br'],
        )
    except Exception as exc:
        logger.error("Error rendering doc %s: %s", filename, exc)
        content_html = f'<p class="text-danger">Error al renderizar el documento: {exc}</p>'

    return render(request, 'analyst/docs.html', {
        'title':        title,
        'content_html': content_html,
        'doc_key':      doc_key,
        'docs':         {k: v[1] for k, v in _DOCS.items()},
    })
