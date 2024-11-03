# models.py

from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Room(models.Model):
    version = models.PositiveBigIntegerField(default=0)
    bumped_at = models.DateTimeField(auto_now_add=True)
    last_message = models.ForeignKey(
        'Message', related_name='last_message_rooms',
        on_delete=models.SET_NULL, null=True, blank=True,
    )
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_rooms')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms', null=True, blank=True)
    administrators = models.ManyToManyField(User, related_name='administered_rooms', blank=True)
    capacity = models.IntegerField(default=0)
    address = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='room_images/', blank=True)
    permissions = models.CharField(max_length=255, choices=[
        ('public', 'Pública'),
        ('private', 'Privada'),
        ('restricted', 'Restringida')
    ], default='public')
    comments = models.ManyToManyField(User, through='Comment', related_name='comments')
    evaluations = models.ManyToManyField(User, through='Evaluation', related_name='evaluations')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    x = models.IntegerField(default=0)  # Posición x
    y = models.IntegerField(default=0)  # Posición y
    z = models.IntegerField(default=0)  # Posición z
    longitud = models.IntegerField(default=2)  # Longitud
    anchura = models.IntegerField(default=2)  # Anchura
    altura = models.IntegerField(default=2)  # Altura
    pitch = models.IntegerField(default=0)  # Rotación x
    yaw = models.IntegerField(default=0)  # Rotación y
    roll = models.IntegerField(default=0)  # Rotación z
    type = models.CharField(max_length=10, choices=[  # Tipo de habitación
        ('INDIVIDUAL', 'Individual'),
        ('DOBLES', 'Dobles'),
        ('SUITE', 'Suite')
    ])
    beds = models.IntegerField(default=1)  # Número de camas
    bathrooms = models.IntegerField(default=1)  # Número de baños
    surface = models.IntegerField(default=10)  # Superficie en metros cuadrados
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Precio por noche
    available = models.BooleanField(default=True)  # Disponibilidad
    parent_room = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)  # Habitación contenedora

    def increment_version(self):
        self.version += 1
        self.save()
        return self.version

    def __str__(self):
        return self.name

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.room.name}"

class Evaluation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.room.name}"

class EntranceExit(models.Model):
    name = models.CharField(max_length=255)  # Nombre de la entrada/salida
    room = models.ForeignKey('Room', on_delete=models.CASCADE)  # Habitación asociada
    description = models.TextField(blank=True)
    face = models.CharField(max_length=10, choices=[  # Cara de la caja
        ('NORTE', 'Norte'),
        ('SUR', 'Sur'),
        ('ESTE', 'Este'),
        ('OESTE', 'Oeste'),
        ('ARRIBA', 'Arriba'),
        ('ABAJO', 'Abajo')
    ])
    type = models.CharField(max_length=10, choices=[  # Tipo de entrada/salida
        ('PUERTA', 'Puerta'),
        ('VENTANA', 'Ventana'),
        ('SOTANO', 'Sotano'),
        ('ATICO', 'Ático')
    ])
    enabled = models.BooleanField(default=True)  # Estado de la entrada/salida

    def __str__(self):
        return f"{self.name} ({self.room.name} - {self.face})"

class Portal(models.Model):
    name = models.CharField(max_length=255)  # Nombre del portal
    entrance = models.ForeignKey('EntranceExit', related_name='entrance', on_delete=models.CASCADE)  # Punto de entrada
    description = models.TextField(blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    exit = models.ForeignKey('EntranceExit', related_name='exit', on_delete=models.CASCADE)  # Punto de salida

    def __str__(self):
        return f"{self.name} ({self.entrance.room.name} -> {self.exit.room.name})"












class RoomMember(models.Model):
    room = models.ForeignKey(Room, related_name='memberships', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='rooms', on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('room', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.room.name}"


class Message(models.Model):
    room = models.ForeignKey(Room, related_name='messages', on_delete=models.CASCADE)
    # Note, message may have null user – we consider such messages "system". These messages
    # initiated by the backend and have no user author. We are not using such messages in
    # the example currently, but leave the opportunity to extend.
    user = models.ForeignKey(User, related_name='messages', on_delete=models.CASCADE, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Outbox(models.Model):
    method = models.TextField(default="publish")
    payload = models.JSONField()
    partition = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


# While the CDC model here is the same as Outbox it has different partition field semantics,
# also in outbox case we remove processed messages from DB, while in CDC don't. So to not
# mess up with different semantics when switching between broadcast modes of the example app
# we created two separated models here. 
class CDC(models.Model):
    method = models.TextField(default="publish")
    payload = models.JSONField()
    partition = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)