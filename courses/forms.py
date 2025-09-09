from django import forms
from .models import Course, Module, Lesson, Review, CourseCategory

class CourseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError("El precio no puede ser negativo.")
        return price

    def clean(self):
        cleaned_data = super().clean()
        user = self.user

        # Validar que el usuario tenga un perfil de CV si está creando un curso
        if user and not hasattr(user, 'cv'):
            raise forms.ValidationError("Debes tener un perfil de tutor (CV) para crear cursos.")

        return cleaned_data

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

class CategoryForm(forms.ModelForm):
    class Meta:
        model = CourseCategory
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }