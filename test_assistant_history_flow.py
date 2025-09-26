#!/usr/bin/env python
"""
Test script for assistant history flow - simulating user interaction with conversation history
"""
import os
import sys
import django
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from chat.models import Conversation

def test_assistant_history_flow():
    """Test the complete assistant history flow"""
    print("=== Testing Assistant History Flow ===\n")

    # Create test client
    client = Client()

    # Create test user
    user, created = User.objects.get_or_create(
        username='assistant_test_user',
        defaults={
            'email': 'assistant_test@example.com',
            'first_name': 'Assistant',
            'last_name': 'Test'
        }
    )
    print(f"Using test user: {user.username}")

    # Force login the user
    client.force_login(user)
    print("User logged in successfully")

    # Create test conversations with messages
    conversations = []
    for i in range(3):
        conv_id = f"assistant_conv_{user.id}_{int(datetime.now().timestamp())}_{i}"
        conv = Conversation.objects.create(
            user=user,
            conversation_id=conv_id,
            title=f"Assistant Test Conversation {i+1}",
            is_active=(i == 0)
        )

        # Add some messages to each conversation
        for j in range(2):
            conv.add_message(
                sender='user' if j % 2 == 0 else 'ai',
                content=f"Message {j+1} in conversation {i+1}",
                sender_name=user.get_full_name() if j % 2 == 0 else 'Asistente'
            )

        conversations.append(conv)
        print(f"Created conversation: {conv.id} - {conv.title} with {len(conv.messages)} messages")

    print("\n--- Step 1: User opens assistant page ---")
    response = client.get('/chat/ui/')
    print(f"Assistant page status: {response.status_code}")

    print("\n--- Step 2: Frontend loads conversations list ---")
    response = client.post('/chat/api/conversations/',
                          HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    print(f"Conversations API status: {response.status_code}")

    if response.status_code == 200:
        data = json.loads(response.content)
        print(f"API returned {len(data['conversations'])} conversations:")
        for conv in data['conversations'][:3]:
            print(f"  - ID: {conv['id']}, Title: {conv['title']}, Active: {conv['is_active']}, Messages: {conv['message_count']}")

        # Find an inactive conversation to switch to
        target_conv = None
        for conv in data['conversations']:
            if not conv['is_active']:
                target_conv = conv
                break

        if target_conv:
            print(f"\n--- Step 3: User clicks on conversation '{target_conv['title']}' in history ---")
            switch_url = f'/chat/api/conversation/{target_conv["conversation_id"]}/switch/'
            print(f"Calling switch API: {switch_url}")

            response = client.post(switch_url,
                                 HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            print(f"Switch API status: {response.status_code}")

            if response.status_code == 200:
                switch_data = json.loads(response.content)
                print(f"Switch response: {switch_data}")

                print("\n--- Step 4: Frontend loads messages for the switched conversation ---")
                messages_url = f'/chat/api/conversation/{target_conv["conversation_id"]}/messages/'
                print(f"Calling messages API: {messages_url}")

                response = client.get(messages_url,
                                     HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                print(f"Messages API status: {response.status_code}")

                if response.status_code == 200:
                    messages_data = json.loads(response.content)
                    print(f"Messages API returned {messages_data['total_messages']} messages")
                    print(f"Conversation title: {messages_data['conversation_title']}")

                    for msg in messages_data['messages'][:3]:
                        print(f"  - {msg['sender']}: {msg['content'][:50]}...")

                    print("\n--- Step 5: User sends a new message in the switched conversation ---")
                    message_data = {
                        'user_input': 'Hello from the switched conversation!',
                        'chat_history': json.dumps(messages_data['messages'])  # Use loaded messages
                    }

                    response = client.post('/chat/assistant/',
                                         message_data,
                                         HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                    print(f"Send message status: {response.status_code}")

                    # Check if the conversation was updated
                    updated_conv = Conversation.objects.get(
                        conversation_id=target_conv["conversation_id"],
                        user=user
                    )
                    print(f"Updated conversation has {len(updated_conv.messages)} messages")
                    print(f"Last message: {updated_conv.messages[-1]['content'][:50]}...")

                else:
                    print(f"Messages API failed with status {response.status_code}")
            else:
                print(f"Switch API failed with status {response.status_code}")
                print(f"Response content: {response.content.decode()}")
        else:
            print("No inactive conversation found to switch to")
    else:
        print(f"Conversations API failed with status {response.status_code}")

    # Cleanup
    print("\n--- Cleanup ---")
    Conversation.objects.filter(user=user, title__startswith='Assistant Test').delete()
    print("Test conversations deleted")

    if created:
        try:
            user.delete()
            print("Test user deleted")
        except Exception as e:
            print(f"Could not delete user: {e}")

    print("\n=== Assistant History Flow Test Completed ===")

if __name__ == '__main__':
    test_assistant_history_flow()