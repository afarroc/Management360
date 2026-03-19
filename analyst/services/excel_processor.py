# analyst/services/excel_processor.py
import logging
import pandas as pd
from typing import Tuple, Dict, Optional
from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)

class ExcelProcessor:
    """Servicio especializado para procesar archivos Excel con opciones avanzadas"""
    
    # analyst/services/excel_processor.py
    
    @staticmethod
    def process_excel(file, sheet_name=None, cell_range=None, no_header=False):
        """
        Procesa un archivo Excel con opciones de hoja, rango y cabecera
        
        Args:
            file: Archivo Excel
            sheet_name: Nombre de la hoja o índice (None para primera hoja)
            cell_range: Rango de celdas (ej: 'A1:C10')
            no_header: Si True, no usa la primera fila como cabecera
        
        Returns:
            Tuple[pd.DataFrame, Dict]: DataFrame y metadatos
        """
        logger.debug(f"Procesando Excel - Sheet: {sheet_name}, Range: {cell_range}, NoHeader: {no_header}")
        
        excel_file = pd.ExcelFile(file)
        
        # Determinar qué hoja usar
        if sheet_name is None or sheet_name == '':
            selected_sheet = 0
            sheet_name_used = excel_file.sheet_names[0]
        else:
            try:
                selected_sheet = int(sheet_name)
                sheet_name_used = excel_file.sheet_names[selected_sheet]
            except (ValueError, IndexError):
                selected_sheet = sheet_name
                sheet_name_used = sheet_name
        
        logger.info(f"Usando hoja: {sheet_name_used}")
        
        metadata = {
            'type': 'excel',
            'available_sheets': excel_file.sheet_names,
            'selected_sheet': sheet_name_used,
            'no_header': no_header
        }
        
        try:
            if cell_range and ':' in cell_range:
                df = ExcelProcessor._read_with_range(excel_file, selected_sheet, cell_range, no_header)
                metadata['cell_range'] = cell_range
            else:
                # Leer todo el archivo
                if no_header:
                    df = pd.read_excel(excel_file, sheet_name=selected_sheet, header=None)
                    # Asignar nombres genéricos a las columnas
                    df.columns = [f"Columna{i+1}" for i in range(len(df.columns))]
                else:
                    df = pd.read_excel(excel_file, sheet_name=selected_sheet)
                metadata['cell_range'] = 'full'
            
            # Validar DataFrame
            if df.empty:
                raise ValueError("El archivo Excel no contiene datos en el rango especificado")
            
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
    
    @staticmethod
    def _read_with_range(excel_file, sheet_name, cell_range, no_header=False):
        """
        Lee un Excel con un rango específico de celdas
        """
        start, end = cell_range.split(':')
        
        # Parsear coordenadas
        start_col = ExcelProcessor._get_col_letters(start)
        start_row = ExcelProcessor._get_row_number(start) - 1
        end_col = ExcelProcessor._get_col_letters(end)
        end_row = ExcelProcessor._get_row_number(end)
        
        start_col_idx = ExcelProcessor._col_to_index(start_col)
        end_col_idx = ExcelProcessor._col_to_index(end_col)
        
        # Leer Excel sin headers
        full_df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
        
        # Validar límites
        max_rows, max_cols = full_df.shape
        ExcelProcessor._validate_range(start_col_idx, end_col_idx, start_row, 
                                      end_row, max_cols, max_rows)
        
        # Extraer datos
        data = full_df.iloc[start_row:end_row, start_col_idx:end_col_idx + 1]
        
        if no_header:
            # Si no hay cabecera, usar nombres genéricos
            df = pd.DataFrame(data.values)
            df.columns = [f"Columna{i+1}" for i in range(len(df.columns))]
            return df
        else:
            # Usar primera fila como headers
            if len(data) > 0:
                headers = [str(col) for col in data.iloc[0]]
                result_df = pd.DataFrame(data.values[1:], columns=headers)
                return result_df
        
        return pd.DataFrame()    

    @staticmethod
    def _get_col_letters(cell: str) -> str:
        """Extrae las letras de columna de una referencia de celda (ej: 'A1' -> 'A')"""
        letters = ''.join([c for c in str(cell) if c.isalpha()])
        if not letters:
            raise ValueError(f"Formato de celda inválido: '{cell}'")
        return letters.upper()
    
    @staticmethod
    def _get_row_number(cell: str) -> int:
        """Extrae el número de fila de una referencia de celda (ej: 'A1' -> 1)"""
        digits = ''.join([c for c in str(cell) if c.isdigit()])
        if not digits:
            raise ValueError(f"Formato de celda inválido: '{cell}'")
        return int(digits)
    
    @staticmethod
    def _col_to_index(col_letters: str) -> int:
        """Convierte letras de columna a índice base 0 (A=0, B=1, ..., Z=25, AA=26)"""
        index = 0
        for char in col_letters:
            if not char.isalpha():
                raise ValueError(f"Carácter inválido en columna: '{char}'")
            index = index * 26 + (ord(char.upper()) - ord('A') + 1)
        return index - 1
    
    @staticmethod
    def _validate_range(start_col: int, end_col: int, start_row: int, 
                       end_row: int, max_cols: int, max_rows: int):
        """Valida que el rango esté dentro de los límites del Excel"""
        if start_col >= max_cols or end_col >= max_cols:
            max_col_letter = ExcelProcessor._index_to_col(max_cols - 1)
            raise ValueError(
                f"El rango de columnas excede las disponibles (máx: columna {max_col_letter})"
            )
        
        if start_row >= max_rows or end_row > max_rows:
            raise ValueError(
                f"El rango de filas excede las disponibles (máx: fila {max_rows})"
            )
    
    @staticmethod
    def _index_to_col(index: int) -> str:
        """Convierte un índice de columna a letras (0=A, 1=B, ..., 25=Z, 26=AA)"""
        letters = ""
        index += 1
        while index > 0:
            index -= 1
            letters = chr(65 + (index % 26)) + letters
            index //= 26
        return letters