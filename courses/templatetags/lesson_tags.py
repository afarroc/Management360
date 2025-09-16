from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

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
                html.append(f'<p class="lesson-content">{content.replace(chr(10), "<br>")}</p>')
            html.append('</div>')

        elif element_type == 'list':
            html.append('<div class="lesson-list-container">')
            if title:
                html.append(f'<h4 class="lesson-list-title"><i class="bi bi-list-check me-2 text-warning"></i>{title}</h4>')
            if items:
                html.append('<ul class="lesson-list">')
                for item in items:
                    html.append(f'<li class="lesson-list-item"><span class="list-bullet">✓</span> {item}</li>')
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

    return mark_safe('\n'.join(html))

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