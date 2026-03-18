from django import forms
from .models import Curriculum, Experience, Education, Skill, Language, Certification, Document, Image, Database
from django.core.validators import FileExtensionValidator, URLValidator, EmailValidator
from django.core.exceptions import ValidationError
import re

class BaseModelForm(forms.ModelForm):
    """Formulario base con estilos comunes y mejor validación"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Clases CSS base
            field.widget.attrs.update({'class': 'form-control'})
            
            # Placeholders descriptivos
            if field.required:
                field.widget.attrs.update({
                    'placeholder': f'Ingrese {field.label.lower()} (requerido)'
                })
                field.error_messages = {
                    'required': f'El campo "{field.label}" es obligatorio.',
                    'invalid': f'El valor ingresado en "{field.label}" no es válido.'
                }
            else:
                field.widget.attrs.update({
                    'placeholder': f'Ingrese {field.label.lower()} (opcional)'
                })
                field.error_messages = {
                    'invalid': f'El valor ingresado en "{field.label}" no es válido.'
                }
            
            # Atributos adicionales para campos específicos
            if isinstance(field, forms.EmailField):
                field.widget.attrs.update({
                    'placeholder': 'ejemplo@correo.com',
                    'pattern': '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}',
                    'title': 'Ingrese un email válido (ejemplo@correo.com)'
                })
            elif isinstance(field, forms.URLField):
                field.widget.attrs.update({
                    'placeholder': 'https://ejemplo.com',
                    'pattern': 'https?://.+',
                    'title': 'Ingrese una URL válida (https://ejemplo.com)'
                })
            elif isinstance(field, forms.DateField):
                field.widget.attrs.update({
                    'placeholder': 'AAAA-MM-DD'
                })
    
    def clean(self):
        """Validaciones personalizadas con mensajes claros"""
        cleaned_data = super().clean()
        
        # Validar que no haya espacios en blanco innecesarios
        for field_name, value in cleaned_data.items():
            if isinstance(value, str):
                cleaned_data[field_name] = value.strip()
        
        return cleaned_data


class CurriculumForm(BaseModelForm):
    class Meta:
        model = Curriculum
        fields = '__all__'
        exclude = ['user', 'created_at', 'updated_at']
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Cuéntanos sobre ti, tu experiencia, objetivos profesionales...'
            }),
            'address': forms.TextInput(attrs={
                'placeholder': 'Ej: Av. Principal 123, Lima, Perú'
            }),
            'hire_date': forms.DateInput(attrs={
                'type': 'date',
                'placeholder': 'AAAA-MM-DD'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'Ej: +51 999 999 999',
                'pattern': '[+]?[0-9]{9,15}',
                'title': 'Ingrese un número de teléfono válido'
            }),
        }
        error_messages = {
            'full_name': {
                'required': 'Por favor, ingresa tu nombre completo.',
                'max_length': 'El nombre es demasiado largo (máximo 100 caracteres).',
            },
            'profession': {
                'required': 'Por favor, ingresa tu profesión.',
            },
            'bio': {
                'required': 'Por favor, escribe una breve biografía.',
            },
            'email': {
                'required': 'El email es necesario para contactarte.',
                'invalid': 'Por favor, ingresa un email válido (ej: nombre@dominio.com).',
            },
        }
    
    def clean_email(self):
        """Validación específica para email"""
        email = self.cleaned_data.get('email')
        if email and Curriculum.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Este email ya está registrado por otro usuario.')
        return email
    
    def clean_phone(self):
        """Validación específica para teléfono"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Eliminar espacios y caracteres especiales
            phone_clean = re.sub(r'[^\d+]', '', phone)
            if len(phone_clean) < 9 or len(phone_clean) > 15:
                raise ValidationError('El número de teléfono debe tener entre 9 y 15 dígitos.')
            return phone_clean
        return phone


class ExperienceForm(BaseModelForm):
    class Meta:
        model = Experience
        fields = '__all__'
        exclude = ['cv']
        widgets = {
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'placeholder': 'AAAA-MM-DD'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'placeholder': 'AAAA-MM-DD (dejar vacío si es trabajo actual)'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Describe tus responsabilidades y logros...'
            }),
        }
        error_messages = {
            'job_title': {
                'required': 'El cargo es obligatorio.',
            },
            'company_name': {
                'required': 'El nombre de la empresa es obligatorio.',
            },
            'start_date': {
                'required': 'La fecha de inicio es obligatoria.',
            },
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError('La fecha de fin no puede ser anterior a la fecha de inicio.')
        
        return cleaned_data


class EducationForm(BaseModelForm):
    class Meta:
        model = Education
        fields = '__all__'
        exclude = ['cv']
        widgets = {
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'placeholder': 'AAAA-MM-DD'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'placeholder': 'AAAA-MM-DD (dejar vacío si es educación actual)'
            }),
            'description': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Describe tu formación (opcional)...'
            }),
        }
        error_messages = {
            'institution_name': {
                'required': 'El nombre de la institución es obligatorio.',
            },
            'degree': {
                'required': 'El título o grado es obligatorio.',
            },
            'field_of_study': {
                'required': 'El campo de estudio es obligatorio.',
            },
            'start_date': {
                'required': 'La fecha de inicio es obligatoria.',
            },
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise ValidationError('La fecha de fin no puede ser anterior a la fecha de inicio.')
        
        return cleaned_data


class SkillForm(BaseModelForm):
    class Meta:
        model = Skill
        fields = '__all__'
        exclude = ['cv']
        widgets = {
            'proficiency_level': forms.Select(attrs={'class': 'form-control'}),
        }
        error_messages = {
            'skill_name': {
                'required': 'El nombre de la habilidad es obligatorio.',
            },
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proficiency_level'].choices = [
            ('', 'Seleccione nivel'),
            ('B', 'Básico'),
            ('I', 'Intermedio'),
            ('A', 'Avanzado')
        ]
        self.fields['proficiency_level'].error_messages = {
            'required': 'Por favor, seleccione un nivel de competencia.'
        }
    
    def clean_skill_name(self):
        skill_name = self.cleaned_data.get('skill_name')
        if skill_name:
            # Capitalizar primera letra
            return skill_name.strip().capitalize()
        return skill_name


class LanguageForm(BaseModelForm):
    class Meta:
        model = Language
        fields = '__all__'
        exclude = ['cv']
        widgets = {
            'proficiency_level': forms.Select(attrs={'class': 'form-control'}),
        }
        error_messages = {
            'language_name': {
                'required': 'El nombre del idioma es obligatorio.',
            },
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
        self.fields['proficiency_level'].error_messages = {
            'required': 'Por favor, seleccione un nivel de competencia.'
        }
    
    def clean_language_name(self):
        language_name = self.cleaned_data.get('language_name')
        if language_name:
            return language_name.strip().capitalize()
        return language_name


class CertificationForm(BaseModelForm):
    class Meta:
        model = Certification
        fields = '__all__'
        exclude = ['cv']
        widgets = {
            'issue_date': forms.DateInput(attrs={
                'type': 'date',
                'placeholder': 'AAAA-MM-DD'
            }),
            'expiration_date': forms.DateInput(attrs={
                'type': 'date',
                'placeholder': 'AAAA-MM-DD (si no expira, dejar vacío)'
            }),
            'credential_url': forms.URLInput(attrs={
                'placeholder': 'https://ejemplo.com/credencial'
            }),
        }
        error_messages = {
            'certification_name': {
                'required': 'El nombre de la certificación es obligatorio.',
            },
            'issuing_organization': {
                'required': 'La organización emisora es obligatoria.',
            },
            'issue_date': {
                'required': 'La fecha de emisión es obligatoria.',
            },
        }
    
    def clean(self):
        cleaned_data = super().clean()
        issue_date = cleaned_data.get('issue_date')
        expiration_date = cleaned_data.get('expiration_date')
        
        if issue_date and expiration_date and expiration_date < issue_date:
            raise ValidationError('La fecha de expiración no puede ser anterior a la fecha de emisión.')
        
        return cleaned_data


class FileUploadForm(forms.Form):
    """Formulario base para subida de archivos con mejor validación"""
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.docx,.ppt,.jpg,.jpeg,.png,.gif,.csv,.xlsx,.xls'
        }),
        error_messages={
            'required': 'Por favor, seleccione un archivo para subir.',
            'invalid': 'El archivo seleccionado no es válido.'
        }
    )
    
    def __init__(self, *args, **kwargs):
        self.valid_extensions = kwargs.pop('valid_extensions', [])
        super().__init__(*args, **kwargs)
        
        # Validación de extensión personalizada
        self.fields['file'].validators.append(
            FileExtensionValidator(
                self.valid_extensions,
                message=f'Extensión no permitida. Extensiones válidas: {", ".join(self.valid_extensions)}'
            )
        )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Validar tamaño (máximo 10MB)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError('El archivo no puede superar los 10MB.')
            
            # Validar nombre de archivo (sin caracteres especiales)
            filename = file.name
            if not re.match(r'^[\w\-. ]+$', filename):
                raise ValidationError('El nombre del archivo contiene caracteres no permitidos.')
        
        return file


class DocumentForm(FileUploadForm):
    def __init__(self, *args, **kwargs):
        kwargs['valid_extensions'] = ['pdf', 'docx', 'ppt']
        super().__init__(*args, **kwargs)
        self.fields['file'].widget.attrs.update({
            'accept': '.pdf,.docx,.ppt'
        })


class ImageForm(FileUploadForm):
    def __init__(self, *args, **kwargs):
        kwargs['valid_extensions'] = ['jpg', 'jpeg', 'png', 'gif']
        super().__init__(*args, **kwargs)
        self.fields['file'].widget.attrs.update({
            'accept': '.jpg,.jpeg,.png,.gif'
        })


class DatabaseForm(FileUploadForm):
    def __init__(self, *args, **kwargs):
        kwargs['valid_extensions'] = ['csv', 'xlsx', 'xls']
        super().__init__(*args, **kwargs)
        self.fields['file'].widget.attrs.update({
            'accept': '.csv,.xlsx,.xls'
        })