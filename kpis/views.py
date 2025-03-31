# kpis/views.py
from django.db.models import Avg, Count
import json
from random import randint
import csv
import chardet
from django.shortcuts import render, redirect
from .forms import UploadCSVForm
from .models import CallRecord
from django.http import JsonResponse
from django.contrib import messages

def detect_encoding(file):
    # Leer primeros 10KB para detección más precisa
    raw_data = file.read(10240)
    result = chardet.detect(raw_data)
    file.seek(0)
    
    # Manejar casos comunes para español
    if result['encoding'] in ['ISO-8859-1', 'Windows-1252']:
        return 'latin-1'
    return result['encoding'] if result['confidence'] > 0.6 else 'latin-1'

def upload_csv(request):
    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            try:
                # 1. Limpiar la tabla existente (TRUNCATE eficiente)
                CallRecord.objects.all().delete()
                messages.info(request, "Datos anteriores eliminados correctamente")
                
                # 2. Detectar codificación
                encoding = detect_encoding(csv_file)
                
                try:
                    decoded_file = csv_file.read().decode(encoding)
                except UnicodeDecodeError as e:
                    decoded_file = csv_file.read().decode(encoding, errors='replace')
                    messages.warning(request, 
                        "Algunos caracteres fueron reemplazados debido a problemas de codificación")
                
                # 3. Procesar CSV
                reader = csv.DictReader(decoded_file.splitlines(), delimiter=';')
                
                # 4. Validar headers
                required_headers = {
                    'semana': {'semana', 'week', 'periodo'},
                    'agente': {'agente', 'agent', 'operador'},
                    'supervisor': {'supervisor', 'leader', 'manager'},
                    'servicio': {'servicio', 'service', 'tipo'},
                    'canal': {'canal', 'channel', 'medio'},
                    'eventos': {'eventos', 'events', 'interacciones'},
                    'aht': {'aht', 'tiempo_medio', 'average_handling_time'},
                    'evaluaciones': {'evaluaciones', 'evaluations', 'calificaciones'},
                    'satisfacción': {'satisfacción', 'satisfaccion', 'satisfaction', 'nps'}
                }
                
                normalized_headers = {col.lower().strip(): col for col in reader.fieldnames}
                missing_columns = [
                    key for key, aliases in required_headers.items()
                    if not any(alias in normalized_headers for alias in aliases)
                ]
                
                if missing_columns:
                    friendly_names = {
                        'semana': 'Semana', 'agente': 'Agente', 'supervisor': 'Supervisor',
                        'servicio': 'Servicio', 'canal': 'Canal', 'eventos': 'Eventos',
                        'aht': 'AHT', 'evaluaciones': 'Evaluaciones', 'satisfacción': 'Satisfacción'
                    }
                    raise ValueError(
                        f"Columnas requeridas faltantes: {', '.join(friendly_names[col] for col in missing_columns)}"
                    )
                
                # 5. Procesar registros
                records = []
                total_rows = 0
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Normalizar nombres de columnas
                        normalized_row = {
                            'Semana': row.get(normalized_headers.get('semana', 'semana')),
                            'Agente': row.get(normalized_headers.get('agente', 'agente')),
                            'Supervisor': row.get(normalized_headers.get('supervisor', 'supervisor')),
                            'Servicio': row.get(normalized_headers.get('servicio', 'servicio')),
                            'Canal': row.get(normalized_headers.get('canal', 'canal')),
                            'Eventos': row.get(normalized_headers.get('eventos', 'eventos')),
                            'AHT': row.get(normalized_headers.get('aht', 'aht')),
                            'Evaluaciones': row.get(normalized_headers.get('evaluaciones', 'evaluaciones')),
                            'Satisfacción': row.get(normalized_headers.get('satisfacción', 'satisfacción'))
                        }
                        
                        records.append(CallRecord(
                            semana=int(normalized_row['Semana']),
                            agente=normalized_row['Agente'].strip(),
                            supervisor=normalized_row['Supervisor'].strip(),
                            servicio=normalized_row['Servicio'].strip(),
                            canal=normalized_row['Canal'].strip(),
                            eventos=int(normalized_row['Eventos']),
                            aht=float(normalized_row['AHT'].replace(',', '.')),
                            evaluaciones=int(normalized_row['Evaluaciones']),
                            satisfaccion=float(normalized_row['Satisfacción'].replace(',', '.'))
                        ))
                        total_rows += 1
                            
                    except (ValueError, KeyError) as e:
                        messages.warning(request, f"Error en fila {row_num}: {str(e)} - Fila omitida")
                        continue
                
                # 6. Carga masiva optimizada
                if records:
                    CallRecord.objects.bulk_create(records, batch_size=1000)
                    messages.success(request, 
                        f"Carga exitosa: {total_rows} registros importados correctamente")
                else:
                    messages.info(request, "No se encontraron registros válidos para importar")
                
                return redirect('dashboard')
                
            except ValueError as e:
                form.add_error('csv_file', str(e))
            except Exception as e:
                form.add_error('csv_file', f'Error inesperado: {str(e)}')
                # Revertir cambios si hubo error después de borrar
                CallRecord.objects.all().delete()
                messages.error(request, "Error durante la importación. La base de datos ha sido limpiada.")
    
    else:
        form = UploadCSVForm()
    
    return render(request, 'upload_csv.html', {
        'form': form,
        'active_tab': 'upload'
    })

def aht_dashboard(request):
    # Obtener datos por servicio
    aht_por_servicio = list(CallRecord.objects.values('servicio').annotate(
        avg_aht=Avg('aht'),
        total_eventos=Count('id')
    ).order_by('-avg_aht'))
    
    # Obtener datos por canal
    aht_por_canal = list(CallRecord.objects.values('canal').annotate(
        avg_aht=Avg('aht'),
        total_eventos=Count('id')
    ).order_by('-avg_aht'))
    
    # Obtener datos por semana
    aht_por_semana = list(CallRecord.objects.values('semana').annotate(
        avg_aht=Avg('aht'),
        total_eventos=Count('id')
    ).order_by('semana'))
    
    # Obtener datos por supervisor
    aht_por_supervisor = list(CallRecord.objects.values('supervisor').annotate(
        avg_aht=Avg('aht'),
        total_eventos=Count('id')
    ).order_by('-avg_aht'))
    
    # Preparar datos para el gráfico principal (por servicio)
    chart_data = {
        'labels': [item['servicio'] for item in aht_por_servicio],
        'data': [float(item['avg_aht']) for item in aht_por_servicio],
        'backgroundColors': [
            f'rgba({randint(50, 200)}, {randint(50, 200)}, {randint(50, 200)}, 0.6)'
            for _ in aht_por_servicio
        ]
    }
    
    # Contexto para la plantilla
    context = {
        'chart_data_json': json.dumps(chart_data, ensure_ascii=False),
        'aht_por_servicio': aht_por_servicio,
        'aht_por_canal': aht_por_canal,
        'aht_por_semana': aht_por_semana,
        'aht_por_supervisor': aht_por_supervisor,
        
        # Datos adicionales para resumen
        'total_llamadas': CallRecord.objects.count(),
        'aht_promedio_general': CallRecord.objects.aggregate(avg_aht=Avg('aht'))['avg_aht'],
        'servicio_mas_alto': max(aht_por_servicio, key=lambda x: x['avg_aht'], default={'servicio': 'N/A', 'avg_aht': 0}),
        'servicio_mas_bajo': min(aht_por_servicio, key=lambda x: x['avg_aht'], default={'servicio': 'N/A', 'avg_aht': 0}),
    }
    
    return render(request, 'kpi_dashboard.html', context)

def export_data(request):  
    data = list(CallRecord.objects.values())  
    return JsonResponse(data, safe=False)  