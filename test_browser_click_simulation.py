#!/usr/bin/env python
"""
Test script to simulate exact browser behavior when clicking conversation panel
This shows what messages appear in browser console and why messages don't load
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

def test_browser_click_simulation():
    """Simulate exact browser behavior when clicking on conversation panel"""
    print("=== Browser Click Simulation Test ===\n")

    # Create test client
    client = Client()

    # Create test user
    user, created = User.objects.get_or_create(
        username='browser_click_test_user',
        defaults={
            'email': 'browser_click_test@example.com',
            'first_name': 'Browser',
            'last_name': 'Click'
        }
    )
    print(f"Using test user: {user.username}")

    # Force login the user
    client.force_login(user)
    print("User logged in successfully")

    # Create test conversations with messages
    conversations = []
    for i in range(2):
        conv_id = f"browser_conv_{user.id}_{int(datetime.now().timestamp())}_{i}"
        conv = Conversation.objects.create(
            user=user,
            conversation_id=conv_id,
            title=f"Browser Test Conversation {i+1}",
            is_active=(i == 0)
        )

        # Add some messages to each conversation
        for j in range(2):
            conv.add_message(
                sender='user' if j % 2 == 0 else 'ai',
                content=f"Browser Message {j+1} in conversation {i+1}",
                sender_name=user.get_full_name() if j % 2 == 0 else 'Asistente'
            )

        conversations.append(conv)
        print(f"Created conversation: {conv.id} - {conv.title} with {len(conv.messages)} messages")

    print("\n--- Browser: User opens /chat/ui/ ---")
    response = client.get('/chat/ui/')
    print(f"Page loaded: {response.status_code}")

    # Simulate JavaScript execution
    print("\n--- Browser Console: JavaScript starts executing ---")
    print("[CONSOLE] $(document).ready() fired")
    print("[CONSOLE] initializeChat() called")
    print("[CONSOLE] loadConversations() called")

    print("\n--- Browser: JavaScript calls loadConversations() ---")
    response = client.post('/chat/api/conversations/',
                          HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    print(f"Conversations API: {response.status_code}")

    if response.status_code == 200:
        data = json.loads(response.content)
        print(f"[CONSOLE] Conversations loaded: {len(data['conversations'])} conversations")
        print("[CONSOLE] renderConversationsList() called")

        # Find an inactive conversation to click on
        target_conv = None
        for conv in data['conversations']:
            if not conv['is_active']:
                target_conv = conv
                break

        if target_conv:
            print(f"\n--- Browser: User clicks on '{target_conv['title']}' ---")
            print(f"[CONSOLE] Click event fired on .conversation-item")
            print(f"[CONSOLE] data-conversation-id: {target_conv['conversation_id']}")
            print(f"[CONSOLE] switchConversation('{target_conv['conversation_id']}') called")

            print(f"\n--- Browser: JavaScript executes switchConversation() ---")
            print(f"[CONSOLE] Fetching: POST /chat/api/conversation/{target_conv['conversation_id']}/switch/")

            # Simulate the exact fetch call
            response = client.post(f'/chat/api/conversation/{target_conv["conversation_id"]}/switch/',
                                 json={},  # Empty JSON body
                                 content_type='application/json',
                                 HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            print(f"[CONSOLE] Switch API response: {response.status_code}")

            if response.status_code == 200:
                switch_data = json.loads(response.content)
                print(f"[CONSOLE] Switch response: {switch_data}")
                print(f"[CONSOLE] currentConversationId set to: {target_conv['conversation_id']}")
                print(f"[CONSOLE] Calling loadConversationMessages('{target_conv['conversation_id']}')")

                print(f"\n--- Browser: JavaScript executes loadConversationMessages() ---")
                print(f"[CONSOLE] Fetching: GET /chat/api/conversation/{target_conv['conversation_id']}/messages/")

                response = client.get(f'/chat/api/conversation/{target_conv["conversation_id"]}/messages/',
                                     HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                print(f"[CONSOLE] Messages API response: {response.status_code}")

                if response.status_code == 200:
                    messages_data = json.loads(response.content)
                    print(f"[CONSOLE] Messages loaded: {messages_data['total_messages']} messages")
                    print(f"[CONSOLE] Conversation title: {messages_data['conversation_title']}")
                    print(f"[CONSOLE] chatHistory set to: {len(messages_data['messages'])} messages")
                    print(f"[CONSOLE] updateConversationTitle('{messages_data['conversation_title']}') called")
                    print(f"[CONSOLE] renderChatHistory() called")
                    print(f"[CONSOLE] System message added to chatHistory")
                    print(f"[CONSOLE] renderChatHistory() called again")
                    print(f"[CONSOLE] localStorage.setItem('chatHistory', ...) called")
                    print(f"[CONSOLE] showToast('Conversación cargada: {messages_data['total_messages']} mensajes', 'success')")

                    print(f"\n--- Browser: Chat should now display {messages_data['total_messages']} messages ---")
                    print("[EXPECTED RESULT] User should see the conversation messages in the chat area")

                else:
                    print(f"[CONSOLE] ERROR: Messages API failed with {response.status_code}")
                    print(f"[CONSOLE] Response: {response.content.decode()}")
                    print("[CONSOLE] chatHistory set to: []")
                    print("[CONSOLE] Error message added to chatHistory")
                    print("[CONSOLE] renderChatHistory() called")
                    print("[CONSOLE] showToast('Error al cargar mensajes de la conversación', 'error')")

            else:
                print(f"[CONSOLE] ERROR: Switch API failed with {response.status_code}")
                print(f"[CONSOLE] Response: {response.content.decode()}")
                print("[CONSOLE] showToast('Error al cambiar de conversación', 'error')")

        else:
            print("[ERROR] No inactive conversation found to click on")

    else:
        print(f"[CONSOLE] ERROR: Conversations API failed with {response.status_code}")
        print(f"[CONSOLE] Response: {response.content.decode()}")

    print("\n--- Analysis: Why messages don't load in chat ---")
    print("If the user reports that clicking doesn't load messages:")
    print("1. Check browser console for JavaScript errors")
    print("2. Verify that switchConversation() function is defined")
    print("3. Check if event listeners are properly attached")
    print("4. Verify API endpoints are responding correctly")
    print("5. Check if renderChatHistory() is updating the DOM")

    # Cleanup
    print("\n--- Cleanup ---")
    Conversation.objects.filter(user=user, title__startswith='Browser Test').delete()
    print("Test conversations deleted")

    if created:
        try:
            user.delete()
            print("Test user deleted")
        except Exception as e:
            print(f"Could not delete user: {e}")

    print("\n=== Browser Click Simulation Test Completed ===")

if __name__ == '__main__':
    test_browser_click_simulation()