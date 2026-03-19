from django.contrib import admin
from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo Article."""
    list_display = ['title', 'publication_date', 'is_published', 'get_excerpt_display']
    list_filter = ['is_published', 'publication_date']
    search_fields = ['title', 'content', 'excerpt']
    list_editable = ['is_published']
    date_hierarchy = 'publication_date'
    readonly_fields = ['publication_date']
    
    fieldsets = (
        ('Información básica', {
            'fields': ('title', 'excerpt', 'content', 'is_published')
        }),
        ('Metadatos', {
            'fields': ('publication_date',),
            'classes': ('collapse',)
        }),
    )