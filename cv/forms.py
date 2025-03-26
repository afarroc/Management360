# cv/forms.py
from django import forms
from .models import Curriculum, Experience, Education, Skill

class CurriculumForm(forms.ModelForm):
    class Meta:
        model = Curriculum
        fields = [
            'full_name', 'profession', 'bio', 'skills', 'experience', 'education',
            'location', 'profile_picture', 'linkedin_url', 'github_url', 'twitter_url',
            'facebook_url', 'instagram_url', 'role', 'company', 'job_title', 'country',
            'address', 'phone', 'email'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'skills': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Separar habilidades con comas'}),
            'experience': forms.Textarea(attrs={'rows': 5}),
            'education': forms.Textarea(attrs={'rows': 3}),
            'address': forms.TextInput(attrs={'placeholder': 'Calle, número, ciudad'}),
            'phone': forms.TextInput(attrs={'placeholder': '+34 600 000 000'}),
        }
        labels = {
            'full_name': 'Nombre completo',
            'profession': 'Profesión',
            'bio': 'Biografía profesional'
        }

class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ['job_title', 'company_name', 'start_date', 'end_date', 'description']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'job_title': 'Puesto de trabajo',
            'company_name': 'Nombre de la empresa',
            'start_date': 'Fecha de inicio',
            'end_date': 'Fecha de finalización',
            'description': 'Descripción de funciones'
        }

class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['institution_name', 'degree', 'field_of_study', 'start_date', 'end_date', 'description']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'degree': 'Título obtenido',
            'field_of_study': 'Área de estudio'
        }

class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['skill_name', 'proficiency_level']
        widgets = {
            'skill_name': forms.TextInput(attrs={'placeholder': 'Ej: Python, Django'}),
            'proficiency_level': forms.Select(choices=[
                ('', 'Seleccione nivel'),
                ('B', 'Básico'),
                ('I', 'Intermedio'),
                ('A', 'Avanzado')
            ])
        }
        labels = {
            'skill_name': 'Habilidad técnica',
            'proficiency_level': 'Nivel de dominio'
        }