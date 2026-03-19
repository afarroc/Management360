# analyst/services/file_processor_service.py
import os
import csv
import logging
import pandas as pd
import chardet
from io import BytesIO, StringIO
from typing import Tuple, List, Dict, Any, Optional
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Model
from analyst.services.excel_processor import ExcelProcessor

logger = logging.getLogger(__name__)

class FileProcessorService:
    """Servicio unificado para procesar archivos CSV y Excel"""
    
    @staticmethod
    def detect_encoding(file) -> str:
        """Detecta la codificación de un archivo CSV"""
        try:
            raw_data = file.read(10240)
            result = chardet.detect(raw_data)
            file.seek(0)
            
            encoding = result['encoding'] if result['confidence'] > 0.6 else 'latin-1'
            if encoding in ['ISO-8859-1', 'Windows-1252']:
                encoding = 'latin-1'
            
            logger.debug(f"Codificación detectada: {encoding}")
            return encoding
        except Exception as e:
            logger.error(f"Error detectando codificación: {str(e)}")
            file.seek(0)
            return 'latin-1'
    
    @staticmethod
    def normalize_name(name: str) -> str:
        """Normaliza nombres de columna"""
        if not name or not isinstance(name, str):
            return ''
        
        name = name.strip().lower()
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ü': 'u', 'ñ': 'n', ' ': '_', '-': '_', '.': '_', 
            '/': '_', '\\': '_', '(': '', ')': '', '[': '', ']': ''
        }
        for orig, repl in replacements.items():
            name = name.replace(orig, repl)
        
        # Eliminar múltiples underscores
        while '__' in name:
            name = name.replace('__', '_')
        
        return name.strip('_')
    
    @classmethod
    def process_file(cls, file, model: Model, sheet_name: str = None, 
                    cell_range: str = None, column_mapping: Dict = None) -> Tuple[List, List[Dict], List[str]]:
        """
        Procesa un archivo (CSV o Excel) y retorna registros, preview y columnas
        
        Returns:
            Tuple[List, List[Dict], List[str]]: (registros, datos_preview, columnas)
        """
        file_extension = os.path.splitext(file.name)[1].lower()
        logger.info(f"Procesando archivo {file.name} - Extensión: {file_extension}")
        
        try:
            if file_extension in ('.xls', '.xlsx'):
                return cls.process_excel(file, model, sheet_name, cell_range, column_mapping)
            else:
                return cls.process_csv(file, model, column_mapping)
        except Exception as e:
            logger.error(f"Error procesando archivo: {str(e)}", exc_info=True)
            raise ValueError(f"Error al procesar el archivo: {str(e)}")
    
    # analyst/services/excel_processor.py
    
    @staticmethod
    def process_excel(file, sheet_name=None, cell_range=None):
        """
        Procesa un archivo Excel con opciones de hoja y rango
        
        Args:
            file: Archivo Excel
            sheet_name: Nombre de la hoja o índice (None para primera hoja)
            cell_range: Rango de celdas (ej: 'A1:C10')
        
        Returns:
            Tuple[pd.DataFrame, Dict]: DataFrame y metadatos
        """
        logger.debug(f"Procesando Excel - Sheet: {sheet_name}, Range: {cell_range}")
        
        excel_file = pd.ExcelFile(file)
        
        # Determinar qué hoja usar
        if sheet_name is None or sheet_name == '':
            selected_sheet = 0  # Primera hoja
            sheet_name_used = excel_file.sheet_names[0]
        else:
            try:
                # Intentar como índice numérico
                selected_sheet = int(sheet_name)
                sheet_name_used = excel_file.sheet_names[selected_sheet]
            except (ValueError, IndexError):
                # Usar como nombre de hoja
                selected_sheet = sheet_name
                sheet_name_used = sheet_name
        
        logger.info(f"Usando hoja: {sheet_name_used} (índice/nombre: {selected_sheet})")
        
        metadata = {
            'type': 'excel',
            'available_sheets': excel_file.sheet_names,
            'selected_sheet': sheet_name_used,
            'sheet_index': selected_sheet if isinstance(selected_sheet, int) else None
        }
        
        try:
            if cell_range and ':' in cell_range:
                df = ExcelProcessor._read_with_range(excel_file, selected_sheet, cell_range)
                metadata['cell_range'] = cell_range
            else:
                df = pd.read_excel(excel_file, sheet_name=selected_sheet)
                metadata['cell_range'] = 'full'
            
            # Validar DataFrame
            if df.empty:
                raise ValueError("El archivo Excel no contiene datos en el rango especificado")
            
            # Información adicional
            metadata.update({
                'max_columns': len(df.columns),
                'max_rows': len(df),
                'sheet_used': sheet_name_used
            })
            
            logger.info(f"Excel procesado - Shape: {df.shape}, Hoja: {sheet_name_used}")
            return df, metadata
            
        except Exception as e:
            logger.error(f"Error procesando Excel: {str(e)}", exc_info=True)
            raise ValueError(f"Error al procesar archivo Excel: {str(e)}")    

    @classmethod
    def process_csv(cls, file, model: Model, column_mapping: Dict = None, 
                   delimiter: str = ';') -> Tuple[List, List[Dict], List[str]]:
        """Procesa un archivo CSV"""
        try:
            # Detectar codificación
            encoding = cls.detect_encoding(file)
            
            # Leer CSV
            content = file.read().decode(encoding, errors='replace')
            file.seek(0)
            
            # Detectar delimitador
            if delimiter == ';' and ',' in content.split('\n')[0]:
                delimiter = ','
            
            # Leer con pandas para mejor manejo
            df = pd.read_csv(StringIO(content), delimiter=delimiter, encoding=encoding)
            
            # Normalizar nombres de columnas
            df.columns = [cls.normalize_name(str(col)) for col in df.columns]
            
            # Limpiar datos
            df = df.replace({pd.NA: None, '': None})
            
            # Preview
            preview_data = df.head(10).to_dict('records')
            columns = df.columns.tolist()
            
            # Crear registros
            if column_mapping:
                records = cls._create_instances_with_mapping(df, model, column_mapping)
            else:
                records = cls._create_instances_auto(df, model)
            
            logger.info(f"CSV procesado - {len(records)} registros, {len(columns)} columnas")
            return records, preview_data, columns
            
        except Exception as e:
            logger.error(f"Error procesando CSV: {str(e)}", exc_info=True)
            raise ValueError(f"Error al procesar archivo CSV: {str(e)}")
    
    @classmethod
    def get_model_fields(cls, model: Model) -> Dict:
        """Obtiene campos del modelo normalizados"""
        from django.db.models import Field
        
        fields = {}
        for field in model._meta.get_fields():
            if isinstance(field, Field) and not field.auto_created:
                normalized = cls.normalize_name(field.name)
                fields[normalized] = field
        return fields
    
    @classmethod
    def _create_instances_auto(cls, df: pd.DataFrame, model: Model) -> List:
        """
        Crea instancias usando mapeo automático.

        Strategy: build a reverse map  normalized_col_name → original_df_col_name
        so that model fields like "fecha_llamada" can find DF columns named
        "Fecha Llamada", "fecha-llamada", "FECHA LLAMADA", etc.
        """
        model_fields = cls.get_model_fields(model)  # {norm_field_name: field_obj}

        # Map: normalized(df_col) → original df column name
        # Use positional enumeration to safely handle duplicate column names
        norm_to_orig = {}
        for i, col in enumerate(df.columns):
            norm_col = cls.normalize_name(str(col))
            if norm_col not in norm_to_orig:          # first occurrence wins
                norm_to_orig[norm_col] = col

        # Intersect: which model fields have a matching DF column?
        matched = {}   # field_obj → original_df_col_name
        for norm_field, field_obj in model_fields.items():
            if norm_field in norm_to_orig:
                matched[field_obj] = norm_to_orig[norm_field]

        if not matched:
            logger.warning(
                "_create_instances_auto: no model fields matched any DataFrame column. "
                "Model fields (norm): %s | DF cols (norm): %s",
                list(model_fields.keys()), list(norm_to_orig.keys())
            )
            return []

        logger.debug(
            "_create_instances_auto: matched %d/%d fields: %s",
            len(matched), len(model_fields),
            {f.name: orig for f, orig in matched.items()}
        )

        records = []
        for idx, row in df.iterrows():
            instance_data = {}
            for field_obj, orig_col in matched.items():
                val = row[orig_col]
                if pd.isna(val) if not isinstance(val, str) else val == '':
                    continue
                try:
                    converted = cls._convert_value(field_obj, val)
                    if converted is not None:
                        instance_data[field_obj.name] = converted
                except (ValueError, TypeError) as e:
                    logger.debug(
                        "Error convirtiendo '%s' → %s: %s", val, field_obj.name, e
                    )
                    continue

            if instance_data:
                try:
                    records.append(model(**instance_data))
                except Exception as e:
                    logger.warning("Error creando instancia fila %s: %s", idx, e)
                    continue

        return records
    
    @classmethod
    def _create_instances_with_mapping(cls, df: pd.DataFrame, model: Model,
                                      column_mapping: Dict) -> List:
        """
        Crea instancias usando mapeo personalizado.
        column_mapping: {df_col_name: model_field_name}
        Both exact and normalized matching are attempted for df_col_name.
        """
        # Build normalized→original reverse map for the DF
        norm_to_orig = {}
        for col in df.columns:
            norm = cls.normalize_name(str(col))
            if norm not in norm_to_orig:
                norm_to_orig[norm] = col

        records = []
        for idx, row in df.iterrows():
            instance_data = {}
            for csv_col, model_field in column_mapping.items():
                if not model_field:
                    continue
                # Try exact match first, then normalized match
                orig_col = csv_col if csv_col in df.columns else norm_to_orig.get(cls.normalize_name(csv_col))
                if not orig_col:
                    continue
                val = row[orig_col]
                if pd.isna(val) if not isinstance(val, str) else val == '':
                    continue
                try:
                    field = model._meta.get_field(model_field)
                    value = cls._convert_value(field, val)
                    if value is not None:
                        instance_data[model_field] = value
                except (FieldDoesNotExist, ValueError, TypeError) as e:
                    logger.debug(f"Error con campo {model_field}: {str(e)}")
                    continue

            if instance_data:
                try:
                    records.append(model(**instance_data))
                except Exception as e:
                    logger.warning(f"Error creando instancia fila {idx}: {str(e)}")
                    continue

        return records
    
    @staticmethod
    def _convert_value(field, value):
        """Convierte un valor según el tipo de campo"""
        if pd.isna(value) or value == '':
            return None
        
        field_type = field.get_internal_type()
        
        try:
            if field_type in ['IntegerField', 'AutoField']:
                return int(float(str(value).replace(',', '.')))
            
            elif field_type in ['FloatField', 'DecimalField']:
                return float(str(value).replace(',', '.'))
            
            elif field_type == 'BooleanField':
                if isinstance(value, bool):
                    return value
                str_val = str(value).lower().strip()
                return str_val in ['true', '1', 'yes', 'sí', 'si', 'on']
            
            elif field_type in ['DateField', 'DateTimeField']:
                return pd.to_datetime(value).to_pydatetime()
            
            elif field_type in ['CharField', 'TextField', 'SlugField']:
                return str(value).strip()
            
            return value
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Error convirtiendo valor '{value}' a {field_type}: {str(e)}")
            return None