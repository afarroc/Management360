from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.simple_tag
def render_content_block(content):
    """
    Template tag para renderizar bloques de contenido JSON como componentes HTML
    """
    # Si el contenido ya es un diccionario (ya parseado), usarlo directamente
    if isinstance(content, dict):
        data = content
    # Si el contenido ya es una lista (ya parseada), usarla directamente
    elif isinstance(content, list):
        data = content
    else:
        # Intentar parsear como string JSON
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            # Intentar parsear JSON con comillas simples (más tolerante)
            try:
                # Reemplazar comillas simples por dobles en las claves y valores simples
                fixed_content = str(content).replace("'", '"')
                data = json.loads(fixed_content)
            except (json.JSONDecodeError, TypeError, AttributeError):
                # Si no es JSON válido, devolver como texto plano
                return mark_safe(f'<pre><code>{content}</code></pre>')

    # Procesar los datos parseados
    # Si es una lista de componentes, renderizar cada uno
    if isinstance(data, list) and data:
        html_parts = []
        for component in data:
            if isinstance(component, dict) and 'type' in component:
                html_parts.append(render_component(component))
        return mark_safe(''.join(html_parts))
    # Si es un solo componente, renderizarlo
    elif isinstance(data, dict) and 'type' in data:
        return mark_safe(render_component(data))
    else:
        # Si no es un componente estructurado, devolver como JSON formateado
        return mark_safe(f'<pre><code class="language-json">{json.dumps(data, indent=2)}</code></pre>')

def render_component(component):
    """
    Renderiza un componente individual basado en su tipo
    """
    component_type = component.get('type', '')
    content = component.get('content', {})

    if component_type == 'ad_banner':
        return render_ad_banner(content)
    elif component_type == 'ad_card':
        return render_ad_card(content)
    elif component_type == 'ad_alert':
        return render_ad_alert(content)
    elif component_type == 'ad_testimonial':
        return render_ad_testimonial(content)
    elif component_type == 'ad_countdown':
        return render_ad_countdown(content)
    elif component_type == 'ad_feature':
        return render_ad_feature(content)
    elif component_type == 'ad_comparison':
        return render_ad_comparison(content)
    elif component_type == 'ad_achievement':
        return render_ad_achievement(content)
    else:
        return f'<div class="alert alert-info">Componente desconocido: {component_type}</div>'

def render_ad_banner(content):
    """Renderiza un banner publicitario"""
    header = content.get('header', '')
    subheader = content.get('subheader', '')
    features = content.get('features', [])
    offer = content.get('offer', '')
    price = content.get('price', {})
    cta = content.get('cta', {})
    secondary_cta = content.get('secondary_cta', {})

    features_html = ''.join([f'<li class="mb-1"><i class="bi bi-check-circle me-2"></i>{feature}</li>' for feature in features])

    html = f'''
    <div class="ad-banner bg-primary text-white p-4 rounded mb-3">
        <h4 class="mb-2">{header}</h4>
        <p class="mb-3">{subheader}</p>
        <ul class="list-unstyled mb-3">
            {features_html}
        </ul>
    '''

    if offer:
        html += f'<div class="alert alert-light text-dark mb-3"><strong>{offer}</strong></div>'

    if price:
        original = price.get('original', '')
        discounted = price.get('discounted', '')
        period = price.get('period', '')
        html += f'''
        <div class="d-flex align-items-center mb-3">
            <span class="text-decoration-line-through me-2">{original}</span>
            <span class="h5 text-warning me-2">{discounted}</span>
            <small class="text-light">{period}</small>
        </div>
        '''

    if cta:
        text = cta.get('text', '')
        url = cta.get('url', '#')
        color = cta.get('color', 'success')
        html += f'<a href="{url}" class="btn btn-{color} me-2">{text}</a>'

    if secondary_cta:
        text = secondary_cta.get('text', '')
        url = secondary_cta.get('url', '#')
        html += f'<a href="{url}" class="btn btn-outline-light">{text}</a>'

    html += '</div>'
    return html

def render_ad_card(content):
    """Renderiza una tarjeta publicitaria"""
    header = content.get('header', '')
    description = content.get('description', '')
    highlights = content.get('highlights', [])
    price = content.get('price', '')
    badge = content.get('badge', '')
    cta = content.get('cta', {})

    highlights_html = ''.join([f'<li class="list-group-item"><i class="bi bi-star me-2 text-warning"></i>{highlight}</li>' for highlight in highlights])

    html = f'''
    <div class="card ad-card mb-3">
        <div class="card-header text-center">
            <span class="badge bg-warning">{badge}</span>
        </div>
        <div class="card-body">
            <h5 class="card-title">{header}</h5>
            <p class="card-text">{description}</p>
            <ul class="list-group list-group-flush mb-3">
                {highlights_html}
            </ul>
            <div class="text-center mb-3">
                <h4 class="text-primary">{price}</h4>
            </div>
    '''

    if cta:
        text = cta.get('text', '')
        url = cta.get('url', '#')
        html += f'<div class="text-center"><a href="{url}" class="btn btn-primary">{text}</a></div>'

    html += '</div></div>'
    return html

def render_ad_alert(content):
    """Renderiza una alerta publicitaria"""
    icon = content.get('icon', '👥')
    title = content.get('title', '')
    message = content.get('message', '')
    features = content.get('features', [])
    cta = content.get('cta', {})

    features_html = ''.join([f'<li>{feature}</li>' for feature in features])

    html = f'''
    <div class="alert alert-info ad-alert mb-3">
        <div class="d-flex">
            <div class="me-3 fs-4">{icon}</div>
            <div class="flex-grow-1">
                <h6 class="alert-heading mb-2">{title}</h6>
                <p class="mb-2">{message}</p>
                <ul class="mb-2">
                    {features_html}
                </ul>
    '''

    if cta:
        text = cta.get('text', '')
        url = cta.get('url', '#')
        html += f'<a href="{url}" class="btn btn-sm btn-primary">{text}</a>'

    html += '</div></div></div>'
    return html

def render_ad_testimonial(content):
    """Renderiza un testimonial"""
    quote = content.get('quote', '')
    author = content.get('author', {})
    achievement = content.get('achievement', '')

    author_name = author.get('name', '')
    author_role = author.get('role', '')
    author_avatar = author.get('avatar', '')
    rating = author.get('rating', 5)

    stars = ''.join(['<i class="bi bi-star-fill text-warning"></i>' for _ in range(rating)])

    html = f'''
    <div class="testimonial-card bg-light p-4 rounded mb-3">
        <div class="text-center">
            <blockquote class="blockquote mb-3">
                <p class="mb-0">{quote}</p>
            </blockquote>
            <img src="{author_avatar}" alt="{author_name}" class="rounded-circle mb-2" style="width: 60px; height: 60px;">
            <h6 class="mb-1">{author_name}</h6>
            <p class="text-muted small mb-2">{author_role}</p>
            <div class="mb-2">
                {stars}
            </div>
            <div class="badge bg-success">{achievement}</div>
        </div>
    </div>
    '''
    return html

def render_ad_countdown(content):
    """Renderiza un contador regresivo"""
    title = content.get('title', '')
    message = content.get('message', '')
    countdown = content.get('countdown', {})
    offer_details = content.get('offer_details', [])
    cta = content.get('cta', {})

    days = countdown.get('days', 2)
    hours = countdown.get('hours', 12)
    minutes = countdown.get('minutes', 30)

    details_html = ''.join([f'<li><i class="bi bi-check-circle me-2"></i>{detail}</li>' for detail in offer_details])

    html = f'''
    <div class="countdown-banner bg-danger text-white p-4 rounded mb-3 text-center">
        <h5 class="mb-2">{title}</h5>
        <p class="mb-3">{message}</p>
        <div class="countdown-timer mb-3">
            <span class="h3">{days}d</span>
            <span class="h3">{hours}h</span>
            <span class="h3">{minutes}m</span>
        </div>
        <ul class="list-unstyled mb-3">
            {details_html}
        </ul>
    '''

    if cta:
        text = cta.get('text', '')
        url = cta.get('url', '#')
        html += f'<a href="{url}" class="btn btn-light btn-lg">{text}</a>'

    html += '</div>'
    return html

def render_ad_feature(content):
    """Renderiza una sección de características"""
    title = content.get('title', '')
    features = content.get('features', [])
    cta = content.get('cta', {})

    features_html = ''
    for feature in features:
        icon = feature.get('icon', '🤖')
        title_feat = feature.get('title', '')
        description = feature.get('description', '')
        features_html += f'''
        <div class="col-md-6 mb-3">
            <div class="d-flex">
                <div class="me-3 fs-2">{icon}</div>
                <div>
                    <h6 class="mb-1">{title_feat}</h6>
                    <p class="text-muted small mb-0">{description}</p>
                </div>
            </div>
        </div>
        '''

    html = f'''
    <div class="feature-section mb-3">
        <h5 class="text-center mb-4">{title}</h5>
        <div class="row">
            {features_html}
        </div>
    '''

    if cta:
        text = cta.get('text', '')
        url = cta.get('url', '#')
        html += f'<div class="text-center mt-3"><a href="{url}" class="btn btn-primary">{text}</a></div>'

    html += '</div>'
    return html

def render_ad_comparison(content):
    """Renderiza una tabla comparativa"""
    title = content.get('title', '')
    plans = content.get('plans', [])

    plans_html = ''
    for plan in plans:
        name = plan.get('name', '')
        price = plan.get('price', '')
        original_price = plan.get('original_price', '')
        popular = plan.get('popular', False)
        features = plan.get('features', [])
        cta = plan.get('cta', {})

        features_html = ''.join([f'<li class="mb-2"><i class="bi bi-check-circle text-success me-2"></i>{feature}</li>' for feature in features])

        card_class = 'border-primary' if popular else ''
        popular_badge = '<div class="popular-badge">Más Popular</div>' if popular else ''

        cta_text = cta.get('text', '')
        cta_variant = cta.get('variant', 'outline')

        plans_html += f'''
        <div class="col-lg-4 mb-3">
            <div class="card h-100 {card_class}">
                {popular_badge}
                <div class="card-header text-center bg-light">
                    <h6 class="mb-1">{name}</h6>
                    {f'<small class="text-decoration-line-through text-muted">{original_price}</small><br>' if original_price else ''}
                    <span class="h5 text-primary">{price}</span>
                </div>
                <div class="card-body">
                    <ul class="list-unstyled">
                        {features_html}
                    </ul>
                    <div class="text-center mt-3">
                        <button class="btn btn-{cta_variant} w-100">{cta_text}</button>
                    </div>
                </div>
            </div>
        </div>
        '''

    html = f'''
    <div class="comparison-section mb-3">
        <h5 class="text-center mb-4">{title}</h5>
        <div class="row">
            {plans_html}
        </div>
    </div>
    '''
    return html

def render_ad_achievement(content):
    """Renderiza una sección de logros"""
    title = content.get('title', '')
    badges = content.get('badges', [])
    progress = content.get('progress', {})

    badges_html = ''
    for badge in badges:
        icon = badge.get('icon', '⭐')
        title_badge = badge.get('title', '')
        description = badge.get('description', '')
        badges_html += f'''
        <div class="col-md-6 mb-3">
            <div class="card text-center h-100">
                <div class="card-body">
                    <div class="fs-1 mb-2">{icon}</div>
                    <h6 class="card-title">{title_badge}</h6>
                    <p class="card-text small text-muted">{description}</p>
                </div>
            </div>
        </div>
        '''

    current = progress.get('current', 3)
    total = progress.get('total', 12)
    message = progress.get('message', '')

    percentage = int((current / total) * 100) if total > 0 else 0

    html = f'''
    <div class="achievement-section mb-3">
        <h5 class="text-center mb-4">{title}</h5>
        <div class="row">
            {badges_html}
        </div>
        <div class="progress-section text-center">
            <div class="progress mb-2" style="height: 20px;">
                <div class="progress-bar bg-success" role="progressbar" style="width: {percentage}%"></div>
            </div>
            <p class="text-muted small">{message}</p>
        </div>
    </div>
    '''
    return html