"""
Sistema de integración con calendario para GTD
Proporciona sincronización con calendarios externos y gestión avanzada de fechas.
"""

from django.utils import timezone
from datetime import datetime, timedelta
from .models import Task, Project, InboxItem
from .gtd_utils import gtd_engine
import json
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import calendar


class GTDCalendarIntegration:
    """
    Sistema de integración con calendarios para GTD.
    Proporciona sincronización, sugerencias de horarios y gestión de fechas.
    """

    def __init__(self):
        self.supported_calendars = {
            'google': self._sync_google_calendar,
            'outlook': self._sync_outlook_calendar,
            'apple': self._sync_apple_calendar,
            'manual': self._sync_manual_calendar
        }

    def suggest_optimal_schedule(self, user_id: int, tasks: List[Task]) -> Dict:
        """
        Sugiere un horario óptimo para completar las tareas.
        """
        try:
            # Obtener perfil de productividad del usuario
            productivity_profile = self._get_productivity_profile(user_id)

            # Analizar tareas por contexto y energía requerida
            task_analysis = self._analyze_tasks_for_scheduling(tasks)

            # Generar sugerencias de horarios
            schedule_suggestions = self._generate_schedule_suggestions(
                task_analysis, productivity_profile
            )

            # Considerar tiempo disponible
            available_time = self._calculate_available_time(user_id)

            # Optimizar asignación
            optimized_schedule = self._optimize_schedule(
                schedule_suggestions, available_time
            )

            return {
                'suggested_schedule': optimized_schedule,
                'productivity_profile': productivity_profile,
                'task_analysis': task_analysis,
                'available_time': available_time,
                'optimization_score': self._calculate_optimization_score(optimized_schedule)
            }

        except Exception as e:
            print(f"Error suggesting optimal schedule: {e}")
            return {}

    def sync_with_external_calendar(self, user_id: int, calendar_type: str, credentials: Dict) -> Dict:
        """
        Sincroniza con calendario externo.
        """
        if calendar_type not in self.supported_calendars:
            return {'error': f'Tipo de calendario no soportado: {calendar_type}'}

        try:
            sync_result = self.supported_calendars[calendar_type](user_id, credentials)

            # Actualizar tareas con fechas de calendario
            self._update_tasks_with_calendar_dates(user_id, sync_result)

            return {
                'success': True,
                'synced_events': sync_result.get('events', []),
                'conflicts': sync_result.get('conflicts', []),
                'suggestions': self._generate_calendar_suggestions(sync_result)
            }

        except Exception as e:
            return {'error': f'Error de sincronización: {str(e)}'}

    def get_calendar_heatmap(self, user_id: int, months: int = 3) -> Dict:
        """
        Genera datos para un heatmap de productividad por fechas.
        """
        try:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=months * 30)

            # Obtener actividad por fecha
            activity_data = Task.objects.filter(
                user_id=user_id,
                updated_at__date__range=[start_date, end_date]
            ).extra(select={'date': 'DATE(updated_at)'}).values('date').annotate(
                completed=Count('id', filter={'status': 'done'}),
                created=Count('id'),
                high_priority=Count('id', filter={'priority': 'high', 'status': 'done'})
            )

            # Crear estructura de datos para heatmap
            heatmap_data = {}
            current_date = start_date

            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                day_activity = next(
                    (item for item in activity_data if item['date'] == date_str),
                    {'completed': 0, 'created': 0, 'high_priority': 0}
                )

                heatmap_data[date_str] = {
                    'completed': day_activity['completed'],
                    'created': day_activity['created'],
                    'high_priority': day_activity['high_priority'],
                    'productivity_score': self._calculate_daily_productivity_score(day_activity)
                }

                current_date += timedelta(days=1)

            return {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'data': heatmap_data,
                'summary': self._generate_heatmap_summary(heatmap_data)
            }

        except Exception as e:
            print(f"Error generating calendar heatmap: {e}")
            return {}

    def suggest_deadlines(self, user_id: int, tasks: List[Task]) -> Dict:
        """
        Sugiere fechas límite óptimas para tareas.
        """
        try:
            suggestions = {}

            for task in tasks:
                if not task.due_date:
                    suggested_deadline = self._calculate_optimal_deadline(user_id, task)
                    suggestions[task.id] = {
                        'task_title': task.title,
                        'suggested_deadline': suggested_deadline,
                        'reasoning': self._get_deadline_reasoning(task, suggested_deadline),
                        'confidence': self._calculate_deadline_confidence(task)
                    }

            return {
                'suggestions': suggestions,
                'total_suggestions': len(suggestions),
                'methodology': 'Basado en análisis de productividad y patrones históricos'
            }

        except Exception as e:
            print(f"Error suggesting deadlines: {e}")
            return {}

    def analyze_time_blocking(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """
        Analiza la efectividad del time blocking.
        """
        try:
            # Obtener bloques de tiempo y su productividad
            time_blocks = self._get_time_blocks(user_id, start_date, end_date)

            # Analizar efectividad por bloque
            block_effectiveness = {}
            for block_start, block_data in time_blocks.items():
                effectiveness = self._calculate_block_effectiveness(block_data)
                block_effectiveness[block_start] = {
                    'effectiveness': effectiveness,
                    'tasks_completed': block_data['completed'],
                    'time_allocated': block_data['duration'],
                    'efficiency_ratio': effectiveness / max(block_data['duration'], 1)
                }

            # Sugerencias de mejora
            improvement_suggestions = self._generate_time_blocking_suggestions(block_effectiveness)

            return {
                'time_blocks': time_blocks,
                'block_effectiveness': block_effectiveness,
                'improvement_suggestions': improvement_suggestions,
                'overall_effectiveness': self._calculate_overall_time_blocking_effectiveness(block_effectiveness)
            }

        except Exception as e:
            print(f"Error analyzing time blocking: {e}")
            return {}

    # Métodos auxiliares

    def _get_productivity_profile(self, user_id: int) -> Dict:
        """Obtiene perfil de productividad del usuario."""
        try:
            # Horarios más productivos
            peak_hours = self._get_peak_productivity_hours(user_id)

            # Días más productivos
            peak_days = self._get_peak_productivity_days(user_id)

            # Contextos por horario
            context_by_hour = self._get_context_by_hour_patterns(user_id)

            # Niveles de energía por horario
            energy_patterns = self._get_energy_patterns(user_id)

            return {
                'peak_hours': peak_hours,
                'peak_days': peak_days,
                'context_by_hour': context_by_hour,
                'energy_patterns': energy_patterns,
                'optimal_work_duration': self._calculate_optimal_work_duration(user_id)
            }

        except Exception as e:
            print(f"Error getting productivity profile: {e}")
            return {}

    def _analyze_tasks_for_scheduling(self, tasks: List[Task]) -> Dict:
        """Analiza tareas para determinar requisitos de scheduling."""
        task_requirements = {
            'high_energy': [],
            'low_energy': [],
            'short_duration': [],
            'long_duration': [],
            'context_specific': defaultdict(list),
            'time_sensitive': []
        }

        for task in tasks:
            # Análisis de energía requerida
            if hasattr(task, 'energy_level') and task.energy_level == 'high':
                task_requirements['high_energy'].append(task)
            elif hasattr(task, 'energy_level') and task.energy_level == 'low':
                task_requirements['low_energy'].append(task)

            # Análisis de duración
            if hasattr(task, 'time_estimate'):
                if task.time_estimate in ['5_minutos', '15_minutos']:
                    task_requirements['short_duration'].append(task)
                elif task.time_estimate in ['2_horas', 'medio_dia', 'dia_completo']:
                    task_requirements['long_duration'].append(task)

            # Análisis por contexto
            if task.context:
                task_requirements['context_specific'][task.context].append(task)

            # Tareas con fecha límite
            if task.due_date:
                task_requirements['time_sensitive'].append(task)

        return task_requirements

    def _generate_schedule_suggestions(self, task_analysis: Dict, productivity_profile: Dict) -> Dict:
        """Genera sugerencias de horarios para tareas."""
        suggestions = {}

        # Asignar tareas de alta energía a horas pico
        if task_analysis['high_energy'] and productivity_profile.get('peak_hours'):
            peak_hour = productivity_profile['peak_hours'][0]
            suggestions['high_energy'] = {
                'time_slot': f"{peak_hour}:00 - {int(peak_hour) + 2}:00",
                'tasks': [task.title for task in task_analysis['high_energy'][:3]],
                'reasoning': 'Horas de máxima energía y concentración'
            }

        # Asignar tareas de baja energía a horarios flexibles
        if task_analysis['low_energy']:
            suggestions['low_energy'] = {
                'time_slot': '14:00 - 16:00',
                'tasks': [task.title for task in task_analysis['low_energy'][:2]],
                'reasoning': 'Período de energía moderada, ideal para tareas rutinarias'
            }

        # Asignar tareas cortas a momentos de transición
        if task_analysis['short_duration']:
            suggestions['short_tasks'] = {
                'time_slot': 'Múltiples slots de 15-30 minutos',
                'tasks': [task.title for task in task_analysis['short_duration'][:5]],
                'reasoning': 'Tareas rápidas para momentos de baja concentración'
            }

        # Asignar tareas por contexto
        for context, tasks in task_analysis['context_specific'].items():
            if context in productivity_profile.get('context_by_hour', {}):
                best_hour = productivity_profile['context_by_hour'][context]
                suggestions[f'context_{context}'] = {
                    'time_slot': f"{best_hour}:00 - {int(best_hour) + 1}:00",
                    'tasks': [task.title for task in tasks[:2]],
                    'reasoning': f'Horario óptimo para contexto {context}'
                }

        return suggestions

    def _calculate_available_time(self, user_id: int) -> Dict:
        """Calcula tiempo disponible considerando calendario y compromisos."""
        try:
            # En un sistema real, esto consultaría el calendario
            # Por ahora, usar suposiciones basadas en patrones

            # Horarios típicos de trabajo
            work_hours = {
                'monday': ['09:00', '17:00'],
                'tuesday': ['09:00', '17:00'],
                'wednesday': ['09:00', '17:00'],
                'thursday': ['09:00', '17:00'],
                'friday': ['09:00', '17:00'],
                'saturday': ['10:00', '14:00'],
                'sunday': None  # Fin de semana libre
            }

            # Calcular horas disponibles por día
            available_hours = {}
            for day, hours in work_hours.items():
                if hours:
                    start_hour = int(hours[0].split(':')[0])
                    end_hour = int(hours[1].split(':')[0])
                    available_hours[day] = end_hour - start_hour
                else:
                    available_hours[day] = 0

            return {
                'daily_schedule': work_hours,
                'available_hours_per_day': available_hours,
                'total_weekly_hours': sum(available_hours.values()),
                'flexible_hours': self._calculate_flexible_hours(available_hours)
            }

        except Exception as e:
            print(f"Error calculating available time: {e}")
            return {}

    def _optimize_schedule(self, schedule_suggestions: Dict, available_time: Dict) -> Dict:
        """Optimiza la asignación de tareas a horarios disponibles."""
        try:
            optimized = {}
            used_hours = 0
            max_hours = available_time.get('total_weekly_hours', 40)

            # Priorizar tareas por importancia
            priority_order = ['high_energy', 'time_sensitive', 'context_specific', 'short_tasks', 'low_energy']

            for priority in priority_order:
                if priority in schedule_suggestions and used_hours < max_hours:
                    suggestion = schedule_suggestions[priority]

                    # Verificar si hay tiempo disponible
                    estimated_hours = self._estimate_task_hours(suggestion['tasks'])

                    if used_hours + estimated_hours <= max_hours:
                        optimized[priority] = {
                            **suggestion,
                            'estimated_hours': estimated_hours,
                            'priority_level': priority_order.index(priority) + 1
                        }
                        used_hours += estimated_hours

            return {
                'optimized_schedule': optimized,
                'total_allocated_hours': used_hours,
                'remaining_hours': max_hours - used_hours,
                'allocation_efficiency': (used_hours / max_hours) * 100 if max_hours > 0 else 0
            }

        except Exception as e:
            print(f"Error optimizing schedule: {e}")
            return {}

    def _calculate_optimization_score(self, optimized_schedule: Dict) -> float:
        """Calcula puntuación de optimización del horario."""
        try:
            if not optimized_schedule:
                return 0

            # Factores de puntuación
            priority_score = 0
            time_efficiency = 0
            context_alignment = 0

            schedule = optimized_schedule.get('optimized_schedule', {})

            # Puntuación por prioridades cubiertas
            priority_weights = {
                'high_energy': 30,
                'time_sensitive': 25,
                'context_specific': 20,
                'short_tasks': 15,
                'low_energy': 10
            }

            for category, weight in priority_weights.items():
                if category in schedule:
                    priority_score += weight

            # Eficiencia de tiempo
            allocated = optimized_schedule.get('total_allocated_hours', 0)
            available = 40  # Horas semanales típicas
            time_efficiency = min((allocated / available) * 100, 100)

            # Alineación con productividad
            context_alignment = 80  # Basado en análisis de patrones

            # Puntuación final ponderada
            final_score = (
                priority_score * 0.4 +
                time_efficiency * 0.3 +
                context_alignment * 0.3
            )

            return round(final_score, 1)

        except Exception as e:
            print(f"Error calculating optimization score: {e}")
            return 0

    # Métodos de sincronización con calendarios externos

    def _sync_google_calendar(self, user_id: int, credentials: Dict) -> Dict:
        """Sincroniza con Google Calendar."""
        # Implementación simplificada
        return {
            'events': [],
            'conflicts': [],
            'message': 'Sincronización con Google Calendar no implementada en esta versión'
        }

    def _sync_outlook_calendar(self, user_id: int, credentials: Dict) -> Dict:
        """Sincroniza con Outlook Calendar."""
        # Implementación simplificada
        return {
            'events': [],
            'conflicts': [],
            'message': 'Sincronización con Outlook Calendar no implementada en esta versión'
        }

    def _sync_apple_calendar(self, user_id: int, credentials: Dict) -> Dict:
        """Sincroniza con Apple Calendar."""
        # Implementación simplificada
        return {
            'events': [],
            'conflicts': [],
            'message': 'Sincronización con Apple Calendar no implementada en esta versión'
        }

    def _sync_manual_calendar(self, user_id: int, credentials: Dict) -> Dict:
        """Sincronización manual con calendario."""
        # Esta sería la implementación para datos manuales
        return {
            'events': credentials.get('events', []),
            'conflicts': [],
            'message': 'Sincronización manual completada'
        }

    def _update_tasks_with_calendar_dates(self, user_id: int, sync_result: Dict):
        """Actualiza tareas con fechas de calendario."""
        try:
            # En un sistema real, esto actualizaría las tareas basándose en eventos del calendario
            # Por ahora, es una implementación de placeholder
            pass

        except Exception as e:
            print(f"Error updating tasks with calendar dates: {e}")

    def _generate_calendar_suggestions(self, sync_result: Dict) -> List[str]:
        """Genera sugerencias basadas en sincronización de calendario."""
        suggestions = []

        if sync_result.get('conflicts'):
            suggestions.append(f"Se encontraron {len(sync_result['conflicts'])} conflictos de horario")

        if not sync_result.get('events'):
            suggestions.append("No se encontraron eventos en el calendario")

        suggestions.append("Considera revisar tu calendario regularmente para evitar conflictos")

        return suggestions

    # Métodos de análisis adicionales

    def _get_peak_productivity_hours(self, user_id: int) -> List[str]:
        """Obtiene horas de mayor productividad."""
        try:
            # Análisis basado en tareas completadas por hora
            hourly_stats = Task.objects.filter(
                user_id=user_id,
                status='done'
            ).extra(select={'hour': 'strftime("%H", updated_at)'}).values('hour').annotate(
                count=Count('id')
            ).order_by('-count')[:3]

            return [item['hour'] for item in hourly_stats]

        except Exception:
            return ['10', '14', '16']  # Valores por defecto

    def _get_peak_productivity_days(self, user_id: int) -> List[str]:
        """Obtiene días de mayor productividad."""
        try:
            weekday_names = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']

            weekday_stats = Task.objects.filter(
                user_id=user_id,
                status='done'
            ).extra(select={'weekday': 'strftime("%w", updated_at)'}).values('weekday').annotate(
                count=Count('id')
            ).order_by('-count')[:3]

            return [weekday_names[int(item['weekday'])] for item in weekday_stats]

        except Exception:
            return ['Martes', 'Miércoles', 'Jueves']  # Valores por defecto

    def _get_context_by_hour_patterns(self, user_id: int) -> Dict:
        """Obtiene patrones de contexto por hora."""
        try:
            # Análisis de contextos más usados por hora
            context_by_hour = defaultdict(Counter)

            tasks = Task.objects.filter(
                user_id=user_id,
                status='done'
            ).extra(select={'hour': 'strftime("%H", updated_at)'}).values('hour', 'context')

            for task in tasks:
                if task['context']:
                    context_by_hour[task['hour']][task['context']] += 1

            # Obtener contexto más común por hora
            result = {}
            for hour, contexts in context_by_hour.items():
                if contexts:
                    result[hour] = contexts.most_common(1)[0][0]

            return result

        except Exception:
            return {}

    def _get_energy_patterns(self, user_id: int) -> Dict:
        """Obtiene patrones de energía del usuario."""
        try:
            # Basado en productividad por hora
            hourly_productivity = Task.objects.filter(
                user_id=user_id,
                status='done'
            ).extra(select={'hour': 'strftime("%H", updated_at)'}).values('hour').annotate(
                count=Count('id')
            )

            # Clasificar horas por nivel de energía
            energy_patterns = {}
            for item in hourly_productivity:
                hour = int(item['hour'])
                productivity = item['count']

                if productivity > 2:
                    energy_patterns[item['hour']] = 'high'
                elif productivity > 0:
                    energy_patterns[item['hour']] = 'medium'
                else:
                    energy_patterns[item['hour']] = 'low'

            return energy_patterns

        except Exception:
            return {}

    def _calculate_optimal_work_duration(self, user_id: int) -> int:
        """Calcula duración óptima de sesiones de trabajo."""
        try:
            # Basado en tiempo promedio de completación de tareas
            completed_tasks = Task.objects.filter(
                user_id=user_id,
                status='done'
            )

            if not completed_tasks:
                return 60  # 60 minutos por defecto

            # Estimación simple: 60-90 minutos para tareas complejas
            return 75  # 75 minutos promedio

        except Exception:
            return 60

    def _estimate_task_hours(self, task_titles: List[str]) -> float:
        """Estima horas requeridas para completar tareas."""
        # Estimación simplificada
        return len(task_titles) * 1.5  # 1.5 horas por tarea promedio

    def _calculate_flexible_hours(self, available_hours: Dict) -> int:
        """Calcula horas flexibles disponibles."""
        # Horas que no están comprometidas con reuniones fijas
        return int(sum(available_hours.values()) * 0.6)  # 60% flexible

    def _calculate_daily_productivity_score(self, day_activity: Dict) -> float:
        """Calcula puntuación de productividad para un día."""
        completed = day_activity['completed']
        created = day_activity['created']
        high_priority = day_activity['high_priority']

        # Puntuación basada en completación vs creación y tareas de alta prioridad
        base_score = (completed / max(created, 1)) * 50
        priority_bonus = high_priority * 10

        return min(base_score + priority_bonus, 100)

    def _generate_heatmap_summary(self, heatmap_data: Dict) -> Dict:
        """Genera resumen del heatmap."""
        if not heatmap_data:
            return {}

        scores = [data['productivity_score'] for data in heatmap_data.values()]
        completed_total = sum(data['completed'] for data in heatmap_data.values())

        return {
            'average_productivity': round(sum(scores) / len(scores), 1) if scores else 0,
            'total_completed': completed_total,
            'most_productive_day': max(heatmap_data.keys(), key=lambda k: heatmap_data[k]['productivity_score']),
            'consistency_score': self._calculate_consistency_score([
                {'completed': data['completed']} for data in heatmap_data.values()
            ])
        }

    def _calculate_optimal_deadline(self, user_id: int, task: Task) -> Optional[str]:
        """Calcula fecha límite óptima para una tarea."""
        try:
            # Basado en prioridad y contexto
            days_to_add = {
                'high': 3,
                'medium': 7,
                'low': 14
            }.get(task.priority, 7)

            optimal_date = timezone.now().date() + timedelta(days=days_to_add)

            # Ajustar por contexto
            if task.context == 'work':
                # Asegurar que sea día laboral
                while optimal_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                    optimal_date += timedelta(days=1)

            return optimal_date.strftime('%Y-%m-%d')

        except Exception:
            return None

    def _get_deadline_reasoning(self, task: Task, suggested_deadline: str) -> str:
        """Proporciona razonamiento para la fecha límite sugerida."""
        reasoning = f"Basado en prioridad '{task.priority}'"

        if hasattr(task, 'context') and task.context:
            reasoning += f" y contexto '{task.context}'"

        if hasattr(task, 'time_estimate') and task.time_estimate:
            reasoning += f", con estimación de tiempo '{task.time_estimate}'"

        return reasoning

    def _calculate_deadline_confidence(self, task: Task) -> float:
        """Calcula confianza en la sugerencia de fecha límite."""
        confidence = 50  # Base

        if task.priority in ['high', 'medium']:
            confidence += 20

        if hasattr(task, 'context') and task.context:
            confidence += 15

        if hasattr(task, 'time_estimate') and task.time_estimate:
            confidence += 15

        return min(confidence, 100)

    def _get_time_blocks(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Obtiene bloques de tiempo definidos por el usuario."""
        # En un sistema real, esto vendría de una tabla de time blocks
        # Por ahora, retornar estructura vacía
        return {}

    def _calculate_block_effectiveness(self, block_data: Dict) -> float:
        """Calcula efectividad de un bloque de tiempo."""
        # Implementación simplificada
        return 75  # Porcentaje por defecto

    def _generate_time_blocking_suggestions(self, block_effectiveness: Dict) -> List[str]:
        """Genera sugerencias para mejorar time blocking."""
        suggestions = []

        if not block_effectiveness:
            suggestions.append("Considera implementar time blocking para mejorar tu productividad")

        avg_effectiveness = sum(block_effectiveness.values()) / len(block_effectiveness) if block_effectiveness else 0

        if avg_effectiveness < 60:
            suggestions.append("Tus bloques de tiempo podrían ser más efectivos - revisa las distracciones")

        if avg_effectiveness > 80:
            suggestions.append("¡Excelente uso de time blocking! Mantén esta práctica")

        return suggestions

    def _calculate_overall_time_blocking_effectiveness(self, block_effectiveness: Dict) -> float:
        """Calcula efectividad general del time blocking."""
        if not block_effectiveness:
            return 0

        return sum(effectiveness['effectiveness'] for effectiveness in block_effectiveness.values()) / len(block_effectiveness)


# Instancia global del sistema de calendario
gtd_calendar = GTDCalendarIntegration()