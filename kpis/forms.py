from django import forms  
from .models import CallRecord  

class UploadCSVForm(forms.Form):  
    csv_file = forms.FileField(label="Subir CSV")  

    def clean_csv_file(self):  
        file = self.cleaned_data['csv_file']  
        if not file.name.endswith('.csv'):  
            raise forms.ValidationError("Solo se permiten archivos CSV.")  
        return file  