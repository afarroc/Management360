# Standard library imports
import os
import csv
from io import BytesIO, StringIO

# Third-party imports
import pandas as pd
import chardet

# Django imports
from django.core.exceptions import FieldDoesNotExist

class FileProcessor:
    """Class to unify the processing of CSV and Excel files"""
    
    @staticmethod
    def detect_encoding(file):
        """Detect the encoding of a CSV file"""
        # Read a portion of the file to detect encoding
        raw_data = file.read(10240)
        result = chardet.detect(raw_data)
        file.seek(0)
        if result['encoding'] in ['ISO-8859-1', 'Windows-1252']:
            return 'latin-1'
        return result['encoding'] if result['confidence'] > 0.6 else 'latin-1'
    
    @staticmethod
    def normalize_name(name):
        """Normalize column names"""
        if not name:
            return ''
        name = str(name).strip().lower()
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            ' ': '_', '-': '_', '.': '_', '/': '_'
        }
        for orig, repl in replacements.items():
            name = name.replace(orig, repl)
        return name
    
    @classmethod
    def get_model_fields(cls, model):
        """Retrieve normalized model fields"""
        return {
            cls.normalize_name(f.name): f 
            for f in model._meta.get_fields() 
            if f.concrete and not f.auto_created
        }
    
    @classmethod
    def process_file(cls, file, model, sheet_name=None, cell_range=None, column_mapping=None):
        """Process a file (CSV or Excel) and return records and metadata"""
        file_extension = os.path.splitext(file.name)[1].lower()
        
        if file_extension in ('.xls', '.xlsx'):
            return cls.process_excel(file, model, sheet_name, cell_range, column_mapping)
        else:
            return cls.process_csv(file, model, column_mapping)
      
    @classmethod
    def process_excel(cls, file, model, sheet_name=None, cell_range=None, column_mapping=None):
        """Process an Excel file"""
        try:
            df = pd.read_excel(
                BytesIO(file.read()),
                sheet_name=sheet_name or 0,
                usecols=cell_range if cell_range else None
            )
            file.seek(0)
            
            # Extract preview data and column names
            preview_data = df.head().to_dict('records')
            columns = [str(col) for col in df.columns.tolist()]
            
            # Create records based on column mapping or auto-mapping
            if column_mapping:
                records = cls._create_instances_with_mapping(df, model, column_mapping)
            else:
                records = cls._create_instances_auto(df, model)
            
            return records, preview_data, columns
        
        except Exception as e:
            raise ValueError(f"Error processing Excel: {str(e)}")
    
    @classmethod
    def process_csv(cls, file, model, column_mapping=None, delimiter=';'):
        """Process a CSV file"""
        try:
            encoding = cls.detect_encoding(file)
            decoded_file = file.read().decode(encoding, errors='replace')
            file.seek(0)
            
            reader = csv.DictReader(StringIO(decoded_file), delimiter=delimiter)
            reader.fieldnames = [cls.normalize_name(name) for name in (reader.fieldnames or [])]
            
            df = pd.DataFrame(list(reader))
            
            # Extract preview data and column names
            preview_data = df.head().to_dict('records')
            columns = [str(col) for col in (df.columns.tolist() if not df.empty else [])]
            
            # Create records based on column mapping or auto-mapping
            if column_mapping:
                records = cls._create_instances_with_mapping(df, model, column_mapping)
            else:
                records = cls._create_instances_auto(df, model)
            
            return records, preview_data, columns
        
        except UnicodeDecodeError as e:
            raise ValueError(f"Error decoding the file: {str(e)}")
        except csv.Error as e:
            raise ValueError(f"CSV format error: {str(e)}")
        except pd.errors.EmptyDataError:
            raise ValueError("The CSV file is empty or contains no valid data")
        except Exception as e:
            raise ValueError(f"Error processing CSV: {str(e)}")
    
    @classmethod
    def _create_instances_auto(cls, df, model):
        """Create model instances using automatic mapping"""
        model_fields = cls.get_model_fields(model)
        records = []
        
        for _, row in df.iterrows():
            instance_data = {}
            for field_name, field in model_fields.items():
                if field_name in df.columns and pd.notna(row[field_name]):
                    instance_data[field.name] = cls._convert_value(field, row[field_name])
            
            if instance_data:
                records.append(model(**instance_data))
        
        return records
    
    @classmethod
    def _create_instances_with_mapping(cls, df, model, column_mapping):
        """Create model instances using custom column mapping"""
        records = []
        
        for _, row in df.iterrows():
            instance_data = {}
            for csv_col, model_field in column_mapping.items():
                if model_field and csv_col in df.columns and pd.notna(row[csv_col]):
                    try:
                        field = model._meta.get_field(model_field)
                        instance_data[model_field] = cls._convert_value(field, row[csv_col])
                    except FieldDoesNotExist:
                        continue
            
            if instance_data:
                records.append(model(**instance_data))
        
        return records
    
    @staticmethod
    def _convert_value(field, value):
        """Convert value based on the field type"""
        if pd.isna(value):
            return None
            
        if field.get_internal_type() == 'IntegerField':
            return int(float(value))
        elif field.get_internal_type() == 'FloatField':
            if isinstance(value, str):
                value = value.replace(',', '.')
            return float(value)
        elif field.get_internal_type() == 'CharField':
            return str(value).strip()
        elif field.get_internal_type() == 'BooleanField':
            return bool(value)
        return value