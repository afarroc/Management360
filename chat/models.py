from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.cache import cache
import json
import logging
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class HardcodedNotificationManager:
    """
    Robust, hardcoded notification system that doesn't rely on database models.
    Uses Django cache for storage with fallback mechanisms.
    """

    CACHE_KEY_PREFIX = 'hardcoded_notifications'
    CACHE_TIMEOUT = 3600  # 1 hour
    MAX_NOTIFICATIONS_PER_USER = 100
    NOTIFICATION_TTL_DAYS = 7  # Auto-cleanup after 7 days

    @classmethod
    def _get_user_cache_key(cls, user_id, key_type):
        """Generate cache key for user notifications"""
        return f"{cls.CACHE_KEY_PREFIX}:user:{user_id}:{key_type}"

    @classmethod
    def _get_all_user_notifications(cls, user_id):
        """Get all notifications for a user from cache"""
        try:
            cache_key = cls._get_user_cache_key(user_id, 'all')
            notifications = cache.get(cache_key, [])

            # Ensure it's a list
            if not isinstance(notifications, list):
                notifications = []

            return notifications
        except Exception as e:
            logger.error(f"Error getting notifications for user {user_id}: {str(e)}")
            return []

    @classmethod
    def _save_user_notifications(cls, user_id, notifications):
        """Save notifications to cache"""
        try:
            cache_key = cls._get_user_cache_key(user_id, 'all')
            cache.set(cache_key, notifications, cls.CACHE_TIMEOUT)
            return True
        except Exception as e:
            logger.error(f"Error saving notifications for user {user_id}: {str(e)}")
            return False

    @classmethod
    def create_chat_notification(cls, user, room, message, sender=None):
        """Create a notification for a new chat message"""
        try:
            # Don't create notification for self-messages
            if sender and sender.id == user.id:
                logger.debug(f"Skipping self-notification for user {user.username}")
                return None

            logger.info(f"Creating notification for user {user.username} from room {getattr(room, 'name', 'Chat')}")

            # Get existing notifications
            notifications = cls._get_all_user_notifications(user.id)

            # Create new notification
            notification_id = str(uuid.uuid4())
            notification = {
                'id': notification_id,
                'user_id': user.id,
                'title': f"New message in {getattr(room, 'name', 'Chat')}",
                'message': f"{getattr(sender, 'get_full_name', lambda: 'Someone')() or 'Someone'}: {message[:100]}{'...' if len(message) > 100 else ''}",
                'notification_type': 'chat',
                'room_id': getattr(room, 'id', None),
                'room_name': getattr(room, 'name', 'Chat'),
                'action_url': f'/chat/room/{getattr(room, "id", "")}/',
                'created_at': datetime.now().isoformat(),
                'is_read': False,
                'read_at': None,
                'sender_id': getattr(sender, 'id', None),
                'sender_name': getattr(sender, 'get_full_name', lambda: 'Someone')() or getattr(sender, 'username', 'Someone')
            }

            # Add to beginning of list
            notifications.insert(0, notification)

            # Limit number of notifications
            if len(notifications) > cls.MAX_NOTIFICATIONS_PER_USER:
                notifications = notifications[:cls.MAX_NOTIFICATIONS_PER_USER]

            # Save back to cache
            success = cls._save_user_notifications(user.id, notifications)
            if not success:
                logger.error(f"Failed to save notifications for user {user.id}")
                return None

            # Update unread count cache
            cls._update_unread_count_cache(user.id)

            logger.info(f"✅ Created hardcoded notification {notification_id} for user {user.username}")
            return notification

        except Exception as e:
            logger.error(f"❌ Error creating notification for user {user.username}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    @classmethod
    def mark_notifications_read(cls, user, notification_ids=None):
        """Mark notifications as read"""
        try:
            notifications = cls._get_all_user_notifications(user.id)
            marked_count = 0

            for notification in notifications:
                if notification.get('is_read', False):
                    continue

                should_mark = False
                if notification_ids:
                    should_mark = notification['id'] in notification_ids
                else:
                    should_mark = True

                if should_mark:
                    notification['is_read'] = True
                    notification['read_at'] = datetime.now().isoformat()
                    marked_count += 1

            # Save updated notifications
            cls._save_user_notifications(user.id, notifications)

            # Update unread count cache
            cls._update_unread_count_cache(user.id)

            logger.info(f"Marked {marked_count} notifications as read for user {user.username}")
            return marked_count

        except Exception as e:
            logger.error(f"Error marking notifications as read for user {user.username}: {str(e)}")
            return 0

    @classmethod
    def get_unread_notifications(cls, user, limit=50):
        """Get unread notifications for user"""
        try:
            notifications = cls._get_all_user_notifications(user.id)
            unread_notifications = [
                n for n in notifications
                if not n.get('is_read', False)
            ][:limit]

            logger.debug(f"Retrieved {len(unread_notifications)} unread notifications for user {user.username}")
            return unread_notifications

        except Exception as e:
            logger.error(f"Error getting unread notifications for user {user.username}: {str(e)}")
            return []

    @classmethod
    def get_notification_count(cls, user):
        """Get count of unread notifications"""
        try:
            cache_key = cls._get_user_cache_key(user.id, 'unread_count')
            cached_count = cache.get(cache_key)

            if cached_count is not None:
                return cached_count

            # Calculate from notifications
            notifications = cls._get_all_user_notifications(user.id)
            count = len([n for n in notifications if not n.get('is_read', False)])

            # Cache the count
            cache.set(cache_key, count, cls.CACHE_TIMEOUT)

            return count

        except Exception as e:
            logger.error(f"Error getting notification count for user {user.username}: {str(e)}")
            return 0

    @classmethod
    def _update_unread_count_cache(cls, user_id):
        """Update the unread count cache"""
        try:
            notifications = cls._get_all_user_notifications(user_id)
            count = len([n for n in notifications if not n.get('is_read', False)])

            cache_key = cls._get_user_cache_key(user_id, 'unread_count')
            cache.set(cache_key, count, cls.CACHE_TIMEOUT)

        except Exception as e:
            logger.error(f"Error updating unread count cache for user {user_id}: {str(e)}")

    @classmethod
    def get_notifications_data(cls, user, limit=50):
        """Get notifications data for API response"""
        try:
            notifications = cls.get_unread_notifications(user, limit)

            notifications_data = []
            for notification in notifications:
                notifications_data.append({
                    'id': notification['id'],
                    'title': notification['title'],
                    'message': notification['message'],
                    'created_at': notification['created_at'],
                    'related_room_id': notification.get('room_id'),
                    'room_name': notification.get('room_name'),
                    'notification_type': notification['notification_type'],
                    'action_url': notification['action_url']
                })

            return {
                'notifications': notifications_data,
                'total_unread': cls.get_notification_count(user)
            }

        except Exception as e:
            logger.error(f"Error getting notifications data for user {user.username}: {str(e)}")
            return {'notifications': [], 'total_unread': 0}

    @classmethod
    def cleanup_old_notifications(cls, user=None):
        """Clean up old notifications"""
        try:
            if user:
                # Clean up for specific user
                notifications = cls._get_all_user_notifications(user.id)
                cutoff_date = datetime.now() - timedelta(days=cls.NOTIFICATION_TTL_DAYS)

                # Filter out old notifications
                active_notifications = []
                for notification in notifications:
                    created_at = datetime.fromisoformat(notification['created_at'])
                    if created_at > cutoff_date:
                        active_notifications.append(notification)

                if len(active_notifications) != len(notifications):
                    cls._save_user_notifications(user.id, active_notifications)
                    logger.info(f"Cleaned up {len(notifications) - len(active_notifications)} old notifications for user {user.username}")

                return len(notifications) - len(active_notifications)
            else:
                # Clean up all users (this would require iterating through all users)
                logger.info("Global cleanup not implemented for hardcoded notifications")
                return 0

        except Exception as e:
            logger.error(f"Error cleaning up old notifications: {str(e)}")
            return 0

    @classmethod
    def ensure_notification_consistency(cls, user):
        """Ensure notification consistency"""
        try:
            # Force refresh caches
            cls._update_unread_count_cache(user.id)
            count = cls.get_notification_count(user)
            notifications = cls.get_unread_notifications(user)

            logger.info(f"Ensured consistency for user {user.username}: {count} notifications")
            return True

        except Exception as e:
            logger.error(f"Error ensuring notification consistency for user {user.username}: {str(e)}")
            return False

    @classmethod
    def get_all_notifications(cls, user, include_read=False):
        """Get all notifications for a user"""
        try:
            notifications = cls._get_all_user_notifications(user.id)

            if not include_read:
                notifications = [n for n in notifications if not n.get('is_read', False)]

            return notifications

        except Exception as e:
            logger.error(f"Error getting all notifications for user {user.username}: {str(e)}")
            return []


# Legacy compatibility
NotificationManager = HardcodedNotificationManager

# Import rooms models for relationships
try:
    from rooms.models import Room, Message
except ImportError:
    # Handle circular import
    Room = None
    Message = None

class MessageReaction(models.Model):
    """Model for message reactions"""
    message = models.ForeignKey('rooms.Message', on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['message', 'user', 'emoji']

    def __str__(self):
        return f"{self.user.username} reacted {self.emoji} to message {self.message.id}"

class TypingStatus(models.Model):
    """Model for typing status tracking"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey('rooms.Room', on_delete=models.CASCADE)
    is_typing = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'room']

    def __str__(self):
        return f"{self.user.username} {'is typing' if self.is_typing else 'stopped typing'} in {self.room.name}"

class UserPresence(models.Model):
    """Model for user presence/online status"""
    PRESENCE_CHOICES = [
        ('online', 'Online'),
        ('away', 'Away'),
        ('offline', 'Offline'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=PRESENCE_CHOICES, default='offline')
    last_seen = models.DateTimeField(default=timezone.now)
    current_room = models.ForeignKey('rooms.Room', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} is {self.status}"

    def update_presence(self, status, room=None):
        """Update user presence"""
        self.status = status
        self.last_seen = timezone.now()
        if room:
            self.current_room = room
        self.save()

    @property
    def is_online(self):
        """Check if user is currently online"""
        # Consider online if last seen within 5 minutes
        return self.status == 'online' and (timezone.now() - self.last_seen).seconds < 300


class SimpleNotification(models.Model):
    """Simple notification model for reliable storage"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='simple_notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, default='chat')
    room_id = models.IntegerField(null=True, blank=True)
    room_name = models.CharField(max_length=100, null=True, blank=True)
    action_url = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    sender_id = models.IntegerField(null=True, blank=True)
    sender_name = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
            return True
        return False


class SimpleNotificationManager:
    """Simple notification manager using database instead of cache"""

    @staticmethod
    def create_chat_notification(user, room, message, sender=None):
        """Create a notification for a new chat message"""
        try:
            # Don't create notification for self-messages
            if sender and sender.id == user.id:
                return None

            notification = SimpleNotification.objects.create(
                user=user,
                title=f"New message in {getattr(room, 'name', 'Chat')}",
                message=f"{getattr(sender, 'get_full_name', lambda: 'Someone')() or 'Someone'}: {message[:100]}{'...' if len(message) > 100 else ''}",
                notification_type='chat',
                room_id=getattr(room, 'id', None),
                room_name=getattr(room, 'name', 'Chat'),
                action_url=f'/chat/room/{getattr(room, "id", "")}/',
                sender_id=getattr(sender, 'id', None),
                sender_name=getattr(sender, 'get_full_name', lambda: 'Someone')() or getattr(sender, 'username', 'Someone')
            )

            return {
                'id': str(notification.id),
                'title': notification.title,
                'message': notification.message,
                'created_at': notification.created_at.isoformat(),
                'is_read': False,
                'room_id': notification.room_id,
                'room_name': notification.room_name,
                'notification_type': notification.notification_type,
                'action_url': notification.action_url
            }

        except Exception as e:
            print(f"Error creating notification: {e}")
            return None

    @staticmethod
    def mark_notifications_read(user, notification_ids=None):
        """Mark notifications as read"""
        try:
            if notification_ids:
                # Mark specific notifications
                updated = SimpleNotification.objects.filter(
                    user=user,
                    id__in=notification_ids,
                    is_read=False
                ).update(is_read=True, read_at=timezone.now())
            else:
                # Mark all notifications as read
                updated = SimpleNotification.objects.filter(
                    user=user,
                    is_read=False
                ).update(is_read=True, read_at=timezone.now())

            return updated

        except Exception as e:
            print(f"Error marking notifications as read: {e}")
            return 0

    @staticmethod
    def get_unread_notifications(user, limit=50):
        """Get unread notifications for user"""
        try:
            notifications = SimpleNotification.objects.filter(
                user=user,
                is_read=False
            ).order_by('-created_at')[:limit]

            return [{
                'id': str(n.id),
                'title': n.title,
                'message': n.message,
                'created_at': n.created_at.isoformat(),
                'is_read': n.is_read,
                'room_id': n.room_id,
                'room_name': n.room_name,
                'notification_type': n.notification_type,
                'action_url': n.action_url
            } for n in notifications]

        except Exception as e:
            print(f"Error getting unread notifications: {e}")
            return []

    @staticmethod
    def get_notification_count(user):
        """Get count of unread notifications"""
        try:
            return SimpleNotification.objects.filter(
                user=user,
                is_read=False
            ).count()
        except Exception as e:
            print(f"Error getting notification count: {e}")
            return 0

    @staticmethod
    def get_notifications_data(user, limit=50):
        """Get notifications data for API response"""
        try:
            notifications = SimpleNotification.objects.filter(
                user=user,
                is_read=False
            ).order_by('-created_at')[:limit]

            notifications_data = [{
                'id': str(n.id),
                'title': n.title,
                'message': n.message,
                'created_at': n.created_at.isoformat(),
                'related_room_id': n.room_id,
                'room_name': n.room_name,
                'notification_type': n.notification_type,
                'action_url': n.action_url
            } for n in notifications]

            return {
                'notifications': notifications_data,
                'total_unread': SimpleNotification.objects.filter(user=user, is_read=False).count()
            }

        except Exception as e:
            print(f"Error getting notifications data: {e}")
            return {'notifications': [], 'total_unread': 0}
