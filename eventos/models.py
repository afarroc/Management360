from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


# Create your models here.

class Status(models.Model):
    status_name = models.CharField(max_length=50)
    icon = models.CharField(max_length=10, blank=True)
    active = models.BooleanField(default=True)
    color = models.CharField(max_length=30, default="white")
    
    def __str__(self):
        return self.status_name

class Project(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    done = models.BooleanField(default=False)

    def __str__(self):
        return self.title + " - " + self.project.name

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    event_status = models.ForeignKey(Status, on_delete=models.CASCADE, default=16)
    venue = models.CharField(max_length=200)
    start_time = models.DateTimeField(auto_now=True)
    end_time = models.DateTimeField(auto_now=True)
    host = models.CharField(max_length=100)
    event_category = models.CharField(max_length=50)
    max_attendees = models.IntegerField(default=0)
    ticket_price = models.DecimalField(default=0, max_digits=6, decimal_places=2)
    attendees = models.ManyToManyField(User, through='EventAttendee')

    def change_status(self, new_status):
        self.event_status = new_status
        self.updated_at = timezone.now()
        self.save()

    def save(self, *args, **kwargs):
        if self.pk is not None:
            self.updated_at = timezone.now()
        super(Event, self).save(*args, **kwargs)
        
    def __str__(self):
        return self.title + " - " + self.event_status.status_name

class EventAttendee(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    registration_time = models.DateTimeField(auto_now_add=True)

