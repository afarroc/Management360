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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None
        self.user = None

    async def connect(self):
        try:
            # Get room name and validate
            self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
            if not self.room_name or not str(self.room_name).isdigit():
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
            
            await self.accept()
            logger.info(f"User {self.user} connected to room {self.room_name}")

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
        except:
            pass
        raise StopConsumer()

    async def receive(self, text_data=None, bytes_data=None):
        try:
            if text_data:
                text_data_json = json.loads(text_data)
                message = text_data_json.get("message", "").strip()
                
                if not message:
                    raise ValueError("Empty message")
                
                # Validate and process message
                processed_message = await self.process_message(message)
                
                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat_message",
                        "message": processed_message,
                        "sender": str(self.user),
                        "user_id": str(self.user.id)
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

    async def chat_message(self, event):
        try:
            # Send message to WebSocket with additional metadata
            await self.send(text_data=json.dumps({
                "message": event["message"],
                "sender": event["sender"],
                "user_id": event["user_id"],
                "timestamp": str(datetime.datetime.now().isoformat())
            }))
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")

    @database_sync_to_async
    def verify_room_access(self):
        """Implement your room access verification logic here"""
        # Example: return Room.objects.filter(id=self.room_name, members=self.user).exists()
        return True  # Placeholder - implement your actual logic

    async def process_message(self, raw_message):
        """Process and sanitize incoming messages"""
        # Add any message processing logic here
        return raw_message[:500]  # Simple length limit example