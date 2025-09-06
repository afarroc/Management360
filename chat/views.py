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
from django.contrib.auth.models import User
import asyncio
import json
import re
from .ollama_api import generate_response
from rooms.models import Room, Message, MessageRead
from datetime import datetime
import csv

@login_required
@csrf_exempt
def mark_messages_read_api(request):
    """Marca como leídos los mensajes indicados por el usuario en una sala."""
    if request.method == 'POST':
        user = request.user
        data = json.loads(request.body)
        room_id = data.get('room_id')
        message_ids = data.get('message_ids', [])
        if not room_id or not message_ids:
            return JsonResponse({'error': 'room_id y message_ids requeridos'}, status=400)
        for msg_id in message_ids:
            MessageRead.objects.get_or_create(user=user, message_id=msg_id)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
@csrf_exempt
def unread_count_api(request):
    """Devuelve el número de mensajes no leídos por sala para el usuario actual."""
    user = request.user
    room_id = request.GET.get('room_id')
    if room_id:
        total_msgs = Message.objects.filter(room_id=room_id).count()
        read_msgs = MessageRead.objects.filter(user=user, message__room_id=room_id).count()
        unread = max(total_msgs - read_msgs, 0)
        return JsonResponse({'unread_count': unread})
    else:
        # Total unread across all rooms
        total_unread = 0
        rooms = Room.objects.all()
        for room in rooms:
            total_msgs = Message.objects.filter(room=room).count()
            read_msgs = MessageRead.objects.filter(user=user, message__room=room).count()
            total_unread += max(total_msgs - read_msgs, 0)
        return JsonResponse({'unread_count': total_unread})


@login_required
@csrf_exempt
def reset_unread_count_api(request):
    """Resetea el contador de mensajes no leídos para una sala específica o todas las salas."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        user = request.user
        data = json.loads(request.body)
        room_id = data.get('room_id')

        if room_id:
            # Reset for specific room
            unread_messages = Message.objects.filter(
                room_id=room_id
            ).exclude(
                id__in=MessageRead.objects.filter(
                    user=user,
                    message__room_id=room_id
                ).values_list('message_id', flat=True)
            )
        else:
            # Reset for all rooms
            unread_messages = Message.objects.filter(
                room__members__user=user,
                room__members__is_active=True
            ).exclude(
                id__in=MessageRead.objects.filter(
                    user=user
                ).values_list('message_id', flat=True)
            ).distinct()

        # Mark all unread messages as read
        message_reads = []
        for message in unread_messages:
            message_reads.append(MessageRead(user=user, message=message))

        if message_reads:
            MessageRead.objects.bulk_create(message_reads)

        return JsonResponse({
            'success': True,
            'marked_read': len(message_reads),
            'message': f'Marked {len(message_reads)} messages as read'
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
def mark_notifications_read_api(request):
    """API to mark specific notifications as read"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        from .models import HardcodedNotificationManager

        data = json.loads(request.body)
        notification_ids = data.get('notification_ids', [])

        # If notification_ids is empty, mark all notifications as read
        if not notification_ids:
            count = HardcodedNotificationManager.mark_notifications_read(request.user, None)
        else:
            count = HardcodedNotificationManager.mark_notifications_read(request.user, notification_ids)

        return JsonResponse({
            'success': True,
            'marked_read': count,
            'message': f'Marked {count} notifications as read'
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error in mark_notifications_read_api for user {request.user.username}: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@login_required
@csrf_exempt
def room_history_api(request, room_id):
    """Devuelve el historial de mensajes de una sala en formato JSON."""
    try:
        room = Room.objects.get(id=room_id)
        chat_history = Message.objects.filter(room=room).select_related('user').order_by('created_at')[:50]
        history = []
        for msg in chat_history:
            user_id = msg.user.id if msg.user else 0
            display_name = f"{msg.user.first_name} {msg.user.last_name}".strip() if msg.user else f"User #{user_id}" if user_id else "Usuario"
            history.append({
                'user_id': user_id,
                'display_name': display_name,
                'content': msg.content,
                'timestamp': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })
        return JsonResponse({'history': history})
    except Room.DoesNotExist:
        return JsonResponse({'error': 'Room not found'}, status=404)

@login_required
@csrf_exempt
def room_list_api(request):
    """Devuelve la lista de salas disponibles en formato JSON."""
    rooms = Room.objects.all().order_by('name')
    rooms_data = [
        {'id': room.id, 'name': room.name}
        for room in rooms
    ]
    return JsonResponse({'rooms': rooms_data})

# All imports are at the top of the file

# Panel flotante para incluir en cualquier página
@login_required
@csrf_exempt
def chat_panel(request):
    rooms = Room.objects.all().order_by('name')
    context = {
        'rooms': rooms,
        'user_full_name': f"{request.user.first_name} {request.user.last_name}",
        'user_email': request.user.email,
        'user_id': request.user.id,
        'user_date_joined': request.user.date_joined,
    }
    return render(request, 'chat/panel.html', context)

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
# Borra el historial de mensajes de una sala
@login_required
@require_POST
def clear_history_room(request, room_name):
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
    
    rooms = Room.objects.all().order_by('name')
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
        },
        "rooms": rooms
    }
    
    return render(request, "chat/room.html", context)


@login_required
@csrf_exempt
def search_history(request):
    query = request.GET.get('q', '').strip()
    room_id = request.GET.get('room_id')
    user_filter = request.GET.get('user')
    date_filter = request.GET.get('date')

    if not query:
        return JsonResponse({"results": [], "total": 0})

    # Build queryset
    from rooms.models import Message
    messages = Message.objects.select_related('user').order_by('-created_at')

    if room_id:
        messages = messages.filter(room_id=room_id)

    # Apply user filter
    if user_filter:
        messages = messages.filter(user__username__icontains=user_filter)

    # Apply date filter
    if date_filter:
        from datetime import datetime, timedelta
        now = datetime.now()

        if date_filter == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_filter == 'week':
            start_date = now - timedelta(days=7)
        elif date_filter == 'month':
            start_date = now - timedelta(days=30)
        else:
            start_date = None

        if start_date:
            messages = messages.filter(created_at__gte=start_date)

    # Apply content search
    messages = messages.filter(content__icontains=query)[:50]  # Limit results

    # Format results
    results = []
    for msg in messages:
        results.append({
            'id': msg.id,
            'content': msg.content,
            'user': msg.user.username if msg.user else 'Unknown',
            'display_name': f"{msg.user.first_name} {msg.user.last_name}".strip() if msg.user else 'Unknown',
            'timestamp': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'room_id': msg.room.id if msg.room else None,
            'room_name': msg.room.name if msg.room else 'Unknown'
        })

    return JsonResponse({
        "results": results,
        "total": len(results),
        "query": query
    })


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
    from rooms.models import Room
    rooms = Room.objects.all().order_by('name')
    context = {
        'pagetitle': 'Chat Rooms',
        'rooms': rooms,
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

    from rooms.models import Room as RoomModel
    all_rooms = RoomModel.objects.all().order_by('name')
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
        'rooms': all_rooms,
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

@login_required
@csrf_exempt
def add_reaction(request, message_id):
    """Add or remove a reaction to a message"""
    if request.method == 'POST':
        try:
            from rooms.models import Message
            from .models import MessageReaction

            data = json.loads(request.body)
            emoji = data.get('emoji')

            if not emoji:
                return JsonResponse({'error': 'Emoji is required'}, status=400)

            try:
                message = Message.objects.get(id=message_id)
            except Message.DoesNotExist:
                return JsonResponse({'error': 'Message not found'}, status=404)

            # Check if reaction already exists
            reaction, created = MessageReaction.objects.get_or_create(
                message=message,
                user=request.user,
                emoji=emoji
            )

            if not created:
                # Remove reaction if it already exists
                reaction.delete()
                action = 'removed'
            else:
                action = 'added'

            return JsonResponse({
                'success': True,
                'action': action,
                'emoji': emoji,
                'message_id': message_id
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    @login_required
    def unread_notifications_api(request):
        """API endpoint for unread notifications"""
        if request.method == 'GET':
            from .models import HardcodedNotificationManager
            notification_manager = HardcodedNotificationManager()
            data = notification_manager.get_notifications_data(request.user)
            return JsonResponse(data)
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    @login_required
    def room_members_api(request, room_id):
        """API endpoint for room members"""
        try:
            from rooms.models import RoomMember, Room
            room = Room.objects.get(id=room_id)
    
            # Check if user has access to this room
            if not RoomMember.objects.filter(room=room, user=request.user).exists():
                return JsonResponse({'error': 'Access denied'}, status=403)
    
            members = RoomMember.objects.filter(room=room).select_related('user')
            members_data = []
    
            for member in members:
                members_data.append({
                    'id': member.user.id,
                    'username': member.user.username,
                    'display_name': f"{member.user.first_name} {member.user.last_name}".strip() or member.user.username,
                    'email': member.user.email,
                    'is_online': True,  # You can implement presence logic here
                    'joined_at': member.joined_at.isoformat() if member.joined_at else None
                })
    
            return JsonResponse({
                'members': members_data,
                'total': len(members_data)
            })
    
        except Room.DoesNotExist:
            return JsonResponse({'error': 'Room not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    @login_required
    def room_notifications_api(request, room_id):
        """API endpoint for room notifications"""
        try:
            from rooms.models import Room
            from .models import HardcodedNotificationManager
    
            room = Room.objects.get(id=room_id)
    
            # Check if user has access to this room
            from rooms.models import RoomMember
            if not RoomMember.objects.filter(room=room, user=request.user).exists():
                return JsonResponse({'error': 'Access denied'}, status=403)
    
            # Get notifications for this room
            notification_manager = HardcodedNotificationManager()
            all_notifications = notification_manager.get_all_notifications(request.user, include_read=True)
    
            room_notifications = [
                n for n in all_notifications
                if n.get('room_id') == str(room_id)
            ]
    
            return JsonResponse({
                'notifications': room_notifications,
                'total': len(room_notifications)
            })
    
        except Room.DoesNotExist:
            return JsonResponse({'error': 'Room not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    @login_required
    def room_admin(request, room_id):
        """Room administration panel"""
        try:
            from rooms.models import Room, RoomMember
            room = Room.objects.get(id=room_id)
    
            # Check if user is admin or owner
            if not (room.administrators.filter(id=request.user.id).exists() or room.owner_id == request.user.id):
                messages.error(request, 'Access denied')
                return redirect('chat:room_list')
    
            members = RoomMember.objects.filter(room=room).select_related('user')
    
            context = {
                'room': room,
                'members': members,
                'pagetitle': f'Admin - {room.name}'
            }
    
            return render(request, 'chat/room_admin.html', context)
    
        except Room.DoesNotExist:
            messages.error(request, 'Room not found')
            return redirect('chat:room_list')
    
    @login_required
    @csrf_exempt
    def reset_unread_count_api(request):
        """API endpoint to reset unread message count for a room"""
        if request.method == 'POST':
            try:
                import json
                from rooms.models import MessageRead, Message
    
                data = json.loads(request.body)
                room_id = data.get('room_id')
    
                if not room_id:
                    return JsonResponse({'error': 'room_id is required'}, status=400)
    
                # Mark all unread messages in this room as read for the current user
                unread_messages = Message.objects.filter(
                    room_id=room_id
                ).exclude(
                    messageread__user=request.user
                )
    
                marked_count = 0
                for message in unread_messages:
                    MessageRead.objects.get_or_create(
                        user=request.user,
                        message=message
                    )
                    marked_count += 1
    
                return JsonResponse({
                    'success': True,
                    'marked_read': marked_count
                })
    
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
    
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    @login_required
    @csrf_exempt
    def mark_notifications_read_api(request):
        """API endpoint to mark notifications as read"""
        if request.method == 'POST':
            try:
                from .models import HardcodedNotificationManager
                import json
    
                data = json.loads(request.body)
                notification_ids = data.get('notification_ids', [])
    
                notification_manager = HardcodedNotificationManager()
                marked_count = notification_manager.mark_notifications_read(request.user, notification_ids)
    
                return JsonResponse({
                    'success': True,
                    'marked_count': marked_count
                })
    
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
    
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
@csrf_exempt
def search_messages(request):
    """Search messages with filters"""
    if request.method == 'GET':
        query = request.GET.get('q', '').strip()
        user_filter = request.GET.get('user', '').strip()
        date_filter = request.GET.get('date', '').strip()
        room_id = request.GET.get('room_id', '').strip()

        from rooms.models import Message, Room
        from django.db.models import Q

        # Base queryset
        messages = Message.objects.select_related('user', 'room').order_by('-created_at')

        # Apply filters
        if query:
            messages = messages.filter(
                Q(content__icontains=query)
            )

        if user_filter:
            messages = messages.filter(user__username__icontains=user_filter)

        if date_filter:
            from datetime import datetime, timedelta
            now = timezone.now()
            if date_filter == 'today':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                messages = messages.filter(created_at__gte=start_date)
            elif date_filter == 'week':
                start_date = now - timedelta(days=7)
                messages = messages.filter(created_at__gte=start_date)
            elif date_filter == 'month':
                start_date = now - timedelta(days=30)
                messages = messages.filter(created_at__gte=start_date)

        if room_id:
            messages = messages.filter(room_id=room_id)

        # Limit results
        messages = messages[:50]

        # Format results
        results = []
        for msg in messages:
            results.append({
                'id': msg.id,
                'content': msg.content,
                'user': msg.user.username,
                'display_name': f"{msg.user.first_name} {msg.user.last_name}".strip() or msg.user.username,
                'room_name': msg.room.name,
                'room_id': msg.room.id,
                'timestamp': msg.created_at.isoformat(),
                'time_display': msg.created_at.strftime('%H:%M %d/%m/%Y')
            })

        return JsonResponse({
            'results': results,
            'total': len(results),
            'query': query
        })

    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
@csrf_exempt
def update_presence(request):
    """Update user presence status"""
    if request.method == 'POST':
        try:
            from .models import UserPresence
            from rooms.models import Room

            data = json.loads(request.body)
            status = data.get('status', 'online')
            room_id = data.get('room_id')

            presence, created = UserPresence.objects.get_or_create(
                user=request.user,
                defaults={'status': status}
            )

            room = None
            if room_id:
                try:
                    room = Room.objects.get(id=room_id)
                except Room.DoesNotExist:
                    pass

            presence.update_presence(status, room)

            return JsonResponse({
                'success': True,
                'status': status,
                'room_id': room_id
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def get_presence(request):
    """Get presence status for users in a room"""
    room_id = request.GET.get('room_id')
    if not room_id:
        return JsonResponse({'error': 'room_id is required'}, status=400)

    from .models import UserPresence
    from rooms.models import RoomMember

    try:
        # Get room members
        members = RoomMember.objects.filter(room_id=room_id).select_related('user')

        presence_data = []
        for member in members:
            try:
                presence = UserPresence.objects.get(user=member.user)
                if presence.is_online:
                    presence_data.append({
                        'user_id': member.user.id,
                        'username': member.user.username,
                        'display_name': f"{member.user.first_name} {member.user.last_name}".strip() or member.user.username,
                        'status': presence.status,
                        'last_seen': presence.last_seen.isoformat()
                    })
            except UserPresence.DoesNotExist:
                # User has no presence record, consider offline
                pass

        return JsonResponse({
            'presence': presence_data,
            'room_id': room_id
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
def room_members_api(request, room_id):
    """API for managing room members"""
    try:
        room = Room.objects.get(id=room_id)

        # Check if user can manage this room
        if not room.can_user_manage(request.user):
            return JsonResponse({'error': 'Permission denied'}, status=403)

        if request.method == 'GET':
            members = room.get_active_members().select_related('user')
            members_data = []
            for member in members:
                members_data.append({
                    'id': member.user.id,
                    'username': member.user.username,
                    'full_name': f"{member.user.first_name} {member.user.last_name}".strip(),
                    'role': member.role,
                    'joined_at': member.joined_at.isoformat(),
                    'last_seen': member.last_seen.isoformat(),
                    'is_online': room.get_online_members().filter(user=member.user).exists()
                })
            return JsonResponse({'members': members_data})

        elif request.method == 'POST':
            data = json.loads(request.body)
            action = data.get('action')
            user_id = data.get('user_id')

            if action == 'add_member':
                try:
                    user = User.objects.get(id=user_id)
                    role = data.get('role', 'member')
                    room.add_member(user, role, request.user)
                    return JsonResponse({'success': True, 'message': f'User {user.username} added to room'})
                except User.DoesNotExist:
                    return JsonResponse({'error': 'User not found'}, status=404)

            elif action == 'remove_member':
                try:
                    user = User.objects.get(id=user_id)
                    if room.remove_member(user, request.user):
                        return JsonResponse({'success': True, 'message': f'User {user.username} removed from room'})
                    else:
                        return JsonResponse({'error': 'User is not a member'}, status=400)
                except User.DoesNotExist:
                    return JsonResponse({'error': 'User not found'}, status=404)

            elif action == 'change_role':
                try:
                    user = User.objects.get(id=user_id)
                    new_role = data.get('role')
                    if new_role in ['member', 'moderator', 'admin']:
                        membership = RoomMember.objects.get(room=room, user=user)
                        membership.role = new_role
                        membership.save()
                        return JsonResponse({'success': True, 'message': f'Role updated for {user.username}'})
                    else:
                        return JsonResponse({'error': 'Invalid role'}, status=400)
                except (User.DoesNotExist, RoomMember.DoesNotExist):
                    return JsonResponse({'error': 'User not found in room'}, status=404)

    except Room.DoesNotExist:
        return JsonResponse({'error': 'Room not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
@csrf_exempt
def unread_notifications_api(request):
    """API to get all unread notifications for the current user with robust caching"""
    try:
        from .models import HardcodedNotificationManager

        # Use the robust hardcoded notification manager
        result = HardcodedNotificationManager.get_notifications_data(request.user, limit=20)

        # Add cache headers for better performance
        response = JsonResponse(result)
        response['Cache-Control'] = 'private, max-age=30'  # Cache for 30 seconds
        return response

    except Exception as e:
        logger.error(f"Error in unread_notifications_api for user {request.user.username}: {str(e)}")
        return JsonResponse({'error': 'Internal server error', 'notifications': []}, status=500)

@login_required
@csrf_exempt
def test_create_notification(request):
    """Test endpoint to create a notification manually"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        from .models import HardcodedNotificationManager
        from rooms.models import Room

        data = json.loads(request.body)
        message = data.get('message', 'Test notification')
        room_id = data.get('room_id', 1)

        # Get room
        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return JsonResponse({'error': 'Room not found'}, status=404)

        # Create test notification
        notification = HardcodedNotificationManager.create_chat_notification(
            user=request.user,
            room=room,
            message=message,
            sender=request.user  # Self-notification for testing
        )

        if notification:
            return JsonResponse({
                'success': True,
                'notification': notification,
                'message': 'Test notification created'
            })
        else:
            return JsonResponse({'error': 'Failed to create notification'}, status=500)

    except Exception as e:
        logger.error(f"Error in test_create_notification: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
def room_notifications_api(request, room_id):
    """API for room notifications"""
    try:
        room = Room.objects.get(id=room_id)

        if request.method == 'GET':
            # Get room notifications for the current user
            notifications = RoomNotification.objects.filter(
                room=room,
                user=request.user
            ).order_by('-created_at')[:20]

            notifications_data = []
            for notification in notifications:
                notifications_data.append({
                    'id': notification.id,
                    'title': notification.title,
                    'message': notification.message,
                    'type': notification.notification_type,
                    'created_at': notification.created_at.isoformat(),
                    'is_read': notification.is_read,
                    'created_by': notification.created_by.username if notification.created_by else None
                })

            return JsonResponse({'notifications': notifications_data})

        elif request.method == 'POST':
            data = json.loads(request.body)
            action = data.get('action')

            if action == 'mark_read':
                notification_ids = data.get('notification_ids', [])
                RoomNotification.objects.filter(
                    id__in=notification_ids,
                    user=request.user
                ).update(is_read=True)
                return JsonResponse({'success': True})

            elif action == 'mark_all_read':
                RoomNotification.objects.filter(
                    room=room,
                    user=request.user,
                    is_read=False
                ).update(is_read=True)
                return JsonResponse({'success': True})

    except Room.DoesNotExist:
        return JsonResponse({'error': 'Room not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def room_admin(request, room_id):
    """Room administration panel"""
    try:
        room = Room.objects.get(id=room_id)

        # Check if user can manage this room
        if not room.can_user_manage(request.user):
            messages.error(request, 'You do not have permission to manage this room.')
            return redirect('chat:room', room_name=room_id)

        context = {
            'room': room,
            'members': room.get_active_members().select_related('user'),
            'pagetitle': f'Manage {room.name}'
        }

        return render(request, 'chat/room_admin.html', context)

    except Room.DoesNotExist:
        messages.error(request, 'Room not found.')
        return redirect('chat:room_list')