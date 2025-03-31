from django import forms  
from .models import CallRecord  

class UploadCSVForm(forms.Form):  
    csv_file = forms.FileField(label="Subir CSV")  

    def clean_csv_file(self):  
        file = self.cleaned_data['csv_file']  
        if not file.name.endswith('.csv'):  
            raise forms.ValidationError("Solo se permiten archivos CSV.")  
        return file  
    
# kpis/forms.py
from django import forms

SERVICE_CHOICES = [
    ('Reclamos', 'Reclamos'),
    ('Consultas', 'Consultas'),
    ('Soporte Técnico', 'Soporte Técnico'),
    ('Ventas', 'Ventas'),
    ('Información', 'Información')
]

CHANNEL_CHOICES = [
    ('Phone', 'Teléfono'),
    ('Mail', 'Correo'),
    ('Chat', 'Chat en línea'),
    ('Social Media', 'Redes Sociales'),
    ('WhatsApp', 'WhatsApp')
]

class DataGenerationForm(forms.Form):
    # Configuración básica
    weeks = forms.IntegerField(
        label='Semanas a generar',
        min_value=1,
        max_value=52,
        initial=12,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    records_per_week = forms.IntegerField(
        label='Registros por semana',
        min_value=10,
        max_value=1000,
        initial=50,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    # Selección de servicios y canales
    services = forms.MultipleChoiceField(
        label='Servicios a incluir',
        choices=SERVICE_CHOICES,
        initial=[x[0] for x in SERVICE_CHOICES],
        widget=forms.CheckboxSelectMultiple()
    )
    
    service_weights = forms.CharField(
        label='Ponderación de servicios (separados por comas)',
        initial="3,2,2,1,1",
        help_text="Asigne pesos relativos para la frecuencia de cada servicio",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    channels = forms.MultipleChoiceField(
        label='Canales a incluir',
        choices=CHANNEL_CHOICES,
        initial=[x[0] for x in CHANNEL_CHOICES],
        widget=forms.CheckboxSelectMultiple()
    )
    
    channel_weights = forms.CharField(
        label='Ponderación de canales (separados por comas)',
        initial="4,2,3,1,2",
        help_text="Asigne pesos relativos para la frecuencia de cada canal",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Configuración de personal
    num_agents = forms.IntegerField(
        label='Número de agentes',
        min_value=5,
        max_value=100,
        initial=20,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    num_supervisors = forms.IntegerField(
        label='Número de supervisores',
        min_value=2,
        max_value=20,
        initial=5,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    # Configuración de métricas
    min_evaluations = forms.IntegerField(
        label='Evaluaciones mínimas por registro',
        min_value=0,
        max_value=50,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    max_evaluations = forms.IntegerField(
        label='Evaluaciones máximas por registro',
        min_value=1,
        max_value=100,
        initial=20,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    # Configuración avanzada
    batch_size = forms.IntegerField(
        label='Tamaño de lote para inserción',
        min_value=100,
        max_value=5000,
        initial=1000,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    random_seed = forms.IntegerField(
        label='Semilla aleatoria (opcional)',
        required=False,
        help_text="Dejar vacío para resultados diferentes cada vez",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    clear_existing = forms.BooleanField(
        label='Eliminar datos existentes',
        initial=True,
        required=False,
        widget=forms.CheckboxInput()
    )
    
    def clean_service_weights(self):
        data = self.cleaned_data['service_weights']
        try:
            weights = [float(x.strip()) for x in data.split(',')]
            if len(weights) != len(self.cleaned_data['services']):
                raise forms.ValidationError("Debe proporcionar exactamente un peso por servicio seleccionado")
            if any(w <= 0 for w in weights):
                raise forms.ValidationError("Todos los pesos deben ser números positivos")
            return weights
        except ValueError:
            raise forms.ValidationError("Ingrese números válidos separados por comas")
    
    def clean_channel_weights(self):
        data = self.cleaned_data['channel_weights']
        try:
            weights = [float(x.strip()) for x in data.split(',')]
            if len(weights) != len(self.cleaned_data['channels']):
                raise forms.ValidationError("Debe proporcionar exactamente un peso por canal seleccionado")
            if any(w <= 0 for w in weights):
                raise forms.ValidationError("Todos los pesos deben ser números positivos")
            return weights
        except ValueError:
            raise forms.ValidationError("Ingrese números válidos separados por comas")
    
    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('min_evaluations', 0) > cleaned_data.get('max_evaluations', 0):
            self.add_error('min_evaluations', "El mínimo no puede ser mayor que el máximo")
        return cleaned_data