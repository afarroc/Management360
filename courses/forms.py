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
    # Campo adicional para facilitar la edición de contenido estructurado
    structured_content_json = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 10,
            'placeholder': 'Ingresa el contenido estructurado en formato JSON...\n\nEjemplo:\n[\n  {"type": "heading", "title": "Título", "content": "Contenido"},\n  {"type": "list", "items": ["Item 1", "Item 2"]}\n]',
            'class': 'form-control'
        }),
        label='Contenido Estructurado (JSON)',
        help_text='Formato JSON para contenido estructurado con elementos como encabezados, listas, imágenes, etc.'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si hay contenido estructurado, mostrarlo en el campo JSON
        if self.instance and self.instance.pk and self.instance.structured_content:
            import json
            self.fields['structured_content_json'].initial = json.dumps(
                self.instance.structured_content,
                indent=2,
                ensure_ascii=False
            )

        # Configurar widgets
        self.fields['content'].widget.attrs.update({
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Contenido simple de la lección (texto plano)...'
        })

        self.fields['quiz_questions'].widget.attrs.update({
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Preguntas del quiz en formato JSON...\n\nEjemplo:\n[\n  {\n    "question": "¿Pregunta?",\n    "options": ["Opción A", "Opción B"],\n    "correct_answer": "Opción A"\n  }\n]'
        })

        self.fields['assignment_instructions'].widget.attrs.update({
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Instrucciones detalladas para la tarea...'
        })

    def clean_structured_content_json(self):
        """Validar y convertir el JSON del contenido estructurado"""
        json_data = self.cleaned_data.get('structured_content_json')
        if json_data:
            try:
                import json
                parsed_data = json.loads(json_data)
                if not isinstance(parsed_data, list):
                    raise forms.ValidationError("El contenido estructurado debe ser una lista de elementos.")
                return parsed_data
            except json.JSONDecodeError as e:
                raise forms.ValidationError(f"JSON inválido: {str(e)}")
        return []

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Guardar el contenido estructurado
        structured_content = self.cleaned_data.get('structured_content_json', [])
        instance.structured_content = structured_content

        if commit:
            instance.save()
        return instance

    class Meta:
        model = Lesson
        fields = [
            'title', 'lesson_type', 'content', 'structured_content_json', 'video_url',
            'duration_minutes', 'order', 'is_free',
            'quiz_questions', 'assignment_instructions',
            'assignment_file', 'assignment_due_date'
        ]
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
            'assignment_instructions': forms.Textarea(attrs={'rows': 4}),
            'quiz_questions': forms.Textarea(attrs={'rows': 4}),
            'assignment_due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'lesson_type': forms.Select(attrs={'class': 'form-select'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_free': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

class CategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ej: Programación, Diseño Gráfico, Marketing Digital...',
            'maxlength': '50',
            'autocomplete': 'off'
        })
        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Describe brevemente el propósito y alcance de esta categoría...',
            'rows': 3,
            'maxlength': '200'
        })

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            # Verificar duplicados (case insensitive)
            if CourseCategory.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Ya existe una categoría con este nombre.")
            # Capitalizar primera letra de cada palabra
            return name.strip().title()
        return name

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description:
            return description.strip()
        return description

    class Meta:
        model = CourseCategory
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }