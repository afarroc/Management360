#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import django
import sys

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from courses.models import ContentBlock

def check_contentblock():
    try:
        cb = ContentBlock.objects.get(id=25)
        print("=== ContentBlock ID 25 ===")
        print("Title:", cb.title)
        print("Slug:", cb.slug)
        print("Content Type:", cb.content_type)
        print("Description:", cb.description)
        print("Author:", cb.author.username)
        print("Is Public:", cb.is_public)
        print("Usage Count:", cb.usage_count)
        print("Created At:", cb.created_at)
        print("Updated At:", cb.updated_at)

        print("\n=== Content ===")
        if cb.content_type == 'html':
            print("HTML Content:")
            print(cb.html_content)
        elif cb.content_type == 'markdown':
            print("Markdown Content:")
            print(cb.markdown_content)
        elif cb.content_type == 'json':
            print("JSON Content:")
            import json
            try:
                # Guardar en archivo para evitar problemas de codificación
                with open('contentblock_25_content.json', 'w', encoding='utf-8') as f:
                    json.dump(cb.json_content, f, indent=2, ensure_ascii=False)
                print("Content saved to contentblock_25_content.json")

                # Intentar imprimir información básica
                if isinstance(cb.json_content, list):
                    print(f"JSON is a list with {len(cb.json_content)} items")
                    for i, item in enumerate(cb.json_content):
                        print(f"  Item {i}: {type(item).__name__}")
                        if isinstance(item, dict):
                            print(f"    Keys: {list(item.keys())}")
                        elif isinstance(item, str):
                            print(f"    Preview: {item[:100]}...")
                elif isinstance(cb.json_content, dict):
                    print(f"JSON is a dict with keys: {list(cb.json_content.keys())}")
                else:
                    print(f"JSON type: {type(cb.json_content)}")

            except Exception as e:
                print("Error handling JSON:", str(e))
                print("Raw type:", type(cb.json_content))
        elif cb.content_type == 'text':
            print("Text Content:")
            print(cb.html_content)
        else:
            print("Content ({}):".format(cb.content_type))
            print(cb.get_content())

        print("\n=== Tags ===")
        print(cb.tags)

    except ContentBlock.DoesNotExist:
        print("ContentBlock with id=25 does not exist.")
    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    check_contentblock()