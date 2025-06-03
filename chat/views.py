# chat/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import StreamingHttpResponse, JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.conf import settings
import asyncio
import json
import re
from .ollama_api import generate_response
from datetime import datetime
import csv


# Rate limiting function
def check_rate_limit(user_id, limit=5, period=60):
    cache_key = f'chat_rate_{user_id}'
    current = cache.get(cache_key, 0)
    if current >= limit:
        return False
    cache.set(cache_key, current + 1, period)
    return True


def moderate_message(content):
    # Lista básica de palabras prohibidas
    forbidden_words = ['badword1', 'badword2']
    for word in forbidden_words:
        if word in content.lower():
            return False
    return True


@login_required
@csrf_exempt
def chat_view(request):
    if request.method == "POST":
        try:
            if not check_rate_limit(request.user.id):
                return JsonResponse({"error": "Rate limit exceeded. Please wait a minute."}, status=429)

            # Get user input safely
            user_input = request.POST.get("user_input", "").strip()
            
            # Procesar comandos
            command_response = process_commands(user_input)
            if command_response:
                return JsonResponse({"command_response": command_response})
            
            # Moderación
            if not moderate_message(user_input):
                return JsonResponse({"error": "Message contains inappropriate content"}, status=400)
            
            chat_history = json.loads(request.POST.get("chat_history", "[]"))
            
            # Store chat history in cache
            cache_key = f'chat_history_{request.user.id}'
            cache.set(cache_key, chat_history, timeout=3600)  # 1 hour expiry

            # Validate and prepare message history
            messages = []
            for msg in chat_history:
                if not isinstance(msg, dict):
                    continue
                if msg.get('sender') == 'user':
                    messages.append({"role": "user", "content": str(msg.get('content', ''))})
                else:
                    messages.append({"role": "assistant", "content": str(msg.get('content', ''))})
            
            messages.append({"role": "user", "content": user_input})

            async def stream_generator():
                try:
                    async for chunk in generate_response(messages):
                        if not chunk or not isinstance(chunk, dict):
                            continue
                        content = chunk.get('message', {}).get('content', '')
                        if content:
                            # Replace newlines and escape special characters
                            yield f"data: {json.dumps({'content': content})}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                finally:
                    yield "data: [DONE]\n\n"

            response = StreamingHttpResponse(
                stream_generator(),
                content_type='text/event-stream'
            )
            response['Cache-Control'] = 'no-cache'
            response['X-Accel-Buffering'] = 'no'
            return response

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid chat history format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return render(request, "chat/assistant.html", {
        "pagetitle": "Chat IA",
        "initial_history": json.dumps([])
    })


@login_required
@csrf_exempt
def clear_chat(request):
    if request.method == "POST":
        try:
            # Add any server-side cleanup logic here
            return JsonResponse({
                "status": "success",
                "message": "Chat cleared successfully"
            })
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    return JsonResponse({
        "status": "error",
        "message": "Method not allowed"
    }, status=405)


@login_required
def export_chat_history(request):
    try:
        chat_history = json.loads(request.POST.get("chat_history", "[]"))
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="chat_history_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Timestamp', 'Sender', 'Message'])
        
        for msg in chat_history:
            writer.writerow([
                msg.get('timestamp', ''),
                msg.get('sender', ''),
                msg.get('content', '')
            ])
        
        return response
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def index(request):
    return render(request, "chat/index.html", {
        'pagetitle': 'Chat Page',
    })


@login_required
def chatroom(request, room_name):
    if not room_name or not str(room_name).isdigit():
        messages.error(request, "Invalid room ID")
        return redirect('chat:index')
    
    # Add analytics
    cache_key = f'room_visits_{room_name}'
    cache.set(cache_key, cache.get(cache_key, 0) + 1)
    
    context = {
        "room_name": room_name,
        "pagetitle": f"Chat Room #{room_name}",
        "current_user": request.user.username,
        "user_id": request.user.id,
        "user_email": request.user.email,
        "user_full_name": f"{request.user.first_name} {request.user.last_name}".strip(),
        "user_date_joined": request.user.date_joined,
        "user_last_login": request.user.last_login,
        "timestamp": timezone.now().isoformat(),
        "is_moderator": request.user.is_staff,
        "is_superuser": request.user.is_superuser,
        "message_format": {
            "date_format": "H:i:s a",
            "timezone": str(timezone.get_current_timezone()),
        },
        "room_stats": {
            "visits": cache.get(f'room_visits_{room_name}', 0),
            "created_at": timezone.now(),
            "last_activity": timezone.now(),
        },
        "chat_settings": {
            "max_length": 1000,
            "rate_limit": 5,
            "rate_period": 60,
        },
        "room_features": {
            "attachments_enabled": True,
            "max_file_size": 5 * 1024 * 1024,
            "allowed_file_types": ['.txt', '.pdf', '.png', '.jpg', '.jpeg'],
            "commands_enabled": True,
            "moderation_enabled": True,
            "search_enabled": True,
        },
        "notifications": {
            "enabled": True,
            "sound_enabled": True,
            "desktop_enabled": True,
        }
    }
    
    return render(request, "chat/room.html", context)


@login_required
@csrf_exempt
def search_history(request):
    query = request.GET.get('q', '').strip()
    chat_history = cache.get(f'chat_history_{request.user.id}', [])
    
    results = [
        msg for msg in chat_history 
        if query.lower() in msg.get('content', '').lower()
    ]
    
    return JsonResponse({"results": results})


@login_required
@csrf_exempt
def upload_attachment(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        # Validar tipo de archivo y tamaño
        if file.size > 5 * 1024 * 1024:  # 5MB limit
            return JsonResponse({"error": "File too large"}, status=400)
            
        allowed_types = ['.txt', '.pdf', '.png', '.jpg', '.jpeg']
        if not any(file.name.lower().endswith(ext) for ext in allowed_types):
            return JsonResponse({"error": "Invalid file type"}, status=400)
            
        # Guardar archivo
        path = default_storage.save(f'chat_attachments/{request.user.id}/{file.name}', file)
        return JsonResponse({"url": default_storage.url(path)})
        
    return JsonResponse({"error": "No file provided"}, status=400)


def process_commands(message):
    commands = {
        '/help': lambda: "Available commands: /help, /clear, /export",
        '/clear': lambda: "Clearing chat history...",
        '/export': lambda: "Exporting chat history..."
    }
    
    if message.startswith('/'):
        command = message.split()[0]
        if command in commands:
            return commands[command]()
    return None