import json
import jwt
import time
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.http import require_POST
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import IntegrityError
from datetime import datetime, timedelta
from django.views import View
import redis

# API Views
def get_csrf(request):
    return JsonResponse({}, headers={'X-CSRFToken': get_token(request)})

def get_connection_token(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {'error': 'Authentication required'}, 
            status=401,
            headers={'WWW-Authenticate': 'Bearer'}
        )

    expiry = datetime.utcnow() + timedelta(seconds=120)
    token_claims = {
        'sub': str(request.user.pk),
        'exp': expiry.timestamp(),
        'iat': datetime.utcnow().timestamp()
    }

def get_subscription_token(request):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'unauthorized'}, status=401)

    channel = request.GET.get('channel')
    if channel != f'personal:{request.user.pk}':
        return JsonResponse({'detail': 'permission denied'}, status=403)

    token_claims = {
        'sub': str(request.user.pk),
        'exp': int(time.time()) + 300,
        'channel': channel
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
        return JsonResponse({
            'user': {
                'id': user.pk,
                'username': user.username
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'invalid JSON'}, status=400)

@require_POST
def logout_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'must be authenticated'}, status=403)

    logout(request)
    return JsonResponse({})

# Web Views
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
        
        return render(request, 'accounts/signup.html', {
            'form': form,
            'error': error
        })
    
    return render(request, 'accounts/signup.html', {
        'form': UserCreationForm()
    })

class RedisTestView(View):
    def get(self, request):
        try:
            r = redis.StrictRedis.from_url(settings.REDIS_URL)
            r.set('test_key', 'redis_ok', ex=10)
            value = r.get('test_key')
            return JsonResponse({'status': 'success', 'value': value.decode() if value else None})
        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)})