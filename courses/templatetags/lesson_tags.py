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
                html.append(f'<p class="lesson-exercise-content">{content}</p>')
            html.append('</div>')

        elif element_type == 'markdown':
            html.append('<div class="lesson-markdown-container">')
            html.append('<div class="lesson-markdown-header">')
            html.append('<i class="bi bi-markdown text-primary me-2"></i>')
            html.append('<span class="markdown-title">Contenido Formateado</span>')
            html.append('</div>')
            if content:
                # Convertir saltos de línea simples a <br> para simular markdown básico
                formatted_content = content.replace('\n', '<br>')
                html.append(f'<div class="lesson-markdown-content">{formatted_content}</div>')
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

        elif element_type == 'content_block':
            # Renderizar un bloque de contenido reutilizable
            block_id = element.get('content')
            if block_id:
                try:
                    from courses.models import ContentBlock
                    block = ContentBlock.objects.get(id=block_id, is_public=True)
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