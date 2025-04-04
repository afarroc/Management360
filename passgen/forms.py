from django import forms
from .generators import PasswordGenerator

class PasswordForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        gen = PasswordGenerator()
        
        # Campo de selección de patrón
        self.fields['pattern_type'] = forms.ChoiceField(
            choices=gen.get_pattern_choices(),
            label="Tipo de patrón",
            widget=forms.RadioSelect(attrs={
                'class': 'pattern-radio',
                'onchange': 'updatePatternInput(this)'
            })
        )
        
        # Campo de patrón personalizado
        self.fields['custom_pattern'] = forms.CharField(
            required=False,
            label="Patrón personalizado",
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: a:3|!:1|x:2',
                'onfocus': "document.querySelector('input[name=\"pattern_type\"][value=\"custom\"]').checked=true"
            })
        )
        
        # Checkbox para acentos
        self.fields['include_accents'] = forms.BooleanField(
            required=False,
            label="Incluir caracteres acentuados",
            widget=forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        )

    length = forms.IntegerField(
        min_value=4, 
        max_value=64,
        initial=12,
        label="Longitud de la contraseña"
    )

    exclude_ambiguous = forms.BooleanField(
        required=False,
        initial=True,
        label="Excluir caracteres ambiguos (1,l,I,0,O,etc.)"
    )