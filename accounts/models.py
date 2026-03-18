from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Modelo de usuario personalizado para Management360"""
    
    # Teléfono
    phone = models.CharField(
        "Teléfono",
        max_length=20,
        blank=True,
        null=True
    )
    
    # Avatar
    avatar = models.ImageField(
        "Avatar",
        upload_to='avatars/',
        blank=True,
        null=True
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
    
    def __str__(self):
        return self.get_full_name() or self.username
