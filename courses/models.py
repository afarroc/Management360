import os
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.text import slugify
from cv.models import Curriculum  # Importamos el modelo Curriculum desde la app cv

# ======================
# CHOICES
# ======================
class CourseLevelChoices(models.TextChoices):
    BEGINNER = 'beginner', 'Principiante'
    INTERMEDIATE = 'intermediate', 'Intermedio'
    ADVANCED = 'advanced', 'Avanzado'

class EnrollmentStatusChoices(models.TextChoices):
    ACTIVE = 'active', 'Activo'
    COMPLETED = 'completed', 'Completado'
    DROPPED = 'dropped', 'Abandonado'

class LessonTypeChoices(models.TextChoices):
    VIDEO = 'video', 'Video'
    TEXT = 'text', 'Texto'
    QUIZ = 'quiz', 'Quiz'
    ASSIGNMENT = 'assignment', 'Tarea'

# ======================
# MAIN MODELS
# ======================
class CourseCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    
    class Meta:
        verbose_name_plural = 'Course Categories'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    
    # Relación con el tutor (debe tener un Curriculum asociado)
    tutor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='courses_taught',
        limit_choices_to={'cv__isnull': False}  # Solo usuarios con CV
    )
    
    # Información del curso
    category = models.ForeignKey(
        CourseCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='courses'
    )
    level = models.CharField(
        max_length=12,
        choices=CourseLevelChoices.choices,
        default=CourseLevelChoices.BEGINNER
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    duration_hours = models.PositiveIntegerField(help_text="Duración total en horas")
    thumbnail = models.ImageField(
        upload_to='courses/thumbnails/', 
        null=True, 
        blank=True
    )
    
    # Metadata
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    students_count = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    
    # Fechas
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
    
    def get_tutor_profile(self):
        """Obtiene el perfil (Curriculum) del tutor"""
        return getattr(self.tutor, 'cv', None)

class Module(models.Model):
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='modules'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Lesson(models.Model):
    module = models.ForeignKey(
        Module, 
        on_delete=models.CASCADE, 
        related_name='lessons'
    )
    title = models.CharField(max_length=200)
    lesson_type = models.CharField(
        max_length=10,
        choices=LessonTypeChoices.choices,
        default=LessonTypeChoices.VIDEO
    )
    content = models.TextField(blank=True)  # Para lecciones de texto
    video_url = models.URLField(blank=True)  # Para lecciones de video
    duration_minutes = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)
    is_free = models.BooleanField(default=False)  # Lección gratuita para preview
    
    # Para quizzes
    quiz_questions = models.JSONField(default=list, blank=True)  # Almacena preguntas y respuestas
    
    # Para assignments
    assignment_instructions = models.TextField(blank=True)
    assignment_file = models.FileField(
        upload_to='courses/assignments/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['pdf', 'docx', 'txt'])]
    )
    assignment_due_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"

class Enrollment(models.Model):
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='course_enrollments'
    )
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='enrollments'
    )
    status = models.CharField(
        max_length=10,
        choices=EnrollmentStatusChoices.choices,
        default=EnrollmentStatusChoices.ACTIVE
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title}"
    
    def save(self, *args, **kwargs):
        # Actualizar contador de estudiantes cuando se crea una nueva inscripción
        if self._state.adding and self.status == EnrollmentStatusChoices.ACTIVE:
            self.course.students_count += 1
            self.course.save()
        super().save(*args, **kwargs)

class Progress(models.Model):
    enrollment = models.ForeignKey(
        Enrollment, 
        on_delete=models.CASCADE, 
        related_name='progress'
    )
    lesson = models.ForeignKey(
        Lesson, 
        on_delete=models.CASCADE, 
        related_name='progress'
    )
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    class Meta:
        unique_together = ['enrollment', 'lesson']
    
    def __str__(self):
        return f"{self.enrollment.student.username} - {self.lesson.title}"

class Review(models.Model):
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='course_reviews'
    )
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='reviews'
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title} - {self.rating}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualizar la calificación promedio del curso
        reviews = self.course.reviews.all()
        if reviews:
            total_rating = sum(review.rating for review in reviews)
            self.course.average_rating = total_rating / reviews.count()
            self.course.save()

# ======================
# SIGNALS
# ======================
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=Review)
def update_course_rating(sender, instance, **kwargs):
    """Actualiza la calificación promedio del curso cuando se crea/actualiza una reseña"""
    course = instance.course
    reviews = course.reviews.all()
    if reviews:
        total_rating = sum(review.rating for review in reviews)
        course.average_rating = total_rating / reviews.count()
    else:
        course.average_rating = 0
    course.save()

@receiver(post_delete, sender=Review)
def update_course_rating_on_delete(sender, instance, **kwargs):
    """Actualiza la calificación promedio cuando se elimina una reseña"""
    course = instance.course
    reviews = course.reviews.all()
    if reviews:
        total_rating = sum(review.rating for review in reviews)
        course.average_rating = total_rating / reviews.count()
    else:
        course.average_rating = 0
    course.save()

@receiver(post_save, sender=Enrollment)
def update_student_count(sender, instance, **kwargs):
    """Actualiza el contador de estudiantes cuando cambia el estado de la inscripción"""
    if instance.status == EnrollmentStatusChoices.ACTIVE and instance._state.adding:
        instance.course.students_count += 1
        instance.course.save()
    elif instance.status in [EnrollmentStatusChoices.COMPLETED, EnrollmentStatusChoices.DROPPED]:
        # No reducimos el count para mantener métricas históricas
        pass