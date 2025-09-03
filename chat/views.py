from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.http import StreamingHttpResponse, JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.conf import settings
import asyncio
import json
import re
from .ollama_api import generate_response
from rooms.models import Room, Message
from datetime import datetime
import csv

# Redirección automática a la sala por defecto
@login_required
def redirect_to_last_room(request):
    last_message = Message.objects.filter(user=request.user).order_by('-created_at').first()
    if last_message:
        room_name = str(last_message.room.id)
    else:
        room_name = 'global'
    return redirect('chat:room', room_name=room_name)

@login_required
def last_room_api(request):
    user = request.user
    last_message = Message.objects.filter(user=user).order_by('-created_at').first()
    if last_message:
        return JsonResponse({'room_name': str(last_message.room.id)})
    # Si no hay historial, usar 'global'
    return JsonResponse({'room_name': 'global'})
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
# Borra el historial de mensajes de una sala
@login_required
@require_POST
def clear_history_room(request, room_name):
    from rooms.models import Room, Message
    try:
        room = Room.objects.get(id=room_name)
        Message.objects.filter(room=room).delete()
        # Broadcast to all clients in the room
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        group_name = f"chat_{room_name}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'history_cleared',
            }
        )
        return JsonResponse({'success': True})
    except Room.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Room not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
class AIResponseError(Exception):
    """Excepción personalizada para errores en la respuesta de la IA."""
    pass
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
from rooms.models import Room, Message
from datetime import datetime

import csv
from rooms.models import Room, Message


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
    if request.method == "GET":
        return JsonResponse({"status": "ok", "message": "Chat API disponible. Usa POST para interactuar."})
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
            user_full_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
            messages = []
            for msg in chat_history:
                if not isinstance(msg, dict):
                    continue
                role = msg.get('role') or msg.get('sender')
                if role == 'user':
                    messages.append({
                        "role": "user",
                        "content": str(msg.get('content', '')),
                        "sender_name": msg.get('sender_name', user_full_name)
                    })
                elif role == 'assistant':
                    messages.append({
                        "role": "assistant",
                        "content": str(msg.get('content', '')),
                        "sender_name": msg.get('sender_name', 'Asistente')
                    })

            # Validar que haya mensaje del usuario
            if not user_input and not messages:
                return JsonResponse({"error": "No se recibió mensaje del usuario ni historial."}, status=400)

            # Añadir el mensaje actual del usuario solo si no está ya como último mensaje
            if user_input and not (messages and messages[-1]["role"] == "user" and messages[-1]["content"] == user_input):
                messages.append({
                    "role": "user",
                    "content": user_input,
                    "sender_name": user_full_name
                })


            async def stream_generator():
                try:
                    async for chunk in generate_response(messages):
                        if not chunk or not isinstance(chunk, dict):
                            continue
                        if 'error' in chunk:
                            raise AIResponseError(chunk['error'])
                        content = chunk.get('message', {}).get('content', '')
                        if content:
                            # Replace newlines and escape special characters
                            yield f"data: {json.dumps({'content': content})}\n\n"
                            await asyncio.sleep(0)  # Forzar flush inmediato del chunk
                except AIResponseError as ai_err:
                    yield f"data: {json.dumps({'error': f'AIResponseError: {str(ai_err)}'})}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'error': f'InternalError: {str(e)}'})}\n\n"
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

    # Si no es GET ni POST, devolver JSON de error
    return JsonResponse({"error": "Método no permitido. Usa POST para interactuar con el chat."}, status=405)


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


@login_required
def room_list(request):
    context = {
        'pagetitle': 'Chat Rooms',
        'rooms': range(1, 5),  # Demo rooms 1-4
        'user_full_name': f"{request.user.first_name} {request.user.last_name}",
        'user_email': request.user.email,
        'user_id': request.user.id,
        'user_date_joined': request.user.date_joined,
    }
    return render(request, 'chat/room_list.html', context)


@login_required
def room(request, room_name):
    user_full_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
    # Buscar la sala por nombre o id
    try:
        room_obj = Room.objects.get(id=room_name)
    except Room.DoesNotExist:
        messages.error(request, "Room not found")
        return redirect('chat:room_list')

    # Obtener historial de mensajes (últimos 50)
    color_palette = [
        "#007bff", "#28a745", "#dc3545", "#fd7e14", "#6610f2",
        "#20c997", "#6f42c1", "#e83e8c", "#17a2b8", "#ffc107", "#343a40"
    ]
    chat_history = Message.objects.filter(room=room_obj).select_related('user').order_by('created_at')[:50]
    history = []
    for msg in chat_history:
        user_id = msg.user.id if msg.user else 0
        color = color_palette[user_id % len(color_palette)]
        if msg.user:
            display_name = f"{msg.user.first_name} {msg.user.last_name}".strip()
            if not display_name:
                display_name = msg.user.username
        else:
            display_name = f"User #{user_id}" if user_id else "Usuario"
        history.append({
            'user_id': user_id,
            'display_name': display_name,
            'content': msg.content,
            'timestamp': msg.created_at,
            'color': color,
        })

    context = {
        'pagetitle': f'Chat Room: {room_obj.name}',
        'room_name': room_obj.id,
        'current_user': request.user.username,
        'user_full_name': user_full_name,
        'user_email': request.user.email,
        'user_id': request.user.id,
        'user_date_joined': request.user.date_joined,
        'is_moderator': request.user.groups.filter(name='Moderators').exists(),
        'chat_history': history,
    }
    return render(request, 'chat/room.html', context)


@login_required
def assistant_view(request):
    context = {
        'pagetitle': 'AI Assistant',
        'user_full_name': f"{request.user.first_name} {request.user.last_name}",
        'user_email': request.user.email,
        'user_id': request.user.id,
        'user_date_joined': request.user.date_joined,
        'initial_history': [],
    }
    return render(request, 'chat/assistant.html', context)


@login_required
def clear_history(request):
    if request.method == 'POST':
        # Add chat clearing logic here
        messages.success(request, 'Chat history cleared successfully')
    return redirect('chat:room_list')