from django import forms
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import date
from .models import MementoConfig




class MementoConfigForm(forms.ModelForm):
    save_config = forms.BooleanField(
        required=False,
        initial=True,
        label='Guardar esta configuración',
        help_text='Desmarca esta opción para solo probar con estas fechas sin guardar',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = MementoConfig
        fields = ['preferred_frequency', 'birth_date', 'death_date']
        widgets = {
            'birth_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'death_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
        }
        labels = {
            'preferred_frequency': 'Frecuencia de visualización',
            'birth_date': 'Fecha de nacimiento',
            'death_date': 'Fecha estimada de fallecimiento',
        }
        help_texts = {
            'birth_date': 'La fecha en que comenzó tu vida',
            'death_date': 'Basado en expectativas de vida promedio o tu propia estimación',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['preferred_frequency'].widget.attrs.update({'class': 'form-select'})
        self.fields['preferred_frequency'].choices = [
            ('daily', 'Diario (Días)'),
            ('weekly', 'Semanal (Semanas)'),
            ('monthly', 'Mensual (Meses/Años)'),
        ]


    def clean(self):
        cleaned_data = super().clean()
        birth_date = cleaned_data.get("birth_date")
        death_date = cleaned_data.get("death_date")

        if not all([birth_date, death_date]):
            return cleaned_data

        # Date validation
        if birth_date >= death_date:
            self.add_error('death_date', "La fecha de fallecimiento debe ser posterior al nacimiento")
        if death_date <= date.today():
            self.add_error('death_date', "La fecha de fallecimiento debe ser en el futuro")

        # Duplicate check
        if hasattr(self, 'user') and self.user and not self.instance.pk:
            exists = MementoConfig.objects.filter(
                user=self.user,
                birth_date=birth_date,
                death_date=death_date
            ).exists()
            if exists:
                self.add_error(None, "Ya tienes una configuración con estas fechas. Por favor edítala.")

        return cleaned_data
