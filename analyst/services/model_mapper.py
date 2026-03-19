# analyst/services/model_mapper.py
import logging
import pandas as pd
from typing import List, Dict, Any, Set, Tuple, Optional
from difflib import get_close_matches
from django.db.models import Model, Field

logger = logging.getLogger(__name__)

class ModelMapper:
    """Servicio para mapear columnas de DataFrame a campos de modelo Django"""
    
    @staticmethod
    def analyze_model_fields(model: Model, df: pd.DataFrame) -> Tuple[List[Dict], Set[str], List[str]]:
        """
        Analiza los campos del modelo y su relación con las columnas del DataFrame
        
        Returns:
            Tuple[List[Dict], Set[str], List[str]]: 
            - Lista de información de campos
            - Set de campos mapeados
            - Lista de campos requeridos
        """
        model_fields_info = []
        mapped_columns = set()
        required_fields = []
        
        for field in model._meta.get_fields():
            if isinstance(field, Field):
                field_info = ModelMapper._get_field_info(field)
                model_fields_info.append(field_info)
                
                if field_info['required']:
                    required_fields.append(field.name)
                
                # Buscar coincidencias
                for col in df.columns:
                    if ModelMapper._matches_field(col, field_info):
                        logger.debug(f"Columna '{col}' mapeada a campo '{field.name}'")
                        mapped_columns.add(field.name)
        
        return model_fields_info, mapped_columns, required_fields
    
    @staticmethod
    def _get_field_info(field: Field) -> Dict:
        """Obtiene información detallada de un campo"""
        return {
            'name': str(field.name),
            'verbose_name': str(getattr(field, 'verbose_name', field.name)),
            'type': field.get_internal_type(),
            'required': not field.null and not getattr(field, 'blank', False),
            'choices': getattr(field, 'choices', None)
        }
    
    @staticmethod
    def _matches_field(column: str, field_info: Dict) -> bool:
        """Verifica si una columna coincide con un campo"""
        col_str = str(column).lower()
        return (col_str == field_info['name'].lower() or 
                col_str == field_info['verbose_name'].lower())
    
    @staticmethod
    def find_best_match(column_name: str, available_fields: Dict) -> Optional[str]:
        """Encuentra la mejor coincidencia para un nombre de columna"""
        col_clean = ModelMapper._clean_string(column_name)
        
        # Coincidencia exacta
        for field_name, field_info in available_fields.items():
            if (col_clean == ModelMapper._clean_string(field_name) or
                col_clean == ModelMapper._clean_string(field_info['verbose_name'])):
                return field_name
        
        # Coincidencia aproximada
        possible_matches = get_close_matches(
            col_clean,
            [ModelMapper._clean_string(f) for f in available_fields.keys()] +
            [ModelMapper._clean_string(f['verbose_name']) for f in available_fields.values()],
            n=1,
            cutoff=0.6
        )
        
        if possible_matches:
            match = possible_matches[0]
            for field_name, field_info in available_fields.items():
                if (match == ModelMapper._clean_string(field_name) or
                    match == ModelMapper._clean_string(field_info['verbose_name'])):
                    return field_name
        
        return None
    
    @staticmethod
    def _clean_string(s: str) -> str:
        """Limpia un string para comparación"""
        return (str(s).lower()
                .replace('á', 'a').replace('é', 'e').replace('í', 'i')
                .replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
                .strip())