#!/usr/bin/env python
"""
Check inbox item data
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from events.models import InboxItem

def check_item():
    try:
        item = InboxItem.objects.get(id=99)
        print(f"Item 99 exists: {item.title}")
        print(f"Created by: {item.created_by}")
        print(f"Description: {item.description}")
        print(f"Created at: {item.created_at}")
        print(f"Priority: {item.priority}")
        print(f"GTD Category: {item.gtd_category}")
        print(f"Assigned to: {item.assigned_to}")
        print(f"Is processed: {item.is_processed}")
    except InboxItem.DoesNotExist:
        print("Item 99 does not exist")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    check_item()