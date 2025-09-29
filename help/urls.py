from django.urls import path
from . import views

app_name = 'help'

urlpatterns = [
    # Página principal
    path('', views.help_home, name='help_home'),

    # Categorías
    path('categories/', views.category_list, name='category_list'),
    path('categories/<slug:slug>/', views.category_detail, name='category_detail'),

    # Artículos
    path('articles/<slug:slug>/', views.article_detail, name='article_detail'),

    # Preguntas frecuentes
    path('faq/', views.faq_list, name='faq_list'),

    # Tutoriales en video
    path('videos/', views.video_tutorials, name='video_tutorials'),

    # Guías de inicio rápido
    path('quick-start/', views.quick_start, name='quick_start'),

    # Búsqueda
    path('search/', views.search_help, name='search'),

    # Feedback y estadísticas (requiere autenticación)
    path('articles/<slug:article_slug>/feedback/', views.submit_feedback, name='submit_feedback'),
    path('articles/<slug:article_slug>/feedback-stats/', views.article_feedback_stats, name='article_feedback_stats'),
]