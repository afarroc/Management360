# -*- coding: utf-8 -*-
from django.shortcuts import render

def home_view(request):
    context = {
        'page_title': 'Home'
    }
    return render(request, 'home/home.html', context)

def about_view(request):
    context = {
        'page_title': 'About Us'
    }
    return render(request, 'about/about.html', context)
    
def contact_view(request):
    context = {
        'page_title': 'Contact'
    }
    return render(request, 'contact/contact.html', context)

def faq_view(request):
    context = {
        'page_title': 'F.A.Q.'
    }
    return render(request, 'faq/faq.html', context)

def blank_view(request):
    context = {
        'page_title': 'Blank Page',
        'message': 'This is a blank page. You can add your own content here.'
    }
    return render(request, 'blank/blank.html', context)

from django.db.models import Q
from .models import Article
from events.models import Event, Project, Task

def search_view(request):
    query = request.GET.get('query', '').strip()
    results = {
        'articles': Article.objects.none(),
        'events': Event.objects.none(),
        'projects': Project.objects.none(),
        'tasks': Task.objects.none()
    }
    
    if query:
        # Búsqueda en Artículos
        results['articles'] = Article.objects.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query) |
            Q(excerpt__icontains=query)
        ).order_by('-publication_date')
        
        # Búsqueda en Eventos
        results['events'] = Event.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(venue__icontains=query) |
            Q(event_category__icontains=query)
        ).select_related('event_status').order_by('-created_at')
        
        # Búsqueda en Proyectos
        results['projects'] = Project.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        ).select_related('project_status').order_by('-created_at')
        
        # Búsqueda en Tareas
        results['tasks'] = Task.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        ).select_related('task_status').order_by('-created_at')
    
    total_results = sum(results[c].count() for c in results.keys())
    
    context = {
        'page_title': 'Search Results',
        'query': query,
        'results': results,
        'total_results': total_results,
        'has_results': total_results > 0
    }
    return render(request, 'search/search.html', context)


# Standard library imports
import os
import re
import ast
from pathlib import Path

# Django imports
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.http import require_GET
from django.shortcuts import render


@require_GET
def url_map_view(request):
    """
    View to generate a URL map structure for all apps in the project.

    Args:
        request: HttpRequest object with optional 'app_name' GET parameter

    Returns:
        JsonResponse with either:
        - List of all apps with their URLs (if no app_name provided)
        - URL structure for specified app
        - Error message if app doesn't exist
    """
    app_name = request.GET.get("app_name", "")

    if not app_name:
        # List all apps with their URL structures
        apps_data = get_all_apps_url_structure()
        return JsonResponse(apps_data, safe=False)

    # Get URL structure for specific app
    app_urls = get_app_url_structure(app_name)
    if app_urls is None:
        return JsonResponse(
            {"error": f"The app '{app_name}' does not exist or has no URLs configured."},
            status=400
        )

    return JsonResponse(app_urls, safe=False)


def get_all_apps_url_structure():
    """
    Get URL structure for all apps in the project.

    Returns:
        List of dictionaries with app information and URL structures
    """
    apps_data = []

    # Get all Django apps from INSTALLED_APPS
    from django.conf import settings
    installed_apps = getattr(settings, 'INSTALLED_APPS', [])

    # Filter local apps (exclude Django core and third-party apps)
    local_apps = []
    for app in installed_apps:
        if not app.startswith('django.') and '.' in app:
            app_name = app.split('.')[-2]  # Get app name from 'app.apps.AppConfig'
            local_apps.append(app_name)

    # Also check for apps in the project directory
    project_dir = Path(settings.BASE_DIR)
    for item in project_dir.iterdir():
        if item.is_dir() and not item.name.startswith('__') and item.name not in ['static', 'media', 'templates']:
            if item.name not in local_apps:
                local_apps.append(item.name)

    for app_name in sorted(local_apps):
        app_urls = get_app_url_structure(app_name)
        if app_urls:
            apps_data.append({
                "name": app_name,
                "type": "app",
                "url_count": len(app_urls.get('urls', [])),
                "urls": app_urls
            })

    return apps_data


def get_app_url_structure(app_name):
    """
    Get URL structure for a specific app.

    Args:
        app_name: Name of the Django app

    Returns:
        Dictionary with app URL information or None if not found
    """
    urls_file = Path(settings.BASE_DIR) / app_name / 'urls.py'

    if not urls_file.exists():
        return None

    try:
        # Read and parse the urls.py file
        with open(urls_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract urlpatterns
        urlpatterns = parse_urlpatterns(content, app_name)

        return {
            "app_name": app_name,
            "urls_file": str(urls_file.relative_to(settings.BASE_DIR)),
            "urls": urlpatterns
        }

    except Exception as e:
        return {
            "app_name": app_name,
            "error": f"Error parsing URLs: {str(e)}",
            "urls": []
        }


def parse_urlpatterns(content, app_name=None):
    """
    Parse Django urlpatterns from Python code.

    Args:
        content: String content of urls.py file
        app_name: Name of the Django app (optional)

    Returns:
        List of parsed URL patterns
    """
    urls = []

    try:
        # Use regex to find path() calls
        path_pattern = r'path\s*\(\s*[\'"](.*?)[\'"]\s*,?\s*([^,]+(?:,.*?)?)\)'
        matches = re.findall(path_pattern, content, re.DOTALL)

        for match in matches:
            url_pattern = match[0]
            view_info = match[1].strip()

            # Clean up the view info
            view_info = re.sub(r'\s+', ' ', view_info)

            # Build full URL pattern including app prefix
            if app_name:
                if url_pattern.startswith('/'):
                    full_pattern = f"/{app_name}{url_pattern}"
                else:
                    full_pattern = f"/{app_name}/{url_pattern}" if url_pattern else f"/{app_name}/"
            else:
                # Fallback for when app_name is not provided
                if url_pattern.startswith('/'):
                    full_pattern = url_pattern
                else:
                    full_pattern = f"/{url_pattern}" if url_pattern else "/"

            urls.append({
                "pattern": url_pattern,
                "view": view_info,
                "type": "path",
                "full_pattern": full_pattern
            })

        # Also look for re_path patterns
        repath_pattern = r're_path\s*\(\s*r?[\'"](.*?)[\'"]\s*,?\s*([^,]+(?:,.*?)?)\)'
        repath_matches = re.findall(repath_pattern, content, re.DOTALL)

        for match in repath_matches:
            url_pattern = match[0]
            view_info = match[1].strip()

            view_info = re.sub(r'\s+', ' ', view_info)

            # For re_path, build full pattern with app prefix
            if app_name:
                if url_pattern.startswith('/'):
                    full_pattern = f"/{app_name}{url_pattern}"
                else:
                    full_pattern = f"/{app_name}/{url_pattern}" if url_pattern else f"/{app_name}/"
            else:
                full_pattern = f"/{url_pattern}" if not url_pattern.startswith('/') else url_pattern

            urls.append({
                "pattern": url_pattern,
                "view": view_info,
                "type": "re_path",
                "full_pattern": full_pattern
            })

    except Exception as e:
        error_pattern = "/error"
        if app_name:
            error_pattern = f"/{app_name}/error"

        urls.append({
            "pattern": "error",
            "view": f"Error parsing: {str(e)}",
            "type": "error",
            "full_pattern": error_pattern
        })

    return urls


def url_map_html_view(request):
    """
    HTML view to display the URL map in a web interface.
    """
    import django
    django_version = django.get_version()

    app_name = request.GET.get("app_name", "")

    if app_name:
        # Show specific app URLs
        app_urls = get_app_url_structure(app_name)
        if app_urls:
            return render(request, 'core/url_map_detail.html', {
                'app_urls': app_urls,
                'app_name': app_name,
                'django_version': django_version
            })
        else:
            return render(request, 'core/url_map_detail.html', {
                'error': f"App '{app_name}' not found or has no URLs",
                'app_name': app_name,
                'django_version': django_version
            })

    # Show all apps
    apps_data = get_all_apps_url_structure()
    return render(request, 'core/url_map.html', {
        'apps_data': apps_data,
        'django_version': django_version
    })
