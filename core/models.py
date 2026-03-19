from django.db import models
from django.urls import reverse


class Article(models.Model):
    """Modelo para artículos o contenido del sitio."""
    title = models.CharField(
        max_length=200,
        verbose_name="Título",
        help_text="Título del artículo (máx. 200 caracteres)"
    )
    
    content = models.TextField(
        verbose_name="Contenido",
        help_text="Contenido completo del artículo"
    )
    
    excerpt = models.CharField(
        max_length=300,
        verbose_name="Extracto",
        help_text="Breve descripción (máx. 300 caracteres)",
        blank=True,
        default=""
    )
    
    publication_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de publicación"
    )
    
    is_published = models.BooleanField(
        default=True,
        verbose_name="Publicado",
        help_text="¿Está visible para los usuarios?"
    )
    
    class Meta:
        verbose_name = "Artículo"
        verbose_name_plural = "Artículos"
        ordering = ['-publication_date']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        # Usar reverse para URLs dinámicas
        # Asegúrate de tener una URL llamada 'article_detail' en tu urls.py
        return reverse('article_detail', kwargs={'pk': self.pk})
    
    def get_excerpt_display(self):
        """Devuelve el extracto o genera uno a partir del contenido."""
        if self.excerpt:
            return self.excerpt
        # Extraer las primeras 150 caracteres del contenido
        return self.content[:150] + "..." if len(self.content) > 150 else self.content