# analyst/views/data_upload.py
import logging
import pandas as pd
import numpy as np
import sys
import traceback
import json
from typing import Dict, Any, List, Set, Tuple, Optional
from django.shortcuts import render, redirect
from django.contrib import messages
from django.apps import apps
from django.db import transaction
from django.db.models import Field
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from difflib import get_close_matches

from analyst.forms import DataUploadForm
from analyst.utils.clipboard import DataFrameClipboard
from analyst.services.data_processor import DataProcessor
from analyst.services.excel_processor import ExcelProcessor
from analyst.services.model_mapper import ModelMapper
from analyst.services.data_importer import DataImporter
from analyst.constants import MAX_SESSION_DATA_SIZE
from analyst.models import StoredDataset, AnalystBase, CrossSource
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

# =============================================================================
# VISTA PRINCIPAL
# =============================================================================
# analyst/views/data_upload.py


def _handle_load_from_clipboard(request):
    """
    Maneja la carga de DataFrames desde el portapapeles (botón en dashboard)
    Ahora redirige al formulario de selección de modelo
    """
    logger.debug("=" * 50)
    logger.debug("INICIANDO _handle_load_from_clipboard (botón dashboard)")
    
    clip_name = request.POST.get('clip_name')
    logger.debug(f"clip_name recibido: {clip_name}")
    
    if not clip_name:
        logger.error("No se seleccionó clip_name")
        messages.error(request, "No se seleccionó ningún DataFrame")
        return redirect('analyst:data_upload')
    
    # Redirigir al formulario de selección de modelo
    logger.info(f"Redirigiendo a formulario de selección para clip: {clip_name}")
    redirect_url = f"{reverse('analyst:load_clipboard_form')}?key={clip_name}"
    logger.debug(f"URL de redirección: {redirect_url}")
    return redirect(redirect_url)

@require_http_methods(["GET", "POST"])
def upload_csv(request):
    """
    Vista principal del panel de administración de cargas
    """
    logger.debug("=" * 50)
    logger.debug("🏠 INICIANDO DASHBOARD - Método: %s", request.method)
    
    # Verificar si viene de carga de clip con datos precargados
    if request.GET.get('preview') == 'clip':
        logger.debug("Mostrando vista previa desde datos precargados")
        if request.session.get('upload_data'):
            return _render_preview_from_session(request)
        else:
            logger.warning("No hay datos en sesión para preview=clip")
            messages.warning(request, "No hay datos precargados. Por favor selecciona un clip.")
            return redirect('analyst:data_upload')
    
    logger.debug("Session ID: %s", request.session.session_key)
    
    # Log detallado del request POST
    if request.method == 'POST':
        logger.debug("📨 POST data recibido:")
        for key, value in request.POST.items():
            if key != 'csrfmiddlewaretoken':
                logger.debug("   - %s: %s", key, value)
        
        logger.debug("📁 FILES recibidos:")
        for key, file in request.FILES.items():
            logger.debug("   - %s: %s (%d bytes)", key, file.name, file.size)
    
    # Inicializar el portapapeles si no existe
    _init_clipboard(request)
    
    if request.method == 'POST':
        logger.debug("➡️ Procesando acciones POST")
        return _handle_post_actions(request)
    
    # Vista GET - Mostrar el panel
    return _render_dashboard(request)


def _init_clipboard(request):
    """Inicializa el portapapeles en la sesión"""
    if 'clipboard_keys' not in request.session:
        logger.debug("📋 Inicializando clipboard_keys en sesión")
        request.session['clipboard_keys'] = []
        request.session.modified = True


def _render_dashboard(request):
    """Renderiza el dashboard principal"""
    logger.debug("🎨 Renderizando vista GET del dashboard")
    form = DataUploadForm()
    clipboard_keys = DataFrameClipboard.list_clips(request)
    logger.debug("📋 Clipboard keys encontradas: %s", clipboard_keys)
    stored_datasets = StoredDataset.objects.filter(created_by=request.user).values(
        'id', 'name', 'rows', 'col_count', 'source_file', 'created_at'
    )
    return render(request, 'analyst/upload_data_csv.html', {
        'form':            form,
        'clipboard_keys':  clipboard_keys,
        'stored_datasets': stored_datasets,
        'analyst_bases':   AnalystBase.objects.filter(
                               created_by=request.user).select_related('dataset'),
        'cross_sources':   CrossSource.objects.filter(
                               created_by=request.user).select_related('last_result'),
        'dashboard_mode':  True,
    })


# =============================================================================
# MANEJADOR PRINCIPAL DE ACCIONES POST
# =============================================================================


def _handle_post_actions(request):
    """
    Maneja todas las acciones POST del dashboard
    """
    logger.debug("=" * 50)
    logger.debug("INICIANDO _handle_post_actions")
    logger.debug("POST keys recibidas: %s", list(request.POST.keys()))
    logger.debug("POST data completo: %s", dict(request.POST))
    
    # PRIMERO: Verificar si es una carga desde archivo (siempre debe ir antes que clipboard)
    if request.FILES and 'file' in request.FILES:
        logger.debug("📁 Archivo detectado - PROCESANDO PREVIEW DESDE ARCHIVO")
        # Limpiar cualquier residuo de clipboard
        if request.session.get('pending_clip_key'):
            del request.session['pending_clip_key']
            request.session.modified = True
        return _handle_preview(request)
    
    # Verificar si es una carga desde clipboard
    is_clipboard_load = request.POST.get('is_clipboard_load') == 'true'
    clip_name = request.POST.get('clip_name')
    model_selected = request.POST.get('model')
    
    logger.debug("🔍 VERIFICANDO CARGA DESDE CLIPBOARD:")
    logger.debug(f"   - is_clipboard_load: '{is_clipboard_load}' (tipo: {type(is_clipboard_load)})")
    logger.debug(f"   - clip_name: '{clip_name}'")
    logger.debug(f"   - model: '{model_selected}'")
    
    if is_clipboard_load and clip_name:
        logger.info("🎯 CARGA DESDE CLIPBOARD DETECTADA - Procesando preview")
        logger.info(f"   Clip: {clip_name}, Modelo: {model_selected}")
        request.session['pending_clip_key'] = clip_name
        request.session.modified = True
        return _handle_preview(request)
    
    # Verificar por pending_clip_key en sesión (solo si no hay archivo)
    if request.session.get('pending_clip_key') and not request.FILES:
        logger.debug("✅ Detectado por pending_clip_key en sesión")
        clip_name = request.session.get('pending_clip_key')
        logger.info("🎯 CARGA DESDE CLIPBOARD DETECTADA (por sesión) - Procesando preview")
        return _handle_preview(request)
    
    # Diccionario de acciones específicas
    action_handlers = {
        'confirm_upload': _handle_confirm_upload,
        'save_to_clipboard': _handle_save_to_clipboard,
        'load_from_clipboard': _handle_load_from_clipboard,
        'delete_clip': _handle_delete_clip,
        'clear_all_clips': _handle_clear_all_clips,
        'edit_clipboard': _handle_clipboard_edit,
        'convert_to_date': _handle_date_conversion
    }
    
    for action, handler in action_handlers.items():
        if action in request.POST:
            logger.debug("Acción específica detectada: %s", action)
            return handler(request)
    
    logger.warning("⚠️ POST sin acción reconocida y sin archivo")
    messages.error(request, "Acción no reconocida. Por favor use el botón 'Previsualizar'.")
    return redirect('analyst:data_upload')


# =============================================================================
# MANEJADORES DE ACCIONES ESPECÍFICAS
# =============================================================================

def _handle_preview(request):
    """
    Maneja la previsualización de datos con logging detallado
    """
    logger.info("=" * 50)
    logger.info("🖼️ INICIANDO _handle_preview")
    
    # Log detallado de lo que llega
    logger.debug(f"POST data en _handle_preview: {dict(request.POST)}")
    
    # Determinar el tipo de carga
    is_file_upload = request.FILES and 'file' in request.FILES
    is_clipboard_load = request.POST.get('is_clipboard_load') == 'true' or request.session.get('pending_clip_key')
    
    logger.debug(f"is_file_upload: {is_file_upload}")
    logger.debug(f"is_clipboard_load: {is_clipboard_load}")
    
    # Validar que solo uno sea True
    if is_file_upload and is_clipboard_load:
        logger.error("Conflicto: ambos tipos de carga detectados")
        messages.error(request, "Conflicto en el tipo de carga. Por favor intente nuevamente.")
        return redirect('analyst:data_upload')
    
    # Obtener clip_name si es clipboard
    clip_name = None
    if is_clipboard_load:
        clip_name = request.POST.get('clip_name') or request.session.get('pending_clip_key')
        logger.debug(f"clip_name: {clip_name}")
    
    # Validar formulario según el tipo
    if is_clipboard_load:
        # Para clipboard, usar formulario especial
        from analyst.forms import ClipboardUploadForm
        form = ClipboardUploadForm(request.POST)
        logger.debug("Usando ClipboardUploadForm (sin archivo)")
    else:
        # Para archivo, usar formulario normal
        form = DataUploadForm(request.POST, request.FILES)
        logger.debug("Usando DataUploadForm (con archivo)")
    
    if not form.is_valid():
        logger.warning("Formulario inválido - Errores: %s", form.errors)
        logger.warning("Datos del formulario: %s", form.data)
        
        if is_clipboard_load:
            messages.error(request, "Error al cargar desde clipboard. Por favor selecciona un modelo válido.")
        else:
            messages.error(request, "Error en el formulario. Por favor verifica los datos.")
            
        return render(request, 'analyst/upload_data_csv.html', {
            'form': form,
            'dashboard_mode': True
        })
    
    try:
        if is_clipboard_load and clip_name:
            # Cargar desde clipboard
            logger.info(f"Cargando datos desde clipboard: {clip_name}")
            df, metadata = DataFrameClipboard.retrieve_df(request, clip_name)
            
            if df is None:
                logger.error(f"Clip no encontrado: {clip_name}")
                messages.error(request, "El clip no existe o ha expirado")
                return redirect('analyst:data_upload')
            
            model = form.cleaned_data['model']
            logger.info(f"Modelo seleccionado: {model.__name__}")
            
            excel_info = metadata.get('sheet_info', {})
            filename = metadata.get('filename', clip_name)
            
            logger.info(f"Clip cargado - Shape: {df.shape}")
            
            # Limpiar pending_clip_key
            if request.session.get('pending_clip_key'):
                del request.session['pending_clip_key']
                request.session.modified = True
            
        else:
            # Cargar desde archivo
            if 'file' not in request.FILES:
                logger.error("No se recibió archivo")
                messages.error(request, "No se seleccionó ningún archivo")
                return redirect('analyst:data_upload')
                
            file = request.FILES['file']
            model = form.cleaned_data['model']
            
            logger.info("Archivo recibido: %s (%d bytes)", file.name, file.size)
            logger.info("Modelo seleccionado: %s", model.__name__)
            
            # Obtener opciones de Excel del formulario
            sheet_name = form.cleaned_data.get('sheet_name')
            cell_range = form.cleaned_data.get('cell_range')
            no_header = form.cleaned_data.get('no_header', False)  # Nueva opción
            
            logger.info(f"Opciones de Excel - Sheet: {sheet_name}, Range: {cell_range}, NoHeader: {no_header}")
            
            # Procesar archivo según el tipo
            if file.name.endswith('.csv'):
                df, metadata = DataProcessor._process_csv(file)
                excel_info = None
            else:
                # Pasar las opciones de Excel al procesador
                logger.info(f"Procesando Excel con sheet: {sheet_name}, range: {cell_range}, no_header: {no_header}")
                df, excel_info = ExcelProcessor.process_excel(
                    file, 
                    sheet_name=sheet_name,
                    cell_range=cell_range,
                    no_header=no_header  # Pasar la opción no_header
                )
                metadata = excel_info
                
                # Registrar la hoja usada
                logger.info(f"Hoja usada: {excel_info.get('selected_sheet', 'desconocida')}")
                logger.info(f"Columnas generadas: {list(df.columns)}")
                
            filename = file.name
        
        # Analizar campos del modelo
        logger.info(f"Analizando campos del modelo para {df.shape[0]} filas, {df.shape[1]} columnas")
        model_fields_info, mapped_columns, required_fields_names = ModelMapper.analyze_model_fields(model, df)
        required_fields = [field for field in model_fields_info if field['required']]
        
        # Guardar en sesión
        if is_clipboard_load:
            session_data = {
                'df_columns': df.columns.tolist(),
                'df_rows': _df_to_session_rows(df),
                'model_path': f"{model._meta.app_label}.{model._meta.model_name}",
                'clear_existing': form.cleaned_data['clear_existing'],
                'file_type': 'clipboard',
                'excel_info': excel_info,
                'filename': filename,
                'clip_name': clip_name
            }
        else:
            session_data = {
                'df_columns': df.columns.tolist(),
                'df_rows': _df_to_session_rows(df),
                'model_path': f"{model._meta.app_label}.{model._meta.model_name}",
                'clear_existing': form.cleaned_data['clear_existing'],
                'file_type': 'file',
                'excel_info': excel_info,
                'filename': filename,
                'sheet_name': sheet_name,
                'cell_range': cell_range,
                'no_header': no_header  # Guardar la opción no_header
            }
        
        request.session['upload_data'] = session_data
        request.session.modified = True
        logger.info(f"Datos guardados en sesión desde {'clipboard' if is_clipboard_load else 'archivo'}")
        
        # Preparar contexto
        context = _prepare_preview_context(
            request, form, df, model_fields_info, mapped_columns, 
            required_fields, excel_info
        )
        
        logger.info("Renderizando vista previa")
        return render(request, 'analyst/upload_data_csv.html', context)
        
    except Exception as e:
        logger.error(f"Error en preview: {str(e)}", exc_info=True)
        form.add_error(None, str(e))
        return render(request, 'analyst/upload_data_csv.html', {
            'form': form,
            'dashboard_mode': True
        })


def _save_to_session(request, df, cleaned_data, metadata, filename):
    """Guarda el DataFrame en sesión"""
    logger.debug("Preparando datos para sesión")
    
    # Convertir NaN a None para JSON serializable
    df_clean = df.replace({np.nan: None})
    
    session_data = {
        'df_columns': df.columns.tolist(),
        'df_rows': df_clean.to_dict('records'),
        'model_path': f"{cleaned_data['model']._meta.app_label}.{cleaned_data['model']._meta.model_name}",
        'clear_existing': cleaned_data['clear_existing'],
        'file_type': 'csv' if filename.endswith('.csv') else 'excel',
        'excel_info': metadata,
        'filename': filename
    }
    
    # Verificar tamaño de sesión
    import pickle
    session_size = len(pickle.dumps(session_data))
    logger.debug("Tamaño de datos de sesión: %d bytes", session_size)
    
    if session_size > MAX_SESSION_DATA_SIZE:
        logger.error("Datos de sesión demasiado grandes: %d bytes", session_size)
        raise ValueError("Los datos son demasiado grandes para procesar")
    
    request.session['upload_data'] = session_data
    request.session.modified = True
    logger.debug("Datos guardados en sesión")


def _rename_duplicate_columns(df):
    """
    Renombra columnas duplicadas añadiendo sufijo _1, _2, … SOLO a las que se repiten.
    Ejemplo: ['Agente','Total','1.0','Total','1.0'] → ['Agente','Total_1','1.0_1','Total_2','1.0_2']
    Los valores NaN/float de nombre de columna (ej. pandas los genera como 'nan') se limpian también.

    Devuelve el DataFrame con columnas únicas (in-place no: crea copia de columnas).
    """
    from collections import Counter
    raw = [str(c) if str(c) != 'nan' else '' for c in df.columns]
    counts = Counter(raw)
    seen   = Counter()
    result = []
    for name in raw:
        seen[name] += 1
        if counts[name] > 1:
            # Renombrar TODAS las ocurrencias desde la primera
            result.append(f"{name}_{seen[name]}" if name else f"Col_{seen[name]}")
        else:
            result.append(name if name else f"Col_{seen[name]}")
    df = df.copy()
    df.columns = result
    return df


def _prepare_preview_context(request, form, df, model_fields_info, mapped_columns, required_fields, excel_info):
    """Prepara el contexto para la vista de preview"""

    # ── Renombrar columnas duplicadas para evitar ambigüedad en el template ────
    df = _rename_duplicate_columns(df)

    # ── Información del DataFrame ──────────────────────────────────────────────
    df_info = {
        'rows':    len(df),
        'columns': len(df.columns),
        'column_stats': [],
    }

    # Iterar POR POSICIÓN para evitar el bug de df[col] cuando hay duplicados
    for i, col in enumerate(df.columns):
        series = df.iloc[:, i]
        missing_count   = int(series.isnull().sum())
        missing_percent = round((missing_count / df_info['rows']) * 100, 2) if df_info['rows'] > 0 else 0
        df_info['column_stats'].append({
            'name':            str(col),
            'type':            str(series.dtype),
            'missing_count':   missing_count,
            'missing_percent': missing_percent,
        })

    # ── Preparar mapeo de columnas ─────────────────────────────────────────────
    column_mapping_info = []
    model_field_names   = {f['name'].lower()         for f in model_fields_info}
    model_verbose_names = {f['verbose_name'].lower()  for f in model_fields_info}

    for i, col in enumerate(df.columns):
        col_str  = str(col)
        series   = df.iloc[:, i]
        matched  = False
        mapped_to = None
        for field in model_fields_info:
            if col_str.lower() in (field['name'].lower(), field['verbose_name'].lower()):
                mapped_to = field['name']
                matched   = True
                break
        column_mapping_info.append({
            'column':   col_str,
            'dtype':    str(series.dtype),
            'mapped_to': mapped_to,
            'matched':  matched,
        })

    # ── Columnas no mapeadas ───────────────────────────────────────────────────
    unmapped_columns = [
        str(col) for col in df.columns
        if str(col).lower() not in model_field_names
        and str(col).lower() not in model_verbose_names
    ]

    # ── column_headers: lista pre-calculada que el template usa directamente ──
    # Evita el bug de slice:forloop.counter0 en Django templates.
    column_headers = [
        {
            'name':            stat['name'],
            'missing_count':   stat['missing_count'],
            'missing_percent': stat['missing_percent'],
        }
        for stat in df_info['column_stats']
    ]

    return {
        'form':               form,
        'preview_mode':       True,
        'target_model':       f"{form.cleaned_data['model']._meta.app_label}.{form.cleaned_data['model']._meta.model_name}",
        'model_verbose_name': str(form.cleaned_data['model']._meta.verbose_name),
        'model_fields_info':  model_fields_info,
        'mapped_columns_count': len(mapped_columns),
        'required_fields':    required_fields,
        'df_info':            df_info,
        'df_preview': {
            'columns':        [str(col) for col in df.columns.tolist()],
            'column_headers': column_headers,   # ← pre-calculado, sin magic de slice
            'rows':           df.head(10).replace({np.nan: None}).values.tolist(),
        },
        'excel_info':         excel_info,
        'unmapped_columns':   unmapped_columns,
        'column_mapping_info': column_mapping_info,
        'clipboard_keys':     DataFrameClipboard.list_clips(request),
        'stored_datasets':    StoredDataset.objects.filter(created_by=request.user).values(
                                  'id', 'name', 'rows', 'col_count', 'source_file', 'created_at'),
        'analyst_bases':      AnalystBase.objects.filter(
                                  created_by=request.user).select_related('dataset'),
        'cross_sources':      CrossSource.objects.filter(
                                  created_by=request.user).select_related('last_result'),
        'dashboard_mode':     True,
    }


def _handle_confirm_upload(request):
    """
    Maneja la confirmación y carga de datos
    """
    logger.info("=" * 50)
    logger.info("INICIANDO _handle_confirm_upload")
    
    upload_data = request.session.get('upload_data')
    if not upload_data:
        logger.error("No hay upload_data en sesión")
        messages.error(request, "La sesión expiró o es inválida. Por favor suba el archivo nuevamente.")
        return redirect('analyst:data_upload')
    
    try:
        # Convertir datos a formato consistente
        upload_data = _convert_to_consistent_format(upload_data)
        df = pd.DataFrame.from_records(upload_data['df_rows'])
        df.columns = upload_data['df_columns']
        
        logger.debug("DataFrame creado - Shape: %s", df.shape)
        
        model = apps.get_model(upload_data['model_path'])
        logger.debug("Modelo obtenido: %s", model.__name__)
        
        # Obtener información de campos del modelo
        model_fields = _get_model_fields_info(model)
        
        # Mapear columnas a campos
        column_mapping, unused_columns = _map_columns_to_model(request, df, model_fields)
        
        # Validar campos requeridos
        missing_required = _validate_required_fields(model_fields, column_mapping)
        if missing_required:
            logger.error("Campos requeridos faltantes: %s", missing_required)
            messages.error(request, f"Campos requeridos faltantes: {', '.join(missing_required)}")
            return redirect('analyst:data_upload')
        
        # Usar DataImporter para la carga
        importer = DataImporter(
            model=model,
            df=df,
            column_mapping=column_mapping,
            clear_existing=upload_data.get('clear_existing', False),
            user=request.user
        )
        
        stats = importer.import_data()
        
        if stats['successful'] > 0:
            messages.success(
                request, 
                f"Se cargaron exitosamente {stats['successful']} registros."
            )
            if stats['failed'] > 0:
                messages.warning(
                    request,
                    f"{stats['failed']} filas tuvieron errores."
                )
        else:
            messages.error(request, "No se crearon registros.")
        
        # Limpiar sesión
        del request.session['upload_data']
        return redirect('analyst:data_upload')
        
    except Exception as e:
        logger.error("Error al cargar datos: %s", str(e), exc_info=True)
        messages.error(request, f"Error al cargar datos: {str(e)}")
        return redirect('analyst:data_upload')


def _handle_save_to_clipboard(request):
    """
    Maneja el guardado de DataFrames al portapapeles
    """
    logger.debug("=" * 50)
    logger.debug("INICIANDO _handle_save_to_clipboard")
    
    upload_data = request.session.get('upload_data')
    if not upload_data:
        logger.error("No hay upload_data en sesión")
        messages.error(request, "No hay datos para guardar en el portapapeles")
        return redirect('analyst:data_upload')
    
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
            'description': clip_description,
            'rows': len(df),
            'columns': len(df.columns)
        }
    )
    
    logger.info("DataFrame guardado en clipboard con key: %s", clip_key)
    messages.success(request, f"DataFrame guardado en portapapeles como '{clip_name}'")
    return redirect('analyst:data_upload')


def _handle_delete_clip(request):
    """
    Maneja la eliminación de un DataFrame del portapapeles
    """
    logger.debug("=" * 50)
    logger.debug("INICIANDO _handle_delete_clip")
    
    clip_name = request.POST.get('clip_name')
    logger.debug("Eliminando clipboard: %s", clip_name)
    
    if DataFrameClipboard.delete_df(request, clip_name):
        logger.info("Clipboard eliminado: %s", clip_name)
        messages.success(request, f"DataFrame '{clip_name}' eliminado del portapapeles")
    else:
        logger.error("No se pudo eliminar clipboard: %s", clip_name)
        messages.error(request, "No se pudo eliminar el DataFrame")
    return redirect('analyst:data_upload')


def _handle_clear_all_clips(request):
    """
    Maneja la limpieza de todo el portapapeles
    """
    logger.debug("=" * 50)
    logger.debug("INICIANDO _handle_clear_all_clips")
    
    count = DataFrameClipboard.clear_clips(request)
    logger.info("Se eliminaron %d clips", count)
    messages.success(request, f"Se eliminaron {count} DataFrames del portapapeles")
    return redirect('analyst:data_upload')


def _handle_date_conversion(request):
    """
    Maneja la conversión de una columna de string a fecha
    """
    logger.debug("=" * 50)
    logger.debug("INICIANDO _handle_date_conversion")
    
    if 'upload_data' not in request.session:
        logger.warning("No hay upload_data en sesión")
        messages.error(request, "No hay datos para editar")
        return redirect('analyst:data_upload')
    
    try:
        upload_data = request.session['upload_data']
        upload_data = _convert_to_consistent_format(upload_data)
        
        # Crear DataFrame
        df = pd.DataFrame.from_records(upload_data['df_rows'])
        df.columns = upload_data['df_columns']
        
        # Obtener parámetros del formulario
        column_to_convert = request.POST.get('date_column')
        date_format = request.POST.get('date_format', '%Y-%m-%d')
        
        if not column_to_convert or column_to_convert not in df.columns:
            logger.error("Columna inválida: %s", column_to_convert)
            messages.error(request, "Columna inválida para conversión")
            return redirect('analyst:data_upload')
        
        # Intentar conversión a fecha
        original_col = df[column_to_convert].copy()
        
        if date_format != 'infer':
            df[column_to_convert] = pd.to_datetime(
                df[column_to_convert], 
                format=date_format,
                errors='coerce'
            )
        else:
            df[column_to_convert] = pd.to_datetime(
                df[column_to_convert],
                infer_datetime_format=True,
                errors='coerce'
            )
        
        # Verificar éxito de conversión
        null_ratio = df[column_to_convert].isna().mean()
        success_rate = 1 - null_ratio
        
        if success_rate < 0.7:
            logger.warning("Tasa de éxito baja: %.2f", success_rate)
            messages.warning(
                request,
                f"Solo {success_rate:.0%} de los valores se pudieron convertir"
            )
        
        # Actualizar datos de sesión
        upload_data['df_rows'] = _df_to_session_rows(df)
        request.session['upload_data'] = upload_data
        request.session.modified = True
        
        logger.info("Conversión exitosa - Columna: %s", column_to_convert)
        messages.success(
            request, 
            f"Columna '{column_to_convert}' convertida a fecha. "
            f"Éxito: {success_rate:.0%}"
        )
        
        return redirect(reverse('analyst:data_upload') + '#preview-section')
        
    except Exception as e:
        logger.error("Error en conversión de fecha: %s", str(e), exc_info=True)
        messages.error(request, f"Error al convertir fechas: {str(e)}")
        return redirect('analyst:data_upload')


def _handle_clipboard_edit(request):
    """
    Maneja las acciones de edición del clipboard
    """
    logger.debug("=" * 50)
    logger.debug("INICIANDO _handle_clipboard_edit")
    
    if 'upload_data' not in request.session:
        logger.error("No hay upload_data en sesión")
        messages.error(request, "No hay datos para editar")
        return redirect('analyst:data_upload')
    
    try:
        upload_data = request.session['upload_data']
        upload_data = _convert_to_consistent_format(upload_data)
        
        # Crear DataFrame
        df = pd.DataFrame.from_records(upload_data['df_rows'])
        df.columns = upload_data['df_columns']
        
        # Procesar acciones
        if 'delete_columns' in request.POST:
            columns_to_delete = request.POST.getlist('columns_to_delete')
            valid_columns = [col for col in columns_to_delete if col in df.columns]
            
            if valid_columns:
                df = df.drop(columns=valid_columns)
                logger.info("Columnas eliminadas: %s", valid_columns)
                messages.success(request, f"Columnas eliminadas: {', '.join(valid_columns)}")
        
        elif 'replace_values' in request.POST:
            column = request.POST.get('replace_column')
            old_value = request.POST.get('old_value', '')
            new_value = request.POST.get('new_value', '')
            
            if column in df.columns:
                df[column] = df[column].replace(old_value, new_value)
                logger.info("Valores reemplazados en columna: %s", column)
                messages.success(request, f"Valores reemplazados en {column}")
        
        elif 'fill_na' in request.POST:
            column = request.POST.get('fill_column')
            fill_value = request.POST.get('fill_value')
            
            if column in df.columns:
                df[column] = df[column].fillna(fill_value)
                logger.info("Nulos rellenados en columna: %s", column)
                messages.success(request, f"Valores nulos rellenados en {column}")
        
        # Guardar cambios
        upload_data['df_columns'] = df.columns.tolist()
        upload_data['df_rows'] = _df_to_session_rows(df)
        request.session['upload_data'] = upload_data
        request.session.modified = True
        
        return redirect(reverse('analyst:data_upload') + '#preview-section')
        
    except Exception as e:
        logger.error("Error editando datos: %s", str(e), exc_info=True)
        messages.error(request, f"Error al editar datos: {str(e)}")
        return redirect('analyst:data_upload')


# =============================================================================
# MÉTODOS AUXILIARES
# =============================================================================

def _df_to_session_rows(df):
    """
    Convierte un DataFrame a lista de dicts JSON-serializable para guardar en sesión.

    Problemas que resuelve:
      - pd.Timestamp / datetime64  → string ISO  "2024-01-31"
      - np.nan                     → None
      - np.int64 / np.float64      → int / float nativos de Python
      - pd.NA / pd.NaT             → None

    Usa df.astype(object) para colapsar todos los dtypes a Python nativo
    antes de llamar a to_dict(), y luego hace un segundo pase para los
    Timestamps que pandas deja como objetos.
    """
    import math

    def _safe(v):
        if v is None:
            return None
        # NaT, NA
        try:
            if pd.isna(v):
                return None
        except (TypeError, ValueError):
            pass
        # Timestamp / datetime
        if hasattr(v, 'isoformat'):
            return v.isoformat()
        # numpy int / float
        if isinstance(v, (np.integer,)):
            return int(v)
        if isinstance(v, (np.floating,)):
            f = float(v)
            return None if math.isnan(f) else f
        return v

    records = df.replace({np.nan: None}).to_dict('records')
    return [{k: _safe(v) for k, v in row.items()} for row in records]


def _convert_to_consistent_format(upload_data):
    """Convierte los datos de la sesión a un formato consistente"""
    if not upload_data.get('df_rows'):
        return upload_data
    
    if upload_data['df_rows'] and isinstance(upload_data['df_rows'][0], dict):
        return upload_data
    
    # Convertir de lista de listas a lista de diccionarios
    columns = upload_data['df_columns']
    rows = upload_data['df_rows']
    
    if rows:
        dict_rows = [dict(zip(columns, row)) for row in rows]
        upload_data['df_rows'] = dict_rows
    
    return upload_data


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


def _map_columns_to_model(request, df, model_fields):
    """Mapea columnas del DataFrame a campos del modelo"""
    column_mapping = {}
    unused_columns = []
    
    for col in df.columns:
        col_str = str(col)
        best_match = _find_best_match(col_str, model_fields)
        if best_match:
            column_mapping[col_str] = best_match
            logger.debug("Columna '%s' mapeada a '%s'", col_str, best_match)
        else:
            unused_columns.append(col_str)
    
    if unused_columns:
        logger.debug("Columnas no mapeadas: %s", unused_columns[:10])
        messages.warning(
            request,
            f"Columnas no mapeadas: {', '.join(unused_columns[:10])}" +
            ("..." if len(unused_columns) > 10 else "")
        )
    
    return column_mapping, unused_columns


def _find_best_match(col_name, available_fields):
    """Encuentra la mejor coincidencia para el nombre de columna"""
    col_clean = (str(col_name).lower()
                .replace('á', 'a').replace('é', 'e').replace('í', 'i')
                .replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
                .strip())
    
    # Coincidencias exactas
    for field_name, field_info in available_fields.items():
        field_name_str = str(field_name).lower()
        verbose_name_str = str(field_info['verbose_name']).lower()
        if col_clean == field_name_str or col_clean == verbose_name_str:
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
            if (match == str(field_name).lower() or 
                match == str(field_info['verbose_name']).lower()):
                return field_name
    
    return None


def _validate_required_fields(model_fields, column_mapping):
    """Valida que todos los campos requeridos estén mapeados"""
    missing = [
        field_name for field_name, field_info in model_fields.items()
        if not field_info['null'] and not field_info['blank']
        and field_name not in column_mapping.values()
    ]
    return missing
    
    
# analyst/views/data_upload.py

import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

@require_POST
def save_clipboard_ajax(request):
    """
    Guarda un DataFrame en el portapapeles vía AJAX
    """
    logger.debug("=" * 50)
    logger.debug("INICIANDO save_clipboard_ajax")
    
    try:
        data = json.loads(request.body)
        clip_name = data.get('clip_name')
        clip_description = data.get('clip_description', '')
        
        upload_data = request.session.get('upload_data')
        if not upload_data:
            return JsonResponse({'error': 'No hay datos para guardar'}, status=400)
        
        df = pd.DataFrame(upload_data['df_rows'], columns=upload_data['df_columns'])
        
        # Guardar en portapapeles
        clip_key = DataFrameClipboard.store_df(
            request,
            df,
            key=clip_name,
            metadata={
                'filename': upload_data.get('filename', ''),
                'model': upload_data.get('model_path', ''),
                'sheet_info': upload_data.get('excel_info', {}),
                'description': clip_description,
                'rows': len(df),
                'columns': len(df.columns)
            }
        )
        
        # Obtener la lista actualizada de clips
        clips = DataFrameClipboard.list_clips(request)
        
        # Asegurarse de que cada clip tenga la estructura correcta
        formatted_clips = []
        for clip in clips:
            formatted_clips.append({
                'key': clip.get('key'),
                'rows': clip.get('rows', clip.get('shape', [0, 0])[0]),
                'cols': clip.get('cols', clip.get('shape', [0, 0])[1]),
                'filename': clip.get('filename', ''),
                'description': clip.get('description', ''),  # ¡Importante! Incluir la descripción
                'created_at': clip.get('created_at', '')
            })
        
        return JsonResponse({
            'success': True,
            'clip_key': clip_key,
            'clips': formatted_clips,
            'message': f'Clip guardado como {clip_name}'
        })
        
    except Exception as e:
        logger.error(f"Error guardando clip: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def load_clipboard_data(request):
    """
    Carga los datos de un clip y los prepara para la vista previa
    """
    logger.debug("=" * 50)
    logger.debug("INICIANDO load_clipboard_data")
    
    clip_name = request.GET.get('clip_name')
    model_path = request.GET.get('model')
    
    if not clip_name or not model_path:
        return JsonResponse({'error': 'Faltan parámetros'}, status=400)
    
    try:
        # Cargar clip
        df, metadata = DataFrameClipboard.retrieve_df(request, clip_name)
        
        if df is None:
            return JsonResponse({'error': 'Clip no encontrado'}, status=404)
        
        # Obtener modelo
        model = apps.get_model(model_path)
        
        # Analizar campos
        model_fields_info, mapped_columns, required_fields_names = ModelMapper.analyze_model_fields(model, df)
        required_fields = [field for field in model_fields_info if field['required']]
        
        # Guardar en sesión
        session_data = {
            'df_columns': df.columns.tolist(),
            'df_rows': _df_to_session_rows(df),
            'model_path': model_path,
            'clear_existing': False,
            'file_type': 'clipboard',
            'excel_info': metadata.get('sheet_info', {}),
            'filename': metadata.get('filename', clip_name),
            'clip_name': clip_name
        }
        request.session['upload_data'] = session_data
        request.session.modified = True
        
        # Preparar información para la vista previa
        df = _rename_duplicate_columns(df)
        df_info = {
            'rows':    len(df),
            'columns': len(df.columns),
            'column_stats': [],
        }
        for i, col in enumerate(df.columns):
            series = df.iloc[:, i]
            missing_count   = int(series.isnull().sum())
            missing_percent = round((missing_count / df_info['rows']) * 100, 2) if df_info['rows'] > 0 else 0
            df_info['column_stats'].append({
                'name':            str(col),
                'type':            str(series.dtype),
                'missing_count':   missing_count,
                'missing_percent': missing_percent,
            })

        # Preparar mapeo de columnas
        column_mapping_info = []
        for i, col in enumerate(df.columns):
            col_str  = str(col)
            series   = df.iloc[:, i]
            matched  = False
            mapped_to = None
            for field in model_fields_info:
                if col_str.lower() in (field['name'].lower(), field['verbose_name'].lower()):
                    mapped_to = field['name']
                    matched   = True
                    break
            column_mapping_info.append({
                'column':    col_str,
                'dtype':     str(series.dtype),
                'mapped_to': mapped_to,
                'matched':   matched,
            })

        # Determinar columnas no mapeadas
        model_field_names   = {f['name'].lower()        for f in model_fields_info}
        model_verbose_names = {f['verbose_name'].lower() for f in model_fields_info}
        unmapped_columns = [
            str(col) for col in df.columns
            if str(col).lower() not in model_field_names
            and str(col).lower() not in model_verbose_names
        ]

        column_headers = [
            {'name': s['name'], 'missing_count': s['missing_count'], 'missing_percent': s['missing_percent']}
            for s in df_info['column_stats']
        ]

        return JsonResponse({
            'success': True,
            'preview_data': {
                'df_info': df_info,
                'df_preview': {
                    'columns':        [str(col) for col in df.columns.tolist()],
                    'column_headers': column_headers,
                    'rows':           df.head(10).replace({np.nan: None}).values.tolist(),
                },
                'model_fields_info':   model_fields_info,
                'mapped_columns_count': len(mapped_columns),
                'required_fields':     required_fields,
                'unmapped_columns':    unmapped_columns,
                'column_mapping_info': column_mapping_info,
                'excel_info': metadata.get('sheet_info', {}),
                'model_verbose_name': str(model._meta.verbose_name)
            }
        })
        
    except Exception as e:
        logger.error(f"Error cargando clip: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
        
def _render_preview_from_session(request):
    """
    Renderiza la vista previa usando los datos guardados en sesión
    (para cuando se carga un clip)
    """
    logger.debug("=" * 50)
    logger.debug("INICIANDO _render_preview_from_session")
    
    upload_data = request.session.get('upload_data')
    if not upload_data:
        logger.error("No hay datos en sesión")
        messages.error(request, "No hay datos para mostrar")
        return redirect('analyst:data_upload')
    
    try:
        # Reconstruir DataFrame
        df = pd.DataFrame(upload_data['df_rows'], columns=upload_data['df_columns'])
        
        # Obtener modelo
        model = apps.get_model(upload_data['model_path'])
        
        # Analizar campos del modelo
        model_fields_info, mapped_columns, required_fields_names = ModelMapper.analyze_model_fields(model, df)
        required_fields = [field for field in model_fields_info if field['required']]
        
        # Crear formulario con valores iniciales (NO lo vamos a validar)
        form = DataUploadForm(initial={
            'model': upload_data['model_path'],
            'clear_existing': upload_data.get('clear_existing', False)
        })
        
        # Preparar información del DataFrame
        df = _rename_duplicate_columns(df)
        df_info = {
            'rows':    len(df),
            'columns': len(df.columns),
            'column_stats': [],
        }
        for i, col in enumerate(df.columns):
            series = df.iloc[:, i]
            missing_count   = int(series.isnull().sum())
            missing_percent = round((missing_count / df_info['rows']) * 100, 2) if df_info['rows'] > 0 else 0
            df_info['column_stats'].append({
                'name':            str(col),
                'type':            str(series.dtype),
                'missing_count':   missing_count,
                'missing_percent': missing_percent,
            })

        # Preparar mapeo de columnas
        column_mapping_info = []
        for i, col in enumerate(df.columns):
            col_str  = str(col)
            series   = df.iloc[:, i]
            matched  = False
            mapped_to = None
            for field in model_fields_info:
                if col_str.lower() in (field['name'].lower(), field['verbose_name'].lower()):
                    mapped_to = field['name']
                    matched   = True
                    break
            column_mapping_info.append({
                'column':    col_str,
                'dtype':     str(series.dtype),
                'mapped_to': mapped_to,
                'matched':   matched,
            })

        # Determinar columnas no mapeadas
        model_field_names   = {f['name'].lower()        for f in model_fields_info}
        model_verbose_names = {f['verbose_name'].lower() for f in model_fields_info}
        unmapped_columns = [
            str(col) for col in df.columns
            if str(col).lower() not in model_field_names
            and str(col).lower() not in model_verbose_names
        ]

        column_headers = [
            {'name': s['name'], 'missing_count': s['missing_count'], 'missing_percent': s['missing_percent']}
            for s in df_info['column_stats']
        ]

        # Obtener lista de clips
        clipboard_keys = DataFrameClipboard.list_clips(request)

        # Preparar contexto SIN usar cleaned_data
        context = {
            'form':               form,
            'preview_mode':       True,
            'target_model':       upload_data['model_path'],
            'model_verbose_name': str(model._meta.verbose_name),
            'model_fields_info':  model_fields_info,
            'mapped_columns_count': len(mapped_columns),
            'required_fields':    required_fields,
            'df_info':            df_info,
            'df_preview': {
                'columns':        [str(col) for col in df.columns.tolist()],
                'column_headers': column_headers,
                'rows':           df.head(10).replace({np.nan: None}).values.tolist(),
            },
            'excel_info':         upload_data.get('excel_info', {}),
            'unmapped_columns':   unmapped_columns,
            'column_mapping_info': column_mapping_info,
            'clipboard_keys':     clipboard_keys,
            'stored_datasets':    StoredDataset.objects.filter(created_by=request.user).values(
                                      'id', 'name', 'rows', 'col_count', 'source_file', 'created_at'),
            'analyst_bases':      AnalystBase.objects.filter(
                                      created_by=request.user).select_related('dataset'),
            'cross_sources':      CrossSource.objects.filter(
                                      created_by=request.user).select_related('last_result'),
            'dashboard_mode':     True,
        }
        
        logger.info("Vista previa desde sesión renderizada correctamente")
        return render(request, 'analyst/upload_data_csv.html', context)
        
    except Exception as e:
        logger.error(f"Error renderizando preview desde sesión: {str(e)}", exc_info=True)
        messages.error(request, f"Error al cargar los datos: {str(e)}")
        return redirect('analyst:data_upload')        


@require_POST
def delete_clip_ajax(request):
    """
    Elimina un DataFrame del portapapeles vía AJAX
    """
    logger.debug("=" * 50)
    logger.debug("INICIANDO delete_clip_ajax")
    
    try:
        data = json.loads(request.body)
        clip_name = data.get('clip_name')
        
        if not clip_name:
            return JsonResponse({'error': 'No se especificó clip'}, status=400)
        
        logger.debug(f"Eliminando clipboard: {clip_name}")
        
        if DataFrameClipboard.delete_df(request, clip_name):
            # Obtener la lista actualizada de clips
            clips = DataFrameClipboard.list_clips(request)
            
            # Formatear clips
            formatted_clips = []
            for clip in clips:
                formatted_clips.append({
                    'key': clip.get('key'),
                    'rows': clip.get('rows', clip.get('shape', [0, 0])[0]),
                    'cols': clip.get('cols', clip.get('shape', [0, 0])[1]),
                    'filename': clip.get('filename', ''),
                    'description': clip.get('description', ''),
                    'created_at': clip.get('created_at', '')
                })
            
            return JsonResponse({
                'success': True,
                'clips': formatted_clips,
                'message': f'Clip {clip_name} eliminado'
            })
        else:
            return JsonResponse({'error': 'No se pudo eliminar el clip'}, status=400)
        
    except Exception as e:
        logger.error(f"Error eliminando clip: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def clear_all_clips_ajax(request):
    """
    Elimina todos los DataFrames del portapapeles vía AJAX
    """
    logger.debug("=" * 50)
    logger.debug("INICIANDO clear_all_clips_ajax")
    
    try:
        count = DataFrameClipboard.clear_clips(request)
        
        # Obtener la lista actualizada de clips (vacía)
        clips = DataFrameClipboard.list_clips(request)
        
        return JsonResponse({
            'success': True,
            'clips': clips,
            'message': f'Se eliminaron {count} clips'
        })
        
    except Exception as e:
        logger.error(f"Error limpiando clips: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)