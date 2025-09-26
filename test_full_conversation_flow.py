#!/usr/bin/env python
"""
Test script for full conversation flow - simulating user clicks and interactions
"""
import os
import sys
import django
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.test import Client, TestCase
from django.contrib.auth.models import User
from chat.models import Conversation

def test_full_conversation_flow():
    """Test the complete flow: create conversations, select from history, send message"""
    print("=== Testing Full Conversation Flow (Simulating User Clicks) ===\n")

    # Create test client
    client = Client()

    # Create test user
    user, created = User.objects.get_or_create(
        username='click_test_user',
        defaults={
            'email': 'click_test@example.com',
            'first_name': 'Click',
            'last_name': 'Test'
        }
    )
    print(f"Using test user: {user.username}")

    # Force login the user (bypasses authentication)
    client.force_login(user)
    print("User logged in successfully")

    # Create some test conversations
    conversations = []
    for i in range(3):
        conv_id = f"click_conv_{user.id}_{int(datetime.now().timestamp())}_{i}"
        conv = Conversation.objects.create(
            user=user,
            conversation_id=conv_id,
            title=f"Click Test Conversation {i+1}",
            is_active=(i == 0)
        )
        conversations.append(conv)
        print(f"Created conversation: {conv.id} - {conv.title}")

    print("\n--- Step 1: User opens conversation history page ---")
    response = client.get('/chat/conversations/')
    print(f"Conversation history page status: {response.status_code}")

    print("\n--- Step 2: Frontend calls conversations API ---")
    response = client.post('/chat/api/conversations/',
                          HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    print(f"Conversations API status: {response.status_code}")

    if response.status_code == 200:
        data = json.loads(response.content)
        print(f"API returned {len(data['conversations'])} conversations:")
        for conv in data['conversations'][:3]:
            print(f"  - ID: {conv['id']}, Title: {conv['title']}, Active: {conv['is_active']}")

        # Find a conversation to switch to (not the active one)
        target_conv = None
        for conv in data['conversations']:
            if not conv['is_active']:
                target_conv = conv
                break

        if target_conv:
            print(f"\n--- Step 3: User clicks on conversation '{target_conv['title']}' ---")
            switch_url = f'/chat/api/conversation/{target_conv["conversation_id"]}/switch/'
            print(f"Calling switch API: {switch_url}")

            response = client.post(switch_url,
                                 HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            print(f"Switch API status: {response.status_code}")

            if response.status_code == 200:
                switch_data = json.loads(response.content)
                print(f"Switch response: {switch_data}")

                print("\n--- Step 4: User opens assistant page ---")
                response = client.get('/chat/assistant/')
                print(f"Assistant page status: {response.status_code}")

                print("\n--- Step 5: User sends a message ---")
                message_data = {
                    'user_input': 'Hello from clicked conversation!',
                    'chat_history': '[]'  # Frontend sends empty, backend loads from conversation
                }

                # Note: This will be a streaming response, so we can't easily test the full flow
                # But we can check that the request is accepted
                print("Sending message to chat endpoint...")
                try:
                    response = client.post('/chat/assistant/',
                                         message_data,
                                         HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                    print(f"Chat message status: {response.status_code}")
                    print("Note: This is a streaming response, full test would require async handling")

                    # Check if the active conversation has the message
                    active_conv = Conversation.objects.get(user=user, is_active=True)
                    print(f"Active conversation after switch: {active_conv.id} - {active_conv.title}")
                    print(f"Messages in active conversation: {len(active_conv.messages)}")

                except Exception as e:
                    print(f"Chat message test failed: {e}")

            else:
                print(f"Switch API failed with status {response.status_code}")
                print(f"Response content: {response.content.decode()}")
        else:
            print("No inactive conversation found to switch to")
    else:
        print(f"Conversations API failed with status {response.status_code}")

    # Cleanup
    print("\n--- Cleanup ---")
    Conversation.objects.filter(user=user, title__startswith='Click Test').delete()
    print("Test conversations deleted")

    if created:
        try:
            user.delete()
            print("Test user deleted")
        except Exception as e:
            print(f"Could not delete user: {e}")

    print("\n=== Full Flow Test Completed ===")

if __name__ == '__main__':
    test_full_conversation_flow()