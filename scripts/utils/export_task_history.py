#!/usr/bin/env python3
"""
Script para exportar historial COMPLETO de TODAS las tareas
Uso: python export_task_history.py [--format csv|json] [--output archivo] [--task TASK_ID]
"""

import os
import sys
import django
import csv
import json
from datetime import datetime
from collections import defaultdict

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

# Importar modelos después de setup
from events.models import Task, TaskHistory, TaskState, TaskStatus
from django.utils import timezone
from django.db.models import Count, Q

def export_all_tasks_history(output_format='csv', output_file=None, task_id=None):
    """
    Exporta historial completo de todas las tareas o de una específica
    """
    # Base queryset
    if task_id:
        tasks = Task.objects.filter(id=task_id)
        if not tasks.exists():
            print(f"❌ Error: No existe tarea con ID {task_id}")
            return False
        print(f"📋 Exportando historial de la tarea {task_id}...")
    else:
        tasks = Task.objects.all().order_by('id')
        total = tasks.count()
        print(f"📋 Exportando historial COMPLETO de {total} tareas...")
    
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = f"task_{task_id}" if task_id else "all_tasks"
        output_file = f"history_{suffix}_{timestamp}.{output_format}"
    
    if output_format == 'json':
        return export_all_as_json(tasks, output_file, task_id)
    else:
        return export_all_as_csv(tasks, output_file, task_id)

def export_all_as_csv(tasks, filename, single_task_id=None):
    """Exportar TODAS las tareas como CSV con historial completo"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(['='*80])
            writer.writerow(['HISTORIAL COMPLETO DE TAREAS'])
            writer.writerow(['='*80])
            writer.writerow(['Generated:', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow(['Total Tasks:', tasks.count()])
            writer.writerow([])
            
            # Resumen global
            writer.writerow(['='*80])
            writer.writerow(['RESUMEN GLOBAL'])
            writer.writerow(['='*80])
            
            total_edits = TaskHistory.objects.filter(task__in=tasks).count()
            total_status_changes = TaskState.objects.filter(task__in=tasks).count()
            
            writer.writerow(['Total Edits:', total_edits])
            writer.writerow(['Total Status Changes:', total_status_changes])
            writer.writerow([])
            
            # Estadísticas por estado
            status_counts = tasks.values('task_status__status_name').annotate(
                count=Count('id')
            ).order_by('-count')
            
            writer.writerow(['TASKS BY STATUS'])
            for status in status_counts:
                writer.writerow([status['task_status__status_name'] or 'No Status', status['count']])
            writer.writerow([])
            
            # Detalle por tarea
            for idx, task in enumerate(tasks, 1):
                print(f"  Procesando tarea {idx}/{tasks.count()}: {task.title[:30]}...")
                
                history = TaskHistory.objects.filter(task=task).select_related('editor').order_by('edited_at')
                states = TaskState.objects.filter(task=task).select_related('status').order_by('start_time')
                
                writer.writerow(['='*80])
                writer.writerow([f'TAREA #{idx} - ID: {task.id}'])
                writer.writerow(['='*80])
                
                # Información básica
                writer.writerow(['BASIC INFORMATION'])
                writer.writerow(['Title:', task.title])
                writer.writerow(['Description:', task.description or ''])
                writer.writerow(['Current Status:', task.task_status.status_name if task.task_status else 'N/A'])
                writer.writerow(['Assigned To:', task.assigned_to.username if task.assigned_to else 'N/A'])
                writer.writerow(['Host:', task.host.username if task.host else 'N/A'])
                writer.writerow(['Project:', task.project.title if task.project else 'N/A'])
                writer.writerow(['Event:', task.event.title if task.event else 'N/A'])
                writer.writerow(['Important:', 'Yes' if task.important else 'No'])
                writer.writerow(['Done:', 'Yes' if task.done else 'No'])
                writer.writerow(['Created:', task.created_at])
                writer.writerow(['Last Updated:', task.updated_at])
                writer.writerow([])
                
                # Estadísticas de la tarea
                writer.writerow(['TASK STATISTICS'])
                writer.writerow(['Total Edits:', history.count()])
                writer.writerow(['Total Status Changes:', states.count()])
                
                if states.exists():
                    # Calcular tiempo total en progreso
                    total_duration = 0
                    for s in states:
                        if s.end_time:
                            total_duration += (s.end_time - s.start_time).total_seconds() / 3600
                    writer.writerow(['Total Time in Progress:', f'{total_duration:.2f} hours'])
                    
                    # Tiempo por estado
                    writer.writerow(['Time per Status:'])
                    status_times = defaultdict(float)
                    for s in states:
                        if s.end_time:
                            duration = (s.end_time - s.start_time).total_seconds() / 3600
                            status_times[s.status.status_name] += duration
                    
                    for status_name, hours in status_times.items():
                        writer.writerow([f'  - {status_name}:', f'{hours:.2f} hours'])
                writer.writerow([])
                
                # Edit History
                if history.exists():
                    writer.writerow(['EDIT HISTORY DETAIL'])
                    writer.writerow(['Date', 'Editor', 'Field', 'Old Value', 'New Value'])
                    for h in history:
                        writer.writerow([
                            h.edited_at.strftime("%Y-%m-%d %H:%M:%S"),
                            h.editor.username if h.editor else 'System',
                            h.field_name,
                            (h.old_value or '')[:100],
                            (h.new_value or '')[:100]
                        ])
                    writer.writerow([])
                
                # Status History
                if states.exists():
                    writer.writerow(['STATUS HISTORY DETAIL'])
                    writer.writerow(['Start Time', 'End Time', 'Status', 'Duration (hours)', 'Duration (readable)'])
                    for s in states:
                        duration_hours = ''
                        duration_readable = ''
                        if s.end_time:
                            delta = s.end_time - s.start_time
                            duration_hours = round(delta.total_seconds() / 3600, 2)
                            days = delta.days
                            hours = delta.seconds // 3600
                            minutes = (delta.seconds % 3600) // 60
                            duration_readable = f"{days}d {hours}h {minutes}m"
                        
                        writer.writerow([
                            s.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                            s.end_time.strftime("%Y-%m-%d %H:%M:%S") if s.end_time else 'CURRENT',
                            s.status.status_name if s.status else 'N/A',
                            duration_hours,
                            duration_readable
                        ])
                    writer.writerow([])
                
                writer.writerow([])  # Espacio entre tareas
            
            # Footer
            writer.writerow(['='*80])
            writer.writerow(['END OF EXPORT'])
            writer.writerow(['='*80])
            writer.writerow(['Total Tasks Exported:', tasks.count()])
            writer.writerow(['Export Completed:', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        
        print(f"\n✅ Exportación completada exitosamente!")
        print(f"📁 Archivo guardado: {filename}")
        print(f"📊 Total tareas exportadas: {tasks.count()}")
        return True
        
    except Exception as e:
        print(f"❌ Error exportando CSV: {e}")
        import traceback
        traceback.print_exc()
        return False

def export_all_as_json(tasks, filename, single_task_id=None):
    """Exportar TODAS las tareas como JSON con historial completo"""
    try:
        data = {
            'export_info': {
                'date': datetime.now().isoformat(),
                'total_tasks': tasks.count(),
                'format': 'full_history'
            },
            'summary': {
                'total_edits': TaskHistory.objects.filter(task__in=tasks).count(),
                'total_status_changes': TaskState.objects.filter(task__in=tasks).count()
            },
            'tasks': []
        }
        
        for idx, task in enumerate(tasks, 1):
            print(f"  Procesando tarea {idx}/{tasks.count()}: {task.title[:30]}...")
            
            history = TaskHistory.objects.filter(task=task).select_related('editor').order_by('edited_at')
            states = TaskState.objects.filter(task=task).select_related('status').order_by('start_time')
            
            # Calcular tiempo por estado
            status_times = {}
            for s in states:
                if s.end_time and s.status:
                    duration = (s.end_time - s.start_time).total_seconds() / 3600
                    status_name = s.status.status_name
                    if status_name in status_times:
                        status_times[status_name] += duration
                    else:
                        status_times[status_name] = duration
            
            task_data = {
                'task_id': task.id,
                'title': task.title,
                'description': task.description,
                'current_status': task.task_status.status_name if task.task_status else None,
                'assigned_to': task.assigned_to.username if task.assigned_to else None,
                'host': task.host.username if task.host else None,
                'project': task.project.title if task.project else None,
                'event': task.event.title if task.event else None,
                'important': task.important,
                'done': task.done,
                'created_at': task.created_at.isoformat(),
                'updated_at': task.updated_at.isoformat(),
                'statistics': {
                    'total_edits': history.count(),
                    'total_status_changes': states.count(),
                    'total_duration_hours': sum(status_times.values()),
                    'time_per_status': status_times
                },
                'edit_history': [
                    {
                        'date': h.edited_at.isoformat(),
                        'editor': h.editor.username if h.editor else 'System',
                        'field': h.field_name,
                        'old_value': h.old_value,
                        'new_value': h.new_value
                    } for h in history
                ],
                'status_history': [
                    {
                        'start': s.start_time.isoformat(),
                        'end': s.end_time.isoformat() if s.end_time else None,
                        'status': s.status.status_name if s.status else None,
                        'duration_hours': round((s.end_time - s.start_time).total_seconds() / 3600, 2) 
                        if s.end_time else None,
                        'duration_readable': str(s.end_time - s.start_time) if s.end_time else None
                    } for s in states
                ]
            }
            data['tasks'].append(task_data)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Exportación completada exitosamente!")
        print(f"📁 Archivo guardado: {filename}")
        print(f"📊 Total tareas exportadas: {tasks.count()}")
        return True
        
    except Exception as e:
        print(f"❌ Error exportando JSON: {e}")
        import traceback
        traceback.print_exc()
        return False

def list_all_tasks():
    """Lista TODAS las tareas con filtros"""
    print("\n" + "="*80)
    print("📋 LISTADO COMPLETO DE TAREAS")
    print("="*80)
    
    # Estadísticas globales
    total = Task.objects.count()
    completed = Task.objects.filter(done=True).count()
    pending = total - completed
    
    print(f"\n📊 ESTADÍSTICAS GLOBALES:")
    print(f"  Total tareas: {total}")
    print(f"  Completadas: {completed} ({completed/total*100:.1f}% )" if total > 0 else "  Completadas: 0")
    print(f"  Pendientes: {pending} ({pending/total*100:.1f}% )" if total > 0 else "  Pendientes: 0")
    
    # Top 10 tareas con más historial
    print(f"\n🏆 TOP 10 TAREAS CON MÁS HISTORIAL:")
    tasks_with_counts = Task.objects.annotate(
        edit_count=Count('taskhistory'),
        status_count=Count('taskstate')
    ).order_by('-edit_count')[:10]
    
    print(f"{'ID':<6} {'Título':<40} {'Edits':<8} {'Status Changes':<15}")
    print("-"*70)
    for task in tasks_with_counts:
        print(f"{task.id:<6} {task.title[:38]:<40} {task.edit_count:<8} {task.status_count:<15}")
    
    # Listado completo paginado
    print(f"\n📋 LISTADO COMPLETO ({total} tareas):")
    print(f"{'ID':<6} {'Estado':<15} {'Importante':<10} {'Título':<50}")
    print("-"*81)
    
    tasks = Task.objects.all().select_related('task_status').order_by('-updated_at')
    for task in tasks:
        status = task.task_status.status_name[:12] if task.task_status else 'N/A'
        important = "★" if task.important else "☆"
        print(f"{task.id:<6} {status:<15} {important:<10} {task.title[:48]}")
    
    print("="*80)

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Exportar historial COMPLETO de tareas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python export_task_history.py                    # Exporta TODAS las tareas a CSV
  python export_task_history.py --format json      # Exporta TODAS a JSON
  python export_task_history.py --task 123         # Exporta SOLO la tarea 123
  python export_task_history.py --output historia.csv  # Exporta a archivo específico
  python export_task_history.py --list             # Lista todas las tareas
  python export_task_history.py --stats            # Muestra estadísticas detalladas
  python export_task_history.py --since 2024-01-01 # Exporta tareas actualizadas desde fecha
        """
    )
    
    parser.add_argument('--format', '-f', choices=['csv', 'json'], default='csv',
                       help='Formato de exportación (default: csv)')
    parser.add_argument('--output', '-o', help='Archivo de salida')
    parser.add_argument('--task', '-t', type=int, help='ID de tarea específica (exporta solo esa)')
    parser.add_argument('--list', '-l', action='store_true', help='Listar TODAS las tareas')
    parser.add_argument('--stats', '-s', action='store_true', help='Mostrar estadísticas detalladas')
    parser.add_argument('--since', help='Exportar tareas actualizadas desde fecha (YYYY-MM-DD)')
    parser.add_argument('--status', help='Filtrar por estado (nombre del estado)')
    
    args = parser.parse_args()
    
    if args.list:
        list_all_tasks()
        return
    
    if args.stats:
        show_detailed_stats()
        return
    
    # Aplicar filtros si existen
    tasks = Task.objects.all()
    
    if args.task:
        tasks = tasks.filter(id=args.task)
    else:
        print("\n🔍 EXPORTANDO HISTORIAL COMPLETO DE TODAS LAS TAREAS")
        print(f"   Total tareas encontradas: {tasks.count()}")
        
        if args.since:
            tasks = tasks.filter(updated_at__date__gte=args.since)
            print(f"   Filtro desde: {args.since}")
        
        if args.status:
            tasks = tasks.filter(task_status__status_name__icontains=args.status)
            print(f"   Filtro estado: {args.status}")
        
        if not tasks.exists():
            print("❌ No se encontraron tareas con los filtros especificados")
            return
        
        print(f"   Tareas a exportar después de filtros: {tasks.count()}")
        
        if tasks.count() > 100:
            print(f"⚠️  ADVERTENCIA: Vas a exportar {tasks.count()} tareas. Esto puede tomar varios minutos.")
            response = input("¿Continuar? (s/N): ").lower()
            if response != 's':
                print("Exportación cancelada.")
                return
    
    # Ejecutar exportación
    success = export_all_tasks_history(
        output_format=args.format,
        output_file=args.output,
        task_id=args.task
    )
    
    sys.exit(0 if success else 1)

def show_detailed_stats():
    """Muestra estadísticas detalladas de todas las tareas"""
    print("\n" + "="*80)
    print("📊 ESTADÍSTICAS DETALLADAS DE TAREAS")
    print("="*80)
    
    # Estadísticas básicas
    total_tasks = Task.objects.count()
    total_history = TaskHistory.objects.count()
    total_states = TaskState.objects.count()
    
    print(f"\n📈 ESTADÍSTICAS GLOBALES:")
    print(f"  Total tareas: {total_tasks}")
    print(f"  Total entradas de historial: {total_history}")
    print(f"  Total cambios de estado: {total_states}")
    print(f"  Promedio ediciones por tarea: {total_history/total_tasks:.2f}" if total_tasks > 0 else "  Promedio ediciones: 0")
    
    # Tareas con más historial
    print(f"\n🏆 TOP 5 TAREAS CON MÁS HISTORIAL:")
    top_tasks = Task.objects.annotate(
        history_count=Count('taskhistory')
    ).order_by('-history_count')[:5]
    
    for task in top_tasks:
        print(f"  {task.id}: {task.title[:50]} - {task.history_count} ediciones")
    
    # Distribución por estado
    print(f"\n📊 DISTRIBUCIÓN POR ESTADO:")
    status_counts = Task.objects.values('task_status__status_name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    for status in status_counts:
        name = status['task_status__status_name'] or 'Sin estado'
        count = status['count']
        percentage = (count / total_tasks * 100) if total_tasks > 0 else 0
        bar = '█' * int(percentage / 5)
        print(f"  {name:<20} {count:5} ({percentage:5.1f}%) {bar}")
    
    # Actividad por mes
    print(f"\n📅 ACTIVIDAD POR MES (últimos 6 meses):")
    from django.db.models import Count
    from django.utils import timezone
    from datetime import timedelta
    
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_activity = TaskHistory.objects.filter(
        edited_at__gte=six_months_ago
    ).extra({
        'month': "strftime('%%Y-%%m', edited_at)"
    }).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    for month in monthly_activity:
        print(f"  {month['month']}: {month['count']} ediciones")
    
    print("="*80)

if __name__ == "__main__":
    main()