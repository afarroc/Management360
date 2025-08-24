from django import forms
from .models import Course, Module, Lesson, Review

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'title', 'category', 'level', 'description', 'short_description',
            'price', 'duration_hours', 'thumbnail', 'is_published', 'is_featured'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'short_description': forms.Textarea(attrs={'rows': 2}),
        }

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'description', 'order']

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            'title', 'lesson_type', 'content', 'video_url', 
            'duration_minutes', 'order', 'is_free',
            'quiz_questions', 'assignment_instructions', 
            'assignment_file', 'assignment_due_date'
        ]
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
            'assignment_instructions': forms.Textarea(attrs={'rows': 4}),
            'quiz_questions': forms.Textarea(attrs={'rows': 4}),
            'assignment_due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }