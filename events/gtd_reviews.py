"""
Sistema de revisiones GTD (Weekly/Monthly/Quarterly Reviews)
Proporciona herramientas para revisar el progreso y planificar el futuro.
"""

from django.utils import timezone
from datetime import datetime, timedelta
from .models import Task, Project, InboxItem
from .gtd_utils import gtd_engine
import json
from typing import Dict, List, Optional
from collections import Counter, defaultdict


class GTDReviewSystem:
    """
    Sistema completo para revisiones GTD.
    Incluye revisiones semanales, mensuales y trimestrales.
    """

    def __init__(self):
        self.review_types = {
            'weekly': self._generate_weekly_review,
            'monthly': self._generate_monthly_review,
            'quarterly': self._generate_quarterly_review
        }

    def generate_review(self, review_type: str, user_id: int, custom_start_date: Optional[datetime] = None) -> Dict:
        """
        Genera una revisión del tipo especificado.
        """
        if review_type not in self.review_types:
            raise ValueError(f"Tipo de revisión no válido: {review_type}")

        return self.review_types[review_type](user_id, custom_start_date)

    def _generate_weekly_review(self, user_id: int, custom_start_date: Optional[datetime] = None) -> Dict:
        """Genera revisión semanal GTD."""
        end_date = timezone.now()
        start_date = custom_start_date or (end_date - timedelta(days=7))

        # Datos básicos
        basic_data = self._get_basic_review_data(user_id, start_date, end_date)

        # Análisis de productividad
        productivity_analysis = self._analyze_productivity(user_id, start_date, end_date)

        # Análisis de contextos
        context_analysis = self._analyze_contexts(user_id, start_date, end_date)

        # Análisis de proyectos
        project_analysis = self._analyze_projects(user_id, start_date, end_date)

        # Sugerencias para la próxima semana
        next_week_suggestions = self._generate_next_week_suggestions(user_id)

        # Insights del motor GTD
        gtd_insights = gtd_engine.get_productivity_insights(user_id)

        return {
            'type': 'weekly',
            'period': f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
            'basic_data': basic_data,
            'productivity_analysis': productivity_analysis,
            'context_analysis': context_analysis,
            'project_analysis': project_analysis,
            'next_week_suggestions': next_week_suggestions,
            'gtd_insights': gtd_insights,
            'generated_at': timezone.now().isoformat()
        }

    def _generate_monthly_review(self, user_id: int, custom_start_date: Optional[datetime] = None) -> Dict:
        """Genera revisión mensual GTD."""
        end_date = timezone.now()
        start_date = custom_start_date or (end_date - timedelta(days=30))

        # Datos básicos
        basic_data = self._get_basic_review_data(user_id, start_date, end_date)

        # Tendencias del mes
        monthly_trends = self._analyze_monthly_trends(user_id, start_date, end_date)

        # Análisis de patrones
        pattern_analysis = self._analyze_patterns(user_id, start_date, end_date)

        # Objetivos del próximo mes
        next_month_goals = self._generate_monthly_goals(user_id)

        # Revisión de proyectos a largo plazo
        long_term_projects = self._review_long_term_projects(user_id)

        return {
            'type': 'monthly',
            'period': f"{start_date.strftime('%m/%Y')}",
            'basic_data': basic_data,
            'monthly_trends': monthly_trends,
            'pattern_analysis': pattern_analysis,
            'next_month_goals': next_month_goals,
            'long_term_projects': long_term_projects,
            'generated_at': timezone.now().isoformat()
        }

    def _generate_quarterly_review(self, user_id: int, custom_start_date: Optional[datetime] = None) -> Dict:
        """Genera revisión trimestral GTD."""
        end_date = timezone.now()
        start_date = custom_start_date or (end_date - timedelta(days=90))

        # Revisión de objetivos trimestrales
        quarterly_goals = self._review_quarterly_goals(user_id, start_date, end_date)

        # Análisis de progreso en áreas clave
        key_areas_progress = self._analyze_key_areas(user_id, start_date, end_date)

        # Revisión de hábitos y rutinas
        habits_review = self._review_habits_and_routines(user_id, start_date, end_date)

        # Planificación del próximo trimestre
        next_quarter_plan = self._plan_next_quarter(user_id)

        return {
            'type': 'quarterly',
            'period': f"Q{((start_date.month-1)//3)+1} {start_date.year}",
            'quarterly_goals': quarterly_goals,
            'key_areas_progress': key_areas_progress,
            'habits_review': habits_review,
            'next_quarter_plan': next_quarter_plan,
            'generated_at': timezone.now().isoformat()
        }

    def _get_basic_review_data(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Obtiene datos básicos para cualquier tipo de revisión."""
        try:
            # Tareas completadas
            tasks_completed = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__range=[start_date, end_date]
            ).count()

            # Tareas creadas
            tasks_created = Task.objects.filter(
                user_id=user_id,
                created_at__range=[start_date, end_date]
            ).count()

            # Tareas pendientes actuales
            tasks_pending = Task.objects.filter(
                user_id=user_id,
                status__in=['pending', 'in_progress']
            ).count()

            # Proyectos activos
            projects_active = Project.objects.filter(
                user_id=user_id,
                status='active'
            ).count()

            # Proyectos completados
            projects_completed = Project.objects.filter(
                user_id=user_id,
                status='completed',
                updated_at__range=[start_date, end_date]
            ).count()

            # Elementos del inbox procesados
            inbox_processed = InboxItem.objects.filter(
                user_id=user_id,
                processed=True,
                captured_at__range=[start_date, end_date]
            ).count()

            return {
                'tasks_completed': tasks_completed,
                'tasks_created': tasks_created,
                'tasks_pending': tasks_pending,
                'projects_active': projects_active,
                'projects_completed': projects_completed,
                'inbox_processed': inbox_processed,
                'completion_rate': (tasks_completed / max(tasks_created, 1)) * 100
            }

        except Exception as e:
            print(f"Error getting basic review data: {e}")
            return {
                'tasks_completed': 0,
                'tasks_created': 0,
                'tasks_pending': 0,
                'projects_active': 0,
                'projects_completed': 0,
                'inbox_processed': 0,
                'completion_rate': 0
            }

    def _analyze_productivity(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Analiza la productividad durante el período."""
        try:
            # Tareas por día de la semana
            tasks_by_weekday = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__range=[start_date, end_date]
            ).extra(select={'day_of_week': 'strftime("%%w", updated_at)'}).values('day_of_week').annotate(count=Count('id'))

            weekday_names = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
            productivity_by_day = {weekday_names[i]: 0 for i in range(7)}

            for item in tasks_by_weekday:
                day_index = int(item['day_of_week'])
                productivity_by_day[weekday_names[day_index]] = item['count']

            # Tareas por contexto
            tasks_by_context = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__range=[start_date, end_date]
            ).values('context').annotate(count=Count('id')).order_by('-count')

            # Tareas por prioridad
            tasks_by_priority = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__range=[start_date, end_date]
            ).values('priority').annotate(count=Count('id')).order_by('-count')

            # Tiempo promedio de completación
            avg_completion_time = self._calculate_avg_completion_time(user_id, start_date, end_date)

            return {
                'productivity_by_day': productivity_by_day,
                'tasks_by_context': list(tasks_by_context),
                'tasks_by_priority': list(tasks_by_priority),
                'avg_completion_time': avg_completion_time,
                'most_productive_day': max(productivity_by_day, key=productivity_by_day.get),
                'most_used_context': tasks_by_context[0]['context'] if tasks_by_context else 'N/A'
            }

        except Exception as e:
            print(f"Error analyzing productivity: {e}")
            return {
                'productivity_by_day': {},
                'tasks_by_context': [],
                'tasks_by_priority': [],
                'avg_completion_time': 'N/A',
                'most_productive_day': 'N/A',
                'most_used_context': 'N/A'
            }

    def _analyze_contexts(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Analiza el uso de contextos durante el período."""
        try:
            # Contextos más utilizados
            contexts_usage = Task.objects.filter(
                user_id=user_id,
                created_at__range=[start_date, end_date]
            ).values('context').annotate(
                created=Count('id'),
                completed=Count('id', filter={'status': 'done'})
            ).order_by('-created')

            # Balance entre contextos
            context_balance = {}
            for context_data in contexts_usage:
                context = context_data['context']
                created = context_data['created']
                completed = context_data['completed']
                completion_rate = (completed / max(created, 1)) * 100
                context_balance[context] = {
                    'created': created,
                    'completed': completed,
                    'completion_rate': completion_rate
                }

            # Sugerencias de balance
            suggestions = []
            work_tasks = sum(1 for c in context_balance.values() if c['created'] > 0 and c['context'] in ['trabajo', 'computadora'])
            personal_tasks = sum(1 for c in context_balance.values() if c['created'] > 0 and c['context'] in ['casa', 'recados'])

            if work_tasks > personal_tasks * 2:
                suggestions.append('Considera equilibrar más tiempo para tareas personales')
            elif personal_tasks > work_tasks * 2:
                suggestions.append('Considera dedicar más tiempo a tareas profesionales')

            return {
                'context_balance': context_balance,
                'most_used_context': max(context_balance, key=lambda k: context_balance[k]['created']) if context_balance else 'N/A',
                'balance_suggestions': suggestions
            }

        except Exception as e:
            print(f"Error analyzing contexts: {e}")
            return {
                'context_balance': {},
                'most_used_context': 'N/A',
                'balance_suggestions': []
            }

    def _analyze_projects(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Analiza el progreso de proyectos."""
        try:
            # Proyectos con más actividad
            projects_activity = Project.objects.filter(
                user_id=user_id,
                created_at__lte=end_date
            ).annotate(
                task_count=Count('tasks'),
                completed_tasks=Count('tasks', filter={'status': 'done'}),
                pending_tasks=Count('tasks', filter={'status__in': ['pending', 'in_progress']})
            ).order_by('-task_count')

            # Progreso de proyectos activos
            active_projects = []
            for project in projects_activity.filter(status='active'):
                total_tasks = project.task_count
                completed_tasks = project.completed_tasks
                progress = (completed_tasks / max(total_tasks, 1)) * 100

                active_projects.append({
                    'name': project.name,
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'pending_tasks': project.pending_tasks,
                    'progress': progress
                })

            # Proyectos que necesitan atención
            projects_needing_attention = [
                project for project in active_projects
                if project['pending_tasks'] > 0 and project['progress'] < 50
            ]

            return {
                'active_projects': active_projects,
                'projects_needing_attention': projects_needing_attention,
                'total_projects': len(active_projects),
                'avg_project_progress': sum(p['progress'] for p in active_projects) / max(len(active_projects), 1)
            }

        except Exception as e:
            print(f"Error analyzing projects: {e}")
            return {
                'active_projects': [],
                'projects_needing_attention': [],
                'total_projects': 0,
                'avg_project_progress': 0
            }

    def _generate_next_week_suggestions(self, user_id: int) -> List[str]:
        """Genera sugerencias para la próxima semana."""
        suggestions = []

        try:
            # Tareas pendientes de alta prioridad
            high_priority_tasks = Task.objects.filter(
                user_id=user_id,
                status__in=['pending', 'in_progress'],
                priority='high'
            ).count()

            if high_priority_tasks > 5:
                suggestions.append(f"Tienes {high_priority_tasks} tareas de alta prioridad - considera priorizar las más importantes")

            # Tareas próximas a vencer
            upcoming_deadlines = Task.objects.filter(
                user_id=user_id,
                status__in=['pending', 'in_progress'],
                due_date__lte=timezone.now().date() + timedelta(days=3),
                due_date__gte=timezone.now().date()
            ).count()

            if upcoming_deadlines > 0:
                suggestions.append(f"Tienes {upcoming_deadlines} tareas con fecha límite próxima - revísalas pronto")

            # Sugerencias basadas en patrones
            insights = gtd_engine.get_productivity_insights(user_id)
            suggestions.extend(insights['suggestions'])

            # Sugerencia general
            if not suggestions:
                suggestions.append("¡Buen trabajo esta semana! Mantén el ritmo y considera planificar tus objetivos para la próxima semana")

        except Exception as e:
            print(f"Error generating next week suggestions: {e}")
            suggestions.append("Revisa tus tareas pendientes y planifica la próxima semana")

        return suggestions

    def _calculate_avg_completion_time(self, user_id: int, start_date: datetime, end_date: datetime) -> str:
        """Calcula el tiempo promedio de completación de tareas."""
        try:
            completed_tasks = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__range=[start_date, end_date]
            ).exclude(created_at__date=updated_at__date)  # Excluir tareas completadas el mismo día

            if not completed_tasks:
                return 'N/A'

            total_time = timedelta(0)
            for task in completed_tasks:
                time_diff = task.updated_at - task.created_at
                total_time += time_diff

            avg_time = total_time / len(completed_tasks)

            # Formatear tiempo
            hours = avg_time.days * 24 + avg_time.seconds // 3600
            minutes = (avg_time.seconds % 3600) // 60

            if hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"

        except Exception as e:
            print(f"Error calculating avg completion time: {e}")
            return 'N/A'

    def _analyze_monthly_trends(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Analiza tendencias mensuales."""
        try:
            # Productividad por semana del mes
            weekly_productivity = []
            current_week_start = start_date

            while current_week_start < end_date:
                week_end = min(current_week_start + timedelta(days=7), end_date)

                week_completed = Task.objects.filter(
                    user_id=user_id,
                    status='done',
                    updated_at__range=[current_week_start, week_end]
                ).count()

                weekly_productivity.append({
                    'week': f"Semana {len(weekly_productivity) + 1}",
                    'completed': week_completed
                })

                current_week_start = week_end

            # Tendencia general
            if len(weekly_productivity) > 1:
                trend = 'up' if weekly_productivity[-1]['completed'] > weekly_productivity[0]['completed'] else 'down'
            else:
                trend = 'stable'

            return {
                'weekly_productivity': weekly_productivity,
                'trend': trend,
                'total_month': sum(w['completed'] for w in weekly_productivity)
            }

        except Exception as e:
            print(f"Error analyzing monthly trends: {e}")
            return {
                'weekly_productivity': [],
                'trend': 'stable',
                'total_month': 0
            }

    def _analyze_patterns(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Analiza patrones de comportamiento."""
        try:
            # Horarios más productivos
            productive_hours = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__range=[start_date, end_date]
            ).extra(select={'hour': 'strftime("%H", updated_at)'}).values('hour').annotate(count=Count('id'))

            hour_counts = {str(i): 0 for i in range(24)}
            for item in productive_hours:
                hour_counts[item['hour']] = item['count']

            most_productive_hour = max(hour_counts, key=hour_counts.get) if any(hour_counts.values()) else 'N/A'

            # Días más productivos
            productive_days = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__range=[start_date, end_date]
            ).extra(select={'day': 'strftime("%w", updated_at)'}).values('day').annotate(count=Count('id'))

            day_counts = {str(i): 0 for i in range(7)}
            for item in productive_days:
                day_counts[item['day']] = item['count']

            most_productive_day = max(day_counts, key=day_counts.get) if any(day_counts.values()) else 'N/A'

            return {
                'most_productive_hour': f"{most_productive_hour}:00" if most_productive_hour != 'N/A' else 'N/A',
                'most_productive_day': ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'][int(most_productive_day)] if most_productive_day != 'N/A' else 'N/A',
                'hour_distribution': hour_counts,
                'day_distribution': day_counts
            }

        except Exception as e:
            print(f"Error analyzing patterns: {e}")
            return {
                'most_productive_hour': 'N/A',
                'most_productive_day': 'N/A',
                'hour_distribution': {},
                'day_distribution': {}
            }

    def _generate_monthly_goals(self, user_id: int) -> List[Dict]:
        """Genera objetivos para el próximo mes."""
        try:
            # Basado en el rendimiento del mes actual
            current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            tasks_this_month = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__gte=current_month
            ).count()

            # Objetivo conservador: mantener el ritmo actual
            conservative_goal = tasks_this_month

            # Objetivo ambicioso: 20% más que el mes actual
            ambitious_goal = int(tasks_this_month * 1.2)

            return [
                {
                    'title': 'Mantener productividad actual',
                    'description': f'Completar al menos {conservative_goal} tareas',
                    'type': 'conservative',
                    'target': conservative_goal
                },
                {
                    'title': 'Mejorar productividad',
                    'description': f'Completar {ambitious_goal} tareas (20% más)',
                    'type': 'ambitious',
                    'target': ambitious_goal
                },
                {
                    'title': 'Revisar proyectos activos',
                    'description': 'Revisar y actualizar el estado de todos los proyectos activos',
                    'type': 'project_review',
                    'target': 'all_active_projects'
                }
            ]

        except Exception as e:
            print(f"Error generating monthly goals: {e}")
            return []

    def _review_long_term_projects(self, user_id: int) -> List[Dict]:
        """Revisa proyectos a largo plazo."""
        try:
            # Proyectos que llevan más de 30 días activos
            long_term_projects = Project.objects.filter(
                user_id=user_id,
                status='active',
                created_at__lte=timezone.now() - timedelta(days=30)
            ).annotate(
                days_active=(timezone.now() - timezone.now()).days,  # TODO: Fix this calculation
                task_count=Count('tasks'),
                completed_tasks=Count('tasks', filter={'status': 'done'})
            )

            projects_review = []
            for project in long_term_projects:
                progress = (project.completed_tasks / max(project.task_count, 1)) * 100
                projects_review.append({
                    'name': project.name,
                    'days_active': (timezone.now().date() - project.created_at.date()).days,
                    'progress': progress,
                    'needs_attention': progress < 25 and project.task_count > 0
                })

            return projects_review

        except Exception as e:
            print(f"Error reviewing long term projects: {e}")
            return []

    def _review_quarterly_goals(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Revisa objetivos trimestrales."""
        try:
            # Esta es una implementación básica - en un sistema real,
            # tendrías una tabla de objetivos trimestrales
            quarterly_goals = {
                'productivity': 'Completar al menos 200 tareas',
                'projects': 'Completar 3 proyectos importantes',
                'learning': 'Dedicar tiempo a aprendizaje y desarrollo',
                'balance': 'Mantener equilibrio trabajo-vida personal'
            }

            # Calcular progreso aproximado
            tasks_completed = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__range=[start_date, end_date]
            ).count()

            projects_completed = Project.objects.filter(
                user_id=user_id,
                status='completed',
                updated_at__range=[start_date, end_date]
            ).count()

            progress = {
                'productivity': min((tasks_completed / 200) * 100, 100),
                'projects': min((projects_completed / 3) * 100, 100),
                'learning': 75,  # Este sería calculado basado en tareas de aprendizaje
                'balance': 80   # Este sería calculado basado en distribución de contextos
            }

            return {
                'goals': quarterly_goals,
                'progress': progress,
                'overall_completion': sum(progress.values()) / len(progress)
            }

        except Exception as e:
            print(f"Error reviewing quarterly goals: {e}")
            return {
                'goals': {},
                'progress': {},
                'overall_completion': 0
            }

    def _analyze_key_areas(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Analiza progreso en áreas clave."""
        try:
            # Definir áreas clave
            key_areas = {
                'trabajo': ['trabajo', 'computadora'],
                'personal': ['casa', 'recados'],
                'desarrollo': ['estudiar', 'aprender', 'curso'],
                'salud': ['ejercicio', 'salud', 'médico'],
                'relaciones': ['familia', 'amigos', 'social']
            }

            area_analysis = {}
            for area, contexts in key_areas.items():
                tasks_in_area = Task.objects.filter(
                    user_id=user_id,
                    context__in=contexts,
                    created_at__range=[start_date, end_date]
                ).count()

                completed_in_area = Task.objects.filter(
                    user_id=user_id,
                    context__in=contexts,
                    status='done',
                    updated_at__range=[start_date, end_date]
                ).count()

                area_analysis[area] = {
                    'total_tasks': tasks_in_area,
                    'completed_tasks': completed_in_area,
                    'completion_rate': (completed_in_area / max(tasks_in_area, 1)) * 100
                }

            return area_analysis

        except Exception as e:
            print(f"Error analyzing key areas: {e}")
            return {}

    def _review_habits_and_routines(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Revisa hábitos y rutinas."""
        try:
            # Análisis de consistencia diaria
            daily_activity = Task.objects.filter(
                user_id=user_id,
                updated_at__range=[start_date, end_date]
            ).extra(select={'date': 'DATE(updated_at)'}).values('date').annotate(count=Count('id'))

            # Calcular días activos vs total de días
            total_days = (end_date - start_date).days
            active_days = len(daily_activity)

            consistency_score = (active_days / max(total_days, 1)) * 100

            # Análisis de horarios
            hourly_activity = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__range=[start_date, end_date]
            ).extra(select={'hour': 'strftime("%H", updated_at)'}).values('hour').annotate(count=Count('id'))

            peak_hours = [item['hour'] for item in hourly_activity if item['count'] > 0]

            return {
                'consistency_score': consistency_score,
                'active_days': active_days,
                'total_days': total_days,
                'peak_hours': peak_hours,
                'routine_suggestions': self._generate_routine_suggestions(consistency_score, peak_hours)
            }

        except Exception as e:
            print(f"Error reviewing habits and routines: {e}")
            return {
                'consistency_score': 0,
                'active_days': 0,
                'total_days': 0,
                'peak_hours': [],
                'routine_suggestions': []
            }

    def _generate_routine_suggestions(self, consistency_score: float, peak_hours: List[str]) -> List[str]:
        """Genera sugerencias para mejorar rutinas."""
        suggestions = []

        if consistency_score < 50:
            suggestions.append('Considera establecer horarios más regulares para trabajar en tareas')

        if len(peak_hours) > 0:
            main_peak = max(set(peak_hours), key=peak_hours.count)
            suggestions.append(f'Tu hora más productiva es alrededor de las {main_peak}:00 - aprovecha ese momento')

        if consistency_score > 80:
            suggestions.append('¡Excelente consistencia! Mantén este buen hábito')

        return suggestions

    def _plan_next_quarter(self, user_id: int) -> Dict:
        """Planifica el próximo trimestre."""
        try:
            # Basado en el rendimiento actual, generar objetivos realistas
            current_quarter_start = timezone.now().replace(month=((timezone.now().month - 1) // 3) * 3 + 1, day=1, hour=0, minute=0, second=0, microsecond=0)

            tasks_this_quarter = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__gte=current_quarter_start
            ).count()

            # Proyectar para el próximo trimestre
            projected_tasks = int(tasks_this_quarter * 1.1)  # 10% de mejora

            return {
                'projected_tasks': projected_tasks,
                'key_focus_areas': ['Productividad', 'Proyectos', 'Aprendizaje', 'Balance'],
                'milestones': [
                    'Revisión mensual de progreso',
                    'Actualización de objetivos',
                    'Evaluación de proyectos activos'
                ]
            }

        except Exception as e:
            print(f"Error planning next quarter: {e}")
            return {
                'projected_tasks': 0,
                'key_focus_areas': [],
                'milestones': []
            }


# Instancia global del sistema de revisiones
gtd_review_system = GTDReviewSystem()