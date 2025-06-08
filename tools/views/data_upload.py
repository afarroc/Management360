from django.shortcuts import render, redirect
from django.contrib import messages
from django.apps import apps
from django.db import transaction
from django.db.models import Field
from difflib import get_close_matches
import pandas as pd
import numpy as np
import sys
from io import StringIO
from tools.forms import DataUploadForm
from tools.utils import DataFrameClipboard
from django.views.decorators.http import require_http_methods
import logging
from django.urls import reverse

logger = logging.getLogger(__name__)

class DataUploadDashboard:
    """
    Clase principal para el panel de administración de cargas de datos
    """
    @staticmethod
    @require_http_methods(["GET", "POST"])
    def dashboard(request):
        """
        Vista principal del panel de administración de cargas
        """
        # Inicializar el portapapeles si no existe
        if 'clipboard_keys' not in request.session:
            request.session['clipboard_keys'] = []
            request.session.modified = True

        if request.method == 'POST':
            return DataUploadDashboard._handle_post_actions(request)
        
        # Vista GET - Mostrar el panel
        form = DataUploadForm()
        return render(request, 'tools/upload_data_csv.html', {
            'form': form,
            'clipboard_keys': DataFrameClipboard.list_clips(request),
            'dashboard_mode': True
        })

    # Añadir esto en data_upload.py dentro de la clase DataUploadDashboard
    
    @staticmethod
    def _handle_date_conversion(request):
        """
        Maneja la conversión de una columna de string a fecha
        """
        if 'upload_data' not in request.session:
            messages.error(request, "No hay datos para editar")
            return redirect('data_upload')
    
        try:
            upload_data = request.session['upload_data']
            upload_data = DataUploadDashboard._convert_to_consistent_format(upload_data)
            
            # Crear DataFrame
            df = pd.DataFrame.from_records(upload_data['df_rows'])
            df.columns = upload_data['df_columns']
    
            # Obtener parámetros del formulario
            column_to_convert = request.POST.get('date_column')
            date_format = request.POST.get('date_format', '%Y-%m-%d')  # Formato por defecto
            
            if not column_to_convert or column_to_convert not in df.columns:
                messages.error(request, "Columna inválida para conversión")
                return redirect('data_upload')
    
            try:
                # Intentar conversión a fecha
                original_col = df[column_to_convert]
                
                # Primero intentar con el formato especificado
                df[column_to_convert] = pd.to_datetime(
                    df[column_to_convert], 
                    format=date_format,
                    errors='coerce'  # Convertir errores a NaT
                )
                
                # Si hay muchos valores nulos, intentar inferir el formato
                if df[column_to_convert].isna().mean() > 0.5:  # Si más del 50% son nulos
                    df[column_to_convert] = pd.to_datetime(
                        original_col,
                        infer_datetime_format=True,
                        errors='coerce'
                    )
                
                # Verificar si la conversión fue exitosa
                success_rate = 1 - df[column_to_convert].isna().mean()
                if success_rate < 0.7:  # Si menos del 70% se convirtió
                    raise ValueError(f"Solo {success_rate:.0%} de los valores se pudieron convertir")
                
                # Actualizar datos de sesión
                upload_data['df_rows'] = df.replace({np.nan: None}).to_dict('records')
                request.session['upload_data'] = upload_data
                request.session.modified = True
                
                messages.success(
                    request, 
                    f"Columna '{column_to_convert}' convertida a fecha. "
                    f"Éxito: {success_rate:.0%}"
                )
                
            except ValueError as e:
                # Revertir cambios si falla
                df[column_to_convert] = original_col
                messages.error(
                    request, 
                    f"Error al convertir '{column_to_convert}' a fecha: {str(e)}"
                )
            
            return redirect(reverse('data_upload') + '#preview-section')
            
        except Exception as e:
            logger.error(f"Error inesperado en conversión de fecha: {str(e)}", exc_info=True)
            messages.error(request, "Error inesperado al procesar la conversión")
            return redirect('data_upload')
    
    # Actualizar el action_handlers para incluir la nueva acción
    @staticmethod
    def _handle_post_actions(request):
        """
        Maneja todas las acciones POST del dashboard
        """
        action_handlers = {
            'preview': DataUploadDashboard._handle_preview,
            'confirm_upload': DataUploadDashboard._handle_confirm_upload,
            'save_to_clipboard': DataUploadDashboard._handle_save_to_clipboard,
            'load_from_clipboard': DataUploadDashboard._handle_load_from_clipboard,
            'delete_clip': DataUploadDashboard._handle_delete_clip,
            'clear_all_clips': DataUploadDashboard._handle_clear_all_clips,
            'edit_clipboard': DataUploadDashboard._handle_clipboard_edit,
            'convert_to_date': DataUploadDashboard._handle_date_conversion  # Nueva acción
        }
    
        for action in action_handlers:
            if action in request.POST:
                return action_handlers[action](request)
        
        return redirect('data_upload')
    @staticmethod
    def _convert_to_consistent_format(upload_data):
        """Convierte los datos de la sesión a un formato consistente"""
        if isinstance(upload_data['df_rows'][0], dict):
            # Ya está en el formato correcto (lista de diccionarios)
            return upload_data
        
        # Convertir de lista de listas a lista de diccionarios
        columns = upload_data['df_columns']
        rows = upload_data['df_rows']
        
        dict_rows = []
        for row in rows:
            dict_rows.append(dict(zip(columns, row)))
            
        upload_data['df_rows'] = dict_rows
        return upload_data

    @staticmethod
    def _handle_preview(request):
        """
        Maneja la previsualización de datos con logging detallado
        """
        logger.info("Iniciando _handle_preview")
        
        form = DataUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            logger.warning("Formulario inválido - Errores: %s", form.errors)
            return render(request, 'tools/upload_data_csv.html', {
                'form': form,
                'dashboard_mode': True
            })
    
        try:
            logger.info("Formulario válido, procesando archivo...")
            file = request.FILES['file']
            excel_info = None
            model = form.cleaned_data['model']
            logger.debug("Modelo seleccionado: %s", model.__name__)
            
            # Leer archivo según su tipo
            try:
                if file.name.endswith('.csv'):
                    logger.info("Leyendo archivo CSV...")
                    df = pd.read_csv(file)
                    logger.debug("CSV leído correctamente. Dimensiones: %s", df.shape)
                else:
                    logger.info("Procesando archivo Excel...")
                    df, excel_info = DataUploadDashboard._process_excel_file(file, form)
                    logger.debug("Excel procesado. Dimensiones: %s, Info: %s", df.shape, excel_info)
            except Exception as e:
                logger.error("Error al leer archivo: %s", str(e), exc_info=True)
                raise
                
            # Validar tamaño de datos
            data_size = sys.getsizeof(df.values.tolist()) + sys.getsizeof(df.columns.tolist())
            logger.debug("Tamaño de datos calculado: %s bytes", data_size)
            if data_size > 1024 * 1024:  # 1MB
                logger.warning("Archivo demasiado grande (%.2f MB)", data_size/(1024*1024))
                messages.error(request, "El archivo es demasiado grande para previsualizar")
                return redirect('data_upload')
            
            # Procesar información del modelo
            try:
                logger.info("Analizando campos del modelo...")
                model_fields_info, mapped_columns, required_fields = DataUploadDashboard._analyze_model_fields(model, df)
                logger.debug("Campos del modelo analizados. Campos mapeados: %d, Requeridos: %s", 
                            len(mapped_columns), required_fields)
            except Exception as e:
                logger.error("Error al analizar campos del modelo: %s", str(e), exc_info=True)
                raise
                
            # Preparar datos para la sesión
            try:
              
                # Modificar esta parte:
                session_data = {
                  
                    'df_columns': df.columns.tolist(),
                    'df_rows': df.replace({np.nan: None}).to_dict('records'),  # Cambiado a dict
                    'model_path': f"{model._meta.app_label}.{model._meta.model_name}",
                    'clear_existing': form.cleaned_data['clear_existing'],
                    'file_type': 'csv' if file.name.endswith('.csv') else 'excel',
                    'excel_info': excel_info
                }
  
                request.session['upload_data'] = session_data
                logger.debug("Datos de sesión preparados: %s", {k: v for k, v in session_data.items() if k != 'df_rows'})
            except Exception as e:
                logger.error("Error al preparar datos de sesión: %s", str(e), exc_info=True)
                raise
                
            # Preparar información de mapeo de columnas
            try:
                column_mapping_info = DataUploadDashboard._prepare_column_mapping(df, model_fields_info)
                logger.debug("Mapeo de columnas preparado. Total columnas: %d", len(column_mapping_info))
            except Exception as e:
                logger.error("Error al preparar mapeo de columnas: %s", str(e), exc_info=True)
                raise
            # Contexto para la vista
            
            missing_values = {str(col): int(df[col].isnull().sum()) for col in df.columns}
            column_types = {str(col): str(dtype) for col, dtype in df.dtypes.items()}
            # In _handle_preview method, update the context preparation:
            df_info = {
                'rows': len(df),
                'columns': len(df.columns),
                'column_stats': []  # This will contain all column statistics
            }
            
            for col in df.columns:
                col_str = str(col)
                missing_count = int(df[col].isnull().sum())
                missing_percent = (missing_count / df_info['rows']) * 100 if df_info['rows'] > 0 else 0
                
                df_info['column_stats'].append({
                    'name': col_str,
                    'type': str(df[col].dtype),
                    'missing_count': missing_count,
                    'missing_percent': missing_percent
                })

            try:
                context = {
                    'form': form,
                    'preview_mode': True,
                    'target_model': f"{model._meta.app_label}.{model._meta.model_name}",
                    'model_verbose_name': model._meta.verbose_name,
                    'model_fields_info': model_fields_info,
                    'mapped_columns_count': len(mapped_columns),
                    'required_fields': required_fields,
                    'df_info':df_info,
                    'df_preview': {
                        'columns': [str(col) for col in df.columns.tolist()],
                        'rows': df.head(10).values.tolist()
                    },
                    'excel_info': excel_info,
                    'unmapped_columns': [str(col) for col in df.columns 
                                        if str(col).lower() not in {f['name'].lower() for f in model_fields_info} 
                                        and str(col).lower() not in {f['verbose_name'].lower() for f in model_fields_info}],
                    'column_mapping_info': column_mapping_info,
                    'clipboard_keys': DataFrameClipboard.list_clips(request),
                    'dashboard_mode': True
                }
                logger.debug("Contexto preparado. Total filas: %d, columnas: %d", len(df), len(df.columns))
                logger.info("Previsualización lista para renderizar")
                
                return render(request, 'tools/upload_data_csv.html', context)
                
            except Exception as e:
                logger.error("Error al preparar contexto: %s", str(e), exc_info=True)
                raise
                
        except Exception as e:
            logger.critical("Error crítico en _handle_preview: %s", str(e), exc_info=True)
            form.add_error(None, f"Error reading file: {str(e)}")
            return render(request, 'tools/upload_data_csv.html', {
                'form': form,
                'dashboard_mode': True
            })           
        except Exception as e:
            form.add_error(None, f"Error reading file: {str(e)}")
            return render(request, 'tools/upload_data_csv.html', {
                'form': form,
                'dashboard_mode': True
            })

    @staticmethod
    def _handle_confirm_upload(request):
        
        """
        Maneja la confirmación y carga de datos
        """
        upload_data = request.session.get('upload_data')
        if not upload_data:
            messages.error(request, "La sesión expiró o es inválida. Por favor suba el archivo nuevamente.")
            return redirect('data_upload')
        
        try:
          
            upload_data = DataUploadDashboard._convert_to_consistent_format(upload_data)
            df = pd.DataFrame.from_records(upload_data['df_rows'])
            df.columns = upload_data['df_columns']
            
            model = apps.get_model(upload_data['model_path'])
          
            # Crear DataFrame compatible con ambos formatos
            if isinstance(upload_data['df_rows'][0], dict):
              
                df = pd.DataFrame.from_records(upload_data['df_rows'])
                df.columns = upload_data['df_columns']  # Asegurar orden de columnas
            else:
                df = pd.DataFrame(
                    data=upload_data['df_rows'],
                    columns=upload_data['df_columns']
                )
            
            # Procesar campos del modelo
            model_fields = DataUploadDashboard._get_model_fields_info(model)
            
            # Mapeo de columnas
            column_mapping, unused_columns = DataUploadDashboard._map_columns_to_model(request, df, model_fields)
            
            # Validar campos requeridos
            missing_required = DataUploadDashboard._validate_required_fields(model_fields, column_mapping)
            if missing_required:
                messages.error(request, f"Campos requeridos faltantes: {', '.join(missing_required)}")
                return redirect('data_upload')
            
            # Procesar la carga de datos
            return DataUploadDashboard._process_data_upload(request, model, df, upload_data, column_mapping, model_fields)
            
        except Exception as e:
            messages.error(request, f"Error al cargar datos: {str(e)}")
            return redirect('data_upload')

    @staticmethod
    def _handle_save_to_clipboard(request):
        """
        Maneja el guardado de DataFrames al portapapeles
        """
        upload_data = request.session.get('upload_data')
        if not upload_data:
            messages.error(request, "No hay datos para guardar en el portapapeles")
            return redirect('data_upload')
        
        df = pd.DataFrame(upload_data['df_rows'], columns=upload_data['df_columns'])
        clip_name = request.POST.get('clip_name', f"clip_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}")
        clip_description = request.POST.get('clip_description', '')
        
        # Guardar en portapapeles
        clip_key = DataFrameClipboard.store_df(
            request,
            df,
            key=clip_name,
            metadata={
                'filename': upload_data.get('filename', ''),
                'model': upload_data.get('model_path', ''),
                'sheet_info': upload_data.get('excel_info', {}),
                'description': clip_description
            }
        )
        
        messages.success(request, f"DataFrame guardado en portapapeles como '{clip_name}'")
        return redirect('data_upload')

    @staticmethod
    def _handle_load_from_clipboard(request):
        """
        Maneja la carga de DataFrames desde el portapapeles
        """
        clip_name = request.POST.get('clip_name')
        if not clip_name:
            messages.error(request, "No se seleccionó ningún DataFrame")
            return redirect('data_upload')
        
        df, metadata = DataFrameClipboard.retrieve_df(request, key=clip_name)
        
        if df is None:
            messages.error(request, "No se encontró el DataFrame o ha expirado")
            return redirect('data_upload')
        
        try:
            # Obtener el modelo si está en los metadatos
            model = None
            if 'model' in metadata:
                try:
                    model = apps.get_model(metadata['model'])
                except LookupError:
                    messages.warning(request, f"Modelo {metadata['model']} no encontrado")
            
            # Preparar datos para la sesión
            session_data = {
                'df_columns': df.columns.tolist(),
                'df_rows': df.applymap(lambda x: str(x) if pd.notna(x) else None).values.tolist(),
                'source': 'clipboard',
                'clip_name': clip_name,
                'filename': metadata.get('filename', ''),
                'model_path': metadata.get('model', ''),
                'excel_info': metadata.get('sheet_info', {}),
                'clear_existing': False  # Valor por defecto
            }
            request.session['upload_data'] = session_data
            
            # Analizar campos del modelo si existe
            model_fields_info = []
            mapped_columns = set()
            required_fields = []
            
            if model:
                model_fields_info, mapped_columns, required_fields = DataUploadDashboard._analyze_model_fields(model, df)
            
            # Preparar información del DataFrame
            df_info = {
                'rows': len(df),
                'columns': len(df.columns),
                'column_stats': []
            }
            
            for col in df.columns:
                col_str = str(col)
                missing_count = int(df[col].isnull().sum())
                missing_percent = (missing_count / df_info['rows']) * 100 if df_info['rows'] > 0 else 0
                
                df_info['column_stats'].append({
                    'name': col_str,
                    'type': str(df[col].dtype),
                    'missing_count': missing_count,
                    'missing_percent': missing_percent
                })
            
            # Preparar contexto para la vista previa
            context = {
                'form': DataUploadForm(initial={
                    'model': model._meta.label if model else '',
                    'clear_existing': False
                }),
                'preview_mode': True,
                'target_model': model._meta.label if model else '',
                'model_verbose_name': model._meta.verbose_name if model else 'No model selected',
                'model_fields_info': model_fields_info,
                'mapped_columns_count': len(mapped_columns),
                'required_fields': required_fields,
                'df_info': df_info,
                'df_preview': {
                    'columns': [str(col) for col in df.columns.tolist()],
                    'rows': df.head(10).values.tolist()
                },
                'excel_info': metadata.get('sheet_info', {}),
                'unmapped_columns': [str(col) for col in df.columns 
                                   if model and str(col).lower() not in {f['name'].lower() for f in model_fields_info} 
                                   and str(col).lower() not in {f['verbose_name'].lower() for f in model_fields_info}],
                'clipboard_keys': DataFrameClipboard.list_clips(request),
                'dashboard_mode': True
            }
            
            messages.info(request, f"DataFrame '{clip_name}' cargado desde portapapeles")
            return render(request, 'tools/upload_data_csv.html', context)
            
        except Exception as e:
            logger.error(f"Error loading clipboard data: {str(e)}", exc_info=True)
            messages.error(request, f"Error al cargar datos: {str(e)}")
            return redirect('data_upload')
    
    @staticmethod
    def _handle_delete_clip(request):
        """
        Maneja la eliminación de un DataFrame del portapapeles
        """
        clip_name = request.POST.get('clip_name')
        if DataFrameClipboard.delete_df(request, clip_name):
            messages.success(request, f"DataFrame '{clip_name}' eliminado del portapapeles")
        else:
            messages.error(request, "No se pudo eliminar el DataFrame")
        return redirect('data_upload')

    @staticmethod
    def _handle_clear_all_clips(request):
        """
        Maneja la limpieza de todo el portapapeles
        """
        count = DataFrameClipboard.clear_clips(request)
        messages.success(request, f"Se eliminaron {count} DataFrames del portapapeles")
        return redirect('data_upload')

    # Métodos auxiliares
    @staticmethod
    def _process_excel_file(file, form):
        """Procesa archivos Excel con opciones de hoja y rango"""
        excel_file = pd.ExcelFile(file)
        sheet_name = form.cleaned_data.get('sheet_name') or 0
        cell_range = form.cleaned_data.get('cell_range')
        
        full_df = pd.read_excel(excel_file, sheet_name=sheet_name)
        form.file_data = {
            'max_col': len(full_df.columns),
            'max_row': len(full_df)
        }
        
        df = process_excel_with_range(file, sheet_name, cell_range)
        excel_info = {
            'available_sheets': excel_file.sheet_names,
            'selected_sheet': sheet_name if isinstance(sheet_name, str) else excel_file.sheet_names[0],
            'max_columns': len(full_df.columns)
        }
        return df.replace({np.nan: None}), excel_info
 
    @staticmethod
    def _analyze_model_fields(model, df):
        """Analiza los campos del modelo y su mapeo con las columnas del DataFrame"""
        model_fields_info = []
        mapped_columns = set()
        required_fields = []
        
        for field in model._meta.get_fields():
            if isinstance(field, Field):
                field_info = {
                    'name': str(field.name),
                    'verbose_name': str(getattr(field, 'verbose_name', field.name)),
                    'type': field.get_internal_type(),
                    'required': not field.null and not field.blank,
                    'choices': getattr(field, 'choices', None)
                }
                model_fields_info.append(field_info)
                
                if field_info['required']:
                    required_fields.append(field.name)
                
                # To be explicit about string conversion
                for col in df.columns:
                    col_str = str(col) if not isinstance(col, str) else col                
                
                    if (col_str.lower() == field_info['name'].lower() or 
                        col_str.lower() == field_info['verbose_name'].lower()):
                        mapped_columns.add(field.name)
        
        return model_fields_info, mapped_columns, required_fields

    @staticmethod
    def _prepare_column_mapping(df, model_fields_info):
        """Prepara la información de mapeo de columnas"""
        column_mapping_info = []
        for col in df.columns:
           # To:
            col_str = str(col) if not isinstance(col, str) else col
            dtype_str = str(df[col].dtype)
            
            
            matched = False
            mapped_to = None
            
            for field in model_fields_info:
                if (col_str.lower() == field['name'].lower() or 
                    col_str.lower() == field['verbose_name'].lower()):
                    mapped_to = field['name']
                    matched = True
                    break
            
            column_mapping_info.append({
                'column': col_str,
                'dtype': dtype_str,
                'mapped_to': mapped_to,
                'matched': matched
            })
        
        return column_mapping_info

    @staticmethod
    def _get_model_fields_info(model):
        """Obtiene información detallada de los campos del modelo"""
        model_fields = {}
        for field in model._meta.get_fields():
            if isinstance(field, Field):
                model_fields[str(field.name)] = {
                    'field': field,
                    'type': field.get_internal_type(),
                    'null': field.null,
                    'blank': getattr(field, 'blank', False),
                    'default': getattr(field, 'default', None),
                    'choices': getattr(field, 'choices', None),
                    'verbose_name': str(getattr(field, 'verbose_name', field.name))
                }
        return model_fields

    @staticmethod
    def _map_columns_to_model(request, df, model_fields):
        """Mapea columnas del DataFrame a campos del modelo"""
        column_mapping = {}
        unused_columns = []
        
        for col in df.columns:
            col_str = str(col)
            best_match = DataUploadDashboard._find_best_match(col_str, model_fields)
            if best_match:
                column_mapping[col_str] = best_match
            else:
                unused_columns.append(col_str)
        
        if unused_columns:
            messages.warning(request, 
                f"Columnas no mapeadas a campos del modelo: {', '.join(unused_columns)}")
        
        return column_mapping, unused_columns

    @staticmethod
    def _find_best_match(col_name, available_fields):
        """Encuentra la mejor coincidencia para el nombre de columna"""
        col_str = str(col_name)
        col_clean = col_str.lower().replace('á', 'a').replace('é', 'e').replace('í', 'i')\
                     .replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n').strip()
        
        # Coincidencias exactas primero
        for field_name, field_info in available_fields.items():
            field_name_str = str(field_name)
            verbose_name_str = str(field_info['verbose_name'])
            if (col_clean == field_name_str.lower() or 
                col_clean == verbose_name_str.lower()):
                return field_name
        
        # Coincidencias aproximadas
        possible_matches = get_close_matches(
            col_clean, 
            [str(f).lower() for f in available_fields.keys()] + 
            [str(f['verbose_name']).lower() for f in available_fields.values()],
            n=1, 
            cutoff=0.6
        )
        
        if possible_matches:
            match = possible_matches[0]
            for field_name, field_info in available_fields.items():
                field_name_str = str(field_name)
                verbose_name_str = str(field_info['verbose_name'])
                if match == field_name_str.lower() or match == verbose_name_str.lower():
                    return field_name
        return None

    @staticmethod
    def _validate_required_fields(model_fields, column_mapping):
        """Valida que todos los campos requeridos estén mapeados"""
        return [
            field_name for field_name, field_info in model_fields.items()
            if not field_info['null'] and not field_info['blank'] 
            and field_name not in column_mapping.values()
        ]

    @staticmethod
    def _process_data_upload(request, model, df, upload_data, column_mapping, model_fields):
        """Procesa la carga de datos a la base de datos"""
        DEFAULT_VALUES = {
            'CharField': '',
            'IntegerField': 0,
            'FloatField': 0.0,
            'BooleanField': False,
            'DateField': None,
            'DateTimeField': None,
            'TextField': ''
        }
        
        try:
            with transaction.atomic():
                if upload_data['clear_existing']:
                    model.objects.all().delete()
                
                objs = []
                error_count = 0
                
                for idx, row in df.iterrows():
                    obj_data = {}
                    row_errors = []
                    
                    for col_name, value in row.items():
                        col_name_str = str(col_name)
                        if col_name_str in column_mapping:
                            field_name = column_mapping[col_name_str]
                            field_info = model_fields[field_name]
                            field = field_info['field']
                            
                            # Manejar campos de fecha/hora
                            if field_info['type'] in ['DateTimeField', 'DateField'] and pd.notna(value):
                                try:
                                    if isinstance(value, str):
                                        value = pd.to_datetime(value)
                                    if field_info['type'] == 'DateField':
                                        value = value.date() if hasattr(value, 'date') else value
                                    elif field_info['type'] == 'DateTimeField':
                                        value = value.to_pydatetime() if hasattr(value, 'to_pydatetime') else value
                                except (ValueError, TypeError) as e:
                                    row_errors.append(f"Valor inválido para '{field_name}': {value}")
                                    continue

                            # Manejar valores nulos/faltantes
                            if pd.isna(value):
                                if field_info['default'] is not None:
                                    obj_data[field_name] = field_info['default']
                                elif field_info['null'] or field_info['blank']:
                                    obj_data[field_name] = None
                                else:
                                    default_value = DEFAULT_VALUES.get(field_info['type'])
                                    if default_value is not None:
                                        obj_data[field_name] = default_value
                                    else:
                                        row_errors.append(f"El campo '{field_name}' no puede ser nulo")
                                        continue
                            else:
                                try:
                                    # Conversión de tipos según el campo
                                    if field_info['type'] == 'IntegerField':
                                        obj_data[field_name] = int(float(value))
                                    elif field_info['type'] == 'FloatField':
                                        obj_data[field_name] = float(value)
                                    elif field_info['type'] == 'BooleanField':
                                        obj_data[field_name] = bool(value)
                                    elif field_info['choices']:
                                        valid_choices = [choice[0] for choice in field_info['choices']]
                                        if value not in valid_choices:
                                            row_errors.append(
                                                f"Valor inválido para '{field_name}'. Opciones válidas: {', '.join(valid_choices)}")
                                            continue
                                        else:
                                            obj_data[field_name] = value
                                    else:
                                        obj_data[field_name] = value
                                except (ValueError, TypeError) as e:
                                    row_errors.append(f"Valor inválido para '{field_name}': {value}")
                                    continue
                    
                    if row_errors:
                        error_count += 1
                        if error_count <= 5:
                            messages.error(request, f"Fila {idx+1}: {', '.join(row_errors)}")
                        continue
                    
                    try:
                        objs.append(model(**obj_data))
                    except Exception as e:
                        error_count += 1
                        if error_count <= 5:
                            messages.error(request, f"Fila {idx+1}: Error al crear registro - {str(e)}")
                        continue
                
                if objs:
                    model.objects.bulk_create(objs)
                    msg = (f"Se cargaron exitosamente {len(objs)} registros. "
                          f"{error_count} filas tuvieron errores." if error_count else "")
                    messages.success(request, msg)
                else:
                    messages.error(request, 
                        "No se crearon registros. Por favor revise los errores mostrados.")
                
                del request.session['upload_data']
                return redirect('dashboard')
        
        except Exception as e:
            messages.error(request, f"Error en la transacción: {str(e)}")
            return redirect('data_upload')

    @staticmethod
    def _handle_clipboard_edit(request):
        """
        Maneja las acciones de edición del clipboard con validaciones mejoradas
        """
        if 'upload_data' not in request.session:
            messages.error(request, "No hay datos para editar")
            return redirect('data_upload')
    
        try:
            upload_data = request.session['upload_data']
            
            # Crear DataFrame desde el formato correcto
            upload_data = request.session['upload_data']
            upload_data = DataUploadDashboard._convert_to_consistent_format(upload_data)
            
            # Crear DataFrame
            df = pd.DataFrame.from_records(upload_data['df_rows'])
            df.columns = upload_data['df_columns']  # Mantener orden de columnas
    
            # Procesar acciones con validaciones
            if 'delete_columns' in request.POST:
                columns_to_delete = request.POST.getlist('columns_to_delete')
                
                # Validar columnas a eliminar
                valid_columns = [col for col in columns_to_delete if col in df.columns]
                invalid_columns = set(columns_to_delete) - set(valid_columns)
                
                if invalid_columns:
                    messages.warning(request, f"Columnas no encontradas: {', '.join(invalid_columns)}")
                
                if valid_columns:
                    # Verificar si se está eliminando una columna requerida
                    model = apps.get_model(upload_data['model_path']) if 'model_path' in upload_data else None
                    if model:
                        model_fields = DataUploadDashboard._get_model_fields_info(model)
                        required_fields = [
                            field_name for field_name, field_info in model_fields.items()
                            if not field_info['null'] and not field_info['blank']
                        ]
                        
                        deleted_required = [col for col in valid_columns if col in required_fields]
                        if deleted_required:
                            messages.error(request, 
                                f"No se pueden eliminar columnas requeridas: {', '.join(deleted_required)}")
                            return redirect('data_upload')
                    
                    df = df.drop(columns=valid_columns)
                    messages.success(request, f"Columnas eliminadas: {', '.join(valid_columns)}")
    
            if 'replace_values' in request.POST:
                column_to_replace = request.POST.get('replace_column')
                old_value = request.POST.get('old_value', '')
                new_value = request.POST.get('new_value', '')
                
                if not column_to_replace or column_to_replace not in df.columns:
                    messages.error(request, "Columna inválida para reemplazo")
                    return redirect('data_upload')
                
                try:
                    # Preservar tipo de datos original
                    original_dtype = df[column_to_replace].dtype
                    df[column_to_replace] = df[column_to_replace].replace(old_value, new_value)
                    
                    # Intentar mantener el tipo de dato original
                    try:
                        if pd.api.types.is_numeric_dtype(original_dtype):
                            df[column_to_replace] = pd.to_numeric(df[column_to_replace], errors='raise')
                        elif pd.api.types.is_datetime64_any_dtype(original_dtype):
                            df[column_to_replace] = pd.to_datetime(df[column_to_replace], errors='raise')
                    except (ValueError, TypeError) as e:
                        messages.warning(request, 
                            f"El nuevo valor no coincide con el tipo original de la columna {column_to_replace}")
                    
                    messages.success(request, 
                        f"Reemplazados '{old_value}' por '{new_value}' en {column_to_replace}")
                except Exception as e:
                    messages.error(request, f"Error al reemplazar valores: {str(e)}")
                    return redirect('data_upload')
    
            if 'fill_na' in request.POST:
                column_to_fill = request.POST.get('fill_column')
                fill_value = request.POST.get('fill_value')
                
                if column_to_fill not in df.columns:
                    messages.error(request, "Columna inválida para rellenar")
                    return redirect('data_upload')
                
                try:
                    # Convertir fill_value según el tipo de columna
                    if pd.api.types.is_numeric_dtype(df[column_to_fill]):
                        fill_value = float(fill_value) if fill_value else 0
                    elif pd.api.types.is_datetime64_any_dtype(df[column_to_fill]):
                        fill_value = pd.to_datetime(fill_value) if fill_value else pd.NaT
                    elif pd.api.types.is_bool_dtype(df[column_to_fill]):
                        fill_value = str(fill_value).lower() in ('true', '1', 'yes')
                    
                    df[column_to_fill] = df[column_to_fill].fillna(fill_value)
                    messages.success(request, 
                        f"Valores nulos en {column_to_fill} rellenados con '{fill_value}'")
                except ValueError as e:
                    messages.error(request, f"Valor de relleno inválido: {str(e)}")
                    return redirect('data_upload')
  
            # Guardar en el formato consistente (lista de diccionarios)
            # Guardar cambios
            upload_data['df_columns'] = df.columns.tolist()
            upload_data['df_rows'] = df.replace({np.nan: None}).to_dict('records')
            request.session['upload_data'] = upload_data
            request.session.modified = True
    
            return redirect(reverse('data_upload') + '#preview-section')
    
        except pd.errors.EmptyDataError:
            messages.error(request, "No hay datos para editar")
        except ValueError as e:
            messages.error(request, f"Error en los valores proporcionados: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado editando datos: {str(e)}", exc_info=True)
            messages.error(request, "Ocurrió un error inesperado al editar los datos")
        
        return redirect('data_upload')
    # Actualizar el action_handlers para incluir la nueva acción
    @staticmethod
    def _handle_post_actions(request):
        """
        Maneja todas las acciones POST del dashboard
        """
        action_handlers = {
            'preview': DataUploadDashboard._handle_preview,
            'confirm_upload': DataUploadDashboard._handle_confirm_upload,
            'save_to_clipboard': DataUploadDashboard._handle_save_to_clipboard,
            'load_from_clipboard': DataUploadDashboard._handle_load_from_clipboard,
            'delete_clip': DataUploadDashboard._handle_delete_clip,
            'clear_all_clips': DataUploadDashboard._handle_clear_all_clips,
            'edit_clipboard': DataUploadDashboard._handle_clipboard_edit  # Nueva acción
        }
    
        for action in action_handlers:
            if action in request.POST:
                return action_handlers[action](request)
        
        return redirect('data_upload')

def process_excel_with_range(file, sheet_name, cell_range):
    """Procesa archivos Excel con rango de celdas especificado"""
    excel_file = pd.ExcelFile(file)
    
    try:
        if not cell_range or not cell_range.strip():
            return pd.read_excel(excel_file, sheet_name=sheet_name)
        
        if ':' not in cell_range:
            raise ValueError("El rango debe contener dos celdas separadas por ':' (ej: A1:B10)")
        
        start, end = cell_range.split(':')
        
        def get_col_letters(s):
            letters = ''.join([c for c in str(s) if c.isalpha()])
            if not letters:
                raise ValueError(f"No se encontraron letras de columna en '{s}'")
            return letters.upper()
        
        def get_row_number(s):
            digits = ''.join([c for c in str(s) if c.isdigit()])
            if not digits:
                raise ValueError(f"No se encontró número de fila en '{s}'")
            return int(digits)
        
        def col_to_index(col_letters):
            index = 0
            for c in col_letters:
                if not c.isalpha():
                    raise ValueError(f"Carácter inválido en columna: '{c}'")
                index = index * 26 + (ord(c.upper()) - ord('A'))
            return index
        
        start_col = get_col_letters(start)
        start_row = get_row_number(start) - 1  # Convertir a índice base 0
        end_col = get_col_letters(end)
        end_row = get_row_number(end)  # Mantener como base 1
        
        start_col_idx = col_to_index(start_col)
        end_col_idx = col_to_index(end_col)
        
        full_df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
        
        max_cols = len(full_df.columns)
        max_rows = len(full_df)
        
        if start_col_idx >= max_cols or end_col_idx >= max_cols:
            available_cols = f"A-{chr(ord('A') + max_cols - 1)}" if max_cols <= 26 else f"A-ZZ"
            raise ValueError(f"El rango de columnas excede las columnas disponibles ({available_cols})")
            
        if start_row >= max_rows or end_row > max_rows:
            raise ValueError(f"El rango de filas excede las filas disponibles (1-{max_rows})")
        
        data = full_df.iloc[start_row:end_row, start_col_idx:end_col_idx+1]
        
        if len(data) > 0:
            result_df = pd.DataFrame(data.values[1:], columns=[str(col) for col in data.iloc[0]])
            return result_df
        return pd.DataFrame()
        
    except Exception as e:
        raise ValueError(f"Error al procesar archivo Excel: {str(e)}")

# Vista principal
upload_csv = DataUploadDashboard.dashboard


from django.http import JsonResponse
from django.template.loader import render_to_string
from tools.utils import DataFrameClipboard

def clipboard_details(request):
    clip_key = request.GET.get('key')
    if not clip_key:
        return JsonResponse({'error': 'No clip key provided'}, status=400)
    
    df, metadata = DataFrameClipboard.retrieve_df(request, key=clip_key)
    if df is None:
        return JsonResponse({'error': 'Clip not found'}, status=404)
    
    # Convert DataFrame to a format that can be rendered in templates
    data_preview = {
        'columns': df.columns.tolist(),
        'rows': df.head(10).values.tolist()
    }
    
    context = {
        'clip': {
            'key': clip_key,
            'data': data_preview,
            'metadata': metadata,
            'size': sys.getsizeof(df),
            'timestamp': metadata.get('timestamp', 'Unknown'),
            'shape': (len(df), len(df.columns))
        }
    }
    
    html = render_to_string('tools/partials/clipboard_details.html', context)
    return JsonResponse({'html': html})
    
from django.http import HttpResponse
import pandas as pd
from io import StringIO

def export_clipboard_csv(request):
    clip_key = request.GET.get('key')
    if not clip_key:
        return HttpResponse('No clip key provided', status=400)
    
    df, metadata = DataFrameClipboard.retrieve_df(request, key=clip_key)
    if df is None:
        return HttpResponse('Clip not found', status=404)
    
    # Create CSV response
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    response = HttpResponse(csv_buffer.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{clip_key}.csv"'
    return response