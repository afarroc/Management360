import json
import jwt
import time

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.http import require_POST
from django.conf import settings


def get_csrf(request):
    return JsonResponse({}, headers={'X-CSRFToken': get_token(request)})


def get_connection_token(request):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'unauthorized'}, status=401)

    token_claims = {
        'sub': str(request.user.pk),
        'exp': int(time.time()) + 120
    }
    token = jwt.encode(token_claims, settings.CENTRIFUGO_TOKEN_SECRET)

    return JsonResponse({'token': token})


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


@require_POST
def logout_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'must be authenticated'}, status=403)

    logout(request)
    return JsonResponse({})

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction

def signup_view(request):
    if request.method == "GET":
        return render(request, 'accounts/signup.html', {
            'form': UserCreationForm
        })       
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(username=request.POST['username'], password=request.POST['password1'])
                user.save()
                login(request, user)
                return redirect('index')  
            except IntegrityError:
                return render(request, 'accounts/signup.html', {
                    'form': UserCreationForm,
                    "error": "User already exist"
                })       
        return render(request, 'accounts/signup.html', { 
            'form': UserCreationForm,
            "error": "Password do not match"
        })    
