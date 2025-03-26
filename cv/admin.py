from django.contrib import admin
from .models import Curriculum, Experience, Education, Skill, Document, Image, Database

class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 1

class EducationInline(admin.TabularInline):
    model = Education
    extra = 1

class SkillInline(admin.TabularInline):
    model = Skill
    extra = 1

@admin.register(Curriculum)
class CurriculumAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'profession', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'full_name', 'profession')
    inlines = [ExperienceInline, EducationInline, SkillInline]
    fieldsets = (
        (None, {'fields': ('user',)}),
        ('Personal Info', {'fields': ('full_name', 'profession', 'bio', 'profile_picture')}),
        ('Contact Info', {'fields': ('location', 'phone', 'email', 'address')}),
        ('Social Media', {'fields': ('linkedin_url', 'github_url', 'twitter_url')}),
        ('Professional Info', {'fields': ('role', 'company', 'job_title')}),
    )

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('cv', 'uploaded_at', 'upload')
    list_filter = ('uploaded_at',)
    search_fields = ('cv__user__username',)

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('cv', 'uploaded_at', 'upload')
    list_filter = ('uploaded_at',)
    search_fields = ('cv__user__username',)

@admin.register(Database)
class DatabaseAdmin(admin.ModelAdmin):
    list_display = ('cv', 'uploaded_at', 'upload')
    list_filter = ('uploaded_at',)
    search_fields = ('cv__user__username',)