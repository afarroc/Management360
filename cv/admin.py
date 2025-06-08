from django.contrib import admin
from .models import Curriculum, Experience, Education, Skill, Document, Image, Database

# ======================
# INLINE ADMIN CLASSES
# ======================
class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 1
    fields = ('job_title', 'company_name', 'start_date', 'end_date', 'description')
    ordering = ('-start_date',)

class EducationInline(admin.TabularInline):
    model = Education
    extra = 1
    fields = ('institution_name', 'degree', 'field_of_study', 'start_date', 'end_date')
    ordering = ('-start_date',)

class SkillInline(admin.TabularInline):
    model = Skill
    extra = 1
    fields = ('skill_name', 'proficiency_level')

# ======================
# MODEL ADMIN CLASSES
# ======================
@admin.register(Curriculum)
class CurriculumAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'profession', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('user__username', 'full_name', 'profession', 'company')
    ordering = ('-created_at',)
    inlines = [ExperienceInline, EducationInline, SkillInline]
    
    fieldsets = (
        ('User Relation', {
            'fields': ('user',),
            'classes': ('collapse',)
        }),
        ('Personal Information', {
            'fields': (
                'full_name', 
                'profession', 
                'bio', 
                'profile_picture'
            )
        }),
        ('Contact Information', {
            'fields': (
                'location', 
                'phone', 
                'email', 
                'address',
                'country'
            )
        }),
        ('Social Media', {
            'fields': (
                'linkedin_url', 
                'github_url', 
                'twitter_url',
                'facebook_url',
                'instagram_url'
            ),
            'classes': ('collapse',)
        }),
        ('Professional Information', {
            'fields': (
                'role', 
                'company', 
                'job_title'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('cv', 'uploaded_at', 'upload')
    list_filter = ('uploaded_at',)
    search_fields = ('cv__user__username', 'cv__full_name')
    date_hierarchy = 'uploaded_at'
    readonly_fields = ('uploaded_at',)

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('cv', 'uploaded_at', 'upload')
    list_filter = ('uploaded_at',)
    search_fields = ('cv__user__username', 'cv__full_name')
    date_hierarchy = 'uploaded_at'
    readonly_fields = ('uploaded_at',)

@admin.register(Database)
class DatabaseAdmin(admin.ModelAdmin):
    list_display = ('cv', 'uploaded_at', 'upload')
    list_filter = ('uploaded_at',)
    search_fields = ('cv__user__username', 'cv__full_name')
    date_hierarchy = 'uploaded_at'
    readonly_fields = ('uploaded_at',)