from django.contrib import admin
from .models import Project, Task , Event, Status, EventAttendee, Document, TaskProgram, Profile

# Register your models here.
admin.site.register(Project)
admin.site.register(Task)
admin.site.register(Event)
admin.site.register(Status)
admin.site.register(EventAttendee)
admin.site.register(Document)
admin.site.register(TaskProgram)
admin.site.register(Profile)