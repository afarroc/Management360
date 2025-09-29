from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib import messages
from .models import (
    HelpCategory, HelpArticle, FAQ, HelpSearchLog,
    HelpFeedback, VideoTutorial, QuickStartGuide
)
import logging

logger = logging.getLogger(__name__)


def help_home(request):
    """
    Página principal del centro de ayuda
    """
    # Estadísticas generales
    stats = {
        'total_articles': HelpArticle.objects.filter(is_active=True).count(),
        'total_categories': HelpCategory.objects.filter(is_active=True).count(),
        'total_faqs': FAQ.objects.filter(is_active=True).count(),
        'total_videos': VideoTutorial.objects.filter(is_active=True).count(),
    }

    # Categorías destacadas
    featured_categories = HelpCategory.objects.filter(
        is_active=True
    ).annotate(
        article_count=Count('articles', filter=Q(articles__is_active=True))
    ).order_by('order')[:6]

    # Artículos destacados
    featured_articles = HelpArticle.objects.filter(
        is_active=True,
        is_featured=True
    ).select_related('category', 'author')[:4]

    # Guías de inicio rápido
    quick_guides = QuickStartGuide.objects.filter(
        is_active=True
    ).order_by('order')[:3]

    # Preguntas frecuentes populares
    popular_faqs = FAQ.objects.filter(
        is_active=True
    ).order_by('-helpful_count')[:5]

    context = {
        'page_title': 'Centro de Ayuda',
        'stats': stats,
        'featured_categories': featured_categories,
        'featured_articles': featured_articles,
        'quick_guides': quick_guides,
        'popular_faqs': popular_faqs,
    }

    return render(request, 'help/help_home.html', context)


def category_list(request):
    """
    Lista todas las categorías de ayuda
    """
    categories = HelpCategory.objects.filter(
        is_active=True
    ).annotate(
        article_count=Count('articles', filter=Q(articles__is_active=True)),
        faq_count=Count('faqs', filter=Q(faqs__is_active=True)),
        video_count=Count('video_tutorials', filter=Q(video_tutorials__is_active=True))
    ).order_by('order')

    context = {
        'page_title': 'Categorías de Ayuda',
        'categories': categories,
    }

    return render(request, 'help/category_list.html', context)


def category_detail(request, slug):
    """
    Muestra los artículos de una categoría específica
    """
    category = get_object_or_404(
        HelpCategory.objects.prefetch_related('articles', 'faqs', 'video_tutorials'),
        slug=slug,
        is_active=True
    )

    # Artículos de la categoría
    articles = category.articles.filter(is_active=True).order_by('-is_featured', '-published_at')

    # FAQs de la categoría
    faqs = category.faqs.filter(is_active=True).order_by('order')

    # Videos tutoriales
    videos = category.video_tutorials.filter(is_active=True).order_by('-is_featured', '-created_at')

    # Paginación para artículos
    paginator = Paginator(articles, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': f'Ayuda - {category.name}',
        'category': category,
        'articles': page_obj,
        'faqs': faqs,
        'videos': videos,
        'total_articles': articles.count(),
    }

    return render(request, 'help/category_detail.html', context)


def article_detail(request, slug):
    """
    Muestra un artículo específico
    """
    article = get_object_or_404(
        HelpArticle.objects.select_related('category', 'author'),
        slug=slug,
        is_active=True
    )

    # Verificar permisos de acceso
    if article.requires_auth and not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesión para ver este artículo.')
        return redirect('accounts:login')

    # Incrementar contador de visualizaciones
    article.increment_view_count()

    # Artículos relacionados
    related_articles = article.get_related_articles()

    # Artículos de la misma categoría (excluyendo el actual)
    category_articles = HelpArticle.objects.filter(
        category=article.category,
        is_active=True
    ).exclude(id=article.id).order_by('-published_at')[:5]

    context = {
        'page_title': article.title,
        'article': article,
        'content': article.get_content(),  # Usar método que incluye contenido referenciado
        'related_articles': related_articles,
        'category_articles': category_articles,
        'meta_title': article.meta_title or article.title,
        'meta_description': article.meta_description or article.excerpt,
    }

    return render(request, 'help/article_detail.html', context)


def faq_list(request):
    """
    Lista todas las preguntas frecuentes
    """
    # Obtener categoría si se especifica
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(HelpCategory, slug=category_slug, is_active=True)
        faqs = FAQ.objects.filter(category=category, is_active=True)
        page_title = f'Preguntas Frecuentes - {category.name}'
    else:
        faqs = FAQ.objects.filter(is_active=True)
        category = None
        page_title = 'Preguntas Frecuentes'

    # Búsqueda
    query = request.GET.get('q')
    if query:
        faqs = faqs.filter(
            Q(question__icontains=query) |
            Q(answer__icontains=query)
        )

    faqs = faqs.select_related('category').order_by('category__order', 'order')

    # Paginación
    paginator = Paginator(faqs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Categorías para filtro
    categories = HelpCategory.objects.filter(
        is_active=True
    ).annotate(
        faq_count=Count('faqs', filter=Q(faqs__is_active=True))
    ).filter(faq_count__gt=0).order_by('order')

    context = {
        'page_title': page_title,
        'faqs': page_obj,
        'categories': categories,
        'current_category': category,
        'query': query,
    }

    return render(request, 'help/faq_list.html', context)


def video_tutorials(request):
    """
    Lista todos los tutoriales en video
    """
    # Filtros
    category_slug = request.GET.get('category')
    difficulty = request.GET.get('difficulty')

    videos = VideoTutorial.objects.filter(is_active=True).select_related('category', 'author')

    if category_slug:
        videos = videos.filter(category__slug=category_slug)
        category = get_object_or_404(HelpCategory, slug=category_slug)
    else:
        category = None

    if difficulty:
        videos = videos.filter(difficulty=difficulty)

    # Ordenar por destacados primero, luego por fecha
    videos = videos.order_by('-is_featured', '-created_at')

    # Paginación
    paginator = Paginator(videos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Categorías para filtro
    categories = HelpCategory.objects.filter(
        is_active=True
    ).annotate(
        video_count=Count('video_tutorials', filter=Q(video_tutorials__is_active=True))
    ).filter(video_count__gt=0).order_by('order')

    context = {
        'page_title': 'Tutoriales en Video',
        'videos': page_obj,
        'categories': categories,
        'current_category': category,
        'current_difficulty': difficulty,
        'difficulty_choices': VideoTutorial._meta.get_field('difficulty').choices,
    }

    return render(request, 'help/video_tutorials.html', context)


def quick_start(request):
    """
    Guías de inicio rápido
    """
    guides = QuickStartGuide.objects.filter(
        is_active=True
    ).order_by('order')

    # Filtrar por audiencia objetivo
    audience = request.GET.get('audience')
    if audience:
        guides = guides.filter(target_audience=audience)

    context = {
        'page_title': 'Guías de Inicio Rápido',
        'guides': guides,
        'current_audience': audience,
        'audience_choices': QuickStartGuide._meta.get_field('target_audience').choices,
    }

    return render(request, 'help/quick_start.html', context)


def search_help(request):
    """
    Búsqueda en el sistema de ayuda
    """
    query = request.GET.get('q', '').strip()

    if not query:
        return redirect('help:help_home')

    # Registrar la búsqueda
    HelpSearchLog.objects.create(
        query=query,
        user=request.user if request.user.is_authenticated else None,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )

    # Buscar en artículos (incluyendo contenido de objetos referenciados)
    articles = HelpArticle.objects.filter(
        Q(is_active=True) & (
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(tags__icontains=query) |
            # Buscar en contenido de cursos referenciados
            Q(referenced_course__title__icontains=query) |
            Q(referenced_course__description__icontains=query) |
            # Buscar en contenido de lecciones referenciadas
            Q(referenced_lesson__title__icontains=query) |
            Q(referenced_lesson__content__icontains=query) |
            # Buscar en contenido de bloques referenciados
            Q(referenced_content_block__title__icontains=query) |
            Q(referenced_content_block__html_content__icontains=query)
        )
    ).select_related(
        'category', 'author',
        'referenced_course', 'referenced_lesson', 'referenced_content_block'
    )[:20]

    # Buscar en FAQs
    faqs = FAQ.objects.filter(
        Q(is_active=True) & (
            Q(question__icontains=query) |
            Q(answer__icontains=query)
        )
    ).select_related('category')[:10]

    # Buscar en videos
    videos = VideoTutorial.objects.filter(
        Q(is_active=True) & (
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query)
        )
    ).select_related('category', 'author')[:10]

    # Buscar en guías
    guides = QuickStartGuide.objects.filter(
        Q(is_active=True) & (
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(content__icontains=query)
        )
    )[:5]

    # Actualizar estadísticas de búsqueda
    search_log = HelpSearchLog.objects.filter(query=query).last()
    if search_log:
        total_results = articles.count() + faqs.count() + videos.count() + guides.count()
        search_log.results_count = total_results
        search_log.has_results = total_results > 0
        search_log.save()

    context = {
        'page_title': f'Resultados de búsqueda: "{query}"',
        'query': query,
        'articles': articles,
        'faqs': faqs,
        'videos': videos,
        'guides': guides,
        'total_results': articles.count() + faqs.count() + videos.count() + guides.count(),
    }

    return render(request, 'help/search_results.html', context)


@login_required
def submit_feedback(request, article_slug):
    """
    Enviar feedback sobre un artículo
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})

    article = get_object_or_404(HelpArticle, slug=article_slug)

    was_helpful = request.POST.get('was_helpful') == 'true'
    rating = int(request.POST.get('rating', 3))
    comment = request.POST.get('comment', '').strip()
    suggestions = request.POST.get('suggestions', '').strip()

    # Crear feedback
    feedback = HelpFeedback.objects.create(
        article=article,
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR'),
        was_helpful=was_helpful,
        rating=rating,
        comment=comment,
        improvement_suggestions=suggestions
    )

    # Actualizar contadores del artículo
    if was_helpful:
        article.helpful_count += 1
    else:
        article.not_helpful_count += 1
    article.save()

    return JsonResponse({
        'success': True,
        'message': '¡Gracias por tu feedback!'
    })


def article_feedback_stats(request, article_slug):
    """
    Obtener estadísticas de feedback de un artículo (para admins)
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'No autorizado'}, status=403)

    article = get_object_or_404(HelpArticle, slug=article_slug)

    feedback_stats = {
        'helpful_count': article.helpful_count,
        'not_helpful_count': article.not_helpful_count,
        'total_feedback': article.helpful_count + article.not_helpful_count,
        'helpful_percentage': article.get_helpful_percentage(),
        'recent_feedback': list(
            HelpFeedback.objects.filter(article=article)
            .select_related('user')
            .order_by('-created_at')[:5]
            .values('was_helpful', 'rating', 'comment', 'created_at',
                   'user__username')
        )
    }

    return JsonResponse(feedback_stats)
