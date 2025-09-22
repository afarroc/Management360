"""
Sistema de análisis de productividad avanzado para GTD
Proporciona métricas detalladas, análisis de patrones y predicciones.
"""

from django.utils import timezone
from datetime import datetime, timedelta
from .models import Task, Project, InboxItem
from .gtd_utils import gtd_engine
import json
from typing import Dict, List, Optional, Tuple
from collections import Counter, defaultdict
import math


class GTDProductivityAnalytics:
    """
    Sistema avanzado de análisis de productividad GTD.
    Proporciona métricas detalladas, análisis de tendencias y predicciones.
    """

    def __init__(self):
        self.metrics_cache = {}
        self.cache_timeout = 300  # 5 minutos

    def get_comprehensive_analytics(self, user_id: int, days: int = 30) -> Dict:
        """
        Obtiene análisis completo de productividad.
        """
        cache_key = f"comprehensive_{user_id}_{days}"
        if cache_key in self.metrics_cache:
            cache_entry = self.metrics_cache[cache_key]
            if timezone.now().timestamp() - cache_entry['timestamp'] < self.cache_timeout:
                return cache_entry['data']

        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        analytics = {
            'overview': self._get_overview_metrics(user_id, start_date, end_date),
            'productivity_trends': self._analyze_productivity_trends(user_id, start_date, end_date),
            'context_analysis': self._analyze_context_performance(user_id, start_date, end_date),
            'time_analysis': self._analyze_time_patterns(user_id, start_date, end_date),
            'project_analysis': self._analyze_project_performance(user_id, start_date, end_date),
            'efficiency_metrics': self._calculate_efficiency_metrics(user_id, start_date, end_date),
            'predictions': self._generate_predictions(user_id, start_date, end_date),
            'insights': self._generate_insights(user_id, start_date, end_date),
            'generated_at': timezone.now().isoformat()
        }

        self.metrics_cache[cache_key] = {
            'data': analytics,
            'timestamp': timezone.now().timestamp()
        }

        return analytics

    def _get_overview_metrics(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Obtiene métricas generales de productividad."""
        try:
            # Tareas básicas
            total_tasks = Task.objects.filter(
                user_id=user_id,
                created_at__range=[start_date, end_date]
            ).count()

            completed_tasks = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__range=[start_date, end_date]
            ).count()

            pending_tasks = Task.objects.filter(
                user_id=user_id,
                status__in=['pending', 'in_progress']
            ).count()

            # Proyectos
            total_projects = Project.objects.filter(
                user_id=user_id,
                created_at__lte=end_date
            ).count()

            active_projects = Project.objects.filter(
                user_id=user_id,
                status='active'
            ).count()

            completed_projects = Project.objects.filter(
                user_id=user_id,
                status='completed',
                updated_at__range=[start_date, end_date]
            ).count()

            # Inbox
            inbox_items = InboxItem.objects.filter(
                user_id=user_id,
                captured_at__range=[start_date, end_date]
            ).count()

            processed_inbox = InboxItem.objects.filter(
                user_id=user_id,
                processed=True,
                captured_at__range=[start_date, end_date]
            ).count()

            # Cálculos de tasas
            completion_rate = (completed_tasks / max(total_tasks, 1)) * 100
            inbox_processing_rate = (processed_inbox / max(inbox_items, 1)) * 100
            project_completion_rate = (completed_projects / max(total_projects, 1)) * 100

            # Tasa de creación vs completación
            creation_rate = total_tasks / max(days, 1)  # Tareas por día
            completion_rate_per_day = completed_tasks / max(days, 1)

            return {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'pending_tasks': pending_tasks,
                'total_projects': total_projects,
                'active_projects': active_projects,
                'completed_projects': completed_projects,
                'inbox_items': inbox_items,
                'processed_inbox': processed_inbox,
                'completion_rate': round(completion_rate, 1),
                'inbox_processing_rate': round(inbox_processing_rate, 1),
                'project_completion_rate': round(project_completion_rate, 1),
                'creation_rate_per_day': round(creation_rate, 1),
                'completion_rate_per_day': round(completion_rate_per_day, 1),
                'productivity_ratio': round(completion_rate_per_day / max(creation_rate, 0.1), 2)
            }

        except Exception as e:
            print(f"Error getting overview metrics: {e}")
            return {}

    def _analyze_productivity_trends(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Analiza tendencias de productividad a lo largo del tiempo."""
        try:
            # Productividad diaria
            daily_productivity = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__range=[start_date, end_date]
            ).extra(select={'date': 'DATE(updated_at)'}).values('date').annotate(
                completed=Count('id'),
                created=Count('id', filter={'created_at__date': 'updated_at__date'})
            ).order_by('date')

            # Convertir a formato serializable
            daily_data = []
            for item in daily_productivity:
                daily_data.append({
                    'date': item['date'],
                    'completed': item['completed'],
                    'created': item['created']
                })

            # Calcular tendencia usando regresión lineal simple
            if len(daily_data) > 1:
                x_values = list(range(len(daily_data)))
                y_values = [item['completed'] for item in daily_data]

                slope = self._calculate_trend_slope(x_values, y_values)
                trend_direction = 'up' if slope > 0.1 else 'down' if slope < -0.1 else 'stable'
            else:
                trend_direction = 'insufficient_data'

            # Promedios semanales
            weekly_averages = self._calculate_weekly_averages(daily_data)

            # Días más productivos
            if daily_data:
                sorted_days = sorted(daily_data, key=lambda x: x['completed'], reverse=True)
                most_productive_day = sorted_days[0]['date']
                avg_productive_day = sum(item['completed'] for item in daily_data) / max(len(daily_data), 1)
            else:
                most_productive_day = None
                avg_productive_day = 0

            return {
                'daily_data': daily_data,
                'trend_direction': trend_direction,
                'weekly_averages': weekly_averages,
                'most_productive_day': most_productive_day,
                'avg_productive_day': round(avg_productive_day, 1),
                'total_completed': sum(item['completed'] for item in daily_data),
                'consistency_score': self._calculate_consistency_score(daily_data)
            }

        except Exception as e:
            print(f"Error analyzing productivity trends: {e}")
            return {}

    def _analyze_context_performance(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Analiza el rendimiento por contexto."""
        try:
            # Rendimiento por contexto
            context_performance = Task.objects.filter(
                user_id=user_id,
                created_at__range=[start_date, end_date]
            ).values('context').annotate(
                total=Count('id'),
                completed=Count('id', filter={'status': 'done'}),
                avg_completion_time=self._calculate_avg_completion_time_per_context(user_id, start_date, end_date)
            )

            # Calcular tasas de completación por contexto
            context_stats = {}
            for context in context_performance:
                ctx = context['context']
                total = context['total']
                completed = context['completed']
                completion_rate = (completed / max(total, 1)) * 100

                context_stats[ctx] = {
                    'total_tasks': total,
                    'completed_tasks': completed,
                    'completion_rate': round(completion_rate, 1),
                    'efficiency_score': self._calculate_context_efficiency_score(completion_rate, total)
                }

            # Contextos más eficientes
            if context_stats:
                most_efficient = max(context_stats.items(), key=lambda x: x[1]['efficiency_score'])
                least_efficient = min(context_stats.items(), key=lambda x: x[1]['efficiency_score'])
            else:
                most_efficient = None
                least_efficient = None

            # Distribución de contextos
            total_tasks = sum(stats['total_tasks'] for stats in context_stats.values())
            context_distribution = {
                ctx: (stats['total_tasks'] / max(total_tasks, 1)) * 100
                for ctx, stats in context_stats.items()
            }

            return {
                'context_stats': context_stats,
                'most_efficient_context': most_efficient[0] if most_efficient else None,
                'least_efficient_context': least_efficient[0] if least_efficient else None,
                'context_distribution': context_distribution,
                'balance_score': self._calculate_context_balance_score(context_distribution)
            }

        except Exception as e:
            print(f"Error analyzing context performance: {e}")
            return {}

    def _analyze_time_patterns(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Analiza patrones de tiempo y horarios."""
        try:
            # Horarios de mayor productividad
            hourly_productivity = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__range=[start_date, end_date]
            ).extra(select={'hour': 'strftime("%H", updated_at)'}).values('hour').annotate(
                count=Count('id')
            )

            hour_stats = {str(i): 0 for i in range(24)}
            for item in hourly_productivity:
                hour_stats[item['hour']] = item['count']

            # Días de la semana más productivos
            weekday_productivity = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__range=[start_date, end_date]
            ).extra(select={'weekday': 'strftime("%w", updated_at)'}).values('weekday').annotate(
                count=Count('id')
            )

            weekday_names = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
            weekday_stats = {weekday_names[i]: 0 for i in range(7)}
            for item in weekday_productivity:
                day_index = int(item['weekday'])
                weekday_stats[weekday_names[day_index]] = item['count']

            # Tiempo promedio de completación
            avg_completion_time = self._calculate_avg_completion_time(user_id, start_date, end_date)

            # Patrones de energía
            energy_patterns = self._analyze_energy_patterns(user_id, start_date, end_date)

            return {
                'hourly_distribution': hour_stats,
                'peak_hours': self._get_peak_hours(hour_stats),
                'weekday_distribution': weekday_stats,
                'most_productive_weekday': max(weekday_stats, key=weekday_stats.get) if weekday_stats else None,
                'avg_completion_time': avg_completion_time,
                'energy_patterns': energy_patterns,
                'optimal_work_periods': self._identify_optimal_periods(hour_stats, weekday_stats)
            }

        except Exception as e:
            print(f"Error analyzing time patterns: {e}")
            return {}

    def _analyze_project_performance(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Analiza el rendimiento de proyectos."""
        try:
            # Proyectos con estadísticas
            project_stats = Project.objects.filter(
                user_id=user_id,
                created_at__lte=end_date
            ).annotate(
                total_tasks=Count('tasks'),
                completed_tasks=Count('tasks', filter={'status': 'done'}),
                pending_tasks=Count('tasks', filter={'status__in': ['pending', 'in_progress']}),
                avg_task_completion_time=self._calculate_project_avg_completion_time(user_id, start_date, end_date)
            )

            # Análisis de proyectos
            projects_analysis = {}
            for project in project_stats:
                if project.total_tasks > 0:
                    completion_rate = (project.completed_tasks / project.total_tasks) * 100
                    velocity = project.completed_tasks / max((end_date - project.created_at).days, 1)

                    projects_analysis[project.name] = {
                        'total_tasks': project.total_tasks,
                        'completed_tasks': project.completed_tasks,
                        'pending_tasks': project.pending_tasks,
                        'completion_rate': round(completion_rate, 1),
                        'velocity': round(velocity, 2),
                        'status': project.status,
                        'days_active': (end_date - project.created_at).days
                    }

            # Proyectos más exitosos
            if projects_analysis:
                most_successful = max(
                    projects_analysis.items(),
                    key=lambda x: x[1]['completion_rate']
                )
                most_active = max(
                    projects_analysis.items(),
                    key=lambda x: x[1]['total_tasks']
                )
            else:
                most_successful = None
                most_active = None

            # Análisis de bottlenecks
            bottlenecks = self._identify_project_bottlenecks(projects_analysis)

            return {
                'projects_analysis': projects_analysis,
                'most_successful_project': most_successful[0] if most_successful else None,
                'most_active_project': most_active[0] if most_active else None,
                'total_projects': len(projects_analysis),
                'avg_project_completion': self._calculate_avg_project_completion(projects_analysis),
                'bottlenecks': bottlenecks
            }

        except Exception as e:
            print(f"Error analyzing project performance: {e}")
            return {}

    def _calculate_efficiency_metrics(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Calcula métricas de eficiencia."""
        try:
            # Tiempo promedio de respuesta (para inbox)
            inbox_response_time = self._calculate_inbox_response_time(user_id, start_date, end_date)

            # Tasa de delegación
            delegated_tasks = Task.objects.filter(
                user_id=user_id,
                delegated_to__isnull=False,
                created_at__range=[start_date, end_date]
            ).count()

            total_tasks = Task.objects.filter(
                user_id=user_id,
                created_at__range=[start_date, end_date]
            ).count()

            delegation_rate = (delegated_tasks / max(total_tasks, 1)) * 100

            # Tasa de tareas waiting for
            waiting_tasks = Task.objects.filter(
                user_id=user_id,
                status='waiting',
                created_at__range=[start_date, end_date]
            ).count()

            waiting_rate = (waiting_tasks / max(total_tasks, 1)) * 100

            # Eficiencia de procesamiento
            processing_efficiency = self._calculate_processing_efficiency(user_id, start_date, end_date)

            # Puntuación de eficiencia general
            efficiency_score = self._calculate_overall_efficiency_score(
                inbox_response_time, delegation_rate, waiting_rate, processing_efficiency
            )

            return {
                'inbox_response_time': inbox_response_time,
                'delegation_rate': round(delegation_rate, 1),
                'waiting_rate': round(waiting_rate, 1),
                'processing_efficiency': round(processing_efficiency, 1),
                'overall_efficiency_score': round(efficiency_score, 1),
                'efficiency_trend': self._calculate_efficiency_trend(user_id, start_date, end_date)
            }

        except Exception as e:
            print(f"Error calculating efficiency metrics: {e}")
            return {}

    def _generate_predictions(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Genera predicciones basadas en datos históricos."""
        try:
            # Predicción de completación semanal
            weekly_completion_prediction = self._predict_weekly_completion(user_id, start_date, end_date)

            # Predicción de contextos más usados
            context_prediction = self._predict_context_usage(user_id, start_date, end_date)

            # Predicción de bottlenecks
            bottleneck_prediction = self._predict_bottlenecks(user_id, start_date, end_date)

            # Predicción de productividad para la próxima semana
            next_week_prediction = self._predict_next_week_productivity(user_id, start_date, end_date)

            return {
                'weekly_completion_prediction': weekly_completion_prediction,
                'context_prediction': context_prediction,
                'bottleneck_prediction': bottleneck_prediction,
                'next_week_prediction': next_week_prediction,
                'confidence_level': self._calculate_prediction_confidence(user_id, start_date, end_date)
            }

        except Exception as e:
            print(f"Error generating predictions: {e}")
            return {}

    def _generate_insights(self, user_id: int, start_date: datetime, end_date: datetime) -> List[str]:
        """Genera insights accionables basados en los datos."""
        insights = []

        try:
            # Obtener datos básicos
            overview = self._get_overview_metrics(user_id, start_date, end_date)
            trends = self._analyze_productivity_trends(user_id, start_date, end_date)
            context_analysis = self._analyze_context_performance(user_id, start_date, end_date)

            # Insights basados en tasas de completación
            if overview.get('completion_rate', 0) < 50:
                insights.append("Tu tasa de completación es baja. Considera enfocarte en menos tareas pero completarlas todas.")

            if overview.get('completion_rate', 0) > 80:
                insights.append("¡Excelente tasa de completación! Estás siendo muy efectivo.")

            # Insights basados en tendencias
            if trends.get('trend_direction') == 'down':
                insights.append("Tu productividad está disminuyendo. Considera revisar tus hábitos y eliminar distracciones.")

            if trends.get('trend_direction') == 'up':
                insights.append("¡Tu productividad está mejorando! Sigue con los buenos hábitos.")

            # Insights basados en contextos
            if context_analysis.get('balance_score', 0) < 30:
                insights.append("Tus contextos están desbalanceados. Considera diversificar tus actividades.")

            # Insights basados en eficiencia
            efficiency = self._calculate_efficiency_metrics(user_id, start_date, end_date)
            if efficiency.get('waiting_rate', 0) > 20:
                insights.append("Tienes muchas tareas en espera. Considera hacer seguimiento más activo.")

            # Insights basados en consistencia
            consistency = trends.get('consistency_score', 0)
            if consistency < 50:
                insights.append("Tu consistencia es baja. Considera establecer rutinas más regulares.")

            if consistency > 80:
                insights.append("¡Excelente consistencia! Esto es clave para mantener la productividad.")

            # Limitar a máximo 5 insights
            return insights[:5]

        except Exception as e:
            print(f"Error generating insights: {e}")
            return ["Revisa tus datos para obtener insights personalizados"]

    # Métodos auxiliares para cálculos

    def _calculate_trend_slope(self, x_values: List[int], y_values: List[float]) -> float:
        """Calcula la pendiente de una tendencia usando regresión lineal simple."""
        n = len(x_values)
        if n < 2:
            return 0

        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x_squared = sum(x ** 2 for x in x_values)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x_squared - sum_x ** 2)
        return slope

    def _calculate_weekly_averages(self, daily_data: List[Dict]) -> Dict:
        """Calcula promedios semanales."""
        if not daily_data:
            return {}

        # Agrupar por semanas
        weekly_data = defaultdict(list)
        for item in daily_data:
            date = datetime.strptime(item['date'], '%Y-%m-%d').date()
            week_start = date - timedelta(days=date.weekday())
            weekly_data[week_start].append(item['completed'])

        # Calcular promedios
        weekly_averages = {}
        for week_start, completions in weekly_data.items():
            weekly_averages[week_start.strftime('%Y-%m-%d')] = round(sum(completions) / len(completions), 1)

        return weekly_averages

    def _calculate_consistency_score(self, daily_data: List[Dict]) -> float:
        """Calcula puntuación de consistencia (0-100)."""
        if not daily_data:
            return 0

        completions = [item['completed'] for item in daily_data]
        mean = sum(completions) / len(completions)
        variance = sum((x - mean) ** 2 for x in completions) / len(completions)
        std_dev = math.sqrt(variance)

        # Normalizar a 0-100 (menor desviación = mayor consistencia)
        consistency = max(0, 100 - (std_dev / max(mean, 1)) * 50)
        return round(consistency, 1)

    def _get_peak_hours(self, hour_stats: Dict[str, int]) -> List[str]:
        """Obtiene las horas de mayor productividad."""
        if not hour_stats:
            return []

        max_count = max(hour_stats.values())
        if max_count == 0:
            return []

        peak_hours = [hour for hour, count in hour_stats.items() if count == max_count]
        return peak_hours

    def _calculate_avg_completion_time(self, user_id: int, start_date: datetime, end_date: datetime) -> str:
        """Calcula tiempo promedio de completación."""
        try:
            completed_tasks = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__range=[start_date, end_date]
            ).exclude(created_at__date=timezone.now().date())

            if not completed_tasks:
                return 'N/A'

            total_time = timedelta(0)
            for task in completed_tasks:
                time_diff = task.updated_at - task.created_at
                total_time += time_diff

            avg_time = total_time / len(completed_tasks)

            hours = avg_time.days * 24 + avg_time.seconds // 3600
            minutes = (avg_time.seconds % 3600) // 60

            if hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"

        except Exception:
            return 'N/A'

    def _calculate_context_efficiency_score(self, completion_rate: float, total_tasks: int) -> float:
        """Calcula puntuación de eficiencia para un contexto."""
        # Combinar tasa de completación con volumen de trabajo
        volume_factor = min(total_tasks / 10, 1)  # Máximo en 10 tareas
        return (completion_rate * 0.7) + (volume_factor * 100 * 0.3)

    def _calculate_context_balance_score(self, context_distribution: Dict[str, float]) -> float:
        """Calcula puntuación de balance entre contextos (0-100)."""
        if not context_distribution:
            return 0

        # Calcular entropía de Shannon como medida de balance
        total = sum(context_distribution.values())
        if total == 0:
            return 0

        entropy = 0
        for percentage in context_distribution.values():
            if percentage > 0:
                p = percentage / total
                entropy -= p * math.log2(p)

        max_entropy = math.log2(len(context_distribution))  # Máxima entropía posible
        balance_score = (entropy / max_entropy) * 100 if max_entropy > 0 else 0

        return round(balance_score, 1)

    def _identify_optimal_periods(self, hour_stats: Dict, weekday_stats: Dict) -> Dict:
        """Identifica períodos óptimos de trabajo."""
        peak_hours = self._get_peak_hours(hour_stats)
        most_productive_weekday = max(weekday_stats, key=weekday_stats.get) if weekday_stats else None

        return {
            'peak_hours': peak_hours,
            'most_productive_weekday': most_productive_weekday,
            'suggested_work_blocks': self._suggest_work_blocks(peak_hours)
        }

    def _suggest_work_blocks(self, peak_hours: List[str]) -> List[Dict]:
        """Sugiere bloques de trabajo óptimos."""
        if not peak_hours:
            return []

        suggestions = []
        peak_hours_int = sorted([int(hour) for hour in peak_hours])

        # Agrupar horas consecutivas
        blocks = []
        current_block = [peak_hours_int[0]]

        for hour in peak_hours_int[1:]:
            if hour == current_block[-1] + 1:
                current_block.append(hour)
            else:
                blocks.append(current_block)
                current_block = [hour]

        blocks.append(current_block)

        # Crear sugerencias de bloques
        for block in blocks:
            start_hour = min(block)
            end_hour = max(block) + 1
            suggestions.append({
                'start_time': f"{start_hour:02d}:00",
                'end_time': f"{end_hour:02d}:00",
                'duration_hours': len(block),
                'productivity_level': 'high'
            })

        return suggestions

    def _predict_weekly_completion(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Predice completación semanal basada en tendencias."""
        try:
            # Obtener datos de las últimas 4 semanas
            weekly_data = []
            for i in range(4):
                week_start = start_date - timedelta(days=7 * i)
                week_end = week_start + timedelta(days=7)

                completed = Task.objects.filter(
                    user_id=user_id,
                    status='done',
                    updated_at__range=[week_start, week_end]
                ).count()

                weekly_data.append(completed)

            if not weekly_data:
                return {'predicted': 0, 'confidence': 0}

            # Calcular promedio y tendencia
            avg_completion = sum(weekly_data) / len(weekly_data)

            # Predicción simple: promedio + tendencia
            if len(weekly_data) > 1:
                trend = weekly_data[0] - weekly_data[-1]  # Más reciente - más antigua
                prediction = avg_completion + trend * 0.3  # 30% de la tendencia
            else:
                prediction = avg_completion

            prediction = max(0, prediction)  # No puede ser negativo

            # Calcular confianza basada en consistencia
            variance = sum((x - avg_completion) ** 2 for x in weekly_data) / len(weekly_data)
            confidence = max(0, 100 - (variance / avg_completion) * 50) if avg_completion > 0 else 0

            return {
                'predicted': round(prediction),
                'confidence': round(confidence, 1),
                'historical_average': round(avg_completion, 1)
            }

        except Exception as e:
            print(f"Error predicting weekly completion: {e}")
            return {'predicted': 0, 'confidence': 0}

    def _predict_context_usage(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Predice uso de contextos para la próxima semana."""
        try:
            # Obtener uso de contextos en las últimas semanas
            context_trends = Task.objects.filter(
                user_id=user_id,
                created_at__range=[start_date, end_date]
            ).values('context').annotate(count=Count('id')).order_by('-count')

            if not context_trends:
                return {}

            # Calcular tendencias
            predictions = {}
            for context_data in context_trends[:5]:  # Top 5 contextos
                context = context_data['context']
                current_usage = context_data['count']

                # Predicción simple basada en uso actual
                predictions[context] = {
                    'current_weekly_usage': current_usage,
                    'predicted_next_week': max(1, current_usage),  # Al menos 1
                    'trend': 'stable'
                }

            return predictions

        except Exception as e:
            print(f"Error predicting context usage: {e}")
            return {}

    def _predict_bottlenecks(self, user_id: int, start_date: datetime, end_date: datetime) -> List[str]:
        """Predice posibles bottlenecks."""
        bottlenecks = []

        try:
            # Análisis de tareas waiting for
            waiting_tasks = Task.objects.filter(
                user_id=user_id,
                status='waiting',
                created_at__lte=end_date - timedelta(days=7)
            ).count()

            if waiting_tasks > 10:
                bottlenecks.append("Acumulación de tareas en espera - revisar dependencias")

            # Análisis de proyectos estancados
            stalled_projects = Project.objects.filter(
                user_id=user_id,
                status='active',
                updated_at__lte=end_date - timedelta(days=14)
            ).count()

            if stalled_projects > 0:
                bottlenecks.append(f"Proyectos estancados ({stalled_projects}) - requieren atención")

            # Análisis de sobrecarga de contextos
            context_load = Task.objects.filter(
                user_id=user_id,
                status__in=['pending', 'in_progress'],
                created_at__range=[end_date - timedelta(days=7), end_date]
            ).values('context').annotate(count=Count('id'))

            overloaded_contexts = [item['context'] for item in context_load if item['count'] > 20]
            if overloaded_contexts:
                bottlenecks.append(f"Contextos sobrecargados: {', '.join(overloaded_contexts[:3])}")

        except Exception as e:
            print(f"Error predicting bottlenecks: {e}")

        return bottlenecks

    def _predict_next_week_productivity(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Predice productividad para la próxima semana."""
        try:
            # Basado en tendencias recientes
            recent_trend = self._analyze_productivity_trends(user_id, start_date, end_date)

            if recent_trend.get('trend_direction') == 'up':
                prediction = 'Aumento esperado en productividad'
                confidence = 70
            elif recent_trend.get('trend_direction') == 'down':
                prediction = 'Posible disminución en productividad'
                confidence = 60
            else:
                prediction = 'Productividad estable esperada'
                confidence = 80

            return {
                'prediction': prediction,
                'confidence': confidence,
                'based_on': 'Tendencias de las últimas semanas'
            }

        except Exception as e:
            print(f"Error predicting next week productivity: {e}")
            return {
                'prediction': 'No se puede determinar',
                'confidence': 0,
                'based_on': 'Datos insuficientes'
            }

    def _calculate_prediction_confidence(self, user_id: int, start_date: datetime, end_date: datetime) -> float:
        """Calcula nivel de confianza general de las predicciones."""
        try:
            # Basado en cantidad y calidad de datos disponibles
            total_tasks = Task.objects.filter(
                user_id=user_id,
                created_at__range=[start_date, end_date]
            ).count()

            days_with_data = Task.objects.filter(
                user_id=user_id,
                updated_at__range=[start_date, end_date]
            ).extra(select={'date': 'DATE(updated_at)'}).values('date').distinct().count()

            total_days = (end_date - start_date).days

            # Confianza basada en volumen de datos
            data_confidence = min(total_tasks / 50, 1) * 100  # 50 tareas = 100% confianza

            # Confianza basada en consistencia
            consistency_confidence = min(days_with_data / max(total_days, 1), 1) * 100

            # Confianza general
            overall_confidence = (data_confidence * 0.6) + (consistency_confidence * 0.4)

            return round(overall_confidence, 1)

        except Exception as e:
            print(f"Error calculating prediction confidence: {e}")
            return 0

    def _calculate_inbox_response_time(self, user_id: int, start_date: datetime, end_date: datetime) -> str:
        """Calcula tiempo promedio de respuesta a inbox."""
        try:
            processed_items = InboxItem.objects.filter(
                user_id=user_id,
                processed=True,
                captured_at__range=[start_date, end_date]
            )

            if not processed_items:
                return 'N/A'

            total_time = timedelta(0)
            for item in processed_items:
                # Este es un cálculo aproximado - en un sistema real tendrías timestamps de procesamiento
                time_diff = timedelta(hours=2)  # Asumir 2 horas promedio
                total_time += time_diff

            avg_time = total_time / len(processed_items)

            hours = avg_time.days * 24 + avg_time.seconds // 3600
            minutes = (avg_time.seconds % 3600) // 60

            if hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"

        except Exception:
            return 'N/A'

    def _calculate_processing_efficiency(self, user_id: int, start_date: datetime, end_date: datetime) -> float:
        """Calcula eficiencia de procesamiento."""
        try:
            # Tareas procesadas vs tiempo invertido
            # Este es un cálculo simplificado
            completed_tasks = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__range=[start_date, end_date]
            ).count()

            # Asumir que cada tarea toma aproximadamente 1 hora
            estimated_hours = completed_tasks * 1

            # Eficiencia = tareas completadas / tiempo estimado
            efficiency = min(completed_tasks / max(estimated_hours, 1), 10) * 100

            return min(efficiency, 100)

        except Exception:
            return 0

    def _calculate_overall_efficiency_score(self, inbox_time: str, delegation_rate: float,
                                          waiting_rate: float, processing_efficiency: float) -> float:
        """Calcula puntuación general de eficiencia."""
        try:
            # Convertir tiempo de inbox a horas
            inbox_hours = 2  # Simplificado

            # Puntuaciones individuales (0-100)
            inbox_score = max(0, 100 - inbox_hours * 10)  # Menos tiempo = mejor puntuación
            delegation_score = min(delegation_rate * 2, 100)  # Más delegación = mejor
            waiting_score = max(0, 100 - waiting_rate)  # Menos waiting = mejor
            processing_score = processing_efficiency

            # Puntuación ponderada
            overall_score = (
                inbox_score * 0.2 +
                delegation_score * 0.2 +
                waiting_score * 0.3 +
                processing_score * 0.3
            )

            return overall_score

        except Exception:
            return 0

    def _calculate_efficiency_trend(self, user_id: int, start_date: datetime, end_date: datetime) -> str:
        """Calcula tendencia de eficiencia."""
        try:
            # Comparar primera y segunda mitad del período
            mid_date = start_date + (end_date - start_date) / 2

            first_half = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__range=[start_date, mid_date]
            ).count()

            second_half = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__range=[mid_date, end_date]
            ).count()

            if second_half > first_half:
                return 'improving'
            elif second_half < first_half:
                return 'declining'
            else:
                return 'stable'

        except Exception:
            return 'unknown'


# Instancia global del sistema de análisis
gtd_analytics = GTDProductivityAnalytics()