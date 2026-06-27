import base64
import json
import re

from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from courses.models import ContentBlock


def _parse_basic_auth(request):
    auth = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth.startswith('Basic '):
        return None
    try:
        encoded = auth.split(' ', 1)[1]
        decoded = base64.b64decode(encoded).decode('utf-8')
        username, password = decoded.split(':', 1)
    except Exception:
        return None
    return username, password


def basic_auth_required(view_func):
    def _wrapped(request, *args, **kwargs):
        credentials = _parse_basic_auth(request)
        if not credentials:
            response = JsonResponse({'detail': 'Authentication credentials were not provided.'}, status=401)
            response['WWW-Authenticate'] = 'Basic realm="api"'
            return response
        username, password = credentials
        user = authenticate(request, username=username, password=password)
        if user is None:
            response = JsonResponse({'detail': 'Invalid username/password.'}, status=401)
            response['WWW-Authenticate'] = 'Basic realm="api"'
            return response
        request.user = user
        return view_func(request, *args, **kwargs)
    return _wrapped


def _build_slug(title: str) -> str:
    base = re.sub(r'[^a-zA-Z0-9]+', '-', title.strip().lower()).strip('-') or 'contenido'
    return base[:80]


@csrf_exempt
@require_POST
@basic_auth_required
def publish_content(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'Cuerpo JSON inválido.'}, status=400)

    title = (payload.get('title') or '').strip()
    body = payload.get('body') or ''
    description = (payload.get('description') or '').strip()
    content_type = payload.get('content_type', 'html')
    category = (payload.get('category') or '').strip()
    tags = (payload.get('tags') or '').strip()
    is_public = bool(payload.get('is_public', True))
    is_featured = bool(payload.get('is_featured', False))
    if content_type not in dict(ContentBlock.CONTENT_TYPES):
        content_type = 'html'

    if not title:
        return JsonResponse({'detail': 'El campo "title" es obligatorio.'}, status=400)

    block = ContentBlock(
        title=title,
        description=description,
        content_type=content_type,
        author=request.user,
        category=category,
        tags=tags,
        is_public=is_public,
        is_featured=is_featured,
        slug=_build_slug(title),
    )
    if content_type == 'markdown':
        block.markdown_content = body
    elif content_type == 'json':
        block.json_content = body
    else:
        block.html_content = body
    block.save()

    public_url = '/courses/content/public/'
    return JsonResponse({
        'id': str(block.pk),
        'title': block.title,
        'slug': block.slug,
        'url': public_url,
        'is_public': block.is_public,
        'created_at': block.created_at.isoformat(),
    }, status=201)
