from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.utils import timezone
import os
from decimal import Decimal

class Curriculum(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cv')
    full_name = models.CharField(max_length=100)
    profession = models.CharField(max_length=100)
    bio = models.TextField()
    skills = models.TextField(help_text="Separate skills with commas")
    experience = models.TextField()
    education = models.TextField()
    
    # Campos adicionales del Profile
    location = models.CharField(max_length=30, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    
    ROLE_CHOICES = [
        ('SU', 'Supervisor'),
        ('GE', 'Gestor de Eventos'),
        ('AD', 'Administrador'),
        ('US', 'Usuario Estándar'),
    ]
    role = models.CharField(max_length=2, choices=ROLE_CHOICES, default='US')
    company = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"CV de {self.user.username}"

class Experience(models.Model):
    cv = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='experiences')
    job_title = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField()

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"

class Education(models.Model):
    cv = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='educations')
    institution_name = models.CharField(max_length=100)
    degree = models.CharField(max_length=100)
    field_of_study = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.degree} in {self.field_of_study} from {self.institution_name}"

class Skill(models.Model):
    cv = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='skills_list')
    skill_name = models.CharField(max_length=100)
    proficiency_level = models.CharField(max_length=50)

    def __str__(self):
        return self.skill_name

def get_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    path = f'documents/{ext}/' if ext in ['pdf', 'docx', 'ppt'] else f'images/{ext}/'
    return os.path.join(path, filename)

class Document(models.Model):
    cv = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    upload = models.FileField(upload_to=get_upload_path, validators=[FileExtensionValidator(['pdf', 'docx', 'ppt'])])

class Image(models.Model):
    cv = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='images')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    upload = models.FileField(upload_to=get_upload_path, validators=[FileExtensionValidator(['jpg', 'bmp', 'png'])])

class Database(models.Model):
    cv = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='databases')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    upload = models.FileField(upload_to=get_upload_path, validators=[FileExtensionValidator(['csv', 'txt', 'xlsx', 'xlsm'])])