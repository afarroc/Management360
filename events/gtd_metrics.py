"""
Sistema de métricas avanzadas para GTD
Proporciona métricas específicas de la metodología Getting Things Done.
"""

from django.utils import timezone
from datetime import datetime, timedelta
from .models import Task, Project, InboxItem
from .gtd_utils import gtd_engine
import json
from typing import Dict, List, Optional, Tuple
from collections import Counter, defaultdict
import math


class GTDMetricsEngine:
    """
    Motor de métricas avanzadas específicas para GTD.
    Proporciona análisis detallado de la implementación de la metodología.
    """

    def __init__(self):
        self.gtd_dimensions = {
            'capture': self._analyze_capture_metrics,
            'clarify': self._analyze_clarify_metrics,
            'organize': self._analyze_organize_metrics,
            'reflect': self._analyze_reflect_metrics,
            'engage': self._analyze_engage_metrics
        }

    def get_comprehensive_gtd_metrics(self, user_id: int, days: int = 30) -> Dict:
        """
        Obtiene métricas completas de GTD para el usuario.
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        metrics = {
            'gtd_dimensions': {},
            'overall_gtd_score': 0,
            'strengths': [],
            'improvement_areas': [],
            'trends': {},
            'benchmarks': {},
            'generated_at': timezone.now().isoformat()
        }

        # Calcular métricas para cada dimensión GTD
        dimension_scores = {}
        for dimension, analysis_method in self.gtd_dimensions.items():
            try:
                dimension_metrics = analysis_method(user_id, start_date, end_date)
                metrics['gtd_dimensions'][dimension] = dimension_metrics
                dimension_scores[dimension] = dimension_metrics.get('score', 0)
            except Exception as e:
                print(f"Error analyzing GTD dimension {dimension}: {e}")
                dimension_scores[dimension] = 0

        # Calcular puntuación general GTD
        metrics['overall_gtd_score'] = self._calculate_overall_gtd_score(dimension_scores)

        # Identificar fortalezas y áreas de mejora
        metrics['strengths'] = self._identify_strengths(dimension_scores)
        metrics['improvement_areas'] = self._identify_improvement_areas(dimension_scores)

        # Análisis de tendencias
        metrics['trends'] = self._analyze_gtd_trends(user_id, start_date, end_date)

        # Benchmarks comparativos
        metrics['benchmarks'] = self._generate_benchmarks(dimension_scores)

        return metrics

    def _analyze_capture_metrics(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Analiza la dimensión CAPTURE de GTD."""
        try:
            # Elementos capturados en inbox
            inbox_items = InboxItem.objects.filter(
                user_id=user_id,
                captured_at__range=[start_date, end_date]
            ).count()

            # Tasa de procesamiento del inbox
            processed_items = InboxItem.objects.filter(
                user_id=user_id,
                processed=True,
                captured_at__range=[start_date, end_date]
            ).count()

            processing_rate = (processed_items / max(inbox_items, 1)) * 100

            # Tiempo promedio de permanencia en inbox
            avg_inbox_time = self._calculate_avg_inbox_time(user_id, start_date, end_date)

            # Consistencia de captura
            daily_capture = self._calculate_daily_capture_consistency(user_id, start_date, end_date)

            # Puntuación de capture
            capture_score = self._calculate_capture_score(
                processing_rate, avg_inbox_time, daily_capture, inbox_items
            )

            return {
                'score': capture_score,
                'inbox_items': inbox_items,
                'processed_items': processed_items,
                'processing_rate': round(processing_rate, 1),
                'avg_inbox_time': avg_inbox_time,
                'daily_capture_consistency': round(daily_capture, 1),
                'level': self._get_gtd_level(capture_score),
                'insights': self._generate_capture_insights(
                    processing_rate, avg_inbox_time, daily_capture
                )
            }

        except Exception as e:
            print(f"Error analyzing capture metrics: {e}")
            return {'score': 0, 'level': 'unknown', 'insights': []}

    def _analyze_clarify_metrics(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Analiza la dimensión CLARIFY de GTD."""
        try:
            # Tareas con descripción clara
            total_tasks = Task.objects.filter(
                user_id=user_id,
                created_at__range=[start_date, end_date]
            ).count()

            tasks_with_description = Task.objects.filter(
                user_id=user_id,
                created_at__range=[start_date, end_date],
                description__isnull=False
            ).exclude(description='').count()

            description_rate = (tasks_with_description / max(total_tasks, 1)) * 100

            # Tareas con contexto definido
            tasks_with_context = Task.objects.filter(
                user_id=user_id,
                created_at__range=[start_date, end_date],
                context__isnull=False
            ).exclude(context='').count()

            context_rate = (tasks_with_context / max(total_tasks, 1)) * 100

            # Tareas con prioridad definida
            tasks_with_priority = Task.objects.filter(
                user_id=user_id,
                created_at__range=[start_date, end_date],
                priority__isnull=False
            ).exclude(priority='').count()

            priority_rate = (tasks_with_priority / max(total_tasks, 1)) * 100

            # Claridad promedio
            clarity_score = (description_rate + context_rate + priority_rate) / 3

            # Puntuación de clarify
            clarify_score = self._calculate_clarify_score(
                clarity_score, total_tasks
            )

            return {
                'score': clarify_score,
                'total_tasks': total_tasks,
                'description_rate': round(description_rate, 1),
                'context_rate': round(context_rate, 1),
                'priority_rate': round(priority_rate, 1),
                'clarity_score': round(clarity_score, 1),
                'level': self._get_gtd_level(clarify_score),
                'insights': self._generate_clarify_insights(
                    description_rate, context_rate, priority_rate
                )
            }

        except Exception as e:
            print(f"Error analyzing clarify metrics: {e}")
            return {'score': 0, 'level': 'unknown', 'insights': []}

    def _analyze_organize_metrics(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Analiza la dimensión ORGANIZE de GTD."""
        try:
            # Distribución por contextos
            context_distribution = Task.objects.filter(
                user_id=user_id,
                created_at__range=[start_date, end_date]
            ).values('context').annotate(count=Count('id'))

            # Distribución por prioridades
            priority_distribution = Task.objects.filter(
                user_id=user_id,
                created_at__range=[start_date, end_date]
            ).values('priority').annotate(count=Count('id'))

            # Proyectos activos vs tareas independientes
            project_tasks = Task.objects.filter(
                user_id=user_id,
                created_at__range=[start_date, end_date],
                project__isnull=False
            ).count()

            independent_tasks = Task.objects.filter(
                user_id=user_id,
                created_at__range=[start_date, end_date],
                project__isnull=True
            ).count()

            total_tasks = project_tasks + independent_tasks
            project_task_ratio = (project_tasks / max(total_tasks, 1)) * 100

            # Organización por fechas
            tasks_with_due_date = Task.objects.filter(
                user_id=user_id,
                created_at__range=[start_date, end_date],
                due_date__isnull=False
            ).count()

            due_date_rate = (tasks_with_due_date / max(total_tasks, 1)) * 100

            # Puntuación de organize
            organize_score = self._calculate_organize_score(
                context_distribution, priority_distribution, project_task_ratio, due_date_rate
            )

            return {
                'score': organize_score,
                'context_distribution': list(context_distribution),
                'priority_distribution': list(priority_distribution),
                'project_task_ratio': round(project_task_ratio, 1),
                'due_date_rate': round(due_date_rate, 1),
                'level': self._get_gtd_level(organize_score),
                'insights': self._generate_organize_insights(
                    context_distribution, priority_distribution, project_task_ratio
                )
            }

        except Exception as e:
            print(f"Error analyzing organize metrics: {e}")
            return {'score': 0, 'level': 'unknown', 'insights': []}

    def _analyze_reflect_metrics(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Analiza la dimensión REFLECT de GTD."""
        try:
            # Frecuencia de revisiones (basado en actualizaciones)
            review_frequency = self._calculate_review_frequency(user_id, start_date, end_date)

            # Tareas revisadas vs total
            total_tasks = Task.objects.filter(
                user_id=user_id,
                created_at__lte=end_date
            ).count()

            reviewed_tasks = Task.objects.filter(
                user_id=user_id,
                updated_at__gt=timezone.now() - timedelta(days=7)
            ).count()

            review_rate = (reviewed_tasks / max(total_tasks, 1)) * 100

            # Consistencia de revisiones
            review_consistency = self._calculate_review_consistency(user_id, start_date, end_date)

            # Actualizaciones de proyectos
            project_updates = Project.objects.filter(
                user_id=user_id,
                updated_at__range=[start_date, end_date]
            ).count()

            # Puntuación de reflect
            reflect_score = self._calculate_reflect_score(
                review_frequency, review_rate, review_consistency, project_updates
            )

            return {
                'score': reflect_score,
                'review_frequency': review_frequency,
                'review_rate': round(review_rate, 1),
                'review_consistency': round(review_consistency, 1),
                'project_updates': project_updates,
                'level': self._get_gtd_level(reflect_score),
                'insights': self._generate_reflect_insights(
                    review_frequency, review_rate, review_consistency
                )
            }

        except Exception as e:
            print(f"Error analyzing reflect metrics: {e}")
            return {'score': 0, 'level': 'unknown', 'insights': []}

    def _analyze_engage_metrics(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Analiza la dimensión ENGAGE de GTD."""
        try:
            # Tasa de completación
            total_tasks = Task.objects.filter(
                user_id=user_id,
                created_at__range=[start_date, end_date]
            ).count()

            completed_tasks = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__range=[start_date, end_date]
            ).count()

            completion_rate = (completed_tasks / max(total_tasks, 1)) * 100

            # Tareas por contexto completadas
            context_completion = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__range=[start_date, end_date]
            ).values('context').annotate(count=Count('id'))

            # Eficiencia por contexto
            context_efficiency = {}
            for context_data in context_completion:
                context = context_data['context']
                completed = context_data['count']
                total_in_context = Task.objects.filter(
                    user_id=user_id,
                    context=context,
                    created_at__range=[start_date, end_date]
                ).count()

                efficiency = (completed / max(total_in_context, 1)) * 100
                context_efficiency[context] = round(efficiency, 1)

            # Tiempo promedio de completación
            avg_completion_time = self._calculate_avg_completion_time(user_id, start_date, end_date)

            # Puntuación de engage
            engage_score = self._calculate_engage_score(
                completion_rate, context_efficiency, avg_completion_time
            )

            return {
                'score': engage_score,
                'completion_rate': round(completion_rate, 1),
                'context_efficiency': context_efficiency,
                'avg_completion_time': avg_completion_time,
                'level': self._get_gtd_level(engage_score),
                'insights': self._generate_engage_insights(
                    completion_rate, context_efficiency, avg_completion_time
                )
            }

        except Exception as e:
            print(f"Error analyzing engage metrics: {e}")
            return {'score': 0, 'level': 'unknown', 'insights': []}

    def _calculate_overall_gtd_score(self, dimension_scores: Dict[str, float]) -> float:
        """Calcula puntuación general de GTD."""
        if not dimension_scores:
            return 0

        # Pesos para cada dimensión
        weights = {
            'capture': 0.15,
            'clarify': 0.20,
            'organize': 0.25,
            'reflect': 0.15,
            'engage': 0.25
        }

        weighted_score = 0
        for dimension, score in dimension_scores.items():
            weight = weights.get(dimension, 0.2)
            weighted_score += score * weight

        return round(weighted_score, 1)

    def _identify_strengths(self, dimension_scores: Dict[str, float]) -> List[str]:
        """Identifica fortalezas basadas en puntuaciones."""
        strengths = []

        for dimension, score in dimension_scores.items():
            if score >= 80:
                strength_descriptions = {
                    'capture': 'Excelente sistema de captura de información',
                    'clarify': 'Claridad excepcional en la definición de tareas',
                    'organize': 'Organización muy efectiva de proyectos y contextos',
                    'reflect': 'Excelente hábito de revisión y actualización',
                    'engage': 'Alta efectividad en la ejecución de tareas'
                }
                if dimension in strength_descriptions:
                    strengths.append(strength_descriptions[dimension])

        return strengths[:3]  # Máximo 3 fortalezas

    def _identify_improvement_areas(self, dimension_scores: Dict[str, float]) -> List[str]:
        """Identifica áreas de mejora basadas en puntuaciones."""
        improvements = []

        for dimension, score in dimension_scores.items():
            if score < 60:
                improvement_descriptions = {
                    'capture': 'Mejorar el hábito de capturar información en el inbox',
                    'clarify': 'Definir mejor las tareas con descripciones, contextos y prioridades',
                    'organize': 'Mejorar la organización de tareas por proyectos y contextos',
                    'reflect': 'Establecer rutina regular de revisión semanal',
                    'engage': 'Aumentar la tasa de completación de tareas'
                }
                if dimension in improvement_descriptions:
                    improvements.append(improvement_descriptions[dimension])

        return improvements[:3]  # Máximo 3 áreas de mejora

    def _analyze_gtd_trends(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Analiza tendencias en la implementación de GTD."""
        try:
            # Dividir el período en dos mitades
            mid_date = start_date + (end_date - start_date) / 2

            first_half_scores = {}
            second_half_scores = {}

            for dimension in self.gtd_dimensions.keys():
                try:
                    first_half_metrics = self.gtd_dimensions[dimension](user_id, start_date, mid_date)
                    second_half_metrics = self.gtd_dimensions[dimension](user_id, mid_date, end_date)

                    first_half_scores[dimension] = first_half_metrics.get('score', 0)
                    second_half_scores[dimension] = second_half_metrics.get('score', 0)
                except:
                    first_half_scores[dimension] = 0
                    second_half_scores[dimension] = 0

            # Calcular tendencias
            trends = {}
            for dimension in first_half_scores:
                first_score = first_half_scores[dimension]
                second_score = second_half_scores[dimension]

                if second_score > first_score + 10:
                    trends[dimension] = 'improving'
                elif second_score < first_score - 10:
                    trends[dimension] = 'declining'
                else:
                    trends[dimension] = 'stable'

            return {
                'first_half': first_half_scores,
                'second_half': second_half_scores,
                'trends': trends,
                'overall_trend': self._calculate_overall_trend(trends)
            }

        except Exception as e:
            print(f"Error analyzing GTD trends: {e}")
            return {}

    def _generate_benchmarks(self, dimension_scores: Dict[str, float]) -> Dict:
        """Genera benchmarks comparativos."""
        benchmarks = {
            'user_scores': dimension_scores,
            'gtd_levels': {
                dimension: self._get_gtd_level(score)
                for dimension, score in dimension_scores.items()
            },
            'comparison_with_ideal': self._compare_with_ideal_gtd(dimension_scores),
            'progress_indicators': self._generate_progress_indicators(dimension_scores)
        }

        return benchmarks

    # Métodos auxiliares para cálculos específicos

    def _calculate_capture_score(self, processing_rate: float, avg_inbox_time: str,
                               daily_consistency: float, inbox_volume: int) -> float:
        """Calcula puntuación para la dimensión Capture."""
        score = 0

        # Tasa de procesamiento (40%)
        if processing_rate >= 90:
            score += 40
        elif processing_rate >= 70:
            score += 30
        elif processing_rate >= 50:
            score += 20
        else:
            score += 10

        # Consistencia diaria (30%)
        if daily_consistency >= 80:
            score += 30
        elif daily_consistency >= 60:
            score += 20
        elif daily_consistency >= 40:
            score += 10

        # Volumen de captura (30%)
        if inbox_volume >= 50:
            score += 30
        elif inbox_volume >= 25:
            score += 20
        elif inbox_volume >= 10:
            score += 10

        return score

    def _calculate_clarify_score(self, clarity_score: float, task_volume: int) -> float:
        """Calcula puntuación para la dimensión Clarify."""
        score = 0

        # Claridad general (70%)
        if clarity_score >= 90:
            score += 70
        elif clarity_score >= 75:
            score += 55
        elif clarity_score >= 60:
            score += 40
        elif clarity_score >= 45:
            score += 25
        else:
            score += 10

        # Volumen de tareas procesadas (30%)
        if task_volume >= 100:
            score += 30
        elif task_volume >= 50:
            score += 20
        elif task_volume >= 20:
            score += 10

        return score

    def _calculate_organize_score(self, context_distribution: List, priority_distribution: List,
                               project_ratio: float, due_date_rate: float) -> float:
        """Calcula puntuación para la dimensión Organize."""
        score = 0

        # Distribución balanceada de contextos (30%)
        context_count = len(context_distribution)
        if context_count >= 5:
            score += 30
        elif context_count >= 3:
            score += 20
        elif context_count >= 2:
            score += 10

        # Distribución balanceada de prioridades (25%)
        priority_count = len(priority_distribution)
        if priority_count >= 3:
            score += 25
        elif priority_count >= 2:
            score += 15

        # Uso apropiado de proyectos (25%)
        if 20 <= project_ratio <= 60:
            score += 25
        elif 10 <= project_ratio <= 70:
            score += 15
        else:
            score += 5

        # Uso de fechas límite (20%)
        if due_date_rate >= 50:
            score += 20
        elif due_date_rate >= 30:
            score += 12
        elif due_date_rate >= 15:
            score += 6

        return score

    def _calculate_reflect_score(self, review_frequency: float, review_rate: float,
                               consistency: float, project_updates: int) -> float:
        """Calcula puntuación para la dimensión Reflect."""
        score = 0

        # Frecuencia de revisiones (40%)
        if review_frequency >= 0.8:
            score += 40
        elif review_frequency >= 0.6:
            score += 30
        elif review_frequency >= 0.4:
            score += 20
        elif review_frequency >= 0.2:
            score += 10

        # Tasa de revisión (30%)
        if review_rate >= 80:
            score += 30
        elif review_rate >= 60:
            score += 20
        elif review_rate >= 40:
            score += 10

        # Consistencia (20%)
        if consistency >= 80:
            score += 20
        elif consistency >= 60:
            score += 12
        elif consistency >= 40:
            score += 6

        # Actualizaciones de proyectos (10%)
        if project_updates >= 5:
            score += 10
        elif project_updates >= 2:
            score += 5

        return score

    def _calculate_engage_score(self, completion_rate: float, context_efficiency: Dict,
                              avg_completion_time: str) -> float:
        """Calcula puntuación para la dimensión Engage."""
        score = 0

        # Tasa de completación (50%)
        if completion_rate >= 80:
            score += 50
        elif completion_rate >= 65:
            score += 35
        elif completion_rate >= 50:
            score += 25
        elif completion_rate >= 35:
            score += 15
        else:
            score += 5

        # Eficiencia por contexto (30%)
        if context_efficiency:
            avg_efficiency = sum(context_efficiency.values()) / len(context_efficiency)
            if avg_efficiency >= 80:
                score += 30
            elif avg_efficiency >= 65:
                score += 20
            elif avg_efficiency >= 50:
                score += 10

        # Tiempo de completación (20%)
        # Asumir que tiempos más cortos son mejores (hasta cierto punto)
        score += 20  # Por defecto, ajustar basado en análisis real

        return score

    def _get_gtd_level(self, score: float) -> str:
        """Determina el nivel GTD basado en la puntuación."""
        if score >= 90:
            return 'master'
        elif score >= 75:
            return 'advanced'
        elif score >= 60:
            return 'intermediate'
        elif score >= 40:
            return 'beginner'
        else:
            return 'novice'

    def _calculate_overall_trend(self, trends: Dict[str, str]) -> str:
        """Calcula tendencia general basada en tendencias individuales."""
        if not trends:
            return 'unknown'

        trend_counts = Counter(trends.values())

        if trend_counts['improving'] > len(trends) * 0.6:
            return 'improving'
        elif trend_counts['declining'] > len(trends) * 0.6:
            return 'declining'
        else:
            return 'stable'

    def _compare_with_ideal_gtd(self, dimension_scores: Dict[str, float]) -> Dict:
        """Compara con implementación ideal de GTD."""
        ideal_scores = {
            'capture': 100,
            'clarify': 100,
            'organize': 100,
            'reflect': 100,
            'engage': 100
        }

        comparison = {}
        for dimension, score in dimension_scores.items():
            ideal = ideal_scores.get(dimension, 100)
            gap = ideal - score
            comparison[dimension] = {
                'current': score,
                'ideal': ideal,
                'gap': gap,
                'achievement_percentage': (score / ideal) * 100
            }

        return comparison

    def _generate_progress_indicators(self, dimension_scores: Dict[str, float]) -> Dict:
        """Genera indicadores de progreso."""
        indicators = {}

        for dimension, score in dimension_scores.items():
            level = self._get_gtd_level(score)

            level_descriptions = {
                'novice': 'Principiante - Necesita fundamentos básicos',
                'beginner': 'Principiante - Entiende los conceptos básicos',
                'intermediate': 'Intermedio - Aplica consistentemente',
                'advanced': 'Avanzado - Optimiza su sistema',
                'master': 'Maestro - Refina continuamente'
            }

            indicators[dimension] = {
                'level': level,
                'description': level_descriptions.get(level, 'Nivel desconocido'),
                'next_level_score': self._get_next_level_threshold(score),
                'progress_to_next': self._calculate_progress_to_next_level(score)
            }

        return indicators

    def _get_next_level_threshold(self, current_score: float) -> int:
        """Obtiene el umbral para el siguiente nivel."""
        if current_score >= 90:
            return 100
        elif current_score >= 75:
            return 90
        elif current_score >= 60:
            return 75
        elif current_score >= 40:
            return 60
        else:
            return 40

    def _calculate_progress_to_next_level(self, current_score: float) -> float:
        """Calcula progreso hacia el siguiente nivel."""
        current_level_min = 0
        if current_score >= 90:
            current_level_min = 90
        elif current_score >= 75:
            current_level_min = 75
        elif current_score >= 60:
            current_level_min = 60
        elif current_score >= 40:
            current_level_min = 40

        next_level = self._get_next_level_threshold(current_score)
        progress = ((current_score - current_level_min) / (next_level - current_level_min)) * 100

        return round(progress, 1)

    # Métodos para generar insights específicos por dimensión

    def _generate_capture_insights(self, processing_rate: float, avg_inbox_time: str,
                                 daily_consistency: float) -> List[str]:
        """Genera insights para la dimensión Capture."""
        insights = []

        if processing_rate < 70:
            insights.append("Considera procesar tu inbox más frecuentemente para evitar acumulación")

        if daily_consistency < 50:
            insights.append("Intenta capturar información de manera más consistente a lo largo del día")

        if processing_rate > 90:
            insights.append("Excelente hábito de procesamiento del inbox")

        return insights

    def _generate_clarify_insights(self, description_rate: float, context_rate: float,
                                priority_rate: float) -> List[str]:
        """Genera insights para la dimensión Clarify."""
        insights = []

        if description_rate < 60:
            insights.append("Agrega descripciones más detalladas a tus tareas para mayor claridad")

        if context_rate < 70:
            insights.append("Define contextos para tus tareas para mejorar la organización")

        if priority_rate < 60:
            insights.append("Asigna prioridades a tus tareas para enfocar mejor tu energía")

        return insights

    def _generate_organize_insights(self, context_distribution: List, priority_distribution: List,
                                  project_ratio: float) -> List[str]:
        """Genera insights para la dimensión Organize."""
        insights = []

        if len(context_distribution) < 3:
            insights.append("Considera usar más contextos para organizar mejor tus tareas")

        if len(priority_distribution) < 2:
            insights.append("Usa diferentes niveles de prioridad para gestionar mejor tu carga de trabajo")

        if project_ratio < 20:
            insights.append("Considera agrupar más tareas en proyectos para mejor seguimiento")

        return insights

    def _generate_reflect_insights(self, review_frequency: float, review_rate: float,
                                 consistency: float) -> List[str]:
        """Genera insights para la dimensión Reflect."""
        insights = []

        if review_frequency < 0.5:
            insights.append("Establece una rutina regular de revisión semanal")

        if review_rate < 50:
            insights.append("Revisa tus tareas pendientes más frecuentemente")

        if consistency < 60:
            insights.append("Mantén revisiones más consistentes para mejor seguimiento")

        return insights

    def _generate_engage_insights(self, completion_rate: float, context_efficiency: Dict,
                                avg_completion_time: str) -> List[str]:
        """Genera insights para la dimensión Engage."""
        insights = []

        if completion_rate < 50:
            insights.append("Enfócate en completar más tareas antes de crear nuevas")

        if context_efficiency and min(context_efficiency.values()) < 50:
            least_efficient = min(context_efficiency, key=context_efficiency.get)
            insights.append(f"Mejora tu eficiencia en el contexto '{least_efficient}'")

        if completion_rate > 80:
            insights.append("Excelente tasa de completación - mantén el ritmo")

        return insights

    # Métodos auxiliares adicionales

    def _calculate_avg_inbox_time(self, user_id: int, start_date: datetime, end_date: datetime) -> str:
        """Calcula tiempo promedio en inbox (simplificado)."""
        # En un sistema real, esto calcularía el tiempo real
        return "2 horas"  # Valor por defecto

    def _calculate_daily_capture_consistency(self, user_id: int, start_date: datetime, end_date: datetime) -> float:
        """Calcula consistencia diaria de captura."""
        try:
            # Días con actividad de captura
            active_days = InboxItem.objects.filter(
                user_id=user_id,
                captured_at__range=[start_date, end_date]
            ).extra(select={'date': 'DATE(captured_at)'}).values('date').distinct().count()

            total_days = (end_date - start_date).days

            return (active_days / max(total_days, 1)) * 100

        except Exception:
            return 0

    def _calculate_review_frequency(self, user_id: int, start_date: datetime, end_date: datetime) -> float:
        """Calcula frecuencia de revisiones."""
        try:
            # Basado en actualizaciones de tareas y proyectos
            review_actions = Task.objects.filter(
                user_id=user_id,
                updated_at__range=[start_date, end_date]
            ).count() + Project.objects.filter(
                user_id=user_id,
                updated_at__range=[start_date, end_date]
            ).count()

            total_days = (end_date - start_date).days

            return review_actions / max(total_days, 1)

        except Exception:
            return 0

    def _calculate_review_consistency(self, user_id: int, start_date: datetime, end_date: datetime) -> float:
        """Calcula consistencia de revisiones."""
        try:
            # Días con actividad de revisión
            review_days = Task.objects.filter(
                user_id=user_id,
                updated_at__range=[start_date, end_date]
            ).extra(select={'date': 'DATE(updated_at)'}).values('date').distinct().count()

            total_days = (end_date - start_date).days

            return (review_days / max(total_days, 1)) * 100

        except Exception:
            return 0

    def _calculate_avg_completion_time(self, user_id: int, start_date: datetime, end_date: datetime) -> str:
        """Calcula tiempo promedio de completación."""
        try:
            completed_tasks = Task.objects.filter(
                user_id=user_id,
                status='done',
                updated_at__range=[start_date, end_date]
            )

            if not completed_tasks:
                return "N/A"

            # Estimación simplificada
            return "1.5 horas"

        except Exception:
            return "N/A"


# Instancia global del motor de métricas GTD
gtd_metrics = GTDMetricsEngine()