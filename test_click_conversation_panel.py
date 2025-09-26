#!/usr/bin/env python
"""
Test script for clicking conversation panel - simulating exact user click behavior
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

def test_click_conversation_panel():
    """Test the exact flow when user clicks on a conversation in the panel"""
    print("=== Testing Click on Conversation Panel ===\n")

    # Create test client
    client = Client()

    # Create test user
    user, created = User.objects.get_or_create(
        username='click_panel_test_user',
        defaults={
            'email': 'click_panel_test@example.com',
            'first_name': 'Click',
            'last_name': 'Panel'
        }
    )
    print(f"Using test user: {user.username}")

    # Force login the user
    client.force_login(user)
    print("User logged in successfully")

    # Create test conversations with messages
    conversations = []
    for i in range(3):
        conv_id = f"panel_conv_{user.id}_{int(datetime.now().timestamp())}_{i}"
        conv = Conversation.objects.create(
            user=user,
            conversation_id=conv_id,
            title=f"Panel Test Conversation {i+1}",
            is_active=(i == 0)
        )

        # Add some messages to each conversation
        for j in range(3):
            conv.add_message(
                sender='user' if j % 2 == 0 else 'ai',
                content=f"Panel Message {j+1} in conversation {i+1}",
                sender_name=user.get_full_name() if j % 2 == 0 else 'Asistente'
            )

        conversations.append(conv)
        print(f"Created conversation: {conv.id} - {conv.title} with {len(conv.messages)} messages")

    print("\n--- Simulating User Opening Assistant Page ---")
    response = client.get('/chat/ui/')
    print(f"Assistant page status: {response.status_code}")

    # For testing purposes, we'll assume CSRF is handled properly
    print("Note: CSRF token handling is assumed to work in browser")

    print("\n--- Step 1: Frontend loads conversations list (loadConversations()) ---")
    response = client.post('/chat/api/conversations/',
                          HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    print(f"Conversations API status: {response.status_code}")

    if response.status_code == 200:
        data = json.loads(response.content)
        print(f"[OK] Conversations loaded: {len(data['conversations'])} conversations")
        for conv in data['conversations']:
            print(f"   - {conv['conversation_id']}: {conv['title']} ({conv['message_count']} msgs, active: {conv['is_active']})")

        # Find an inactive conversation to click on
        target_conv = None
        for conv in data['conversations']:
            if not conv['is_active']:
                target_conv = conv
                break

        if target_conv:
            print(f"\n--- Step 2: User clicks on '{target_conv['title']}' (switchConversation() function) ---")
            print(f"[CONSOLE] Would log: 'Switching to conversation: {target_conv['conversation_id']}'")

            switch_url = f'/chat/api/conversation/{target_conv["conversation_id"]}/switch/'
            print(f"[HTTP] Making POST request to: {switch_url}")

            # Simulate the exact fetch call from JavaScript
            response = client.post(switch_url,
                                 json={},  # Empty JSON body as in JS
                                 content_type='application/json',
                                 HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            print(f"[HTTP] Switch API response status: {response.status_code}")

            if response.status_code == 200:
                switch_data = json.loads(response.content)
                print(f"[OK] Switch API response: {switch_data}")
                print("[CONSOLE] Would log: 'Conversation switched successfully'")

                print(f"\n--- Step 3: Frontend calls loadConversationMessages() for {target_conv['conversation_id']} ---")
                messages_url = f'/chat/api/conversation/{target_conv["conversation_id"]}/messages/'
                print(f"[HTTP] Making GET request to: {messages_url}")

                response = client.get(messages_url,
                                     HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                print(f"[HTTP] Messages API response status: {response.status_code}")

                if response.status_code == 200:
                    messages_data = json.loads(response.content)
                    print(f"[OK] Messages loaded: {messages_data['total_messages']} messages")
                    print(f"[CHAT] Conversation title: {messages_data['conversation_title']}")

                    print("[CONSOLE] Would log messages:")
                    for i, msg in enumerate(messages_data['messages'][:3]):
                        print(f"   [{i+1}] {msg['sender']}: {msg['content'][:50]}...")

                    print("\n[UI] Frontend would call renderChatHistory() to display messages")
                    print("[CONSOLE] Would log: 'Chat history rendered'")

                    print("\n[UI] Frontend would add system message about conversation switch")
                    print("[CONSOLE] Would log: 'System message added to chat'")

                    print("\n[STORAGE] Frontend would save to localStorage")
                    print("[CONSOLE] Would log: 'Chat history saved to localStorage'")

                    print("\n[UI] Frontend would show success toast")
                    print("[CONSOLE] Would log: 'Toast shown: Conversación cargada: X mensajes'")

                else:
                    print(f"[ERROR] Messages API failed with status {response.status_code}")
                    print(f"[HTTP] Response content: {response.content.decode()}")
                    print("[CONSOLE] Would log: 'Error loading conversation messages'")
                    print("[UI] Frontend would show error toast")

            else:
                print(f"[ERROR] Switch API failed with status {response.status_code}")
                print(f"[HTTP] Response content: {response.content.decode()}")
                print("[CONSOLE] Would log: 'Error switching conversation'")
                print("[UI] Frontend would show error toast")

        else:
            print("[ERROR] No inactive conversation found to click on")
    else:
        print(f"[ERROR] Conversations API failed with status {response.status_code}")
        print(f"[HTTP] Response content: {response.content.decode()}")

    # Cleanup
    print("\n--- Cleanup ---")
    Conversation.objects.filter(user=user, title__startswith='Panel Test').delete()
    print("Test conversations deleted")

    if created:
        try:
            user.delete()
            print("Test user deleted")
        except Exception as e:
            print(f"Could not delete user: {e}")

    print("\n=== Click Conversation Panel Test Completed ===")

if __name__ == '__main__':
    test_click_conversation_panel()