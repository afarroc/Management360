from django.db import models
from django.contrib.auth.models import User

class PlayerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='player_profile')
    current_room = models.ForeignKey('Room', on_delete=models.SET_NULL, null=True, blank=True)
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    energy = models.IntegerField(default=100)
    productivity = models.IntegerField(default=50)
    social = models.IntegerField(default=50)
    last_interaction = models.DateTimeField(auto_now=True)
    state = models.CharField(max_length=20, choices=[
        ('WORKING', 'Trabajando'),
        ('RESTING', 'Descansando'),
        ('SOCIALIZING', 'Socializando'),
        ('IDLE', 'Inactivo')
    ], default='IDLE')
    skills = models.JSONField(default=list)  # Ej: ["programming", "design"]
    last_state_change = models.DateTimeField(auto_now=True)
    
    def move_to_room(self, direction):
        current_room = self.current_room
        entrance = current_room.entrances.filter(face=direction.upper(), enabled=True).first()
        
        if not entrance or not entrance.connection:
            return False  # No hay conexión en esa dirección
        
        connection = entrance.connection
        if connection.bidirectional or connection.from_room == current_room:
            self.current_room = connection.to_room
            self.position_x, self.position_y = self.calculate_new_position(direction)
            self.save()
            return True
        return False

    def calculate_new_position(self, direction):
        # Lógica para posicionar al jugador en la entrada correspondiente de la nueva habitación
        if direction == 'NORTH':
            return self.position_x, 0
        elif direction == 'SOUTH':
            return self.position_x, self.current_room.width
        # ... otras direcciones ...
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    

class RoomManager(models.Manager):
    pass

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
        ('public', 'Public'),
        ('private', 'Private'),
        ('restricted', 'Restricted')
    ], default='public')
    comments = models.ManyToManyField(User, through='Comment', related_name='comments')
    evaluations = models.ManyToManyField(User, through='Evaluation', related_name='evaluations')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    z = models.IntegerField(default=0)
    length = models.IntegerField(default=30)
    width = models.IntegerField(default=30)
    height = models.IntegerField(default=10)
    pitch = models.IntegerField(default=0)
    yaw = models.IntegerField(default=0)
    roll = models.IntegerField(default=0)
    room_type = models.CharField(max_length=20, choices=[
        ('OFFICE', 'Office'),
        ('MEETING', 'Meeting Room'),
        ('LOUNGE', 'Lounge'),
        ('KITCHEN', 'Kitchen'),
        ('BATHROOM', 'Bathroom'),
        ('SPECIAL', 'Special Area')
    ], default='OFFICE')
    connections = models.ManyToManyField(
        'self',
        through='RoomConnection',
        symmetrical=False,
        related_name='connected_rooms',  # Ensure unique related_name
    )
    parent_room = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='child_of_rooms',  # Ensure unique related_name
    )
    portals = models.ManyToManyField('Portal', related_name='rooms', blank=True)  # Define the relationship
    objects = RoomManager()  # Define a custom manager to avoid conflicts

    def increment_version(self):
        self.version += 1
        self.save()
        return self.version

    def get_image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return None  # Return None if no file is associated

    def __str__(self):
        return self.name

class RoomConnection(models.Model):
    from_room = models.ForeignKey(Room, related_name='from_connections', on_delete=models.CASCADE)
    to_room = models.ForeignKey(Room, related_name='to_connections', on_delete=models.CASCADE)
    entrance = models.ForeignKey('EntranceExit', related_name='room_connections', on_delete=models.CASCADE)
    bidirectional = models.BooleanField(default=True)
    energy_cost = models.IntegerField(default=0)

    class Meta:
        unique_together = ('from_room', 'to_room', 'entrance')

    def __str__(self):
        return f"{self.from_room.name} -> {self.to_room.name} via {self.entrance.name}"

class RoomObject(models.Model):
    name = models.CharField(max_length=100)
    room = models.ForeignKey(Room, related_name='room_objects', on_delete=models.CASCADE)  # Updated related_name
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    object_type = models.CharField(max_length=50, choices=[
        ('WORK', 'Workstation'),
        ('SOCIAL', 'Social Area'),
        ('REST', 'Rest Zone'),
        ('DOOR', 'Door'),
        ('EQUIPMENT', 'Equipment')
    ])
    effect = models.JSONField(default=dict)
    interaction_cooldown = models.IntegerField(default=60)

    def interact(self, player):
        if self.object_type == 'WORK':
            player.state = 'WORKING'
            player.productivity += 10
        elif self.object_type == 'SOCIAL':
            player.state = 'SOCIALIZING'
            player.social += 5
        player.save()
        return {"status": player.state, "energy": player.energy}                
    
    def __str__(self):
        return f"{self.name} ({self.get_object_type_display()}) in {self.room.name}"


class EntranceExit(models.Model):
    name = models.CharField(max_length=255)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='entrance_exits')
    description = models.TextField(blank=True)
    face = models.CharField(max_length=10, choices=[
        ('NORTH', 'North'),
        ('SOUTH', 'South'),
        ('EAST', 'East'),
        ('WEST', 'West'),
        ('UP', 'Up'),
        ('DOWN', 'Down')
    ])
    position_x = models.IntegerField(null=True, blank=True)
    position_y = models.IntegerField(null=True, blank=True)
    enabled = models.BooleanField(default=True)
    connection = models.OneToOneField(RoomConnection, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.position_x is None or self.position_y is None:
            self.assign_default_position()
        super().save(*args, **kwargs)

    def assign_default_position(self):
        if self.face == 'NORTH':
            self.position_x = self.room.length // 2
            self.position_y = self.room.width
        elif self.face == 'SOUTH':
            self.position_x = self.room.length // 2
            self.position_y = 0
        elif self.face == 'EAST':
            self.position_x = self.room.length
            self.position_y = self.room.width // 2
        elif self.face == 'WEST':
            self.position_x = 0
            self.position_y = self.room.width // 2
        else:
            self.position_x = self.room.length // 2
            self.position_y = self.room.width // 2

    def __str__(self):
        return f"{self.name} ({self.room.name} - {self.face})"


class Portal(models.Model):
    name = models.CharField(max_length=255)
    entrance = models.ForeignKey(EntranceExit, related_name='portal_entrance', on_delete=models.CASCADE)
    exit = models.ForeignKey(EntranceExit, related_name='portal_exit', on_delete=models.CASCADE)
    energy_cost = models.IntegerField(default=10)
    cooldown = models.IntegerField(default=300)
    last_used = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.entrance.room.name} ↔ {self.exit.room.name})"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Evaluation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class RoomMember(models.Model):
    room = models.ForeignKey(Room, related_name='members', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='room_memberships', on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('room', 'user')


class Message(models.Model):
    room = models.ForeignKey(Room, related_name='messages', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='messages', on_delete=models.CASCADE, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Outbox(models.Model):
    method = models.TextField(default="publish")
    payload = models.JSONField()
    partition = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class CDC(models.Model):
    method = models.TextField(default="publish")
    payload = models.JSONField()
    partition = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
