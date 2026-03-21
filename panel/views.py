import json
import jwt
import time
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import IntegrityError
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST
import redis

User = get_user_model()


# ---------------------------------------------------------------------------
# API Views — autenticación JSON
# ---------------------------------------------------------------------------

def get_csrf(request):
    return JsonResponse({}, headers={'X-CSRFToken': get_token(request)})


@login_required
def get_connection_token(request):
    """JWT de conexión para Centrifugo. Expira en 120 s."""
    token_claims = {
        'sub': str(request.user.pk),
        'exp': int(time.time()) + 120,
        'iat': int(time.time()),
    }
    token = jwt.encode(token_claims, settings.CENTRIFUGO_TOKEN_SECRET)
    return JsonResponse({'token': token})


@login_required
def get_subscription_token(request):
    """JWT de suscripción al canal personal del usuario. Expira en 300 s."""
    channel = request.GET.get('channel')
    if channel != f'personal:{request.user.pk}':
        return JsonResponse({'detail': 'permission denied'}, status=403)

    token_claims = {
        'sub': str(request.user.pk),
        'exp': int(time.time()) + 300,
        'channel': channel,
    }
    token = jwt.encode(token_claims, settings.CENTRIFUGO_TOKEN_SECRET)
    return JsonResponse({'token': token})


@require_POST
def login_view(request):
    try:
        credentials = json.loads(request.body)
        username = credentials.get('username')
        password = credentials.get('password')

        if not username or not password:
            return JsonResponse({'detail': 'provide username and password'}, status=400)

        user = authenticate(username=username, password=password)
        if not user:
            return JsonResponse({'detail': 'invalid credentials'}, status=400)

        login(request, user)
        return JsonResponse({'user': {'id': user.pk, 'username': user.username}})
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'invalid JSON'}, status=400)


@require_POST
def logout_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'must be authenticated'}, status=403)
    logout(request)
    return JsonResponse({})


# ---------------------------------------------------------------------------
# Web Views
# ---------------------------------------------------------------------------

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                return redirect('index')
            except IntegrityError:
                error = "User already exists"
        else:
            error = "Passwords don't match" if 'password1' in form.errors else "Invalid form"

        return render(request, 'accounts/signup.html', {'form': form, 'error': error})

    return render(request, 'accounts/signup.html', {'form': UserCreationForm()})


# ---------------------------------------------------------------------------
# Diagnóstico — solo staff/autenticados
# ---------------------------------------------------------------------------

@method_decorator(login_required, name='dispatch')
class RedisTestView(View):
    """Diagnóstico de conexión Redis. Requiere autenticación."""
    def get(self, request):
        try:
            r = redis.StrictRedis.from_url(settings.REDIS_URL)
            r.set('test_key', 'redis_ok', ex=10)
            value = r.get('test_key')
            return JsonResponse({'status': 'success', 'value': value.decode() if value else None})
        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)})
