from django import forms
from .models import Course, Module, Lesson, Review, CourseCategory

class CourseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Personalizar widgets con clases CSS modernas
        self.fields['title'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ej: Introducción a la Programación en Python',
            'maxlength': '200'
        })

        self.fields['short_description'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Describe brevemente qué aprenderán los estudiantes...',
            'rows': '3',
            'maxlength': '300'
        })

        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Describe detalladamente el contenido del curso, objetivos, metodología...',
            'rows': '6'
        })

        self.fields['category'].widget.attrs.update({
            'class': 'form-select'
        })

        self.fields['level'].widget.attrs.update({
            'class': 'form-select'
        })

        self.fields['price'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '0.00',
            'min': '0',
            'step': '0.01'
        })

        self.fields['duration_hours'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ej: 40',
            'min': '1',
            'max': '500'
        })

        self.fields['thumbnail'].widget.attrs.update({
            'class': 'd-none',
            'accept': 'image/*'
        })

        self.fields['is_published'].widget.attrs.update({
            'class': 'form-check-input'
        })

        self.fields['is_featured'].widget.attrs.update({
            'class': 'form-check-input'
        })

        # Personalizar labels
        self.fields['title'].label = 'Título del Curso'
        self.fields['category'].label = 'Categoría'
        self.fields['level'].label = 'Nivel de Dificultad'
        self.fields['description'].label = 'Descripción Completa'
        self.fields['short_description'].label = 'Descripción Corta'
        self.fields['price'].label = 'Precio (USD)'
        self.fields['duration_hours'].label = 'Duración Total (horas)'
        self.fields['thumbnail'].label = 'Imagen del Curso'
        self.fields['is_published'].label = 'Publicar curso'
        self.fields['is_featured'].label = 'Destacar curso'

        # Personalizar help texts
        self.fields['title'].help_text = 'El título debe ser descriptivo y atractivo (máx. 200 caracteres)'
        self.fields['short_description'].help_text = 'Resumen breve que aparecerá en las tarjetas de curso (máx. 300 caracteres)'
        self.fields['description'].help_text = 'Descripción detallada del contenido, objetivos y beneficios del curso'
        self.fields['price'].help_text = 'Precio en dólares estadounidenses. Use 0 para cursos gratuitos'
        self.fields['duration_hours'].help_text = 'Duración estimada total del curso en horas'
        self.fields['thumbnail'].help_text = 'Imagen representativa del curso (JPG, PNG, GIF - máx. 5MB)'

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 5:
            raise forms.ValidationError("El título debe tener al menos 5 caracteres.")
        if len(title) > 200:
            raise forms.ValidationError("El título no puede exceder 200 caracteres.")
        return title

    def clean_short_description(self):
        short_desc = self.cleaned_data.get('short_description', '').strip()
        if len(short_desc) > 300:
            raise forms.ValidationError("La descripción corta no puede exceder 300 caracteres.")
        return short_desc

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        if len(description) < 50:
            raise forms.ValidationError("La descripción debe tener al menos 50 caracteres.")
        return description

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None:
            if price < 0:
                raise forms.ValidationError("El precio no puede ser negativo.")
            if price > 10000:
                raise forms.ValidationError("El precio no puede exceder $10,000.")
        return price

    def clean_duration_hours(self):
        duration = self.cleaned_data.get('duration_hours')
        if duration is not None:
            if duration < 1:
                raise forms.ValidationError("La duración debe ser al menos 1 hora.")
            if duration > 500:
                raise forms.ValidationError("La duración no puede exceder 500 horas.")
        return duration

    def clean_thumbnail(self):
        thumbnail = self.cleaned_data.get('thumbnail')
        if thumbnail:
            # Validar tamaño del archivo (5MB máximo)
            if thumbnail.size > 5 * 1024 * 1024:
                raise forms.ValidationError("La imagen no puede ser mayor a 5MB.")

            # Validar tipo de archivo
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            if hasattr(thumbnail, 'content_type') and thumbnail.content_type not in allowed_types:
                raise forms.ValidationError("Solo se permiten archivos de imagen (JPG, PNG, GIF).")

        return thumbnail

    def clean(self):
        cleaned_data = super().clean()
        user = self.user

        # Validar que el usuario tenga un perfil de CV si está creando un curso
        if user and not hasattr(user, 'cv'):
            raise forms.ValidationError("Debes tener un perfil de tutor (CV) para crear cursos.")

        # Validar que si el curso está marcado como destacado, también esté publicado
        is_featured = cleaned_data.get('is_featured')
        is_published = cleaned_data.get('is_published')

        if is_featured and not is_published:
            raise forms.ValidationError("Un curso destacado debe estar publicado primero.")

        return cleaned_data

    class Meta:
        model = Course
        fields = [
            'title', 'category', 'level', 'description', 'short_description',
            'price', 'duration_hours', 'thumbnail', 'is_published', 'is_featured'
        ]

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