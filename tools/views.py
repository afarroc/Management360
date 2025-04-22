# Standard library imports
import logging
import os
import csv
from io import BytesIO, StringIO

# Third-party imports
import pandas as pd
import chardet

# Django imports
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages
from django.apps import apps
from django.core.exceptions import FieldDoesNotExist

# Local imports
from .planning import (AgentsFTE, utilisation)
from .utils import calcular_trafico_intensidad
from .forms import DataUploadForm

# Configurar el logger para incluir el nombre de la función
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s'
)

logger = logging.getLogger(__name__)


class FileProcessor:
    """Clase para unificar el procesamiento de archivos CSV y Excel"""
    
    @staticmethod
    def detect_encoding(file):
        """Detectar codificación de archivos CSV"""
        raw_data = file.read(10240)
        result = chardet.detect(raw_data)
        file.seek(0)
        if result['encoding'] in ['ISO-8859-1', 'Windows-1252']:
            return 'latin-1'
        return result['encoding'] if result['confidence'] > 0.6 else 'latin-1'
    
    @staticmethod
    def normalize_name(name):
        """Normalizar nombres de columnas"""
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
        """Obtener campos del modelo normalizados"""
        return {
            cls.normalize_name(f.name): f 
            for f in model._meta.get_fields() 
            if f.concrete and not f.auto_created
        }
    
    @classmethod
    def process_file(cls, file, model, sheet_name=None, cell_range=None, column_mapping=None):
        """Procesar archivo (CSV o Excel) y devolver registros y metadatos"""  # Corregido typo
        logger.info(f"Procesando archivo: {file.name}")
        logger.info(f"Tipo de archivo: {file.content_type}")
        logger.info(f"Nombre de la hoja: {sheet_name}")
        logger.info(f"Rango de celdas: {cell_range}")
        logger.info(f"Datos del mapeo: {column_mapping}")
        
        file_extension = os.path.splitext(file.name)[1].lower()
        
        if file_extension in ('.xls', '.xlsx'):
            
            logger.info(f"Archivo es Excel, procesando como Excel")
            logger.info(f"Tipo de archivo: {file.content_type}")
            return cls.process_excel(file, model, sheet_name, cell_range, column_mapping)
        else:
            logger.info(f"Archivo no es Excel, procesando como CSV")
            logger.info(f"Tipo de archivo: {file.content_type}")
                
            logger.info(f"Nombre de la hoja: {sheet_name}")
            logger.info(f"Rango de celdas: {cell_range}")
            logger.info(f"Datos del mapeo: {column_mapping}")
            logger.info(f"Datos del formulario: {file.name}")
            logger.info(f"Datos del formulario: {file.content_type}")
            return cls.process_csv(file, model, column_mapping)
      
    @classmethod
    def process_excel(cls, file, model, sheet_name=None, cell_range=None, column_mapping=None):
        """Procesar archivo Excel"""
        try:
            df = pd.read_excel(
                BytesIO(file.read()),
                sheet_name=sheet_name or 0,
                usecols=cell_range if cell_range else None
            )
            file.seek(0)
            
            preview_data = df.head().to_dict('records')
            columns = [str(col) for col in df.columns.tolist()]
            
            if column_mapping:
                records = cls._create_instances_with_mapping(df, model, column_mapping)
            else:
                records = cls._create_instances_auto(df, model)
            
            return records, preview_data, columns
        
        except Exception as e:
            raise ValueError(f"Error al procesar Excel: {str(e)}")
    
    @classmethod
    def process_csv(cls, file, model, column_mapping=None, delimiter=';'):  # Delimiter configurable
        """Procesar archivo CSV"""
        logger.info(f"Iniciando procesamiento de archivo CSV: {file.name}")
        logger.info(f"Tipo de archivo: {file.content_type}")
        logger.info(f"Delimitador configurado: {delimiter}")
        logger.info(f"Configuración de mapeo de columnas: {column_mapping}")
        logger.info(f"Modelo destino: {model.__name__}")
        
        try:
            # Detectar codificación del archivo CSV
            logger.info("Detectando codificación del archivo...")
            encoding = cls.detect_encoding(file)
            logger.info(f"Codificación detectada: {encoding}")
            
            logger.info("Decodificando archivo...")
            decoded_file = file.read().decode(encoding, errors='replace')
            file.seek(0)  # Resetear posición del archivo para posibles lecturas futuras
            logger.debug(f"Primeros 100 caracteres decodificados: {decoded_file[:100]}...")
            
            logger.info("Creando lector CSV...")
            reader = csv.DictReader(StringIO(decoded_file), delimiter=delimiter)
            original_fieldnames = reader.fieldnames
            reader.fieldnames = [cls.normalize_name(name) for name in (reader.fieldnames or [])]
            logger.info(f"Nombres de columnas originales: {original_fieldnames}")
            logger.info(f"Nombres de columnas normalizados: {reader.fieldnames}")
            
            # Convertir a DataFrame para consistencia con Excel
            logger.info("Convirtiendo datos a DataFrame...")
            df = pd.DataFrame(list(reader))
            logger.info(f"DataFrame creado con {len(df)} filas y {len(df.columns)} columnas")
            
            preview_data = df.head().to_dict('records')
            columns = [str(col) for col in (df.columns.tolist() if not df.empty else [])]
            logger.info(f"Datos de vista previa: {preview_data}")
            logger.info(f"Columnas disponibles: {columns}")
            
            if column_mapping:
                logger.info("Procesando con mapeo de columnas especificado...")
                records = cls._create_instances_with_mapping(df, model, column_mapping)
                logger.info(f"Se crearon {len(records)} instancias usando mapeo personalizado")
            else:
                logger.info("Procesando con mapeo automático de columnas...")
                records = cls._create_instances_auto(df, model)
                logger.info(f"Se crearon {len(records)} instancias usando mapeo automático")
            
            logger.info("Procesamiento de CSV completado exitosamente")
            return records, preview_data, columns
        
        except UnicodeDecodeError as e:
            logger.error(f"Error de decodificación: {str(e)}")
            raise ValueError(f"Error al decodificar el archivo: {str(e)}")
        except csv.Error as e:
            logger.error(f"Error de formato CSV: {str(e)}")
            raise ValueError(f"Error en el formato del archivo CSV: {str(e)}")
        except pd.errors.EmptyDataError:
            logger.error("El archivo CSV está vacío")
            raise ValueError("El archivo CSV está vacío o no contiene datos válidos")
        except Exception as e:
            logger.error(f"Error inesperado al procesar CSV: {str(e)}", exc_info=True)
            raise ValueError(f"Error al procesar CSV: {str(e)}")
    
    @classmethod
    def _create_instances_auto(cls, df, model):
        """Crear instancias del modelo con mapeo automático"""
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
        """Crear instancias del modelo con mapeo personalizado"""
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
        """Convertir valor según el tipo de campo"""
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


# Calculator views
def calculate_agents(request):
    if request.method == 'POST':
        calls = int(request.POST.get('calls'))
        reporting_period = int(request.POST.get('reporting_period'))
        average_handling_time = float(request.POST.get('average_handling_time'))
        service_level_agreement = float(request.POST.get('service_level_agreement'))
        service_level_time = float(request.POST.get('service_level_time'))
        shrinkage = float(request.POST.get('shrinkage'))

        agents_required = AgentsFTE(calls, reporting_period, average_handling_time, 
                                  service_level_agreement, service_level_time, shrinkage)
        utilization = utilisation(calls, agents_required)

        context = {'agents_required': agents_required, 'utilization': utilization}
        return render(request, 'calculator.html', context)
    else:
        return render(request, 'calculator.html')


def calcular_trafico_intensidad_view(request):
    if request.method == 'POST':
        llamadas = int(request.POST.get('llamadas'))
        tiempo_manejo_promedio = int(request.POST.get('tiempo_manejo_promedio'))

        trafico_intensidad = calcular_trafico_intensidad(llamadas, tiempo_manejo_promedio)

        return JsonResponse({'trafico_intensidad': trafico_intensidad})

    return render(request, 'calculator.html')


# File management views
def file_tree_view(request):
    """
    Generate a JSON response with the file tree structure of a given app directory.
    If no app_name is provided, list all apps in the project.
    """
    app_name = request.GET.get("app_name", "")  # Get the app name from the query parameters

    if not app_name:
        # List all apps in the project
        apps_dir = os.path.join(settings.BASE_DIR)
        apps = [
            {"name": app, "type": "directory"}
            for app in os.listdir(apps_dir)
            if os.path.isdir(os.path.join(apps_dir, app)) and not app.startswith("__")
        ]
        return JsonResponse(apps, safe=False)

    # Generate file tree for the specified app
    base_dir = os.path.join(settings.BASE_DIR, app_name)
    if not os.path.exists(base_dir):
        return JsonResponse({"error": f"The app '{app_name}' does not exist or its directory is invalid."}, status=400)

    def get_file_tree(directory):
        tree = []
        for entry in os.listdir(directory):
            entry_path = os.path.join(directory, entry)
            if os.path.isdir(entry_path):
                tree.append({"name": entry, "type": "directory", "children": get_file_tree(entry_path)})
            else:
                tree.append({"name": entry, "type": "file"})
        return tree

    file_tree = get_file_tree(base_dir)
    return JsonResponse(file_tree, safe=False)


from .constants import FORBIDDEN_MODELS, MAX_RECORDS_FOR_DELETION, MAX_RECORDS_FOR_IMPORT

def upload_data(request):
    if request.method == 'POST':
        # Verificar si el usuario tiene permisos para cargar datos        
        form = DataUploadForm(request.POST, request.FILES)        
        is_confirmation = request.POST.get('is_confirmation') == 'true'

        # Para confirmaciones, reconstruir el formulario con el archivo
        if is_confirmation:
            # Reconstruir el formulario con los datos originales
            # Copiar los datos del formulario original
            form_data = request.POST.copy()
            form_files = request.FILES.copy()
            logger.info("Confirmación de carga de datos")
            logger.info(f"Datos del formulario original: {form_data}")
            logger.info(f"Archivos del formulario original: {form_files}")
            
            # Si no hay archivo en FILES pero hay uno en el formulario original
            if not form_files.get('file') and 'original_filename' in request.POST:
                # Reconstruir el formulario con los datos originales
                form = DataUploadForm(form_data, form_files)
            else:
                form = DataUploadForm(request.POST, request.FILES)
        else:
            form = DataUploadForm(request.POST, request.FILES)
        
        logger.info(f"Usuario {request.user.id} - {request.user.username} inició la carga de datos")
        logger.info(f"IP del usuario: {request.META.get('REMOTE_ADDR')}")
        logger.info(f"Datos del formulario recibidos: {request.POST}")
        logger.info(f"Archivos recibidos: {request.FILES}")
        logger.info(f"Archivo recibido: {request.FILES.get('file')}")
        logger.info(f"Modelo recibido: {request.POST.get('model')}")
        logger.info(f"Nombre de la hoja: {request.POST.get('sheet_name')}")
        logger.info(f"Rango de celdas: {request.POST.get('cell_range')}")
        logger.info(f"Datos del mapeo: {request.POST.get('map_columns')}")
        logger.info(f"-----------------------------")
        logger.info("Iniciando procesamiento del formulario")
        logger.info(f"-----------------------------")         
               
        if form.is_valid():
            try:
                logger.info("Formulario válido, procesando datos")
                logger.info(f"Datos del formulario limpiados: {form.cleaned_data}")
                logger.info(f"Datos del formulario: {form.cleaned_data.get('file')}")
                logger.info(f"Datos del formulario: {form.cleaned_data.get('model')}")
                logger.info(f"Datos del formulario: {form.cleaned_data.get('sheet_name')}")
                logger.info(f"Datos del formulario: {form.cleaned_data.get('cell_range')}")
                logger.info(f"Datos del formulario: {request.POST.get('map_columns')}") 
                logger.info(f"-----------------------------")
                logger.info("Iniciando procesamiento del archivo")
                logger.info(f"-----------------------------")
                
                model = form.cleaned_data['model']
                file = form.cleaned_data.get('file')
                
                # Si es confirmación y no hay archivo en cleaned_data, intentar obtenerlo de FILES
                if is_confirmation and not file:
                    file = request.FILES.get('file')
                
                if not file:
                    messages.error(request, "No se encontró el archivo para procesar")
                    return redirect('upload_data')
                
                model_path = f"{model._meta.app_label}.{model.__name__}"
                
                model_path = f"{model._meta.app_label}.{model.__name__}"
                
                # Validación de modelo prohibido
                if model_path in FORBIDDEN_MODELS:
                    error_msg = (
                        f"Acceso denegado: El modelo '{model._meta.verbose_name}' "
                        f"({model_path}) es un modelo del sistema y no puede ser modificado."
                    )
                    logger.warning(error_msg)
                    raise PermissionError(error_msg)
                
                # Validación de permisos de usuario
                if not request.user.is_superuser and hasattr(model, 'is_restricted') and model.is_restricted:
                    error_msg = (
                        f"Acceso denegado: No tiene permisos suficientes para modificar "
                        f"el modelo '{model._meta.verbose_name}'."
                    )
                    logger.warning(error_msg)
                    raise PermissionError(error_msg)
                
                # Operación de limpieza
                if form.cleaned_data['clear_existing']:
                    logger.info(f"Se solicitó limpiar los datos existentes del modelo: {model_path}")
                    record_count = model.objects.count()
                    logger.info(f"Registros existentes en el modelo: {record_count}")
                    
                    if record_count > MAX_RECORDS_FOR_DELETION:
                        error_msg = (
                            f"Operación cancelada: Intento de borrar {record_count} registros en "
                            f"'{model._meta.verbose_name}'. El límite es {MAX_RECORDS_FOR_DELETION}."
                        )
                        logger.error(error_msg)
                        raise SecurityError(error_msg)
                    
                    model.objects.all().delete()
                    logger.info(f"Se eliminaron todos los registros existentes en {model_path}")
                    messages.info(
                        request, 
                        f"Se eliminaron todos los registros existentes en {model._meta.verbose_name}"
                    )
                
                # Procesamiento según el tipo de acción
                if 'preview' in request.POST:
                    logger.info("Generando vista previa de importación")
                    return handle_preview(request, form, model, file)
                
                elif 'confirm_import' in request.POST:
                    logger.info("Confirmando importación con mapeo de columnas")
                    return handle_import_with_mapping(request, form, model, file)
                
                else:
                    logger.info("Realizando importación directa sin vista previa")
                    return handle_direct_import(request, form, model, file)
            
            except PermissionError as e:
                logger.warning(f"Error de permisos: {str(e)}")
                messages.error(request, str(e))
            
            except SecurityError as e:
                logger.error(f"Error de seguridad: {str(e)}")
                messages.error(request, str(e))
            
            except Exception as e:
                
                logger.error(f"Error inesperado: {str(e)}", exc_info=True)
                messages.error(request, f"Error al procesar los datos: {str(e)}")                


        
        else:
            logger.warning("Formulario inválido, mostrando errores")
            logger.warning(f"Errores del formulario: {form.errors}")
            messages.error(request, "Error en el formulario. Verifique los datos ingresados.")
            # Mostrar errores específicos del formulario
            

                
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return render(request, 'tools/upload_data.html', {'form': form})
                
    return render(request, 'tools/upload_data.html', {'form': form if 'form' in locals() else DataUploadForm()})

# Funciones auxiliares para mejor organización
def handle_preview(request, form, model, file):
    """Maneja la solicitud de vista previa"""
    # Obtener datos de la vista previa
    # y procesar el archivo
    logger.info("Generando vista previa de importación")
    logger.info(f"Cantidad de registros a procesar: {file.size}")
    logger.info(f"Nombre de la hoja: {form.cleaned_data.get('sheet_name')}")
    logger.info(f"Rango de celdas: {form.cleaned_data.get('cell_range')}")
    logger.info(f"Datos del mapeo: {request.POST.get('map_columns')}")
    logger.info(f"Datos del formulario: {request.POST}")
    logger.info(f"Usuario: {request.user.id} - {request.user.username}")
    logger.info(f"IP del usuario: {request.META.get('REMOTE_ADDR')}")
    logger.info(f"Nombre del archivo: {file.name}")
    logger.info(f"Tipo de archivo: {file.content_type}")
    
    
    records, preview_data, columns = FileProcessor.process_file(
        file,
        model,
        form.cleaned_data.get('sheet_name'),
        form.cleaned_data.get('cell_range')
    )
    
    model_fields = [f.name for f in model._meta.get_fields() 
                   if f.concrete and not f.auto_created]
    
    return render(request, 'tools/upload_data.html', {
        'form': form,
        'preview_data': preview_data,
        'columns': columns,
        'model_fields': model_fields,
        'show_preview': True
    })

def handle_import_with_mapping(request, form, model, file):
    """Maneja la importación con mapeo de columnas"""
    try:
        column_mapping = {
            col: request.POST.get(f'map_{col}')
            for col in request.POST.keys() if col.startswith('map_')
        }
        
        logger.info(f"Mapeo de columnas recibido: {column_mapping}")
        
        records, _, _ = FileProcessor.process_file(
            file,
            model,
            form.cleaned_data.get('sheet_name'),
            form.cleaned_data.get('cell_range'),
            column_mapping
        )
        
        if records:
            if len(records) > MAX_RECORDS_FOR_IMPORT:
                raise SecurityError(f"Demasiados registros para importar de una vez (límite: {MAX_RECORDS_FOR_IMPORT})")
            
            model.objects.bulk_create(records)
            msg = (f"¡Importación completada con éxito!<br>"
                  f"<strong>{len(records)}</strong> registros cargados en <strong>{model._meta.verbose_name}</strong>")
            messages.success(request, msg)
            logger.info(f"Importación exitosa: {len(records)} registros en {model.__name__}")
            return redirect('upload_data')
        
        messages.warning(request, "No se encontraron datos válidos para importar")
        return redirect('upload_data')
    
    except Exception as e:
        logger.error(f"Error en importación con mapeo: {str(e)}", exc_info=True)
        messages.error(request, f"Error al importar datos: {str(e)}")
        return redirect('upload_data')

def handle_direct_import(request, form, model, file):
    """Maneja la importación directa sin vista previa"""
    records, _, _ = FileProcessor.process_file(
        file,
        model,
        form.cleaned_data.get('sheet_name'),
        form.cleaned_data.get('cell_range')
    )
    
    if records:
        if len(records) > 10000:  # Límite de registros por importación
            raise SecurityError("Demasiados registros para importar de una vez (límite: 10,000)")
        
        model.objects.bulk_create(records)
        messages.success(request, f"{len(records)} registros cargados en {model._meta.verbose_name}")
        return redirect('upload_data')
    
    messages.warning(request, "No se encontraron datos válidos para importar")
    return redirect('upload_data')

# Excepciones personalizadas
class SecurityError(Exception):
    """Excepción para problemas de seguridad"""
    pass


