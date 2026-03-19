import logging
from typing import List, Dict, Any, Tuple
from django.db import transaction, models
from django.db.models import Model
from django.core.exceptions import ValidationError
import pandas as pd

from analyst.constants import DEFAULT_CHUNK_SIZE, MAX_RECORDS_FOR_IMPORT
from analyst.utils.validators import DataValidator

logger = logging.getLogger(__name__)

class DataImporter:
    """Servicio para importar datos a la base de datos"""
    
    def __init__(self, model: Model, df: pd.DataFrame, column_mapping: Dict,
                 clear_existing: bool = False, user=None):
        """
        Inicializa el importador
        
        Args:
            model: Modelo Django destino
            df: DataFrame con los datos
            column_mapping: Mapeo de columnas a campos del modelo
            clear_existing: Si debe limpiar datos existentes
            user: Usuario que realiza la importación
        """
        self.model = model
        self.df = df
        self.column_mapping = column_mapping
        self.clear_existing = clear_existing
        self.user = user
        
        # Obtener información de campos del modelo
        self.model_fields = self._get_model_fields()
        
        # Estadísticas
        self.stats = {
            'total_rows': len(df),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
    
    def _get_model_fields(self) -> Dict:
        """Obtiene información detallada de los campos del modelo"""
        fields_info = {}
        
        for field in self.model._meta.get_fields():
            if isinstance(field, models.Field):
                fields_info[field.name] = {
                    'field': field,
                    'type': field.get_internal_type(),
                    'null': field.null,
                    'blank': getattr(field, 'blank', False),
                    'default': getattr(field, 'default', None),
                    'choices': getattr(field, 'choices', None),
                    'verbose_name': str(getattr(field, 'verbose_name', field.name))
                }
        
        return fields_info
    
    def import_data(self) -> Dict:
        """
        Ejecuta la importación de datos
        
        Returns:
            Dict: Estadísticas de la importación
        """
        logger.info(f"Iniciando importación para modelo {self.model.__name__}")
        
        try:
            # Validar permisos y límites
            self._validate_import()
            
            with transaction.atomic():
                # Limpiar datos existentes si es necesario
                if self.clear_existing:
                    self._clear_existing_data()
                
                # Procesar en lotes
                for chunk_start in range(0, len(self.df), DEFAULT_CHUNK_SIZE):
                    chunk = self.df.iloc[chunk_start:chunk_start + DEFAULT_CHUNK_SIZE]
                    self._process_chunk(chunk, chunk_start)
                    
                    logger.debug(f"Procesado lote {chunk_start//DEFAULT_CHUNK_SIZE + 1}")
            
            logger.info(f"Importación completada. Éxitos: {self.stats['successful']}, "
                       f"Fallos: {self.stats['failed']}")
            
            return self.stats
            
        except Exception as e:
            logger.error(f"Error en importación: {str(e)}", exc_info=True)
            self.stats['error'] = str(e)
            raise
    
    def _validate_import(self):
        """Valida que la importación sea posible"""
        
        # Validar cantidad de registros
        if len(self.df) > MAX_RECORDS_FOR_IMPORT:
            raise ValidationError(
                f"Demasiados registros para importar. Máximo: {MAX_RECORDS_FOR_IMPORT}"
            )
        
        # Validar que haya mapeo de columnas
        if not self.column_mapping:
            raise ValidationError("No hay mapeo de columnas definido")
        
        # Validar campos requeridos
        required_fields = [
            field_name for field_name, field_info in self.model_fields.items()
            if not field_info['null'] and not field_info['blank']
        ]
        
        mapped_fields = set(self.column_mapping.values())
        missing_required = [f for f in required_fields if f not in mapped_fields]
        
        if missing_required:
            raise ValidationError(
                f"Campos requeridos no mapeados: {', '.join(missing_required)}"
            )
    
    def _clear_existing_data(self):
        """Limpia los datos existentes del modelo"""
        count = self.model.objects.count()
        logger.info(f"Limpiando {count} registros existentes de {self.model.__name__}")
        
        if count > 0:
            self.model.objects.all().delete()
            logger.debug(f"Registros eliminados: {count}")
    
    def _process_chunk(self, chunk: pd.DataFrame, start_idx: int):
        """
        Procesa un lote de datos
        
        Args:
            chunk: DataFrame con el lote a procesar
            start_idx: Índice inicial del lote
        """
        objects_to_create = []
        
        for idx, (_, row) in enumerate(chunk.iterrows()):
            row_idx = start_idx + idx + 1
            
            try:
                # Validar y preparar datos de la fila
                obj_data, errors = DataValidator.validate_and_prepare_row(
                    row, self.column_mapping, self.model_fields, row_idx
                )
                
                if errors:
                    self.stats['failed'] += 1
                    self.stats['errors'].append({
                        'row': row_idx,
                        'errors': errors
                    })
                    continue
                
                # Crear objeto del modelo
                obj = self.model(**obj_data)
                objects_to_create.append(obj)
                self.stats['successful'] += 1
                
            except Exception as e:
                logger.error(f"Error procesando fila {row_idx}: {str(e)}")
                self.stats['failed'] += 1
                self.stats['errors'].append({
                    'row': row_idx,
                    'errors': [str(e)]
                })
        
        # Crear objetos en lote
        if objects_to_create:
            try:
                self.model.objects.bulk_create(
                    objects_to_create,
                    batch_size=DEFAULT_CHUNK_SIZE,
                    ignore_conflicts=False
                )
                logger.debug(f"Creados {len(objects_to_create)} objetos en lote")
            except Exception as e:
                logger.error(f"Error en bulk_create: {str(e)}")
                raise
    
    def get_preview_errors(self, max_errors: int = 10) -> List[Dict]:
        """
        Obtiene una vista previa de los errores
        
        Args:
            max_errors: Máximo número de errores a retornar
            
        Returns:
            List[Dict]: Lista de errores
        """
        return self.stats['errors'][:max_errors]