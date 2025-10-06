from django import forms
from .models import Curriculum, Experience, Education, Skill, Language, Certification, Document, Image, Database
from django.core.validators import FileExtensionValidator

class BaseModelForm(forms.ModelForm):
    """Formulario base con estilos comunes"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class CurriculumForm(BaseModelForm):
    class Meta:
        model = Curriculum
        fields = '__all__'
        exclude = ['user', 'created_at', 'updated_at']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'address': forms.TextInput(attrs={'placeholder': 'Calle, número, ciudad'}),
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ExperienceForm(BaseModelForm):
    class Meta:
        model = Experience
        fields = '__all__'
        exclude = ['cv']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class EducationForm(BaseModelForm):
    class Meta:
        model = Education
        fields = '__all__'
        exclude = ['cv']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class SkillForm(BaseModelForm):
    class Meta:
        model = Skill
        fields = '__all__'
        exclude = ['cv']
        widgets = {
            'proficiency_level': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proficiency_level'].choices = [
            ('', 'Seleccione nivel'),
            ('B', 'Básico'),
            ('I', 'Intermedio'),
            ('A', 'Avanzado')
        ]

class LanguageForm(BaseModelForm):
    class Meta:
        model = Language
        fields = '__all__'
        exclude = ['cv']
        widgets = {
            'proficiency_level': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proficiency_level'].choices = [
            ('', 'Seleccione nivel'),
            ('B', 'Básico'),
            ('C', 'Conversacional'),
            ('F', 'Fluido'),
            ('N', 'Nativo')
        ]

class CertificationForm(BaseModelForm):
    class Meta:
        model = Certification
        fields = '__all__'
        exclude = ['cv']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
        }

class FileUploadForm(forms.Form):
    """Formulario base para subida de archivos"""
    file = forms.FileField(widget=forms.FileInput(attrs={'class': 'form-control'}))
    
    def __init__(self, *args, **kwargs):
        valid_extensions = kwargs.pop('valid_extensions', [])
        super().__init__(*args, **kwargs)
        self.fields['file'].validators.append(
            FileExtensionValidator(valid_extensions)
        )

class DocumentForm(FileUploadForm):
    def __init__(self, *args, **kwargs):
        kwargs['valid_extensions'] = ['pdf', 'docx', 'ppt']
        super().__init__(*args, **kwargs)

class ImageForm(FileUploadForm):
    def __init__(self, *args, **kwargs):
        kwargs['valid_extensions'] = ['jpg', 'jpeg', 'png', 'gif']
        super().__init__(*args, **kwargs)

class DatabaseForm(FileUploadForm):
    def __init__(self, *args, **kwargs):
        kwargs['valid_extensions'] = ['csv', 'xlsx', 'xls']
        super().__init__(*args, **kwargs)