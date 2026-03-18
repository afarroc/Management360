import json
import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def render_content_block(block):
    if not isinstance(block, dict):
        if isinstance(block, str):
            try:
                block = json.loads(block)
            except (json.JSONDecodeError, TypeError):
                return mark_safe(f'<pre><code>{escape(str(block))}</code></pre>')
        else:
            return mark_safe('')

    block_type = block.get('type', '')

    if block_type == 'content_block':
        return mark_safe(_render_content_block(block))

    if block_type.startswith('ad_'):
        return mark_safe(_render_ad_component(block_type, block.get('content', {})))

    if isinstance(block, list):
        parts = []
        for component in block:
            if isinstance(component, dict) and 'type' in component:
                ctype = component.get('type', '')
                parts.append(_render_ad_component(ctype, component.get('content', {})))
        return mark_safe(''.join(parts))

    return mark_safe(
        f'<pre><code class="language-json">'
        f'{escape(json.dumps(block, indent=2, ensure_ascii=False))}'
        f'</code></pre>'
    )


def _render_content_block(block):
    content_type = block.get('content_type', 'html')
    title        = escape(block.get('title', ''))
    raw_content  = block.get('content', '')
    title_html   = f'<h5 class="content-block-title">{title}</h5>' if title else ''

    if content_type in ('html', 'bootstrap'):
        css = f'content-block-{content_type}'
        return f'<div class="content-block {css}">{title_html}{raw_content}</div>'

    elif content_type == 'text':
        return f'<div class="content-block content-block-text">{title_html}<p>{escape(raw_content)}</p></div>'

    elif content_type == 'markdown':
        content = escape(raw_content)
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'\*(.*?)\*',     r'<em>\1</em>',         content)
        content = re.sub(r'`(.*?)`',       r'<code>\1</code>',     content)
        content = content.replace('\n', '<br>')
        return f'<div class="content-block content-block-markdown">{title_html}{content}</div>'

    elif content_type == 'quote':
        content = escape(raw_content)
        return (
            f'<div class="content-block content-block-quote">'
            f'<blockquote class="blockquote"><p class="mb-0">{content}</p></blockquote>'
            f'<footer class="blockquote-footer">{title}</footer></div>'
        )

    elif content_type == 'code':
        return (
            f'<div class="content-block content-block-code">'
            f'{title_html}<pre><code>{escape(raw_content)}</code></pre></div>'
        )

    elif content_type == 'card':
        return (
            f'<div class="content-block content-block-card">'
            f'<div class="card"><div class="card-body">'
            f'<h5 class="card-title">{title}</h5>'
            f'<p class="card-text">{escape(raw_content)}</p>'
            f'</div></div></div>'
        )

    elif content_type == 'alert':
        return (
            f'<div class="content-block content-block-alert">'
            f'<div class="alert alert-info">{title_html}{escape(raw_content)}</div></div>'
        )

    elif content_type == 'json':
        if isinstance(raw_content, (dict, list)):
            formatted = json.dumps(raw_content, indent=2, ensure_ascii=False)
        else:
            try:
                formatted = json.dumps(json.loads(raw_content), indent=2, ensure_ascii=False)
            except (json.JSONDecodeError, TypeError):
                formatted = str(raw_content)
        return (
            f'<div class="content-block content-block-json">'
            f'{title_html}<pre><code class="language-json">{escape(formatted)}</code></pre></div>'
        )

    else:
        content = escape(raw_content) if isinstance(raw_content, str) else ''
        return f'<div class="content-block content-block-default">{title_html}{content}</div>'


def _render_ad_component(component_type, content):
    dispatch = {
        'ad_banner':      _render_ad_banner,
        'ad_card':        _render_ad_card,
        'ad_alert':       _render_ad_alert,
        'ad_testimonial': _render_ad_testimonial,
        'ad_countdown':   _render_ad_countdown,
        'ad_feature':     _render_ad_feature,
        'ad_comparison':  _render_ad_comparison,
        'ad_achievement': _render_ad_achievement,
    }
    handler = dispatch.get(component_type)
    if handler:
        return handler(content)
    return f'<div class="alert alert-secondary">Componente desconocido: {escape(component_type)}</div>'


def _render_ad_banner(content):
    header        = escape(content.get('header', ''))
    subheader     = escape(content.get('subheader', ''))
    features      = content.get('features', [])
    offer         = escape(content.get('offer', ''))
    price         = content.get('price', {})
    cta           = content.get('cta', {})
    secondary_cta = content.get('secondary_cta', {})

    features_html = ''.join(
        f'<li class="mb-1"><i class="bi bi-check-circle me-2"></i>{escape(f)}</li>'
        for f in features
    )
    html = (
        f'<div class="ad-banner bg-primary text-white p-4 rounded mb-3">'
        f'<h4 class="mb-2">{header}</h4><p class="mb-3">{subheader}</p>'
        f'<ul class="list-unstyled mb-3">{features_html}</ul>'
    )
    if offer:
        html += f'<div class="alert alert-light text-dark mb-3"><strong>{offer}</strong></div>'
    if price:
        html += (
            f'<div class="d-flex align-items-center mb-3">'
            f'<span class="text-decoration-line-through me-2">{escape(price.get("original",""))}</span>'
            f'<span class="h5 text-warning me-2">{escape(price.get("discounted",""))}</span>'
            f'<small class="text-light">{escape(price.get("period",""))}</small></div>'
        )
    if cta:
        html += f'<a href="{escape(cta.get("url","#"))}" class="btn btn-{escape(cta.get("color","success"))} me-2">{escape(cta.get("text",""))}</a>'
    if secondary_cta:
        html += f'<a href="{escape(secondary_cta.get("url","#"))}" class="btn btn-outline-light">{escape(secondary_cta.get("text",""))}</a>'
    html += '</div>'
    return html


def _render_ad_card(content):
    header      = escape(content.get('header', ''))
    description = escape(content.get('description', ''))
    highlights  = content.get('highlights', [])
    price       = escape(content.get('price', ''))
    badge       = escape(content.get('badge', ''))
    cta         = content.get('cta', {})

    highlights_html = ''.join(
        f'<li class="list-group-item"><i class="bi bi-star me-2 text-warning"></i>{escape(h)}</li>'
        for h in highlights
    )
    html = (
        f'<div class="card ad-card mb-3">'
        f'<div class="card-header text-center"><span class="badge bg-warning">{badge}</span></div>'
        f'<div class="card-body"><h5 class="card-title">{header}</h5>'
        f'<p class="card-text">{description}</p>'
        f'<ul class="list-group list-group-flush mb-3">{highlights_html}</ul>'
        f'<div class="text-center mb-3"><h4 class="text-primary">{price}</h4></div>'
    )
    if cta:
        html += f'<div class="text-center"><a href="{escape(cta.get("url","#"))}" class="btn btn-primary">{escape(cta.get("text",""))}</a></div>'
    html += '</div></div>'
    return html


def _render_ad_alert(content):
    icon     = escape(content.get('icon', '👥'))
    title    = escape(content.get('title', ''))
    message  = escape(content.get('message', ''))
    features = content.get('features', [])
    cta      = content.get('cta', {})

    features_html = ''.join(f'<li>{escape(f)}</li>' for f in features)
    html = (
        f'<div class="alert alert-info ad-alert mb-3"><div class="d-flex">'
        f'<div class="me-3 fs-4">{icon}</div><div class="flex-grow-1">'
        f'<h6 class="alert-heading mb-2">{title}</h6>'
        f'<p class="mb-2">{message}</p><ul class="mb-2">{features_html}</ul>'
    )
    if cta:
        html += f'<a href="{escape(cta.get("url","#"))}" class="btn btn-sm btn-primary">{escape(cta.get("text",""))}</a>'
    html += '</div></div></div>'
    return html


def _render_ad_testimonial(content):
    quote         = escape(content.get('quote', ''))
    author        = content.get('author', {})
    achievement   = escape(content.get('achievement', ''))
    author_name   = escape(author.get('name', ''))
    author_role   = escape(author.get('role', ''))
    author_avatar = escape(author.get('avatar', ''))
    stars         = '<i class="bi bi-star-fill text-warning"></i>' * int(author.get('rating', 5))

    return (
        f'<div class="testimonial-card bg-light p-4 rounded mb-3"><div class="text-center">'
        f'<blockquote class="blockquote mb-3"><p class="mb-0">{quote}</p></blockquote>'
        f'<img src="{author_avatar}" alt="{author_name}" class="rounded-circle mb-2" style="width:60px;height:60px;">'
        f'<h6 class="mb-1">{author_name}</h6><p class="text-muted small mb-2">{author_role}</p>'
        f'<div class="mb-2">{stars}</div><div class="badge bg-success">{achievement}</div>'
        f'</div></div>'
    )


def _render_ad_countdown(content):
    title         = escape(content.get('title', ''))
    message       = escape(content.get('message', ''))
    countdown     = content.get('countdown', {})
    offer_details = content.get('offer_details', [])
    cta           = content.get('cta', {})
    details_html  = ''.join(f'<li><i class="bi bi-check-circle me-2"></i>{escape(d)}</li>' for d in offer_details)

    html = (
        f'<div class="countdown-banner bg-danger text-white p-4 rounded mb-3 text-center">'
        f'<h5 class="mb-2">{title}</h5><p class="mb-3">{message}</p>'
        f'<div class="countdown-timer mb-3">'
        f'<span class="h3">{int(countdown.get("days",2))}d </span>'
        f'<span class="h3">{int(countdown.get("hours",12))}h </span>'
        f'<span class="h3">{int(countdown.get("minutes",30))}m</span></div>'
        f'<ul class="list-unstyled mb-3">{details_html}</ul>'
    )
    if cta:
        html += f'<a href="{escape(cta.get("url","#"))}" class="btn btn-light btn-lg">{escape(cta.get("text",""))}</a>'
    html += '</div>'
    return html


def _render_ad_feature(content):
    title    = escape(content.get('title', ''))
    features = content.get('features', [])
    cta      = content.get('cta', {})

    features_html = ''.join(
        f'<div class="col-md-6 mb-3"><div class="d-flex">'
        f'<div class="me-3 fs-2">{escape(f.get("icon","🔧"))}</div><div>'
        f'<h6 class="mb-1">{escape(f.get("title",""))}</h6>'
        f'<p class="text-muted small mb-0">{escape(f.get("description",""))}</p>'
        f'</div></div></div>'
        for f in features
    )
    html = f'<div class="feature-section mb-3"><h5 class="text-center mb-4">{title}</h5><div class="row">{features_html}</div>'
    if cta:
        html += f'<div class="text-center mt-3"><a href="{escape(cta.get("url","#"))}" class="btn btn-primary">{escape(cta.get("text",""))}</a></div>'
    html += '</div>'
    return html


def _render_ad_comparison(content):
    title = escape(content.get('title', ''))
    plans_html = ''
    for plan in content.get('plans', []):
        features_html = ''.join(
            f'<li class="mb-2"><i class="bi bi-check-circle text-success me-2"></i>{escape(f)}</li>'
            for f in plan.get('features', [])
        )
        popular       = plan.get('popular', False)
        original      = escape(plan.get('original_price', ''))
        original_html = f'<small class="text-decoration-line-through text-muted">{original}</small><br>' if original else ''
        cta           = plan.get('cta', {})

        plans_html += (
            f'<div class="col-lg-4 mb-3"><div class="card h-100 {"border-primary" if popular else ""}">'
            f'{"<div class=popular-badge>Más Popular</div>" if popular else ""}'
            f'<div class="card-header text-center bg-light">'
            f'<h6 class="mb-1">{escape(plan.get("name",""))}</h6>{original_html}'
            f'<span class="h5 text-primary">{escape(plan.get("price",""))}</span></div>'
            f'<div class="card-body"><ul class="list-unstyled">{features_html}</ul>'
            f'<div class="text-center mt-3"><button class="btn btn-{escape(cta.get("variant","outline-primary"))} w-100">{escape(cta.get("text",""))}</button></div>'
            f'</div></div></div>'
        )
    return f'<div class="comparison-section mb-3"><h5 class="text-center mb-4">{title}</h5><div class="row">{plans_html}</div></div>'


def _render_ad_achievement(content):
    title    = escape(content.get('title', ''))
    progress = content.get('progress', {})
    total    = int(progress.get('total', 1))
    current  = int(progress.get('current', 0))
    pct      = int((current / total) * 100) if total > 0 else 0

    badges_html = ''.join(
        f'<div class="col-md-6 mb-3"><div class="card text-center h-100"><div class="card-body">'
        f'<div class="fs-1 mb-2">{escape(b.get("icon","🏆"))}</div>'
        f'<h6 class="card-title">{escape(b.get("title",""))}</h6>'
        f'<p class="card-text small text-muted">{escape(b.get("description",""))}</p>'
        f'</div></div></div>'
        for b in content.get('badges', [])
    )
    return (
        f'<div class="achievement-section mb-3">'
        f'<h5 class="text-center mb-4">{title}</h5>'
        f'<div class="row">{badges_html}</div>'
        f'<div class="progress-section text-center">'
        f'<div class="progress mb-2" style="height:20px;">'
        f'<div class="progress-bar bg-success" role="progressbar" style="width:{pct}%"></div></div>'
        f'<p class="text-muted small">{escape(progress.get("message",""))}</p>'
        f'</div></div>'
    )
