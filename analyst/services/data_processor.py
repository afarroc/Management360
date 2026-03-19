# analyst/services/data_processor.py
import logging
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, Optional, List
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Model

logger = logging.getLogger(__name__)

class DataProcessor:
    """Servicio para procesar archivos de datos (CSV/Excel)"""
    
    @staticmethod
    def process_file(file: UploadedFile, model: Model, sheet_name: Optional[str] = None, 
                    cell_range: Optional[str] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Procesa un archivo y retorna un DataFrame con metadatos
        
        Returns:
            Tuple[pd.DataFrame, Dict]: DataFrame procesado y metadatos
        """
        logger.info(f"Procesando archivo: {file.name}")
        
        try:
            if file.name.endswith('.csv'):
                df, metadata = DataProcessor._process_csv(file)
            else:
                from analyst.services.excel_processor import ExcelProcessor
                df, metadata = ExcelProcessor.process_excel(file, sheet_name, cell_range)
            
            # Validaciones comunes
            if df.empty:
                raise ValueError("El archivo no contiene datos")
            
            logger.info(f"Archivo procesado - Shape: {df.shape}")
            return df, metadata
            
        except Exception as e:
            logger.error(f"Error procesando archivo: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def _process_csv(file: UploadedFile) -> Tuple[pd.DataFrame, Dict]:
        """Procesa archivos CSV con múltiples codificaciones"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                file.seek(0)
                df = pd.read_csv(file, encoding=encoding)
                logger.info(f"CSV leído con encoding: {encoding}")
                return df, {'encoding': encoding, 'type': 'csv'}
            except UnicodeDecodeError:
                continue
        
        # Último intento
        file.seek(0)
        df = pd.read_csv(file, encoding='utf-8', errors='ignore')
        return df, {'encoding': 'utf-8 (with errors ignored)', 'type': 'csv'}