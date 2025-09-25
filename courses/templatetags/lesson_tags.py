from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

def process_markdown(text):
    """
    Convierte formato Markdown básico a HTML
    Soporta: negrita, itálica, código inline, enlaces, listas, encabezados, código en bloque
    """
    import re

    if not text:
        return text

    # Dividir el texto en líneas para procesar bloques
    lines = text.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 1. Código en bloque (```)
        if stripped.startswith('```'):
            # Verificar si hay un lenguaje especificado en la misma línea
            lang = stripped[3:].strip()  # Extraer lenguaje después de ```

            # Encontrar el final del bloque de código
            code_lines = []
            i += 1  # Saltar la línea de apertura

            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1  # Saltar la línea de cierre

            # Procesar el bloque de código
            code_content = '\n'.join(code_lines)

            # Lenguajes de programación comunes
            common_languages = {
                'python', 'javascript', 'js', 'html', 'css', 'java', 'c', 'cpp', 'c++',
                'php', 'ruby', 'go', 'rust', 'swift', 'kotlin', 'dart', 'scala',
                'sql', 'bash', 'shell', 'powershell', 'yaml', 'json', 'xml', 'markdown'
            }

            # Si se especificó un lenguaje válido, usarlo
            if lang and lang.lower() in common_languages:
                result.append(f'<pre><code class="language-{lang.lower()}">{code_content}</code></pre>')
            elif code_lines and not lang:
                # Verificar si la primera línea del código es un lenguaje
                first_line = code_lines[0].strip()
                if first_line.lower() in common_languages:
                    # Es un lenguaje, quitarlo del contenido
                    code_body = '\n'.join(code_lines[1:]) if len(code_lines) > 1 else ''
                    result.append(f'<pre><code class="language-{first_line.lower()}">{code_body}</code></pre>')
                else:
                    # No es un lenguaje, incluir todo
                    result.append(f'<pre><code>{code_content}</code></pre>')
            else:
                # Lenguaje no válido o no especificado
                result.append(f'<pre><code>{code_content}</code></pre>')
            continue

        # 2. Encabezados (# ## ###)
        header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if header_match:
            level = len(header_match.group(1))
            content = header_match.group(2).strip()
            # Procesar elementos inline en el contenido del encabezado
            content = process_inline_elements(content)
            result.append(f'<h{level}>{content}</h{level}>')
            i += 1
            continue

        # 3. Listas no ordenadas (- o * o ?)
        if (stripped.startswith(('- ', '* ', '? ')) and
            not stripped.startswith('**') and
            not stripped.startswith('??')):
            # Procesar bloque de lista no ordenada
            list_items = []
            while i < len(lines):
                current_line = lines[i].strip()
                if ((current_line.startswith(('- ', '* ', '? ')) and
                     not current_line.startswith('**') and
                     not current_line.startswith('??'))):
                    # Es un item de lista
                    item_content = current_line[2:].strip()
                    # Procesar elementos inline en el item
                    item_content = process_inline_elements(item_content)
                    list_items.append(f'<li>{item_content}</li>')
                    i += 1
                else:
                    break

            if list_items:
                result.append(f'<ul>{"".join(list_items)}</ul>')
            continue

        # 4. Listas ordenadas (1. 2. 3.)
        if re.match(r'^\d+\.\s', stripped):
            # Procesar bloque de lista ordenada
            list_items = []
            while i < len(lines):
                current_line = lines[i].strip()
                if re.match(r'^\d+\.\s', current_line):
                    # Es un item de lista ordenada
                    item_content = re.sub(r'^\d+\.\s+', '', current_line)
                    # Procesar elementos inline en el item
                    item_content = process_inline_elements(item_content)
                    list_items.append(f'<li>{item_content}</li>')
                    i += 1
                else:
                    break

            if list_items:
                result.append(f'<ol>{"".join(list_items)}</ol>')
            continue

        # 5. Líneas horizontales (--- o ***)
        if re.match(r'^[-*_]{3,}$', stripped):
            result.append('<hr>')
            i += 1
            continue

        # 6. Líneas normales - procesar elementos inline
        if stripped:  # Solo líneas no vacías
            processed_line = process_inline_elements(line)
            result.append(processed_line)
        else:
            # Línea vacía - podría indicar separación de párrafos
            if result and not result[-1].startswith('<'):
                # Si la línea anterior no es un bloque, agregar un salto
                result.append('')
            else:
                result.append('')

        i += 1

    # Unir líneas y convertir a párrafos donde sea apropiado
    final_result = []
    current_paragraph = []

    for line in result:
        if line.startswith(('<h', '<ul', '<ol', '<pre', '<hr')):
            # Es un bloque HTML - cerrar párrafo anterior si existe
            if current_paragraph:
                final_result.append('<p>' + ' '.join(current_paragraph) + '</p>')
                current_paragraph = []
            final_result.append(line)
        elif line.strip() == '':
            # Línea vacía - cerrar párrafo
            if current_paragraph:
                final_result.append('<p>' + ' '.join(current_paragraph) + '</p>')
                current_paragraph = []
        else:
            # Línea de texto normal
            current_paragraph.append(line)

    # Cerrar último párrafo si existe
    if current_paragraph:
        final_result.append('<p>' + ' '.join(current_paragraph) + '</p>')

    return '\n'.join(final_result)

def process_inline_elements(text):
    """
    Procesa elementos inline: negrita, itálica, código, enlaces
    """
    import re

    if not text:
        return text

    # 1. Código inline (`código`) - procesar primero para evitar conflictos
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    # 2. Enlaces [texto](url) - antes de negrita/itálica para evitar conflictos
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', text)

    # 3. Negrita (**texto**) - debe ir antes de itálica
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

    # 4. Itálica (*texto*) - después de negrita para evitar conflictos
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)

    return text

@register.filter
def render_structured_content(structured_content):
    """
    Renderiza contenido estructurado de lecciones desde JSON
    """
    if not structured_content:
        return ''

    html = []

    for element in structured_content:
        element_type = element.get('type', 'text')
        content = element.get('content', '')
        title = element.get('title', '')
        items = element.get('items', [])

        if element_type == 'heading':
            html.append('<div class="lesson-heading-container">')
            if title:
                html.append(f'<h2 class="lesson-heading-main"><i class="bi bi-hash me-2 text-primary"></i>{title}</h2>')
            if content:
                html.append(f'<p class="lesson-heading-subtitle">{content}</p>')
            html.append('</div>')

        elif element_type == 'text':
            html.append('<div class="lesson-text-container">')
            if title:
                html.append(f'<h4 class="lesson-subheading"><i class="bi bi-textarea me-2 text-success"></i>{title}</h4>')
            if content:
                # Procesar formato Markdown completo
                processed_content = process_markdown(content)
                html.append(f'<div class="lesson-content">{processed_content}</div>')
            html.append('</div>')

        elif element_type == 'list':
            html.append('<div class="lesson-list-container">')
            if title:
                html.append(f'<h4 class="lesson-list-title"><i class="bi bi-list-check me-2 text-warning"></i>{title}</h4>')
            if items:
                html.append('<ul class="lesson-list">')
                for item in items:
                    # Procesar Markdown inline (sin párrafos) para items de lista
                    processed_item = process_inline_elements(item)
                    html.append(f'<li class="lesson-list-item"><span class="list-bullet">✓</span> {processed_item}</li>')
                html.append('</ul>')
            html.append('</div>')

        elif element_type == 'image':
            if content:
                alt_text = title or 'Imagen de la lección'
                html.append('<div class="lesson-image-container">')
                html.append(f'<img src="{content}" alt="{alt_text}" class="lesson-image">')
                if title:
                    html.append(f'<p class="lesson-image-caption"><i class="bi bi-image me-1 text-muted"></i>{title}</p>')
                html.append('</div>')

        elif element_type == 'file':
            if content and title:
                html.append('<div class="lesson-file">')
                html.append(f'<a href="{content}" target="_blank" class="lesson-file-link">')
                html.append(f'<i class="bi bi-file-earmark me-2"></i> {title}')
                html.append('</a>')
                html.append('</div>')

        elif element_type == 'video':
            if content:
                if isinstance(content, dict):
                    description = content.get('description', 'Video de la lección')
                    duration = content.get('duration', 0)
                    html.append('<div class="lesson-video-container">')
                    html.append(f'<div class="lesson-video-info">')
                    html.append(f'<i class="bi bi-play-circle-fill text-danger me-2"></i>')
                    html.append(f'<span class="video-description">{description}</span>')
                    if duration:
                        html.append(f'<span class="video-duration badge bg-info ms-2">{duration} min</span>')
                    html.append('</div>')
                    html.append('</div>')
                else:
                    # URL directa
                    html.append('<div class="lesson-video-container">')
                    html.append(f'<div class="lesson-video-info">')
                    html.append(f'<i class="bi bi-play-circle-fill text-danger me-2"></i>')
                    html.append(f'<span class="video-description">{content}</span>')
                    html.append('</div>')
                    html.append('</div>')

        elif element_type == 'exercise':
            html.append('<div class="lesson-exercise-container">')
            html.append('<div class="lesson-exercise-header">')
            html.append('<i class="bi bi-pencil-square text-success me-2"></i>')
            html.append('<span class="exercise-title">Ejercicio Práctico</span>')
            html.append('</div>')
            if content:
                # Procesar formato Markdown completo para exercises
                processed_content = process_markdown(content)
                html.append(f'<div class="lesson-exercise-content">{processed_content}</div>')
            html.append('</div>')

        elif element_type == 'markdown':
            html.append('<div class="lesson-markdown-container">')
            html.append('<div class="lesson-markdown-header">')
            html.append('<i class="bi bi-markdown text-primary me-2"></i>')
            html.append('<span class="markdown-title">Contenido Formateado</span>')
            html.append('</div>')
            if content:
                # Procesar formato Markdown completo
                processed_content = process_markdown(content)
                html.append(f'<div class="lesson-markdown-content">{processed_content}</div>')
            html.append('</div>')

        elif element_type == 'link':
            if content:
                html.append('<div class="lesson-link-container">')
                html.append('<div class="lesson-link-header">')
                html.append('<i class="bi bi-link-45deg text-info me-2"></i>')
                html.append('<span class="link-title">Recurso Adicional</span>')
                html.append('</div>')
                html.append(f'<a href="{content}" target="_blank" class="lesson-resource-link">')
                html.append(f'<i class="bi bi-box-arrow-up-right me-1"></i> {content}')
                html.append('</a>')
                html.append('</div>')

        elif element_type == 'calculator':
            html.append('<div class="lesson-calculator-container">')
            html.append('<div class="lesson-calculator-header">')
            html.append('<i class="bi bi-calculator text-warning me-2"></i>')
            html.append('<span class="calculator-title">Herramienta Interactiva</span>')
            html.append('</div>')
            if content:
                html.append(f'<p class="lesson-calculator-description">{content}</p>')
            html.append('</div>')

        elif element_type == 'case_study':
            html.append('<div class="lesson-case-study-container">')
            html.append('<div class="lesson-case-study-header">')
            html.append('<i class="bi bi-journal-text text-secondary me-2"></i>')
            html.append('<span class="case-study-title">Caso de Estudio</span>')
            html.append('</div>')
            if content:
                html.append(f'<p class="lesson-case-study-content">{content}</p>')
            html.append('</div>')

        elif element_type == 'project':
            html.append('<div class="lesson-project-container">')
            html.append('<div class="lesson-project-header">')
            html.append('<i class="bi bi-lightbulb text-warning me-2"></i>')
            html.append('<span class="project-title">Proyecto Práctico</span>')
            html.append('</div>')
            if content:
                html.append(f'<p class="lesson-project-description">{content}</p>')
            html.append('</div>')

        elif element_type == 'interactive_diagram':
            html.append('<div class="lesson-diagram-container">')
            html.append('<div class="lesson-diagram-header">')
            html.append('<i class="bi bi-diagram-3 text-primary me-2"></i>')
            html.append('<span class="diagram-title">Diagrama Interactivo</span>')
            html.append('</div>')
            if content:
                html.append(f'<p class="lesson-diagram-description">{content}</p>')
            html.append('</div>')

        elif element_type == 'interactive_grapher':
            html.append('<div class="lesson-grapher-container">')
            html.append('<div class="lesson-grapher-header">')
            html.append('<i class="bi bi-graph-up text-success me-2"></i>')
            html.append('<span class="grapher-title">Graficador Interactivo</span>')
            html.append('</div>')
            if content:
                html.append(f'<p class="lesson-grapher-description">{content}</p>')
            html.append('</div>')

        elif element_type == 'application':
            html.append('<div class="lesson-application-container">')
            html.append('<div class="lesson-application-header">')
            html.append('<i class="bi bi-gear text-info me-2"></i>')
            html.append('<span class="application-title">Aplicación Práctica</span>')
            html.append('</div>')
            if content:
                html.append(f'<p class="lesson-application-description">{content}</p>')
            html.append('</div>')

        elif element_type == 'game':
            html.append('<div class="lesson-game-container">')
            html.append('<div class="lesson-game-header">')
            html.append('<i class="bi bi-controller text-danger me-2"></i>')
            html.append('<span class="game-title">Actividad Interactiva</span>')
            html.append('</div>')
            if content:
                html.append(f'<p class="lesson-game-description">{content}</p>')
            html.append('</div>')

        elif element_type == 'formula_sheet':
            html.append('<div class="lesson-formula-container">')
            html.append('<div class="lesson-formula-header">')
            html.append('<i class="bi bi-file-earmark-spreadsheet text-success me-2"></i>')
            html.append('<span class="formula-title">Fórmulas de Referencia</span>')
            html.append('</div>')
            if content:
                html.append(f'<p class="lesson-formula-description">{content}</p>')
            html.append('</div>')

        elif element_type == 'animation':
            html.append('<div class="lesson-animation-container">')
            html.append('<div class="lesson-animation-header">')
            html.append('<i class="bi bi-film text-warning me-2"></i>')
            html.append('<span class="animation-title">Animación</span>')
            html.append('</div>')
            if content:
                html.append(f'<p class="lesson-animation-description">{content}</p>')
            html.append('</div>')

        elif element_type == 'simulator':
            html.append('<div class="lesson-simulator-container">')
            html.append('<div class="lesson-simulator-header">')
            html.append('<i class="bi bi-play-circle text-primary me-2"></i>')
            html.append('<span class="simulator-title">Simulador Interactivo</span>')
            html.append('</div>')
            if content:
                html.append(f'<p class="lesson-simulator-description">{content}</p>')
            html.append('</div>')

        elif element_type == 'infographic':
            html.append('<div class="lesson-infographic-container">')
            html.append('<div class="lesson-infographic-header">')
            html.append('<i class="bi bi-bar-chart text-info me-2"></i>')
            html.append('<span class="infographic-title">Infografía</span>')
            html.append('</div>')
            if content:
                html.append(f'<p class="lesson-infographic-description">{content}</p>')
            html.append('</div>')

        elif element_type == 'quiz':
            html.append('<div class="lesson-quiz-container">')
            html.append('<div class="lesson-quiz-header">')
            html.append('<i class="bi bi-question-circle text-warning me-2"></i>')
            html.append('<span class="quiz-title">Evaluación</span>')
            html.append('</div>')
            if content:
                html.append(f'<p class="lesson-quiz-description">{content}</p>')
            html.append('</div>')

        # ===========================================
        # ADVERTISEMENT ELEMENTS
        # ===========================================

        elif element_type == 'ad_banner':
            html.append('<div class="ad-banner-container bg-primary text-white p-4 rounded mb-4">')
            if title:
                html.append(f'<h3 class="ad-banner-title mb-3">{title}</h3>')
            if content and isinstance(content, dict):
                header = content.get('header', '')
                subheader = content.get('subheader', '')
                features = content.get('features', [])
                offer = content.get('offer', '')
                price = content.get('price', {})
                cta = content.get('cta', {})
                secondary_cta = content.get('secondary_cta', {})

                if header:
                    html.append(f'<h4 class="ad-banner-header">{header}</h4>')
                if subheader:
                    html.append(f'<p class="ad-banner-subheader mb-3">{subheader}</p>')

                if features:
                    html.append('<ul class="ad-features list-unstyled">')
                    for feature in features:
                        html.append(f'<li class="mb-2"><i class="bi bi-check-circle-fill me-2"></i>{feature}</li>')
                    html.append('</ul>')

                if offer:
                    html.append(f'<div class="ad-offer bg-warning text-dark p-2 rounded my-3"><strong>{offer}</strong></div>')

                if price:
                    original = price.get('original', '')
                    discounted = price.get('discounted', '')
                    period = price.get('period', '')
                    html.append('<div class="ad-price mb-3">')
                    if original:
                        html.append(f'<span class="original-price text-decoration-line-through me-2">{original}</span>')
                    if discounted:
                        html.append(f'<span class="discounted-price fw-bold fs-4 text-success">{discounted}</span>')
                    if period:
                        html.append(f'<small class="text-muted d-block">{period}</small>')
                    html.append('</div>')

                if cta:
                    text = cta.get('text', 'Ver más')
                    url = cta.get('url', '#')
                    color = cta.get('color', 'primary')
                    html.append(f'<a href="{url}" class="btn btn-{color} btn-lg me-2">{text}</a>')

                if secondary_cta:
                    text = secondary_cta.get('text', '')
                    url = secondary_cta.get('url', '#')
                    if text:
                        html.append(f'<a href="{url}" class="btn btn-outline-light">{text}</a>')
            html.append('</div>')

        elif element_type == 'ad_card':
            html.append('<div class="ad-card-container card border-primary mb-4">')
            html.append('<div class="card-body">')
            if title:
                html.append(f'<h5 class="card-title text-primary">{title}</h5>')
            if content and isinstance(content, dict):
                header = content.get('header', '')
                description = content.get('description', '')
                highlights = content.get('highlights', [])
                price = content.get('price', '')
                badge = content.get('badge', '')
                cta = content.get('cta', {})

                if header:
                    html.append(f'<h6 class="card-subtitle mb-2 text-muted">{header}</h6>')
                if description:
                    html.append(f'<p class="card-text">{description}</p>')

                if highlights:
                    html.append('<ul class="ad-highlights">')
                    for highlight in highlights:
                        html.append(f'<li>{highlight}</li>')
                    html.append('</ul>')

                if price:
                    html.append(f'<div class="ad-price fw-bold text-success fs-5 my-2">{price}</div>')
                if badge:
                    html.append(f'<span class="badge bg-warning text-dark mb-2">{badge}</span>')

                if cta:
                    text = cta.get('text', 'Ver más')
                    url = cta.get('url', '#')
                    html.append(f'<a href="{url}" class="btn btn-primary">{text}</a>')
            html.append('</div>')
            html.append('</div>')

        elif element_type == 'ad_alert':
            variant = 'info'
            if content and isinstance(content, dict):
                variant = content.get('variant', 'info')
            html.append(f'<div class="ad-alert-container alert alert-{variant} mb-4">')
            if content and isinstance(content, dict):
                icon = content.get('icon', '')
                title_alert = content.get('title', '')
                message = content.get('message', '')
                features = content.get('features', [])
                cta = content.get('cta', {})

                if icon:
                    html.append(f'<i class="bi bi-{icon} me-2"></i>')
                if title_alert:
                    html.append(f'<strong>{title_alert}</strong>')
                if message:
                    html.append(f'<br>{message}')

                if features:
                    html.append('<ul class="mb-2 mt-2">')
                    for feature in features:
                        html.append(f'<li>{feature}</li>')
                    html.append('</ul>')

                if cta:
                    text = cta.get('text', 'Ver más')
                    url = cta.get('url', '#')
                    html.append(f'<br><a href="{url}" class="btn btn-sm btn-{variant}">{text}</a>')
            html.append('</div>')

        elif element_type == 'ad_testimonial':
            html.append('<div class="ad-testimonial-container card mb-4">')
            html.append('<div class="card-body">')
            html.append('<blockquote class="blockquote mb-0">')
            if content and isinstance(content, dict):
                quote = content.get('quote', '')
                author = content.get('author', {})
                achievement = content.get('achievement', '')

                if quote:
                    html.append(f'<p class="mb-2">{quote}</p>')
                html.append('<footer class="blockquote-footer">')
                if author:
                    name = author.get('name', '')
                    role = author.get('role', '')
                    rating = author.get('rating', 0)
                    if name:
                        html.append(f'<cite title="Source Title">{name}</cite>')
                    if role:
                        html.append(f'<br><small class="text-muted">{role}</small>')
                    if rating:
                        stars = '⭐' * rating
                        html.append(f'<br><small class="text-warning">{stars}</small>')
                html.append('</footer>')
                if achievement:
                    html.append(f'<div class="text-muted small mt-2">{achievement}</div>')
            html.append('</blockquote>')
            html.append('</div>')
            html.append('</div>')

        elif element_type == 'ad_countdown':
            html.append('<div class="ad-countdown-container bg-dark text-white p-4 rounded mb-4 text-center">')
            if content and isinstance(content, dict):
                title_cd = content.get('title', '')
                message = content.get('message', '')
                countdown = content.get('countdown', {})
                offer_details = content.get('offer_details', [])
                cta = content.get('cta', {})

                if title_cd:
                    html.append(f'<h4 class="mb-3">{title_cd}</h4>')
                if message:
                    html.append(f'<p class="mb-3">{message}</p>')

                if countdown:
                    days = countdown.get('days', 0)
                    hours = countdown.get('hours', 0)
                    minutes = countdown.get('minutes', 0)
                    html.append('<div class="countdown-timer d-flex justify-content-center mb-3">')
                    html.append(f'<div class="countdown-item mx-2"><span class="fs-2 fw-bold">{days}</span><br><small>Días</small></div>')
                    html.append(f'<div class="countdown-item mx-2"><span class="fs-2 fw-bold">{hours}</span><br><small>Horas</small></div>')
                    html.append(f'<div class="countdown-item mx-2"><span class="fs-2 fw-bold">{minutes}</span><br><small>Min</small></div>')
                    html.append('</div>')

                if offer_details:
                    html.append('<ul class="offer-details text-start d-inline-block mb-3">')
                    for detail in offer_details:
                        html.append(f'<li class="mb-1">{detail}</li>')
                    html.append('</ul>')

                if cta:
                    text = cta.get('text', 'Ver más')
                    url = cta.get('url', '#')
                    html.append(f'<a href="{url}" class="btn btn-warning btn-lg">{text}</a>')
            html.append('</div>')

        elif element_type == 'ad_feature':
            html.append('<div class="ad-feature-container mb-4">')
            if content and isinstance(content, dict):
                title_feat = content.get('title', '')
                features = content.get('features', [])
                cta = content.get('cta', {})

                if title_feat:
                    html.append(f'<h4 class="text-center mb-4">{title_feat}</h4>')

                if features:
                    html.append('<div class="row">')
                    for feature in features:
                        icon = feature.get('icon', '🤖')
                        title_f = feature.get('title', '')
                        description = feature.get('description', '')
                        html.append('<div class="col-md-6 col-lg-3 mb-3">')
                        html.append('<div class="feature-item text-center p-3 border rounded">')
                        html.append(f'<i class="bi bi-{icon} fs-1 text-primary mb-2"></i>')
                        if title_f:
                            html.append(f'<h6 class="mb-2">{title_f}</h6>')
                        if description:
                            html.append(f'<p class="small text-muted">{description}</p>')
                        html.append('</div>')
                        html.append('</div>')
                    html.append('</div>')

                if cta:
                    text = cta.get('text', 'Ver más')
                    url = cta.get('url', '#')
                    html.append(f'<div class="text-center mt-4"><a href="{url}" class="btn btn-primary">{text}</a></div>')
            html.append('</div>')

        elif element_type == 'ad_comparison':
            html.append('<div class="ad-comparison-container mb-4">')
            if content and isinstance(content, dict):
                title_comp = content.get('title', '')
                plans = content.get('plans', [])

                if title_comp:
                    html.append(f'<h4 class="text-center mb-4">{title_comp}</h4>')

                if plans:
                    html.append('<div class="row">')
                    for plan in plans:
                        name = plan.get('name', '')
                        price = plan.get('price', '')
                        original_price = plan.get('original_price', '')
                        popular = plan.get('popular', False)
                        features = plan.get('features', [])
                        cta = plan.get('cta', {})

                        col_class = "col-md-4 mb-3"
                        card_class = "plan-card card h-100 border-secondary"
                        if popular:
                            card_class += " popular-plan"

                        html.append(f'<div class="{col_class}">')
                        html.append(f'<div class="{card_class}">')
                        if popular:
                            html.append('<div class="popular-badge bg-primary text-white text-center py-1">MÁS POPULAR</div>')
                        html.append('<div class="card-body text-center">')
                        if name:
                            html.append(f'<h5 class="card-title">{name}</h5>')
                        if price:
                            html.append(f'<div class="plan-price fs-3 fw-bold text-primary mb-3">{price}</div>')
                        if original_price:
                            html.append(f'<small class="text-decoration-line-through text-muted">{original_price}</small>')
                        if features:
                            html.append('<ul class="list-unstyled">')
                            for feature in features:
                                if feature.startswith('✓'):
                                    html.append(f'<li class="text-success"><small>{feature}</small></li>')
                                elif feature.startswith('✗'):
                                    html.append(f'<li class="text-danger"><small>{feature}</small></li>')
                                else:
                                    html.append(f'<li><small>{feature}</small></li>')
                            html.append('</ul>')
                        if cta:
                            text = cta.get('text', 'Seleccionar')
                            variant = cta.get('variant', 'primary')
                            html.append(f'<a href="#" class="btn btn-{variant} mt-3">{text}</a>')
                        html.append('</div>')
                        html.append('</div>')
                        html.append('</div>')
                    html.append('</div>')
            html.append('</div>')

        elif element_type == 'ad_achievement':
            html.append('<div class="ad-achievement-container mb-4">')
            if content and isinstance(content, dict):
                title_ach = content.get('title', '')
                badges = content.get('badges', [])
                progress = content.get('progress', {})

                if title_ach:
                    html.append(f'<h4 class="text-center mb-4">{title_ach}</h4>')

                if badges:
                    html.append('<div class="row">')
                    for badge in badges:
                        icon = badge.get('icon', '⭐')
                        title_b = badge.get('title', '')
                        description = badge.get('description', '')
                        html.append('<div class="col-md-3 mb-3">')
                        html.append('<div class="badge-item text-center p-3 border rounded">')
                        html.append(f'<i class="bi bi-{icon} fs-2 text-warning mb-2"></i>')
                        if title_b:
                            html.append(f'<h6 class="mb-2">{title_b}</h6>')
                        if description:
                            html.append(f'<p class="small text-muted">{description}</p>')
                        html.append('</div>')
                        html.append('</div>')
                    html.append('</div>')

                if progress:
                    current = progress.get('current', 0)
                    total = progress.get('total', 12)
                    message = progress.get('message', '')
                    percentage = (current / total * 100) if total > 0 else 0
                    html.append('<div class="progress-container mt-4">')
                    html.append(f'<div class="progress mb-2"><div class="progress-bar bg-success" role="progressbar" style="width: {percentage}%" aria-valuenow="{percentage}" aria-valuemin="0" aria-valuemax="100"></div></div>')
                    if message:
                        html.append(f'<small class="text-muted">{message}</small>')
                    html.append('</div>')
            html.append('</div>')

        elif element_type == 'ad_banner':
            # Banner publicitario
            html.append('<div class="ad-banner-container bg-primary text-white p-4 rounded mb-4">')
            if title:
                html.append(f'<h3 class="ad-banner-title mb-3">{title}</h3>')
            if content:
                if content.get('header'):
                    html.append(f'<h4 class="ad-banner-header">{content["header"]}</h4>')
                if content.get('subheader'):
                    html.append(f'<p class="ad-banner-subheader mb-3">{content["subheader"]}</p>')
                if content.get('features'):
                    html.append('<ul class="ad-features list-unstyled">')
                    for feature in content['features']:
                        html.append(f'<li class="mb-2"><i class="bi bi-check-circle-fill me-2"></i>{feature}</li>')
                    html.append('</ul>')
                if content.get('offer'):
                    html.append(f'<div class="ad-offer bg-warning text-dark p-2 rounded my-3"><strong>{content["offer"]}</strong></div>')
                if content.get('price'):
                    price = content['price']
                    html.append('<div class="ad-price mb-3">')
                    html.append(f'<span class="original-price text-decoration-line-through me-2">{price.get("original", "")}</span>')
                    html.append(f'<span class="discounted-price fw-bold fs-4 text-success">{price.get("discounted", "")}</span>')
                    html.append(f'<small class="text-muted d-block">{price.get("period", "")}</small>')
                    html.append('</div>')
                if content.get('cta'):
                    cta = content['cta']
                    html.append(f'<a href="{cta.get("url", "#")}" class="btn btn-{cta.get("color", "light")} btn-lg me-2">{cta.get("text", "Ver más")}</a>')
                if content.get('secondary_cta'):
                    secondary_cta = content['secondary_cta']
                    html.append(f'<a href="{secondary_cta.get("url", "#")}" class="btn btn-outline-light">{secondary_cta.get("text", "Más información")}</a>')
            html.append('</div>')

        elif element_type == 'ad_card':
            # Tarjeta publicitaria
            html.append('<div class="ad-card-container card border-primary mb-4">')
            html.append('<div class="card-body">')
            if title:
                html.append(f'<h5 class="card-title text-primary">{title}</h5>')
            if content:
                if content.get('header'):
                    html.append(f'<h6 class="card-subtitle mb-2 text-muted">{content["header"]}</h6>')
                if content.get('description'):
                    html.append(f'<p class="card-text">{content["description"]}</p>')
                if content.get('highlights'):
                    html.append('<ul class="ad-highlights">')
                    for highlight in content['highlights']:
                        html.append(f'<li>{highlight}</li>')
                    html.append('</ul>')
                if content.get('price'):
                    html.append(f'<div class="ad-price fw-bold text-success fs-5 my-2">{content["price"]}</div>')
                if content.get('badge'):
                    html.append(f'<span class="badge bg-warning text-dark mb-2">{content["badge"]}</span>')
                if content.get('cta'):
                    cta = content['cta']
                    html.append(f'<a href="{cta.get("url", "#")}" class="btn btn-primary">{cta.get("text", "Ver más")}</a>')
            html.append('</div>')
            html.append('</div>')

        elif element_type == 'ad_alert':
            # Alerta publicitaria
            variant = content.get('variant', 'info') if content else 'info'
            html.append(f'<div class="ad-alert-container alert alert-{variant} mb-4">')
            if content:
                if content.get('icon'):
                    html.append(f'<i class="bi bi-{content["icon"]} me-2"></i>')
                if content.get('title'):
                    html.append(f'<strong>{content["title"]}</strong><br>')
                if content.get('message'):
                    html.append(f'{content["message"]}')
                if content.get('features'):
                    html.append('<ul class="mb-2 mt-2">')
                    for feature in content['features']:
                        html.append(f'<li>{feature}</li>')
                    html.append('</ul>')
                if content.get('cta'):
                    cta = content['cta']
                    html.append(f'<br><a href="{cta.get("url", "#")}" class="btn btn-sm btn-{variant}">{cta.get("text", "Ver más")}</a>')
            html.append('</div>')

        elif element_type == 'ad_testimonial':
            # Testimonial publicitario
            html.append('<div class="ad-testimonial-container card mb-4">')
            html.append('<div class="card-body">')
            if content:
                html.append('<blockquote class="blockquote mb-0">')
                if content.get('quote'):
                    html.append(f'<p class="mb-2">"{content["quote"]}"</p>')
                if content.get('author'):
                    author = content['author']
                    html.append('<footer class="blockquote-footer">')
                    html.append(f'<cite title="Source Title">{author.get("name", "")}</cite>')
                    if author.get('role'):
                        html.append(f'<br><small class="text-muted">{author["role"]}</small>')
                    if author.get('rating'):
                        stars = '⭐' * author['rating']
                        html.append(f'<br><small class="text-warning">{stars}</small>')
                    html.append('</footer>')
                if content.get('achievement'):
                    html.append(f'<div class="text-muted small mt-2">{content["achievement"]}</div>')
                html.append('</blockquote>')
            html.append('</div>')
            html.append('</div>')

        elif element_type == 'ad_countdown':
            # Contador regresivo publicitario
            html.append('<div class="ad-countdown-container bg-dark text-white p-4 rounded mb-4 text-center">')
            if content:
                if content.get('title'):
                    html.append(f'<h4 class="mb-3">{content["title"]}</h4>')
                if content.get('message'):
                    html.append(f'<p class="mb-3">{content["message"]}</p>')
                if content.get('countdown'):
                    countdown = content['countdown']
                    html.append('<div class="countdown-timer d-flex justify-content-center mb-3">')
                    html.append(f'<div class="countdown-item mx-2"><span class="fs-2 fw-bold">{countdown.get("days", 0)}</span><br><small>Días</small></div>')
                    html.append(f'<div class="countdown-item mx-2"><span class="fs-2 fw-bold">{countdown.get("hours", 0)}</span><br><small>Horas</small></div>')
                    html.append(f'<div class="countdown-item mx-2"><span class="fs-2 fw-bold">{countdown.get("minutes", 0)}</span><br><small>Min</small></div>')
                    html.append('</div>')
                if content.get('offer_details'):
                    html.append('<ul class="offer-details text-start d-inline-block mb-3">')
                    for detail in content['offer_details']:
                        html.append(f'<li class="mb-1">{detail}</li>')
                    html.append('</ul>')
                if content.get('cta'):
                    cta = content['cta']
                    html.append(f'<a href="{cta.get("url", "#")}" class="btn btn-warning btn-lg">{cta.get("text", "Comprar ahora")}</a>')
            html.append('</div>')

        elif element_type == 'ad_feature':
            # Características destacadas
            html.append('<div class="ad-feature-container mb-4">')
            if content:
                if content.get('title'):
                    html.append(f'<h4 class="text-center mb-4">{content["title"]}</h4>')
                if content.get('features'):
                    html.append('<div class="row">')
                    for feature in content['features']:
                        html.append('<div class="col-md-6 col-lg-3 mb-3">')
                        html.append('<div class="feature-item text-center p-3 border rounded">')
                        if feature.get('icon'):
                            html.append(f'<i class="bi bi-{feature["icon"]} fs-1 text-primary mb-2"></i>')
                        if feature.get('title'):
                            html.append(f'<h6 class="mb-2">{feature["title"]}</h6>')
                        if feature.get('description'):
                            html.append(f'<p class="small text-muted">{feature["description"]}</p>')
                        html.append('</div>')
                        html.append('</div>')
                    html.append('</div>')
                if content.get('cta'):
                    cta = content['cta']
                    html.append(f'<div class="text-center mt-4"><a href="{cta.get("url", "#")}" class="btn btn-primary">{cta.get("text", "Ver más")}</a></div>')
            html.append('</div>')

        elif element_type == 'ad_comparison':
            # Tabla de comparación
            html.append('<div class="ad-comparison-container mb-4">')
            if content:
                if content.get('title'):
                    html.append(f'<h4 class="text-center mb-4">{content["title"]}</h4>')
                if content.get('plans'):
                    html.append('<div class="row">')
                    for plan in content['plans']:
                        popular_class = 'border-primary popular-plan' if plan.get('popular') else 'border-secondary'
                        html.append(f'<div class="col-md-4 mb-3">')
                        html.append(f'<div class="plan-card card h-100 {popular_class}">')
                        if plan.get('popular'):
                            html.append('<div class="popular-badge bg-primary text-white text-center py-1">MÁS POPULAR</div>')
                        html.append('<div class="card-body text-center">')
                        html.append(f'<h5 class="card-title">{plan.get("name", "")}</h5>')
                        html.append(f'<div class="plan-price fs-3 fw-bold text-primary mb-3">{plan.get("price", "")}</div>')
                        if plan.get('original_price'):
                            html.append(f'<small class="text-decoration-line-through text-muted">{plan["original_price"]}</small>')
                        if plan.get('features'):
                            html.append('<ul class="list-unstyled">')
                            for feature in plan['features']:
                                icon = '✓' if not feature.startswith('✗') else '✗'
                                css_class = 'text-success' if not feature.startswith('✗') else 'text-danger'
                                html.append(f'<li class="{css_class}"><small>{feature}</small></li>')
                            html.append('</ul>')
                        if plan.get('cta'):
                            cta = plan['cta']
                            variant = cta.get('variant', 'primary')
                            html.append(f'<a href="#" class="btn btn-{variant} mt-3">{cta.get("text", "Seleccionar")}</a>')
                        html.append('</div>')
                        html.append('</div>')
                        html.append('</div>')
                    html.append('</div>')
            html.append('</div>')

        elif element_type == 'ad_achievement':
            # Logros y badges
            html.append('<div class="ad-achievement-container mb-4">')
            if content:
                if content.get('title'):
                    html.append(f'<h4 class="text-center mb-4">{content["title"]}</h4>')
                if content.get('badges'):
                    html.append('<div class="row">')
                    for badge in content['badges']:
                        html.append('<div class="col-md-3 mb-3">')
                        html.append('<div class="badge-item text-center p-3 border rounded">')
                        if badge.get('icon'):
                            html.append(f'<i class="bi bi-{badge["icon"]} fs-2 text-warning mb-2"></i>')
                        if badge.get('title'):
                            html.append(f'<h6 class="mb-2">{badge["title"]}</h6>')
                        if badge.get('description'):
                            html.append(f'<p class="small text-muted">{badge["description"]}</p>')
                        html.append('</div>')
                        html.append('</div>')
                    html.append('</div>')
                if content.get('progress'):
                    progress = content['progress']
                    percentage = int((progress.get('current', 0) / progress.get('total', 1)) * 100)
                    html.append('<div class="progress-container mt-4">')
                    html.append(f'<div class="progress mb-2"><div class="progress-bar bg-success" role="progressbar" style="width: {percentage}%" aria-valuenow="{percentage}" aria-valuemin="0" aria-valuemax="100"></div></div>')
                    html.append(f'<small class="text-muted">{progress.get("message", "")}</small>')
                    html.append('</div>')
            html.append('</div>')

        elif element_type == 'content_block':
            # Renderizar un bloque de contenido reutilizable
            block_id = element.get('content')
            if block_id:
                try:
                    from courses.models import ContentBlock
                    block = ContentBlock.objects.get(id=block_id, is_public=True)

                    # Obtener elementos estructurados del ContentBlock
                    structured_elements = get_structured_content(block)

                    # Si el ContentBlock se convierte en múltiples elementos, renderizarlos recursivamente
                    if structured_elements:
                        html.append('<div class="lesson-content-block-container">')
                        html.append('<div class="lesson-content-block-header">')
                        html.append('<i class="bi bi-blockquote-left text-primary me-2"></i>')
                        html.append(f'<span class="content-block-title">Bloque: {block.title}</span>')
                        html.append('</div>')

                        # Renderizar recursivamente los elementos estructurados
                        for structured_element in structured_elements:
                            # Crear una copia del elemento con el título del bloque si no tiene título
                            element_copy = structured_element.copy()
                            if not element_copy.get('title') and block.title:
                                element_copy['title'] = block.title

                            # Renderizar el elemento usando la lógica recursiva
                            element_html = render_structured_content([element_copy])
                            html.append(element_html)

                        html.append('</div>')
                    else:
                        # Fallback: renderizar directamente si no hay elementos estructurados
                        html.append('<div class="lesson-content-block-container">')
                        html.append('<div class="lesson-content-block-header">')
                        html.append('<i class="bi bi-blockquote-left text-primary me-2"></i>')
                        html.append(f'<span class="content-block-title">Bloque: {block.title}</span>')
                        html.append('</div>')

                        # Renderizar el contenido del bloque según su tipo
                        if block.content_type == 'html' or block.content_type == 'bootstrap':
                            html.append(block.html_content)
                        elif block.content_type == 'markdown':
                            # Usar la función de procesamiento de markdown
                            processed_markdown = process_markdown(block.markdown_content)
                            html.append(processed_markdown)
                        elif block.content_type == 'json':
                            # Para JSON, mostrar como código formateado
                            import json
                            formatted_json = json.dumps(block.json_content, indent=2, ensure_ascii=False)
                            html.append(f'<pre><code>{formatted_json}</code></pre>')
                        elif block.content_type == 'text':
                            html.append(f'<p>{block.html_content}</p>')

                        html.append('</div>')

                except ContentBlock.DoesNotExist:
                    html.append('<div class="alert alert-warning">')
                    html.append('<i class="bi bi-exclamation-triangle me-2"></i>')
                    html.append(f'Bloque de contenido "{block_id}" no encontrado.')
                    html.append('</div>')
                except Exception as e:
                    html.append('<div class="alert alert-danger">')
                    html.append('<i class="bi bi-exclamation-circle me-2"></i>')
                    html.append(f'Error al cargar bloque de contenido: {str(e)}')
                    html.append('</div>')
            else:
                html.append('<div class="alert alert-info">')
                html.append('<i class="bi bi-info-circle me-2"></i>')
                html.append('Selecciona un bloque de contenido para mostrar aquí.')
                html.append('</div>')

    return mark_safe('\n'.join(html))

@register.filter
def markdown(text):
    """
    Convierte texto Markdown a HTML usando el procesador personalizado
    """
    return mark_safe(process_markdown(text))

@register.filter
def has_structured_content(lesson):
    """
    Verifica si una lección tiene contenido estructurado
    """
    return bool(lesson.structured_content)

@register.filter
def get_attached_files(lesson):
    """
    Obtiene todos los archivos adjuntos de una lección con detalles completos
    """
    files = []

    # Archivos del contenido estructurado
    if lesson.structured_content:
        for index, item in enumerate(lesson.structured_content):
            if item.get('type') == 'file' and item.get('content'):
                file_info = {
                    'id': f'structured_{index}',
                    'type': 'structured_file',
                    'title': item.get('title', 'Archivo adjunto'),
                    'url': item.get('content'),
                    'description': item.get('description', 'Archivo del contenido estructurado'),
                    'file_type': get_file_type(item.get('content', '')),
                    'file_size': get_file_size_from_url(item.get('content', '')),
                    'downloadable': True,
                    'category': 'Contenido de Lección',
                    'order': index,
                    'file_extension': get_file_extension(item.get('content', '')),
                    'is_external': is_external_url(item.get('content', '')),
                    'last_modified': 'Desconocido',
                    'author': 'Sistema'
                }
                files.append(file_info)

    # Archivos adjuntos de la lección (múltiples)
    for attachment in lesson.attachments.all():
        attachment_info = {
            'id': f'attachment_{attachment.id}',
            'type': 'lesson_attachment',
            'title': attachment.title,
            'url': attachment.file.url,
            'description': f'Archivo adjunto: {attachment.file_type}',
            'file_type': attachment.file_type,
            'file_size': attachment.file_size,
            'downloadable': True,
            'category': 'Archivos Adjuntos',
            'order': attachment.order,
            'file_extension': get_file_extension(str(attachment.file)),
            'is_external': False,
            'last_modified': attachment.uploaded_at.strftime('%d/%m/%Y %H:%M'),
            'author': lesson.module.course.tutor.username
        }
        files.append(attachment_info)

    # Archivo de tarea (legacy - mantener compatibilidad)
    if lesson.assignment_file:
        task_file_info = {
            'id': 'assignment_file',
            'type': 'assignment_file',
            'title': lesson.assignment_instructions[:50] + '...' if len(lesson.assignment_instructions or '') > 50 else (lesson.assignment_instructions or 'Recursos de tarea'),
            'url': lesson.assignment_file.url,
            'description': 'Archivo de recursos para la tarea práctica',
            'file_type': get_file_type(str(lesson.assignment_file)),
            'file_size': get_file_size(lesson.assignment_file),
            'downloadable': True,
            'category': 'Recursos de Tarea',
            'order': 999,  # Aparece al final
            'file_extension': get_file_extension(str(lesson.assignment_file)),
            'is_external': False,
            'last_modified': 'Desconocido',
            'author': lesson.module.course.tutor.username
        }
        files.append(task_file_info)

    # Ordenar archivos por orden definido
    files.sort(key=lambda x: x.get('order', 999))

    return files

def get_file_type(url):
    """
    Determina el tipo de archivo basado en la extensión de la URL
    """
    if not url:
        return 'Desconocido'

    # Convertir a string si es un objeto FileField
    url_str = str(url).lower()

    # Extensiones comunes
    file_types = {
        # Documentos
        '.pdf': 'PDF Documento',
        '.doc': 'Documento Word',
        '.docx': 'Documento Word',
        '.xls': 'Hoja de Cálculo Excel',
        '.xlsx': 'Hoja de Cálculo Excel',
        '.ppt': 'Presentación PowerPoint',
        '.pptx': 'Presentación PowerPoint',
        '.txt': 'Archivo de Texto',

        # Imágenes
        '.jpg': 'Imagen JPEG',
        '.jpeg': 'Imagen JPEG',
        '.png': 'Imagen PNG',
        '.gif': 'Imagen GIF',
        '.svg': 'Imagen SVG',
        '.webp': 'Imagen WebP',

        # Videos
        '.mp4': 'Video MP4',
        '.avi': 'Video AVI',
        '.mov': 'Video MOV',
        '.wmv': 'Video WMV',

        # Audio
        '.mp3': 'Audio MP3',
        '.wav': 'Audio WAV',
        '.aac': 'Audio AAC',

        # Archivos comprimidos
        '.zip': 'Archivo Comprimido',
        '.rar': 'Archivo Comprimido',
        '.7z': 'Archivo Comprimido',

        # Código
        '.py': 'Código Python',
        '.js': 'Código JavaScript',
        '.html': 'Código HTML',
        '.css': 'Código CSS',
        '.json': 'Archivo JSON',
        '.xml': 'Archivo XML'
    }

    for ext, file_type in file_types.items():
        if url_str.endswith(ext):
            return file_type

    return 'Archivo'

def get_file_size(file_field):
    """
    Obtiene el tamaño del archivo en formato legible
    """
    try:
        if hasattr(file_field, 'size'):
            size = file_field.size

            # Convertir bytes a unidades legibles
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return ".1f"
                size /= 1024.0

        return 'Desconocido'
    except:
        return 'Desconocido'

def get_file_size_from_url(url):
    """
    Obtiene el tamaño aproximado del archivo desde la URL (simulado)
    """
    try:
        if not url:
            return 'Desconocido'

        # Para archivos locales, intentar obtener el tamaño real
        if url.startswith('/media/'):
            # Aquí podrías implementar lógica para obtener el tamaño real del archivo
            # Por ahora, devolver un tamaño estimado basado en la extensión
            ext = get_file_extension(url).lower()
            size_estimates = {
                '.pdf': '2.5 MB',
                '.docx': '1.2 MB',
                '.doc': '850 KB',
                '.pptx': '3.1 MB',
                '.ppt': '2.8 MB',
                '.xls': '1.5 MB',
                '.xlsx': '950 KB',
                '.zip': '4.2 MB',
                '.rar': '3.8 MB',
                '.jpg': '450 KB',
                '.png': '320 KB',
                '.gif': '680 KB',
                '.mp4': '15.2 MB',
                '.avi': '12.8 MB'
            }
            return size_estimates.get(ext, 'Desconocido')

        return 'Desconocido'
    except:
        return 'Desconocido'

def get_file_extension(url):
    """
    Obtiene la extensión del archivo desde la URL
    """
    try:
        if not url:
            return ''

        # Extraer la extensión del archivo
        from urllib.parse import urlparse
        path = urlparse(url).path
        if '.' in path:
            return '.' + path.split('.')[-1].lower()

        return ''
    except:
        return ''

def is_external_url(url):
    """
    Verifica si la URL es externa (no pertenece al dominio actual)
    """
    try:
        if not url:
            return False

        from urllib.parse import urlparse
        parsed = urlparse(url)

        # Si no tiene esquema o es relativo, no es externo
        if not parsed.scheme or parsed.scheme not in ['http', 'https']:
            return False

        # Aquí podrías agregar lógica para verificar si pertenece a tu dominio
        # Por ejemplo: return not url.startswith('https://tudominio.com')
        return True
    except:
        return False

@register.filter
def get_structured_content(content_block):
    """
    Convierte un ContentBlock en elementos estructurados para renderizar como lección
    """
    if not content_block:
        return []

    structured_content = []

    try:
        # Mapeo de tipos de content block a tipos de elementos estructurados
        if content_block.content_type == 'html' or content_block.content_type == 'bootstrap':
            # HTML/Bootstrap se convierte en elemento 'text' con contenido HTML
            structured_content.append({
                'type': 'text',
                'title': content_block.title,
                'content': content_block.html_content
            })

        elif content_block.content_type == 'markdown':
            # Markdown se convierte en elemento 'markdown'
            structured_content.append({
                'type': 'markdown',
                'title': content_block.title,
                'content': content_block.markdown_content
            })

        elif content_block.content_type == 'json':
            # JSON puede contener elementos estructurados directamente
            if isinstance(content_block.json_content, list):
                # Si es una lista de elementos estructurados, devolverla directamente
                structured_content.extend(content_block.json_content)
            else:
                # Si es un objeto JSON simple, mostrarlo como código
                import json
                formatted_json = json.dumps(content_block.json_content, indent=2, ensure_ascii=False)
                structured_content.append({
                    'type': 'text',
                    'title': content_block.title,
                    'content': f'<pre><code class="language-json">{formatted_json}</code></pre>'
                })

        elif content_block.content_type == 'text':
            # Texto simple
            structured_content.append({
                'type': 'text',
                'title': content_block.title,
                'content': content_block.html_content
            })

        elif content_block.content_type == 'image':
            # Imagen
            structured_content.append({
                'type': 'image',
                'title': content_block.title,
                'content': content_block.json_content.get('url', ''),
                'items': []  # No aplica para imagen
            })

        elif content_block.content_type == 'video':
            # Video
            structured_content.append({
                'type': 'video',
                'title': content_block.title,
                'content': {
                    'url': content_block.json_content.get('url', ''),
                    'description': content_block.title,
                    'duration': 0
                }
            })

        elif content_block.content_type == 'quote':
            # Cita se convierte en texto con formato especial
            quote_text = content_block.json_content.get('text', 'Cita no especificada')
            author = content_block.json_content.get('author', '')
            formatted_quote = f'<blockquote>"{quote_text}"'
            if author:
                formatted_quote += f'<footer class="blockquote-footer">{author}</footer>'
            formatted_quote += '</blockquote>'

            structured_content.append({
                'type': 'text',
                'title': content_block.title,
                'content': formatted_quote
            })

        elif content_block.content_type == 'code':
            # Código se muestra como bloque de código
            code_content = content_block.json_content.get('code', 'Código no especificado')
            language = content_block.json_content.get('language', 'text')
            formatted_code = f'<pre><code class="language-{language}">{code_content}</code></pre>'

            structured_content.append({
                'type': 'text',
                'title': content_block.title,
                'content': formatted_code
            })

        elif content_block.content_type == 'list':
            # Lista
            list_type = content_block.json_content.get('type', 'unordered')
            items = content_block.json_content.get('items', [])

            structured_content.append({
                'type': 'list',
                'title': content_block.title,
                'content': '',
                'items': items
            })

        elif content_block.content_type == 'table':
            # Tabla se convierte en HTML de tabla
            headers = content_block.json_content.get('headers', [])
            rows = content_block.json_content.get('rows', [])

            table_html = '<table class="table table-striped">'
            if headers:
                table_html += '<thead><tr>'
                for header in headers:
                    table_html += f'<th>{header}</th>'
                table_html += '</tr></thead>'

            table_html += '<tbody>'
            for row in rows:
                table_html += '<tr>'
                for cell in row:
                    table_html += f'<td>{cell}</td>'
                table_html += '</tr>'
            table_html += '</tbody></table>'

            structured_content.append({
                'type': 'text',
                'title': content_block.title,
                'content': table_html
            })

        elif content_block.content_type == 'card':
            # Tarjeta se convierte en HTML de card
            card_html = '<div class="card">'
            if content_block.json_content.get('header'):
                card_html += f'<div class="card-header">{content_block.json_content["header"]}</div>'

            card_html += '<div class="card-body">'
            if content_block.json_content.get('title'):
                card_html += f'<h5 class="card-title">{content_block.json_content["title"]}</h5>'
            if content_block.json_content.get('text'):
                card_html += f'<p class="card-text">{content_block.json_content["text"]}</p>'
            if content_block.json_content.get('button'):
                button = content_block.json_content['button']
                card_html += f'<a href="{button.get("url", "#")}" class="btn btn-primary">{button.get("text", "Ver más")}</a>'
            card_html += '</div></div>'

            structured_content.append({
                'type': 'text',
                'title': content_block.title,
                'content': card_html
            })

        elif content_block.content_type == 'alert':
            # Alerta
            alert_type = content_block.json_content.get('type', 'info')
            message = content_block.json_content.get('message', 'Mensaje de alerta')
            alert_html = f'<div class="alert alert-{alert_type}" role="alert">{message}</div>'

            structured_content.append({
                'type': 'text',
                'title': content_block.title,
                'content': alert_html
            })

        elif content_block.content_type == 'button':
            # Botón
            button_html = f'<a href="{content_block.json_content.get("url", "#")}" class="btn btn-{content_block.json_content.get("style", "primary")} btn-{content_block.json_content.get("size", "md")}">'
            if content_block.json_content.get('icon'):
                button_html += f'<i class="bi bi-{content_block.json_content["icon"]}></i> '
            button_html += f'{content_block.json_content.get("text", "Botón")}</a>'

            structured_content.append({
                'type': 'text',
                'title': content_block.title,
                'content': button_html
            })

        elif content_block.content_type == 'form':
            # Formulario se convierte en HTML básico
            form_html = f'<form method="post" action="{content_block.json_content.get("action", "#")}">'
            for field in content_block.json_content.get('fields', []):
                form_html += f'<div class="mb-3"><label class="form-label">{field.get("label", "")}</label>'
                if field.get('type') == 'textarea':
                    form_html += f'<textarea class="form-control" name="{field.get("name", "")}" placeholder="{field.get("placeholder", "")}"></textarea>'
                else:
                    form_html += f'<input type="{field.get("type", "text")}" class="form-control" name="{field.get("name", "")}" placeholder="{field.get("placeholder", "")}">'
                form_html += '</div>'
            form_html += f'<button type="submit" class="btn btn-primary">{content_block.json_content.get("submit_text", "Enviar")}</button></form>'

            structured_content.append({
                'type': 'text',
                'title': content_block.title,
                'content': form_html
            })

        elif content_block.content_type == 'divider':
            # Separador
            structured_content.append({
                'type': 'text',
                'title': '',
                'content': '<hr class="my-4">'
            })

        elif content_block.content_type == 'icon':
            # Ícono
            icon_html = f'<div class="text-center"><i class="bi bi-{content_block.json_content.get("icon", "star")} fs-1 text-{content_block.json_content.get("color", "primary")}"></i>'
            if content_block.json_content.get('text'):
                icon_html += f'<p class="mt-2">{content_block.json_content["text"]}</p>'
            icon_html += '</div>'

            structured_content.append({
                'type': 'text',
                'title': content_block.title,
                'content': icon_html
            })

        elif content_block.content_type == 'progress':
            # Barra de progreso
            value = content_block.json_content.get('value', 50)
            color = content_block.json_content.get('color', 'primary')
            progress_html = f'<div class="progress mb-3"><div class="progress-bar bg-{color}" role="progressbar" style="width: {value}%" aria-valuenow="{value}" aria-valuemin="0" aria-valuemax="100">{value}%</div></div>'

            structured_content.append({
                'type': 'text',
                'title': content_block.title,
                'content': progress_html
            })

        elif content_block.content_type == 'badge':
            # Insignia
            badge_html = f'<span class="badge bg-{content_block.json_content.get("color", "primary")} fs-6">'
            if content_block.json_content.get('icon'):
                badge_html += f'<i class="bi bi-{content_block.json_content["icon"]}></i> '
            badge_html += f'{content_block.json_content.get("text", "Insignia")}</span>'

            structured_content.append({
                'type': 'text',
                'title': content_block.title,
                'content': badge_html
            })

        elif content_block.content_type == 'timeline':
            # Línea de tiempo se convierte en lista
            items = content_block.json_content.get('items', [])
            timeline_html = '<div class="timeline">'
            for item in items:
                timeline_html += f'<div class="timeline-item"><div class="timeline-marker bg-{item.get("color", "primary")}"></div><div class="timeline-content"><h6>{item.get("title", "")}</h6><p>{item.get("description", "")}</p><small class="text-muted">{item.get("date", "")}</small></div></div>'
            timeline_html += '</div>'

            structured_content.append({
                'type': 'text',
                'title': content_block.title,
                'content': timeline_html
            })

        else:
            # Tipo desconocido - mostrar como texto plano
            structured_content.append({
                'type': 'text',
                'title': content_block.title,
                'content': f'<p>Tipo de contenido no soportado: {content_block.content_type}</p>'
            })

    except Exception as e:
        # En caso de error, mostrar mensaje de error
        structured_content.append({
            'type': 'text',
            'title': 'Error',
            'content': f'<div class="alert alert-danger">Error al procesar el bloque de contenido: {str(e)}</div>'
        })

    return structured_content