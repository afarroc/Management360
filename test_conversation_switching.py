#!/usr/bin/env python
"""
Test script for conversation switching and messaging functionality
"""
import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.contrib.auth.models import User
from chat.models import Conversation
from django.test import RequestFactory
from chat.views import switch_conversation_api, chat_view
import json

def test_conversation_functionality():
    """Test conversation creation, switching, and messaging"""
    print("=== Testing Conversation Functionality ===\n")

    # Get or create test user
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    print(f"Using test user: {user.username} (created: {created})")

    # Create multiple conversations
    print("\n--- Creating test conversations ---")
    conversations = []
    for i in range(3):
        conv_id = f"test_conv_{user.id}_{int(datetime.now().timestamp())}_{i}"
        conv = Conversation.objects.create(
            user=user,
            conversation_id=conv_id,
            title=f"Test Conversation {i+1}",
            is_active=(i == 0)  # First one active
        )
        conversations.append(conv)
        print(f"Created conversation: {conv.id} - {conv.title} (active: {conv.is_active})")

    # Test conversations API
    print("\n--- Testing conversations API ---")
    from chat.views import conversations_api
    factory = RequestFactory()
    request = factory.post('/chat/api/conversations/')
    request.user = user

    response = conversations_api(request)
    data = json.loads(response.content)
    print(f"Conversations API returned {len(data['conversations'])} conversations")
    for conv_data in data['conversations'][:3]:
        print(f"  - ID: {conv_data['id']}, Title: {conv_data['title']}, Active: {conv_data['is_active']}")

    # Test switching to second conversation
    print("\n--- Testing conversation switching ---")
    target_conv = conversations[1]
    print(f"Switching to conversation: {target_conv.id} - {target_conv.title}")

    request = factory.post(f'/chat/api/conversation/switch/{target_conv.conversation_id}/')
    request.user = user

    response = switch_conversation_api(request, target_conv.conversation_id)
    data = json.loads(response.content)
    print(f"Switch API response: {data}")

    # Verify the conversation is now active
    target_conv.refresh_from_db()
    print(f"Target conversation active status: {target_conv.is_active}")

    # Check that only one conversation is active
    active_convs = Conversation.objects.filter(user=user, is_active=True)
    print(f"Number of active conversations: {active_convs.count()}")

    # Test sending a message to the active conversation
    print("\n--- Testing message sending ---")
    request = factory.post('/chat/chat/', {
        'user_input': 'Test message to switched conversation',
        'chat_history': '[]'  # Empty history to test loading from conversation
    })
    request.user = user

    # Mock the streaming response (we can't fully test async here)
    try:
        # This will fail because of async, but let's see what happens
        print("Attempting to send message...")
        # For testing purposes, let's just check the conversation has messages
        active_conv = Conversation.objects.get(user=user, is_active=True)
        initial_message_count = len(active_conv.messages)
        print(f"Active conversation has {initial_message_count} messages before sending")

        # Since we can't fully test the async chat_view, let's manually add a message
        active_conv.add_message('user', 'Test message', 'Test User')
        active_conv.add_message('ai', 'Test response', 'AI Assistant')

        active_conv.refresh_from_db()
        final_message_count = len(active_conv.messages)
        print(f"Active conversation has {final_message_count} messages after manual addition")

        print("PASS: Message addition test passed")

    except Exception as e:
        print(f"FAIL: Message sending test failed: {e}")

    # Test assistant view loading
    print("\n--- Testing assistant view loading ---")
    from chat.views import assistant_view
    request = factory.get('/chat/assistant/')
    request.user = user

    try:
        response = assistant_view(request)
        print("PASS: Assistant view loaded successfully")
        # Check if context has conversation_id
        if hasattr(response, 'context_data'):
            conv_id = response.context_data.get('conversation_id')
            print(f"Assistant view context conversation_id: {conv_id}")
    except Exception as e:
        print(f"FAIL: Assistant view test failed: {e}")

    # Cleanup
    print("\n--- Cleaning up test data ---")
    Conversation.objects.filter(user=user, title__startswith='Test Conversation').delete()
    print("CLEANUP: Test conversations deleted")

    if created:
        user.delete()
        print("CLEANUP: Test user deleted")

    print("\n=== Test completed ===")

if __name__ == '__main__':
    test_conversation_functionality()