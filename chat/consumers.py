# chat/consumers.py
import json
import logging
import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def history_cleared(self, event):
        await self.send(text_data=json.dumps({
            'type': 'history_cleared'
        }))
    # Diccionario de usuarios conectados por sala (en memoria, por proceso)
    connected_users = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None
        self.user = None

    async def connect(self):
        try:
            # Get room name and validate
            self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
            # Permitir nombres de sala alfanuméricos (no solo dígitos)
            if not self.room_name or not str(self.room_name).isalnum():
                raise ValueError("Invalid room name")
                
            self.room_group_name = f"chat_{self.room_name}"
            self.user = self.scope["user"]

            # Authentication check
            if isinstance(self.user, AnonymousUser):
                raise PermissionDenied("Authentication required")

            # Verify room access (implement your own logic)
            if not await self.verify_room_access():
                raise PermissionDenied("No access to this room")

            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            # Añadir usuario a la lista de conectados
            await self.add_connected_user()

            await self.accept()
            logger.info(f"User {self.user} connected to room {self.room_name}")

            # Notificar a todos los usuarios la lista actualizada
            await self.broadcast_connected_users()

        except PermissionDenied as e:
            logger.warning(f"Connection refused: {str(e)}")
            await self.close(code=4001)  # Custom close code for permission denied
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            await self.close(code=4000)  # Custom close code for other errors

    async def disconnect(self, close_code):
        try:
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            await self.remove_connected_user()
            await self.broadcast_connected_users()
        except:
            pass
        raise StopConsumer()
    @database_sync_to_async
    def get_user_info(self):
        return {
            'id': str(self.user.id),
            'username': self.user.username,
            'display_name': f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username
        }

    async def add_connected_user(self):
        room = self.room_group_name
        if room not in self.connected_users:
            self.connected_users[room] = set()
        self.connected_users[room].add((str(self.user.id), self.user.username, f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username))

    async def remove_connected_user(self):
        room = self.room_group_name
        if room in self.connected_users:
            self.connected_users[room] = set(u for u in self.connected_users[room] if u[0] != str(self.user.id))
            if not self.connected_users[room]:
                del self.connected_users[room]

    async def broadcast_connected_users(self):
        room = self.room_group_name
        users = []
        if room in self.connected_users:
            for user_id, username, display_name in self.connected_users[room]:
                users.append({'id': user_id, 'username': username, 'display_name': display_name})
        await self.channel_layer.group_send(
            room,
            {
                'type': 'users_list',
                'users': users
            }
        )

    async def users_list(self, event):
        await self.send(text_data=json.dumps({
            'type': 'users',
            'users': event['users']
        }))

    async def receive(self, text_data=None, bytes_data=None):
        try:
            if text_data:
                text_data_json = json.loads(text_data)
                message = text_data_json.get("message", "").strip()
                
                if not message:
                    raise ValueError("Empty message")
                
                # Validate and process message
                processed_message = await self.process_message(message)
                user_full_name = f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username

                # Guardar mensaje en la base de datos
                await self.save_message(self.room_name, self.user, processed_message)

                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat_message",
                        "message": processed_message,
                        "sender": str(self.user),
                        "user_id": str(self.user.id),
                        "display_name": user_full_name
                    }
                )
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "error": "Invalid JSON format"
            }))
        except ValueError as e:
            await self.send(text_data=json.dumps({
                "error": str(e)
            }))
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send(text_data=json.dumps({
                "error": "Internal server error"
            }))

    @database_sync_to_async
    def save_message(self, room_id, user, content):
        from rooms.models import Room, Message
        try:
            room = Room.objects.get(id=room_id)
            Message.objects.create(room=room, user=user, content=content)
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")

    async def chat_message(self, event):
        try:
            # Send message to WebSocket with additional metadata
            await self.send(text_data=json.dumps({
                "message": event["message"],
                "sender": event["sender"],
                "user_id": event["user_id"],
                "display_name": event.get("display_name", "Usuario"),
                "timestamp": str(datetime.datetime.now().isoformat())
            }))
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")

    @database_sync_to_async
    def verify_room_access(self):
        """Verifica si el usuario tiene acceso a la sala (es miembro o administrador)"""
        from rooms.models import Room, RoomMember
        try:
            room = Room.objects.get(id=self.room_name)
            # El usuario debe ser miembro o administrador de la sala
            is_member = RoomMember.objects.filter(room=room, user=self.user).exists()
            is_admin = room.administrators.filter(id=self.user.id).exists()
            is_owner = room.owner_id == self.user.id
            # Las salas públicas permiten acceso a cualquier usuario autenticado
            is_public = room.permissions == 'public'
            return is_member or is_admin or is_owner or is_public
        except Room.DoesNotExist:
            return False

    async def process_message(self, raw_message):
        """Process and sanitize incoming messages"""
        # Add any message processing logic here
        return raw_message[:500]  # Simple length limit example