import logging
from typing import Any, Dict, List, Optional
from django.core.exceptions import ValidationError
from django.db.models import Model, Field
import pandas as pd

logger = logging.getLogger(__name__)

class DataValidator:
    """Validador de datos para cargas masivas"""
    
    # Valores por defecto según tipo de campo
    DEFAULT_VALUES = {
        'CharField': '',
        'IntegerField': 0,
        'FloatField': 0.0,
        'BooleanField': False,
        'DateField': None,
        'DateTimeField': None,
        'TextField': '',
        'EmailField': '',
        'URLField': '',
        'SlugField': '',
        'DecimalField': 0.0
    }
    
    @classmethod
    def validate_and_prepare_row(cls, row: pd.Series, column_mapping: Dict, 
                                 model_fields: Dict, row_idx: int) -> tuple:
        """
        Valida una fila y prepara los datos para crear un objeto del modelo
        
        Returns:
            tuple: (obj_data, errors) - Datos del objeto y lista de errores
        """
        obj_data = {}
        errors = []
        
        for col_name, value in row.items():
            col_name_str = str(col_name)
            
            if col_name_str not in column_mapping:
                continue
                
            field_name = column_mapping[col_name_str]
            field_info = model_fields.get(field_name)
            
            if not field_info:
                continue
            
            # Validar y convertir valor
            try:
                converted_value = cls._convert_value(
                    value, field_info['field'], field_info
                )
                obj_data[field_name] = converted_value
            except ValidationError as e:
                errors.append(f"Campo '{field_name}': {e.message}")
            except Exception as e:
                errors.append(f"Campo '{field_name}': Error inesperado - {str(e)}")
        
        return obj_data, errors
    
    @classmethod
    def _convert_value(cls, value: Any, field: Field, field_info: Dict) -> Any:
        """
        Convierte un valor al tipo apropiado según el campo del modelo
        """
        # Manejar valores nulos
        if pd.isna(value) or value is None:
            return cls._handle_null_value(field_info)
        
        # Convertir según tipo de campo
        field_type = field_info['type']
        
        try:
            if field_type in ['IntegerField']:
                return int(float(str(value).replace(',', '.')))
                
            elif field_type in ['FloatField', 'DecimalField']:
                return float(str(value).replace(',', '.'))
                
            elif field_type in ['BooleanField']:
                return cls._convert_to_bool(value)
                
            elif field_type in ['DateField', 'DateTimeField']:
                return cls._convert_to_datetime(value, field_type)
                
            elif field_type in ['CharField', 'TextField', 'EmailField', 'URLField', 'SlugField']:
                return str(value).strip()
                
            elif field_type == 'JSONField':
                return cls._convert_to_json(value)
                
            elif field_info.get('choices'):
                return cls._validate_choice(value, field_info['choices'])
                
            return value
            
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Valor '{value}' no válido para tipo {field_type}")
    
    @classmethod
    def _handle_null_value(cls, field_info: Dict) -> Any:
        """Maneja valores nulos según configuración del campo"""
        if field_info.get('default') is not None:
            return field_info['default']
        
        if field_info.get('null') or field_info.get('blank'):
            return None
        
        return cls.DEFAULT_VALUES.get(field_info['type'])
    
    @classmethod
    def _convert_to_bool(cls, value: Any) -> bool:
        """Convierte varios formatos a booleano"""
        if isinstance(value, bool):
            return value
        
        str_value = str(value).lower().strip()
        true_values = {'true', '1', 'yes', 'sí', 'si', 'verdadero', 'on', 'ok'}
        false_values = {'false', '0', 'no', 'off', 'none', 'null', ''}
        
        if str_value in true_values:
            return True
        if str_value in false_values:
            return False
        
        raise ValidationError(f"Valor '{value}' no reconocido como booleano")
    
    @classmethod
    def _convert_to_datetime(cls, value: Any, field_type: str) -> Any:
        """Convierte a fecha/datetime"""
        if isinstance(value, (pd.Timestamp, pd.DatetimeIndex)):
            dt_value = value.to_pydatetime()
        else:
            dt_value = pd.to_datetime(value, errors='coerce')
            
            if pd.isna(dt_value):
                raise ValidationError(f"Formato de fecha inválido: '{value}'")
            
            dt_value = dt_value.to_pydatetime()
        
        if field_type == 'DateField':
            return dt_value.date()
        
        return dt_value
    
    @classmethod
    def _validate_choice(cls, value: Any, choices: List) -> Any:
        """Valida que el valor esté entre las opciones permitidas"""
        valid_choices = [choice[0] for choice in choices]
        
        if value not in valid_choices:
            # Intentar conversión a string para comparar
            str_value = str(value)
            valid_str_choices = [str(c) for c in valid_choices]
            
            if str_value in valid_str_choices:
                return valid_choices[valid_str_choices.index(str_value)]
            
            raise ValidationError(
                f"Valor '{value}' no válido. Opciones: {', '.join(valid_choices[:5])}"
            )
        
        return value
    
    @classmethod
    def _convert_to_json(cls, value: Any) -> Any:
        """Convierte a formato JSON válido"""
        import json
        
        if isinstance(value, (dict, list)):
            return value
        
        try:
            if isinstance(value, str):
                return json.loads(value)
            return value
        except json.JSONDecodeError:
            raise ValidationError(f"Valor '{value}' no es un JSON válido")