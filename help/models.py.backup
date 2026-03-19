from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from courses.models import Course, Lesson, ContentBlock, CourseCategory


class HelpCategory(models.Model):
    """
    Categorías para organizar la documentación de ayuda
    """
    name = models.CharField(max_length=100, unique=True, help_text="Nombre de la categoría")
    slug = models.SlugField(unique=True, help_text="Slug para URLs")
    description = models.TextField(blank=True, help_text="Descripción de la categoría")
    icon = models.CharField(max_length=50, blank=True, help_text="Clase de icono (ej: bi-question-circle)")
    color = models.CharField(max_length=7, default='#007bff', help_text="Color en formato hex (#RRGGBB)")
    order = models.PositiveIntegerField(default=0, help_text="Orden de aparición")
    is_active = models.BooleanField(default=True, help_text="Si la categoría está activa")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoría de Ayuda"
        verbose_name_plural = "Categorías de Ayuda"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_active_articles(self):
        """Obtiene artículos activos de esta categoría"""
        return self.articles.filter(is_active=True)


class HelpArticle(models.Model):
    """
    Artículos de ayuda y documentación - pueden referenciar contenido de cursos
    """
    title = models.CharField(max_length=200, help_text="Título del artículo")
    slug = models.SlugField(unique=True, help_text="Slug para URLs")
    content = models.TextField(blank=True, help_text="Contenido del artículo en formato HTML/Markdown")
    excerpt = models.TextField(blank=True, help_text="Resumen breve del artículo")

    category = models.ForeignKey(HelpCategory, on_delete=models.CASCADE, related_name='articles')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='help_articles')

    # Referencias opcionales a objetos del sistema de cursos
    referenced_course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='help_articles',
        help_text="Curso relacionado (opcional)"
    )
    referenced_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='help_articles',
        help_text="Lección relacionada (opcional)"
    )
    referenced_content_block = models.ForeignKey(
        ContentBlock,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='help_articles',
        help_text="Bloque de contenido relacionado (opcional)"
    )

    # Metadatos
    tags = models.CharField(max_length=500, blank=True, help_text="Etiquetas separadas por comas")
    difficulty = models.CharField(max_length=20, choices=[
        ('beginner', 'Principiante'),
        ('intermediate', 'Intermedio'),
        ('advanced', 'Avanzado')
    ], default='beginner', help_text="Nivel de dificultad")

    # Estado y visibilidad
    is_active = models.BooleanField(default=True, help_text="Si el artículo está publicado")
    is_featured = models.BooleanField(default=False, help_text="Si es un artículo destacado")
    requires_auth = models.BooleanField(default=False, help_text="Si requiere autenticación para ver")

    # Estadísticas
    view_count = models.PositiveIntegerField(default=0, help_text="Número de visualizaciones")
    helpful_count = models.PositiveIntegerField(default=0, help_text="Número de votos 'útil'")
    not_helpful_count = models.PositiveIntegerField(default=0, help_text="Número de votos 'no útil'")

    # SEO
    meta_title = models.CharField(max_length=200, blank=True, help_text="Título para SEO")
    meta_description = models.TextField(blank=True, help_text="Descripción para SEO")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True, help_text="Fecha de publicación")

    class Meta:
        verbose_name = "Artículo de Ayuda"
        verbose_name_plural = "Artículos de Ayuda"
        ordering = ['-is_featured', '-published_at', '-created_at']

    def __str__(self):
        base = self.title
        if self.referenced_course:
            base += f" (Curso: {self.referenced_course.title})"
        elif self.referenced_lesson:
            base += f" (Lección: {self.referenced_lesson.title})"
        elif self.referenced_content_block:
            base += f" (Bloque: {self.referenced_content_block.title})"
        return base

    def save(self, *args, **kwargs):
        if self.is_active and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_content(self):
        """Obtiene el contenido principal, ya sea propio o del objeto referenciado"""
        if self.content:
            return self.content
        elif self.referenced_course:
            return self._get_course_content()
        elif self.referenced_lesson:
            return self._get_lesson_content()
        elif self.referenced_content_block:
            return self._get_content_block_content()
        return ""

    def _get_course_content(self):
        """Genera contenido basado en un curso"""
        course = self.referenced_course
        content = f"""
        <h2>Curso: {course.title}</h2>
        <p><strong>Descripción:</strong> {course.description}</p>
        <p><strong>Tutor:</strong> {course.tutor.get_full_name() if course.tutor.get_full_name() else course.tutor.username}</p>
        <p><strong>Nivel:</strong> {course.get_level_display()}</p>
        <p><strong>Duración:</strong> {course.duration_hours} horas</p>
        <p><strong>Precio:</strong> ${course.price}</p>
        """

        if course.modules.exists():
            content += "<h3>Módulos del curso:</h3><ul>"
            for module in course.modules.all():
                content += f"<li><strong>{module.title}</strong>: {module.description}</li>"
            content += "</ul>"

        return content

    def _get_lesson_content(self):
        """Genera contenido basado en una lección"""
        lesson = self.referenced_lesson
        content = f"""
        <h2>Lección: {lesson.title}</h2>
        <p><strong>Tipo:</strong> {lesson.get_lesson_type_display()}</p>
        <p><strong>Duración:</strong> {lesson.duration_minutes} minutos</p>
        """

        if lesson.content:
            content += f"<h3>Contenido:</h3>{lesson.content}"

        if lesson.structured_content:
            content += "<h3>Elementos de la lección:</h3><ul>"
            for element in lesson.structured_content:
                content += f"<li><strong>{element.get('type', 'text').title()}:</strong> {element.get('content', '')}</li>"
            content += "</ul>"

        return content

    def _get_content_block_content(self):
        """Genera contenido basado en un bloque de contenido"""
        block = self.referenced_content_block
        content = f"""
        <h2>Bloque de Contenido: {block.title}</h2>
        <p><strong>Tipo:</strong> {block.get_content_type_display()}</p>
        <p><strong>Autor:</strong> {block.author.get_full_name() if block.author.get_full_name() else block.author.username}</p>
        """

        if block.description:
            content += f"<p><strong>Descripción:</strong> {block.description}</p>"

        content += f"<h3>Contenido:</h3>{block.get_content()}"

        return content

    def get_helpful_percentage(self):
        """Calcula el porcentaje de votos positivos"""
        total_votes = self.helpful_count + self.not_helpful_count
        if total_votes == 0:
            return 0
        return int((self.helpful_count / total_votes) * 100)

    def get_related_articles(self, limit=5):
        """Obtiene artículos relacionados por categoría y tags"""
        related = HelpArticle.objects.filter(
            category=self.category,
            is_active=True
        ).exclude(id=self.id)[:limit]
        return related

    def increment_view_count(self):
        """Incrementa el contador de visualizaciones"""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def get_tags_list(self):
        """Devuelve las etiquetas como lista"""
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]


class FAQ(models.Model):
    """
    Preguntas Frecuentes
    """
    question = models.CharField(max_length=300, help_text="Pregunta")
    answer = models.TextField(help_text="Respuesta en formato HTML")
    category = models.ForeignKey(HelpCategory, on_delete=models.CASCADE, related_name='faqs')

    order = models.PositiveIntegerField(default=0, help_text="Orden de aparición")
    is_active = models.BooleanField(default=True, help_text="Si la FAQ está activa")

    # Estadísticas
    view_count = models.PositiveIntegerField(default=0, help_text="Número de visualizaciones")
    helpful_count = models.PositiveIntegerField(default=0, help_text="Número de votos 'útil'")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pregunta Frecuente"
        verbose_name_plural = "Preguntas Frecuentes"
        ordering = ['order', 'question']

    def __str__(self):
        return self.question


class HelpSearchLog(models.Model):
    """
    Registro de búsquedas en el sistema de ayuda
    """
    query = models.CharField(max_length=200, help_text="Término de búsqueda")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    results_count = models.PositiveIntegerField(default=0, help_text="Número de resultados encontrados")
    has_results = models.BooleanField(default=False, help_text="Si encontró resultados")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de Búsqueda"
        verbose_name_plural = "Registros de Búsqueda"
        ordering = ['-created_at']

    def __str__(self):
        return f"'{self.query}' - {self.results_count} resultados"


class HelpFeedback(models.Model):
    """
    Feedback de usuarios sobre artículos de ayuda
    """
    article = models.ForeignKey(HelpArticle, on_delete=models.CASCADE, related_name='feedback')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    was_helpful = models.BooleanField(help_text="Si el artículo fue útil")
    rating = models.PositiveIntegerField(choices=[
        (1, '1 estrella'),
        (2, '2 estrellas'),
        (3, '3 estrellas'),
        (4, '4 estrellas'),
        (5, '5 estrellas')
    ], help_text="Calificación del artículo")

    comment = models.TextField(blank=True, help_text="Comentario adicional")
    improvement_suggestions = models.TextField(blank=True, help_text="Sugerencias de mejora")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Feedback de Ayuda"
        verbose_name_plural = "Feedback de Ayuda"
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback para '{self.article.title}' - {'Útil' if self.was_helpful else 'No útil'}"


class VideoTutorial(models.Model):
    """
    Tutoriales en video - pueden referenciar lecciones con video
    """
    title = models.CharField(max_length=200, help_text="Título del tutorial")
    slug = models.SlugField(unique=True, help_text="Slug para URLs")
    description = models.TextField(help_text="Descripción del tutorial")

    video_url = models.URLField(blank=True, help_text="URL del video (YouTube, Vimeo, etc.)")
    thumbnail_url = models.URLField(blank=True, help_text="URL de la miniatura")

    category = models.ForeignKey(HelpCategory, on_delete=models.CASCADE, related_name='video_tutorials')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    # Referencia opcional a lección con video
    referenced_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='video_tutorials',
        help_text="Lección con video relacionada (opcional)"
    )

    duration = models.DurationField(null=True, blank=True, help_text="Duración del video")
    difficulty = models.CharField(max_length=20, choices=[
        ('beginner', 'Principiante'),
        ('intermediate', 'Intermedio'),
        ('advanced', 'Avanzado')
    ], default='beginner')

    tags = models.CharField(max_length=500, blank=True, help_text="Etiquetas separadas por comas")

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    # Estadísticas
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tutorial en Video"
        verbose_name_plural = "Tutoriales en Video"
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        base = self.title
        if self.referenced_lesson:
            base += f" (Lección: {self.referenced_lesson.title})"
        return base

    def get_embed_url(self):
        """Convierte URL de YouTube/Vimeo a URL embed"""
        video_url = self.video_url

        # Si no hay video_url propio pero hay lección referenciada con video
        if not video_url and self.referenced_lesson and self.referenced_lesson.video_url:
            video_url = self.referenced_lesson.video_url

        if not video_url:
            return ""

        if 'youtube.com' in video_url or 'youtu.be' in video_url:
            # Extraer ID del video de YouTube
            if 'youtube.com/watch?v=' in video_url:
                video_id = video_url.split('v=')[1].split('&')[0]
            elif 'youtu.be/' in video_url:
                video_id = video_url.split('youtu.be/')[1].split('?')[0]
            else:
                return video_url
            return f"https://www.youtube.com/embed/{video_id}"
        return video_url

    def get_tags_list(self):
        """Devuelve las etiquetas como lista"""
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]


class QuickStartGuide(models.Model):
    """
    Guías de inicio rápido para nuevos usuarios
    """
    title = models.CharField(max_length=200, help_text="Título de la guía")
    slug = models.SlugField(unique=True, help_text="Slug para URLs")
    description = models.TextField(help_text="Descripción breve")

    content = models.TextField(help_text="Contenido de la guía en formato HTML/Markdown")

    # Metadatos
    estimated_time = models.PositiveIntegerField(default=5, help_text="Tiempo estimado en minutos")
    target_audience = models.CharField(max_length=100, choices=[
        ('new_users', 'Nuevos usuarios'),
        ('intermediate', 'Usuarios intermedios'),
        ('power_users', 'Usuarios avanzados'),
        ('administrators', 'Administradores')
    ], default='new_users')

    prerequisites = models.TextField(blank=True, help_text="Prerrequisitos para completar la guía")

    order = models.PositiveIntegerField(default=0, help_text="Orden en la secuencia de guías")
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    # Estadísticas
    completion_count = models.PositiveIntegerField(default=0, help_text="Número de veces completada")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Guía de Inicio Rápido"
        verbose_name_plural = "Guías de Inicio Rápido"
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    def mark_completed(self, user=None):
        """Marca la guía como completada por un usuario"""
        self.completion_count += 1
        self.save(update_fields=['completion_count'])

        # Aquí se podría crear un registro de progreso del usuario
        # UserGuideProgress.objects.create(user=user, guide=self, completed=True)
