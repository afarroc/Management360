import os
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.utils import timezone

# ======================
# HELPER FUNCTIONS
# ======================
def get_upload_path(instance, filename):
    """Dynamic upload path for files based on extension"""
    ext = filename.split('.')[-1].lower()
    path = f'documents/{ext}/' if ext in ['pdf', 'docx', 'ppt'] else f'images/{ext}/'
    return os.path.join(path, filename)

# ======================
# CHOICES
# ======================
class RoleChoices(models.TextChoices):
    SUPERVISOR = 'SU', 'Supervisor'
    EVENT_MANAGER = 'GE', 'Gestor de Eventos'
    ADMIN = 'AD', 'Administrador'
    STANDARD_USER = 'US', 'Usuario Estándar'

# ======================
# MAIN MODELS
# ======================
class Curriculum(models.Model):
    # User relation
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='cv'
    )
    
    # Personal information
    full_name = models.CharField(max_length=100)
    profession = models.CharField(max_length=100)
    bio = models.TextField()
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        null=True, 
        blank=True
    )
    
    # Contact information
    location = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(max_length=100, blank=True)
    
    # Social media
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    
    # Professional information
    role = models.CharField(
        max_length=2, 
        choices=RoleChoices.choices, 
        default=RoleChoices.STANDARD_USER
    )
    company = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Curricula'

    def __str__(self):
        return f"CV de {self.user.username} ({self.full_name})"

# ======================
# RELATED MODELS
# ======================
class Experience(models.Model):
    cv = models.ForeignKey(
        Curriculum, 
        on_delete=models.CASCADE, 
        related_name='experiences'
    )
    job_title = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField()

    class Meta:
        ordering = ['-start_date']
        verbose_name_plural = 'Experiences'

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"

class Education(models.Model):
    cv = models.ForeignKey(
        Curriculum, 
        on_delete=models.CASCADE, 
        related_name='educations'
    )
    institution_name = models.CharField(max_length=100)
    degree = models.CharField(max_length=100)
    field_of_study = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name_plural = 'Education'

    def __str__(self):
        return f"{self.degree} at {self.institution_name}"

class Skill(models.Model):
    PROFICIENCY_CHOICES = [
        ('B', 'Básico'),
        ('I', 'Intermedio'),
        ('A', 'Avanzado'),
    ]
    
    cv = models.ForeignKey(
        Curriculum, 
        on_delete=models.CASCADE, 
        related_name='skills_list'
    )
    skill_name = models.CharField(max_length=100)
    proficiency_level = models.CharField(
        max_length=1,
        choices=PROFICIENCY_CHOICES,
        default='B'
    )

    class Meta:
        ordering = ['skill_name']
        verbose_name_plural = 'Skills'

    def __str__(self):
        return f"{self.skill_name} ({self.get_proficiency_level_display()})"
# ======================
# FILE MODELS
# ======================
class Document(models.Model):
    cv = models.ForeignKey(
        Curriculum, 
        on_delete=models.CASCADE, 
        related_name='documents'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    upload = models.FileField(
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(['pdf', 'docx', 'ppt'])]
    )

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name_plural = 'Documents'

class Image(models.Model):
    cv = models.ForeignKey(
        Curriculum, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    upload = models.FileField(
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'bmp'])]
    )

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name_plural = 'Images'

class Database(models.Model):
    cv = models.ForeignKey(
        Curriculum, 
        on_delete=models.CASCADE, 
        related_name='databases'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    upload = models.FileField(
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(['csv', 'txt', 'xlsx', 'xlsm'])]
    )

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name_plural = 'Databases'