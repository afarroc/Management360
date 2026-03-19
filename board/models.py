from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
from django.utils import timezone
from django.urls import reverse

class Board(models.Model):
    LAYOUT_CHOICES = [
        ('masonry', 'Masonry Grid'),
        ('grid', 'Grid Uniforme'),
        ('free', 'Posición Libre'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='boards')
    collaborators = models.ManyToManyField(User, blank=True, related_name='shared_boards')
    cover_image = models.ImageField(
        upload_to='board/covers/',
        blank=True, 
        null=True,
        # 👈 SIN storage - usa el default
    )
    layout = models.CharField(max_length=20, choices=LAYOUT_CHOICES, default='masonry')
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['owner', '-updated_at']),
            models.Index(fields=['is_public']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('board:detail', args=[self.pk])

class Card(models.Model):
    CARD_TYPES = [
        ('note', '📝 Nota'),
        ('image', '🖼️ Imagen'),
        ('link', '🔗 Enlace'),
        ('task', '✅ Tarea'),
        ('video', '🎬 Video'),
    ]
    
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='cards')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    card_type = models.CharField(max_length=10, choices=CARD_TYPES, default='note')
    
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField(blank=True)
    url = models.URLField(blank=True)
    
    image = models.ImageField(
        upload_to='board/cards/',
        blank=True, 
        null=True,
        # 👈 SIN storage - usa el default
    )
    
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    width = models.IntegerField(default=1)
    height = models.IntegerField(default=1)
    
    color = models.CharField(max_length=20, default='white')
    is_pinned = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['board', '-created_at']),
            models.Index(fields=['board', 'card_type']),
        ]
    
    def __str__(self):
        return self.title or f"{self.get_card_type_display()} - {self.created_at}"

class Activity(models.Model):
    ACTION_CHOICES = [
        ('created', 'creó'),
        ('updated', 'actualizó'),
        ('deleted', 'eliminó'),
        ('moved', 'movió'),
        ('pinned', 'fijó'),
    ]
    
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    target = models.CharField(max_length=100)
    target_id = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['board', '-timestamp']),
        ]