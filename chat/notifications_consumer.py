# chat/notifications_consumer.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        if isinstance(self.user, AnonymousUser):
            await self.close()
            return

        self.notification_group_name = "notifications"

        # Join general notifications group
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave notification group
        await self.channel_layer.group_discard(
            self.notification_group_name,
            self.channel_name
        )

    async def chat_message(self, event):
        # Only send notification if the recipient is not the sender
        if str(self.user.id) != str(event["user_id"]):
            await self.send(text_data=json.dumps({
                "type": "chat_message",
                "message": event["message"],
                "user_id": event["user_id"],
                "display_name": event["display_name"],
                "room_id": event["room_id"]
            }))

    async def new_message(self, event):
        # Only send notification if the recipient is not the sender
        if str(self.user.id) != str(event["user_id"]):
            await self.send(text_data=json.dumps({
                "type": "new_message",
                "message": event["message"],
                "user_id": event["user_id"],
                "display_name": event["display_name"],
                "room_id": event["room_id"]
            }))

    async def system_notification(self, event):
        # System notifications don't have a sender, so send to all users
        await self.send(text_data=json.dumps({
            "type": "system_notification",
            "message": event["message"],
            "title": event.get("title", "System Notification"),
            "notification_type": event.get("notification_type", "system")
        }))