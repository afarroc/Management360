# analyst/views/clipboard.py
import logging
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib import messages
from django.apps import apps
import pandas as pd
from io import StringIO
import sys

from analyst.utils.clipboard import DataFrameClipboard
from analyst.forms import DataUploadForm
from analyst.services.model_mapper import ModelMapper

logger = logging.getLogger(__name__)

@require_GET
def clipboard_details(request):
    """
    Vista para obtener detalles de un DataFrame en el portapapeles
    """
    clip_key = request.GET.get('key')
    
    if not clip_key:
        logger.error("No se proporcionó key del clipboard")
        return JsonResponse({'error': 'No clip key provided'}, status=400)
    
    # Recuperar DataFrame
    df, metadata = DataFrameClipboard.retrieve_df(request, clip_key)
    
    if df is None:
        logger.error(f"Clip no encontrado: {clip_key}")
        return JsonResponse({'error': 'Clip not found'}, status=404)
    
    logger.debug(f"Detalles solicitados para clip: {clip_key} - Shape: {df.shape}")
    
    # Preparar datos para la vista previa
    data_preview = {
        'columns': df.columns.tolist(),
        'rows': df.head(10).replace({pd.NA: None}).values.tolist()
    }
    
    # Calcular estadísticas básicas
    stats = {
        'total_rows': len(df),
        'total_cols': len(df.columns),
        'memory_usage': sys.getsizeof(df),
        'null_counts': df.isnull().sum().to_dict(),
        'dtypes': df.dtypes.astype(str).to_dict()
    }
    
    context = {
        'clip': {
            'key': clip_key,
            'data': data_preview,
            'metadata': metadata,
            'stats': stats,
            'timestamp': metadata.get('created_at', 'Unknown'),
            'filename': metadata.get('filename', 'Sin archivo')
        }
    }
    
    html = render_to_string('analyst/partials/clipboard_details.html', context)
    return JsonResponse({'html': html})


@require_GET
def export_clipboard_csv(request):
    """
    Exporta un DataFrame del portapapeles como CSV
    """
    clip_key = request.GET.get('key')
    
    if not clip_key:
        logger.error("No se proporcionó key del clipboard")
        return HttpResponse('No clip key provided', status=400)
    
    # Recuperar DataFrame
    df, metadata = DataFrameClipboard.retrieve_df(request, clip_key)
    
    if df is None:
        logger.error(f"Clip no encontrado: {clip_key}")
        return HttpResponse('Clip not found', status=404)
    
    logger.info(f"Exportando clip {clip_key} - Shape: {df.shape}")
    
    # Crear respuesta CSV
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    
    filename = metadata.get('filename', clip_key).replace('.', '_') + '.csv'
    
    response = HttpResponse(csv_buffer.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@require_GET
def clipboard_list(request):
    """
    Lista todos los clips disponibles
    """
    clips = DataFrameClipboard.list_clips(request)
    return JsonResponse({'clips': clips})


@require_GET
def load_clipboard_form(request):
    """
    Muestra el formulario para seleccionar modelo al cargar un clip
    """
    clip_key = request.GET.get('key')
    
    if not clip_key:
        messages.error(request, "No se especificó ningún clip")
        return redirect('analyst:data_upload')
    
    # Recuperar DataFrame para mostrar información
    df, metadata = DataFrameClipboard.retrieve_df(request, clip_key)
    
    if df is None:
        messages.error(request, "El clip no existe o ha expirado")
        return redirect('analyst:data_upload')
    
    logger.info(f"Mostrando formulario para cargar clip: {clip_key} - Shape: {df.shape}")
    
    # Guardar clip_key en sesión para usarlo en la carga
    request.session['pending_clip_key'] = clip_key
    
    # Si hay modelo en metadata, guardarlo también
    if metadata and metadata.get('model'):
        request.session['pending_model'] = metadata.get('model')
    
    request.session.modified = True
    
    # Crear formulario con modelo preseleccionado si existe en metadata
    initial_data = {}
    if metadata and metadata.get('model'):
        try:
            model = apps.get_model(metadata['model'])
            if model:
                initial_data['model'] = f"{model._meta.app_label}.{model._meta.model_name}"
        except (LookupError, ValueError):
            pass
    
    form = DataUploadForm(initial=initial_data)
    
    context = {
        'form': form,
        'clip_key': clip_key,
        'clip_info': {
            'filename': metadata.get('filename', 'Sin archivo'),
            'rows': len(df),
            'columns': len(df.columns),
            'created_at': metadata.get('created_at', 'Unknown')
        },
        'dashboard_mode': True
    }
    
    return render(request, 'analyst/load_clipboard_form.html', context)


@require_GET
def load_clipboard_form_data(request):
    """
    Devuelve el HTML del formulario para cargar un clip (usado en el modal)
    """
    clip_key = request.GET.get('key')
    
    if not clip_key:
        return JsonResponse({'success': False, 'error': 'No se especificó clip'}, status=400)
    
    df, metadata = DataFrameClipboard.retrieve_df(request, clip_key)
    
    if df is None:
        return JsonResponse({'success': False, 'error': 'Clip no encontrado'}, status=404)
    
    # Crear formulario con modelo preseleccionado si existe en metadata
    initial_data = {}
    if metadata and metadata.get('model'):
        try:
            model = apps.get_model(metadata['model'])
            if model:
                initial_data['model'] = f"{model._meta.app_label}.{model._meta.model_name}"
        except (LookupError, ValueError):
            pass
    
    form = DataUploadForm(initial=initial_data)
    
    # Generar HTML del formulario
    form_html = f'''
        <div class="form-group">
            <label class="form-label" for="modal_model_select">
                <i class="fas fa-database"></i> Modelo Destino
            </label>
            <select name="model" class="form-control" id="modal_model_select" required>
                <option value="">---------</option>
    '''
    
    for value, label in form.fields['model'].choices:
        selected = 'selected' if form.initial.get('model') == value else ''
        form_html += f'<option value="{value}" {selected}>{label}</option>'
    
    form_html += '''
            </select>
            <small>Selecciona el modelo donde se cargarán los datos del clip</small>
        </div>
    
        <div class="form-group">
            <div class="form-check">
                <input type="checkbox" name="clear_existing" class="form-check-input" id="modal_clear_existing">
                <label class="form-check-label" for="modal_clear_existing">
                    Eliminar datos existentes antes de cargar
                </label>
            </div>
        </div>
    '''
    
    return JsonResponse({
        'success': True,
        'form_html': form_html
    })
    
