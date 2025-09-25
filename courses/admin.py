from django.contrib import admin
from .models import CourseCategory, Course, Module, Lesson, Enrollment, Progress, Review, LessonAttachment, ContentBlock

@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

class ModuleInline(admin.StackedInline):
    model = Module
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'tutor', 'category', 'level', 'price', 'is_published', 'is_featured', 'students_count', 'average_rating']
    list_filter = ['is_published', 'is_featured', 'category', 'level', 'created_at']
    search_fields = ['title', 'description', 'tutor__username']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['students_count', 'average_rating', 'created_at', 'updated_at', 'published_at']
    inlines = [ModuleInline]
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'slug', 'description', 'short_description', 'category', 'level')
        }),
        ('Multimedia', {
            'fields': ('thumbnail',)
        }),
        ('Detalles', {
            'fields': ('tutor', 'price', 'duration_hours')
        }),
        ('Estado', {
            'fields': ('is_published', 'is_featured', 'published_at')
        }),
        ('Métricas', {
            'fields': ('students_count', 'average_rating', 'created_at', 'updated_at')
        }),
    )

class LessonAttachmentInline(admin.TabularInline):
    model = LessonAttachment
    extra = 0
    fields = ['title', 'file', 'order']
    readonly_fields = ['file_type', 'file_size', 'uploaded_at']
    ordering = ['order', 'uploaded_at']

class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 1
    fields = ['title', 'lesson_type', 'order', 'is_free', 'duration_minutes']

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order']
    list_filter = ['course']
    search_fields = ['title', 'course__title']
    inlines = [LessonInline]

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'lesson_type', 'order', 'is_free', 'duration_minutes', 'has_structured_content', 'attachments_count']
    list_filter = ['lesson_type', 'is_free', 'module__course']
    search_fields = ['title', 'module__title', 'content']
    readonly_fields = ['structured_content_count']
    inlines = [LessonAttachmentInline]

    fieldsets = (
        ('Información Básica', {
            'fields': ('module', 'title', 'lesson_type', 'order', 'is_free', 'duration_minutes')
        }),
        ('Contenido Simple', {
            'fields': ('content', 'video_url'),
            'classes': ('collapse',)
        }),
        ('Contenido Estructurado', {
            'fields': ('structured_content', 'structured_content_count'),
            'description': 'Contenido estructurado en formato JSON. Ejemplo: [{"type": "heading", "title": "Título"}, {"type": "list", "items": ["Item 1", "Item 2"]}]',
            'classes': ('collapse',)
        }),
        ('Quiz', {
            'fields': ('quiz_questions',),
            'classes': ('collapse',)
        }),
        ('Tarea', {
            'fields': ('assignment_instructions', 'assignment_file', 'assignment_due_date'),
            'classes': ('collapse',)
        }),
    )

    def has_structured_content(self, obj):
        """Muestra si la lección tiene contenido estructurado"""
        return bool(obj.structured_content)
    has_structured_content.boolean = True
    has_structured_content.short_description = 'Contenido Estructurado'

    def structured_content_count(self, obj):
        """Muestra el número de elementos en el contenido estructurado"""
        if obj.structured_content:
            return len(obj.structured_content)
        return 0
    structured_content_count.short_description = 'Elementos Estructurados'

    def attachments_count(self, obj):
        """Muestra el número de archivos adjuntos"""
        return obj.attachments.count()
    attachments_count.short_description = 'Archivos Adjuntos'

    def get_queryset(self, request):
        """Optimizar consultas incluyendo contenido estructurado"""
        return super().get_queryset(request).select_related('module__course')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'status', 'enrolled_at', 'completed_at']
    list_filter = ['status', 'enrolled_at', 'course']
    search_fields = ['student__username', 'course__title']
    readonly_fields = ['enrolled_at']

@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'lesson', 'completed', 'completed_at', 'score']
    list_filter = ['completed', 'lesson__module__course']
    search_fields = ['enrollment__student__username', 'lesson__title']
    readonly_fields = ['completed_at']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'rating', 'created_at']
    list_filter = ['rating', 'created_at', 'course']
    search_fields = ['student__username', 'course__title']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(LessonAttachment)
class LessonAttachmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'file_type', 'get_file_size_display', 'uploaded_at', 'order']
    list_filter = ['file_type', 'uploaded_at', 'lesson__module__course']
    search_fields = ['title', 'lesson__title', 'lesson__module__course__title']
    readonly_fields = ['file_type', 'file_size', 'uploaded_at']
    ordering = ['-uploaded_at']

    fieldsets = (
        ('Información del Archivo', {
            'fields': ('lesson', 'title', 'file', 'order')
        }),
        ('Metadatos', {
            'fields': ('file_type', 'file_size', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )

    def get_file_size_display(self, obj):
        return obj.get_file_size_display()
    get_file_size_display.short_description = 'Tamaño del Archivo'
@admin.register(ContentBlock)
class ContentBlockAdmin(admin.ModelAdmin):
    list_display = ['title', 'content_type', 'author', 'category', 'is_public', 'is_featured', 'usage_count', 'created_at']
    list_filter = ['content_type', 'is_public', 'is_featured', 'author', 'category', 'created_at']
    search_fields = ['title', 'description', 'tags', 'author__username']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    ordering = ['-updated_at']

    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'slug', 'description', 'content_type', 'category', 'tags')
        }),
        ('Contenido', {
            'fields': ('html_content', 'json_content', 'markdown_content'),
            'classes': ('collapse',)
        }),
        ('Configuración', {
            'fields': ('author', 'is_public', 'is_featured')
        }),
        ('Estadísticas', {
            'fields': ('usage_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_tags_display(self, obj):
        """Muestra las etiquetas como lista legible"""
        tags = obj.get_tags_list()
        return ', '.join(tags) if tags else 'Sin etiquetas'
    get_tags_display.short_description = 'Etiquetas'

    def get_queryset(self, request):
        """Optimizar consultas incluyendo autor"""
        return super().get_queryset(request).select_related('author')