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
