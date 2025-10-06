from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class BitacoraEntry(models.Model):
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)

    CATEGORIA_CHOICES = [
        ('personal', 'Personal'),
        ('viaje', 'Viaje'),
        ('trabajo', 'Trabajo'),
        ('meta', 'Meta'),
        ('idea', 'Idea'),
        ('recuerdo', 'Recuerdo'),
        ('diario', 'Diario'),
        ('reflexion', 'Reflexión'),
    ]
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, default='personal')

    # Relaciones opcionales con otros modelos
    related_event = models.ForeignKey('events.Event', on_delete=models.SET_NULL, null=True, blank=True)
    related_task = models.ForeignKey('events.Task', on_delete=models.SET_NULL, null=True, blank=True)
    related_project = models.ForeignKey('events.Project', on_delete=models.SET_NULL, null=True, blank=True)
    related_room = models.ForeignKey('rooms.Room', on_delete=models.SET_NULL, null=True, blank=True)

    # Ubicación geográfica opcional
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Tags reutilizando el modelo Tag de events
    tags = models.ManyToManyField('events.Tag', blank=True)

    # Integración con contenido estructurado de courses
    structured_content = models.JSONField(default=list, blank=True, help_text="Contenido estructurado con elementos de courses")

    # Privacidad
    is_public = models.BooleanField(default=False)

    # Mood o estado de ánimo
    mood = models.CharField(max_length=50, blank=True)

    # Contenido estructurado (bloques de contenido insertados)
    structured_content = models.JSONField(default=list, blank=True, help_text="Bloques de contenido estructurado insertados")

    def __str__(self):
        return f"{self.titulo} - {self.autor.username}"

    def get_structured_content_blocks(self):
        """Obtiene la lista de bloques de contenido estructurado"""
        return self.structured_content if self.structured_content else []

    def render_structured_content(self):
        """Renderiza el contenido estructurado como HTML"""
        html = ""
        for block in self.get_structured_content_blocks():
            if block.get('type') == 'content_block':
                html += self.render_content_block(block)
        return html

    def render_content_block(self, block):
        """Renderiza un bloque de contenido individual"""
        content = block.get('content', '')
        content_type = block.get('content_type', 'html')
        title = block.get('title', '')

        # Renderizar según el tipo de contenido
        if content_type == 'html':
            return f'<div class="content-block content-block-html"><h5>{title}</h5>{content}</div>'
        elif content_type == 'bootstrap':
            return f'<div class="content-block content-block-bootstrap"><h5>{title}</h5>{content}</div>'
        elif content_type == 'text':
            return f'<div class="content-block content-block-text"><h5>{title}</h5><p>{content}</p></div>'
        elif content_type == 'markdown':
            # Convertir markdown básico a HTML
            import re
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)  # Negrita
            content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)  # Cursiva
            content = re.sub(r'`(.*?)`', r'<code>\1</code>', content)  # Código
            content = content.replace('\n', '<br>')
            return f'<div class="content-block content-block-markdown"><h5>{title}</h5>{content}</div>'
        elif content_type == 'quote':
            return f'<div class="content-block content-block-quote"><blockquote class="blockquote"><p class="mb-0">{content}</p></blockquote><footer class="blockquote-footer">{title}</footer></div>'
        elif content_type == 'code':
            return f'<div class="content-block content-block-code"><h5>{title}</h5><pre><code>{content}</code></pre></div>'
        elif content_type == 'card':
            return f'<div class="content-block content-block-card"><div class="card"><div class="card-body"><h5 class="card-title">{title}</h5><p class="card-text">{content}</p></div></div></div>'
        elif content_type == 'alert':
            return f'<div class="content-block content-block-alert"><div class="alert alert-info"><h5>{title}</h5>{content}</div></div>'
        elif content_type == 'json':
            # Verificar si es contenido publicitario estructurado
            if isinstance(content, list) and content and isinstance(content[0], dict) and 'type' in content[0]:
                # Es contenido publicitario estructurado, renderizar como componentes
                return self.render_ad_content(content, title)
            else:
                # Para contenido JSON regular, formatearlo como código JSON legible
                try:
                    import json
                    if isinstance(content, (dict, list)):
                        # Ya está parseado como objeto Python
                        formatted_json = json.dumps(content, indent=2, ensure_ascii=False)
                    else:
                        # Es un string, intentar parsear
                        parsed = json.loads(content)
                        formatted_json = json.dumps(parsed, indent=2, ensure_ascii=False)
                    return f'<div class="content-block content-block-json"><h5>{title}</h5><pre><code class="language-json">{formatted_json}</code></pre></div>'
                except (json.JSONDecodeError, TypeError):
                    # Si no se puede parsear, mostrar como texto plano
                    return f'<div class="content-block content-block-json"><h5>{title}</h5><pre><code>{content}</code></pre></div>'
        else:
            return f'<div class="content-block content-block-default"><h5>{title}</h5>{content}</div>'

    def render_ad_content(self, ad_components, title):
        """Renderizar componentes publicitarios complejos"""
        html_parts = [f'<div class="content-block content-block-ad"><h5>{title}</h5>']

        for component in ad_components:
            component_type = component.get('type', '')
            content = component.get('content', {})

            if component_type == 'ad_banner':
                html_parts.append(self.render_ad_banner(content))
            elif component_type == 'ad_card':
                html_parts.append(self.render_ad_card(content))
            elif component_type == 'ad_alert':
                html_parts.append(self.render_ad_alert(content))
            elif component_type == 'ad_testimonial':
                html_parts.append(self.render_ad_testimonial(content))
            elif component_type == 'ad_countdown':
                html_parts.append(self.render_ad_countdown(content))
            elif component_type == 'ad_feature':
                html_parts.append(self.render_ad_feature(content))
            elif component_type == 'ad_comparison':
                html_parts.append(self.render_ad_comparison(content))
            elif component_type == 'ad_achievement':
                html_parts.append(self.render_ad_achievement(content))
            else:
                # Fallback para tipos desconocidos
                html_parts.append(f'<div class="alert alert-secondary">Tipo de componente desconocido: {component_type}</div>')

        html_parts.append('</div>')
        return ''.join(html_parts)

    def render_ad_banner(self, content):
        """Renderizar banner publicitario"""
        header = content.get('header', '')
        subheader = content.get('subheader', '')
        features = content.get('features', [])
        offer = content.get('offer', '')
        price = content.get('price', {})
        cta = content.get('cta', {})
        secondary_cta = content.get('secondary_cta', {})

        html = '<div class="ad-banner bg-primary text-white p-4 rounded mb-3">'
        if header:
            html += f'<h4 class="mb-2">{header}</h4>'
        if subheader:
            html += f'<p class="mb-3">{subheader}</p>'

        if features:
            html += '<ul class="list-unstyled mb-3">'
            for feature in features:
                html += f'<li class="mb-1"><i class="bi bi-check-circle me-2"></i>{feature}</li>'
            html += '</ul>'

        if offer:
            html += f'<div class="alert alert-light text-dark mb-3"><strong>{offer}</strong></div>'

        if price:
            original = price.get('original', '')
            discounted = price.get('discounted', '')
            period = price.get('period', '')
            html += '<div class="d-flex align-items-center mb-3">'
            if original:
                html += f'<span class="text-decoration-line-through me-2">{original}</span>'
            if discounted:
                html += f'<span class="h5 text-warning me-2">{discounted}</span>'
            if period:
                html += f'<small class="text-light">{period}</small>'
            html += '</div>'

        if cta:
            text = cta.get('text', 'Click aquí')
            url = cta.get('url', '#')
            color = cta.get('color', 'light')
            html += f'<a href="{url}" class="btn btn-{color} me-2">{text}</a>'

        if secondary_cta:
            text = secondary_cta.get('text', 'Más información')
            url = secondary_cta.get('url', '#')
            html += f'<a href="{url}" class="btn btn-outline-light">{text}</a>'

        html += '</div>'
        return html

    def render_ad_card(self, content):
        """Renderizar tarjeta publicitaria"""
        header = content.get('header', '')
        description = content.get('description', '')
        highlights = content.get('highlights', [])
        price = content.get('price', '')
        badge = content.get('badge', '')
        cta = content.get('cta', {})

        html = '<div class="card ad-card mb-3">'
        if badge:
            html += f'<div class="card-header text-center"><span class="badge bg-warning">{badge}</span></div>'

        html += '<div class="card-body">'
        if header:
            html += f'<h5 class="card-title">{header}</h5>'
        if description:
            html += f'<p class="card-text">{description}</p>'

        if highlights:
            html += '<ul class="list-group list-group-flush mb-3">'
            for highlight in highlights:
                html += f'<li class="list-group-item"><i class="bi bi-star me-2 text-warning"></i>{highlight}</li>'
            html += '</ul>'

        if price:
            html += f'<div class="text-center mb-3"><h4 class="text-primary">{price}</h4></div>'

        if cta:
            text = cta.get('text', 'Comprar')
            url = cta.get('url', '#')
            html += f'<div class="text-center"><a href="{url}" class="btn btn-primary">{text}</a></div>'

        html += '</div></div>'
        return html

    def render_ad_alert(self, content):
        """Renderizar alerta publicitaria"""
        icon = content.get('icon', 'ℹ️')
        title = content.get('title', '')
        message = content.get('message', '')
        features = content.get('features', [])
        cta = content.get('cta', {})
        variant = content.get('variant', 'info')

        html = f'<div class="alert alert-{variant} ad-alert mb-3">'
        html += '<div class="d-flex">'
        html += f'<div class="me-3 fs-4">{icon}</div>'
        html += '<div class="flex-grow-1">'

        if title:
            html += f'<h6 class="alert-heading mb-2">{title}</h6>'
        if message:
            html += f'<p class="mb-2">{message}</p>'

        if features:
            html += '<ul class="mb-2">'
            for feature in features:
                html += f'<li>{feature}</li>'
            html += '</ul>'

        if cta:
            text = cta.get('text', 'Acción')
            url = cta.get('url', '#')
            html += f'<a href="{url}" class="btn btn-sm btn-primary">{text}</a>'

        html += '</div></div></div>'
        return html

    def render_ad_testimonial(self, content):
        """Renderizar testimonial publicitario"""
        quote = content.get('quote', '')
        author = content.get('author', {})
        achievement = content.get('achievement', '')

        html = '<div class="testimonial-card bg-light p-4 rounded mb-3">'
        html += '<div class="text-center">'

        if quote:
            html += f'<blockquote class="blockquote mb-3"><p class="mb-0">"{quote}"</p></blockquote>'

        if author:
            name = author.get('name', '')
            role = author.get('role', '')
            avatar = author.get('avatar', '')
            rating = author.get('rating', 0)

            if avatar:
                html += f'<img src="{avatar}" alt="{name}" class="rounded-circle mb-2" style="width: 60px; height: 60px;">'

            if name:
                html += f'<h6 class="mb-1">{name}</h6>'
            if role:
                html += f'<p class="text-muted small mb-2">{role}</p>'

            if rating:
                html += '<div class="mb-2">'
                for i in range(5):
                    star_class = 'bi-star-fill text-warning' if i < rating else 'bi-star text-muted'
                    html += f'<i class="bi {star_class}"></i>'
                html += '</div>'

        if achievement:
            html += f'<div class="badge bg-success">{achievement}</div>'

        html += '</div></div>'
        return html

    def render_ad_countdown(self, content):
        """Renderizar contador regresivo publicitario"""
        title = content.get('title', '')
        message = content.get('message', '')
        countdown = content.get('countdown', {})
        offer_details = content.get('offer_details', [])
        cta = content.get('cta', {})

        html = '<div class="countdown-banner bg-danger text-white p-4 rounded mb-3 text-center">'

        if title:
            html += f'<h5 class="mb-2">{title}</h5>'
        if message:
            html += f'<p class="mb-3">{message}</p>'

        if countdown:
            days = countdown.get('days', 0)
            hours = countdown.get('hours', 0)
            minutes = countdown.get('minutes', 0)
            html += '<div class="countdown-timer mb-3">'
            html += f'<span class="h3">{days}d</span> <span class="h3">{hours}h</span> <span class="h3">{minutes}m</span>'
            html += '</div>'

        if offer_details:
            html += '<ul class="list-unstyled mb-3">'
            for detail in offer_details:
                html += f'<li><i class="bi bi-check-circle me-2"></i>{detail}</li>'
            html += '</ul>'

        if cta:
            text = cta.get('text', '¡Apúrate!')
            url = cta.get('url', '#')
            html += f'<a href="{url}" class="btn btn-light btn-lg">{text}</a>'

        html += '</div>'
        return html

    def render_ad_feature(self, content):
        """Renderizar sección de características"""
        title = content.get('title', '')
        features = content.get('features', [])
        cta = content.get('cta', {})

        html = '<div class="feature-section mb-3">'

        if title:
            html += f'<h5 class="text-center mb-4">{title}</h5>'

        if features:
            html += '<div class="row">'
            for feature in features:
                icon = feature.get('icon', '🔧')
                feat_title = feature.get('title', '')
                description = feature.get('description', '')

                html += '<div class="col-md-6 mb-3">'
                html += '<div class="d-flex">'
                html += f'<div class="me-3 fs-2">{icon}</div>'
                html += '<div>'
                if feat_title:
                    html += f'<h6 class="mb-1">{feat_title}</h6>'
                if description:
                    html += f'<p class="text-muted small mb-0">{description}</p>'
                html += '</div></div></div>'
            html += '</div>'

        if cta:
            text = cta.get('text', 'Ver más')
            url = cta.get('url', '#')
            html += f'<div class="text-center mt-3"><a href="{url}" class="btn btn-primary">{text}</a></div>'

        html += '</div>'
        return html

    def render_ad_comparison(self, content):
        """Renderizar tabla de comparación"""
        title = content.get('title', '')
        plans = content.get('plans', [])

        html = '<div class="comparison-section mb-3">'

        if title:
            html += f'<h5 class="text-center mb-4">{title}</h5>'

        if plans:
            html += '<div class="row">'
            for plan in plans:
                name = plan.get('name', '')
                price = plan.get('price', '')
                original_price = plan.get('original_price', '')
                popular = plan.get('popular', False)
                features = plan.get('features', [])
                cta = plan.get('cta', {})

                col_class = 'col-lg-4 mb-3'
                card_class = 'card h-100'
                if popular:
                    card_class += ' border-primary'
                    col_class += ' position-relative'

                html += f'<div class="{col_class}">'
                if popular:
                    html += '<div class="popular-badge">Más Popular</div>'

                html += f'<div class="{card_class}">'
                html += '<div class="card-header text-center bg-light">'
                html += f'<h6 class="mb-1">{name}</h6>'

                if original_price:
                    html += f'<small class="text-decoration-line-through text-muted">{original_price}</small><br>'

                html += f'<span class="h5 text-primary">{price}</span>'
                html += '</div>'

                html += '<div class="card-body">'
                if features:
                    html += '<ul class="list-unstyled">'
                    for feature in features:
                        html += f'<li class="mb-2"><i class="bi bi-check-circle text-success me-2"></i>{feature}</li>'
                    html += '</ul>'

                if cta:
                    text = cta.get('text', 'Seleccionar')
                    variant = cta.get('variant', 'primary')
                    html += f'<div class="text-center mt-3"><button class="btn btn-{variant} w-100">{text}</button></div>'

                html += '</div></div></div>'
            html += '</div>'

        html += '</div>'
        return html

    def render_ad_achievement(self, content):
        """Renderizar sección de logros"""
        title = content.get('title', '')
        badges = content.get('badges', [])
        progress = content.get('progress', {})

        html = '<div class="achievement-section mb-3">'

        if title:
            html += f'<h5 class="text-center mb-4">{title}</h5>'

        if badges:
            html += '<div class="row">'
            for badge in badges:
                icon = badge.get('icon', '🏆')
                badge_title = badge.get('title', '')
                description = badge.get('description', '')

                html += '<div class="col-md-6 mb-3">'
                html += '<div class="card text-center h-100">'
                html += '<div class="card-body">'
                html += f'<div class="fs-1 mb-2">{icon}</div>'
                if badge_title:
                    html += f'<h6 class="card-title">{badge_title}</h6>'
                if description:
                    html += f'<p class="card-text small text-muted">{description}</p>'
                html += '</div></div></div>'
            html += '</div>'

        if progress:
            current = progress.get('current', 0)
            total = progress.get('total', 1)
            message = progress.get('message', '')

            percentage = (current / total * 100) if total > 0 else 0
            html += '<div class="progress-section text-center">'
            html += f'<div class="progress mb-2" style="height: 20px;">'
            html += f'<div class="progress-bar bg-success" role="progressbar" style="width: {percentage}%"></div>'
            html += '</div>'
            if message:
                html += f'<p class="text-muted small">{message}</p>'
            html += '</div>'

        html += '</div>'
        return html

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = "Entrada de Bitácora"
        verbose_name_plural = "Entradas de Bitácora"

    def get_structured_content_blocks(self):
        """Obtiene los bloques de contenido estructurado"""
        return self.structured_content if self.structured_content else []

class BitacoraAttachment(models.Model):
    entry = models.ForeignKey(BitacoraEntry, on_delete=models.CASCADE, related_name='attachments')
    archivo = models.FileField(upload_to='bitacora/attachments/')
    tipo = models.CharField(max_length=20, choices=[
        ('image', 'Imagen'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('document', 'Documento'),
    ])
    descripcion = models.CharField(max_length=200, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo} - {self.entry.titulo}"

    class Meta:
        verbose_name = "Adjunto de Bitácora"
        verbose_name_plural = "Adjuntos de Bitácora"
