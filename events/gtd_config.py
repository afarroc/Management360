"""
Configuración y punto de entrada para el sistema GTD completo
Proporciona configuración centralizada y utilidades para el sistema GTD.
"""

from .gtd_utils import gtd_engine, GTDAutomationEngine
from .gtd_reviews import gtd_review_system, GTDReviewSystem
from .gtd_analytics import gtd_analytics, GTDProductivityAnalytics
from .gtd_calendar import gtd_calendar, GTDCalendarIntegration
from .gtd_metrics import gtd_metrics, GTDMetricsEngine
from .models import Task, Project, InboxItem, GTDClassificationPattern, GTDLearningEntry
from django.conf import settings
import os


class GTDSystem:
    """
    Sistema completo de GTD (Getting Things Done)
    Proporciona acceso unificado a todas las funcionalidades GTD.
    """

    def __init__(self):
        self.automation = gtd_engine
        self.reviews = gtd_review_system
        self.analytics = gtd_analytics
        self.calendar = gtd_calendar
        self.metrics = gtd_metrics

        # Configuración del sistema
        self.config = self._load_configuration()

    def _load_configuration(self) -> dict:
        """Carga configuración del sistema GTD."""
        return {
            'version': '2.0.0',
            'features': {
                'automation': True,
                'reviews': True,
                'analytics': True,
                'calendar': True,
                'metrics': True,
                'learning': True
            },
            'settings': {
                'default_contexts': ['trabajo', 'casa', 'computadora', 'recados', 'teléfono'],
                'default_priorities': ['alta', 'media', 'baja'],
                'review_intervals': {
                    'weekly': 7,
                    'monthly': 30,
                    'quarterly': 90
                },
                'automation_thresholds': {
                    'classification_confidence': 0.6,
                    'learning_min_samples': 10,
                    'prediction_confidence': 0.7
                }
            },
            'ui_settings': {
                'theme': 'auto',
                'compact_mode': False,
                'show_advanced_metrics': True,
                'enable_animations': True
            }
        }

    def get_system_status(self) -> dict:
        """Obtiene estado del sistema GTD."""
        return {
            'status': 'active',
            'version': self.config['version'],
            'features': self.config['features'],
            'database_status': self._check_database_status(),
            'last_update': self._get_last_system_update()
        }

    def _check_database_status(self) -> dict:
        """Verifica estado de la base de datos GTD."""
        try:
            # Verificar modelos principales
            task_count = Task.objects.count()
            project_count = Project.objects.count()
            inbox_count = InboxItem.objects.count()

            # Verificar modelos GTD avanzados
            pattern_count = GTDClassificationPattern.objects.count()
            learning_count = GTDLearningEntry.objects.count()

            return {
                'tasks': task_count,
                'projects': project_count,
                'inbox_items': inbox_count,
                'patterns': pattern_count,
                'learning_entries': learning_count,
                'status': 'healthy'
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def _get_last_system_update(self) -> str:
        """Obtiene fecha de última actualización del sistema."""
        try:
            # Obtener la tarea más reciente
            latest_task = Task.objects.latest('updated_at')
            return latest_task.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return 'Nunca'

    def process_inbox_automatically(self, user_id: int, inbox_item: InboxItem) -> dict:
        """
        Procesa automáticamente un elemento del inbox.
        """
        try:
            # Clasificación automática
            classification = self.automation.classify_inbox_item(
                inbox_item.description, user_id
            )

            # Crear tarea sugerida
            suggested_task = {
                'title': inbox_item.description,
                'context': classification['context'],
                'priority': classification['priority'],
                'tags': classification['tags'],
                'time_estimate': classification['time_estimate'],
                'energy_level': classification['energy_level'],
                'due_date_suggestion': classification['due_date_suggestion'],
                'confidence': classification['confidence']
            }

            return {
                'success': True,
                'classification': classification,
                'suggested_task': suggested_task,
                'action_required': classification['confidence'] < 0.6
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'suggested_task': None
            }

    def generate_comprehensive_review(self, user_id: int, review_type: str = 'weekly') -> dict:
        """
        Genera revisión comprehensiva GTD.
        """
        try:
            review_data = self.reviews.generate_review(review_type, user_id)

            # Agregar métricas GTD
            gtd_metrics = self.metrics.get_comprehensive_gtd_metrics(user_id)

            # Agregar análisis de productividad
            productivity_analytics = self.analytics.get_comprehensive_analytics(user_id)

            return {
                'review': review_data,
                'gtd_metrics': gtd_metrics,
                'productivity_analytics': productivity_analytics,
                'recommendations': self._generate_recommendations(
                    review_data, gtd_metrics, productivity_analytics
                )
            }

        except Exception as e:
            return {
                'error': str(e),
                'review': None,
                'gtd_metrics': None,
                'productivity_analytics': None
            }

    def get_dashboard_data(self, user_id: int) -> dict:
        """
        Obtiene datos para el dashboard GTD.
        """
        try:
            # Métricas generales
            overview_metrics = self.analytics._get_overview_metrics(
                user_id, timezone.now() - timedelta(days=30), timezone.now()
            )

            # Próximas acciones
            next_actions = self.automation.suggest_next_actions(user_id)

            # Estado del inbox
            inbox_status = self._get_inbox_status(user_id)

            # Proyectos activos
            active_projects = self._get_active_projects_summary(user_id)

            # Métricas GTD rápidas
            gtd_quick_metrics = self.metrics.get_comprehensive_gtd_metrics(user_id, days=7)

            return {
                'overview': overview_metrics,
                'next_actions': next_actions[:5],  # Top 5
                'inbox_status': inbox_status,
                'active_projects': active_projects,
                'gtd_quick_metrics': {
                    'overall_score': gtd_quick_metrics.get('overall_gtd_score', 0),
                    'strengths': gtd_quick_metrics.get('strengths', [])[:3],
                    'improvement_areas': gtd_quick_metrics.get('improvement_areas', [])[:3]
                },
                'last_updated': timezone.now().isoformat()
            }

        except Exception as e:
            return {
                'error': str(e),
                'overview': {},
                'next_actions': [],
                'inbox_status': {},
                'active_projects': []
            }

    def optimize_workflow(self, user_id: int) -> dict:
        """
        Optimiza el workflow GTD del usuario.
        """
        try:
            # Obtener tareas actuales
            pending_tasks = Task.objects.filter(
                user_id=user_id,
                status__in=['pending', 'in_progress']
            )

            # Generar sugerencias de horarios
            schedule_suggestions = self.calendar.suggest_optimal_schedule(
                user_id, list(pending_tasks)
            )

            # Generar sugerencias de fechas límite
            deadline_suggestions = self.calendar.suggest_deadlines(
                user_id, list(pending_tasks)
            )

            # Análisis de time blocking
            time_blocking_analysis = self.calendar.analyze_time_blocking(
                user_id, timezone.now() - timedelta(days=30), timezone.now()
            )

            return {
                'schedule_suggestions': schedule_suggestions,
                'deadline_suggestions': deadline_suggestions,
                'time_blocking_analysis': time_blocking_analysis,
                'optimization_score': self._calculate_workflow_optimization_score(
                    schedule_suggestions, deadline_suggestions, time_blocking_analysis
                )
            }

        except Exception as e:
            return {
                'error': str(e),
                'schedule_suggestions': {},
                'deadline_suggestions': {},
                'time_blocking_analysis': {}
            }

    def _get_inbox_status(self, user_id: int) -> dict:
        """Obtiene estado actual del inbox."""
        try:
            total_items = InboxItem.objects.filter(user_id=user_id).count()
            processed_items = InboxItem.objects.filter(
                user_id=user_id, processed=True
            ).count()
            unprocessed_items = total_items - processed_items

            return {
                'total': total_items,
                'processed': processed_items,
                'unprocessed': unprocessed_items,
                'processing_rate': (processed_items / max(total_items, 1)) * 100
            }

        except Exception:
            return {'total': 0, 'processed': 0, 'unprocessed': 0, 'processing_rate': 0}

    def _get_active_projects_summary(self, user_id: int) -> list:
        """Obtiene resumen de proyectos activos."""
        try:
            projects = Project.objects.filter(
                user_id=user_id, status='active'
            ).annotate(
                task_count=Count('tasks'),
                completed_tasks=Count('tasks', filter={'status': 'done'})
            )[:5]  # Top 5 proyectos

            summary = []
            for project in projects:
                progress = (project.completed_tasks / max(project.task_count, 1)) * 100
                summary.append({
                    'name': project.name,
                    'total_tasks': project.task_count,
                    'completed_tasks': project.completed_tasks,
                    'progress': round(progress, 1),
                    'status': project.status
                })

            return summary

        except Exception:
            return []

    def _generate_recommendations(self, review_data: dict, gtd_metrics: dict,
                                productivity_analytics: dict) -> list:
        """
        Genera recomendaciones basadas en datos de revisión.
        """
        recommendations = []

        try:
            # Recomendaciones basadas en métricas GTD
            if gtd_metrics.get('overall_gtd_score', 0) < 60:
                recommendations.append({
                    'type': 'gtd_fundamentals',
                    'title': 'Enfocarse en fundamentos GTD',
                    'description': 'Considera revisar los principios básicos de Getting Things Done',
                    'priority': 'high'
                })

            # Recomendaciones basadas en productividad
            trends = productivity_analytics.get('productivity_trends', {})
            if trends.get('trend_direction') == 'down':
                recommendations.append({
                    'type': 'productivity',
                    'title': 'Revisar hábitos de productividad',
                    'description': 'Tu productividad está disminuyendo. Considera ajustar tu rutina.',
                    'priority': 'medium'
                })

            # Recomendaciones basadas en contextos
            context_analysis = productivity_analytics.get('context_analysis', {})
            if context_analysis.get('balance_score', 0) < 50:
                recommendations.append({
                    'type': 'balance',
                    'title': 'Mejorar balance de contextos',
                    'description': 'Tus contextos están desbalanceados. Diversifica tus actividades.',
                    'priority': 'medium'
                })

            # Recomendaciones basadas en revisiones
            if review_data.get('type') == 'weekly':
                next_suggestions = review_data.get('next_week_suggestions', [])
                for suggestion in next_suggestions[:2]:  # Top 2 sugerencias
                    recommendations.append({
                        'type': 'weekly_action',
                        'title': 'Acción semanal sugerida',
                        'description': suggestion,
                        'priority': 'low'
                    })

        except Exception as e:
            print(f"Error generating recommendations: {e}")

        return recommendations[:5]  # Máximo 5 recomendaciones

    def _calculate_workflow_optimization_score(self, schedule_suggestions: dict,
                                            deadline_suggestions: dict,
                                            time_blocking_analysis: dict) -> float:
        """
        Calcula puntuación de optimización del workflow.
        """
        try:
            score = 0

            # Puntuación por sugerencias de horario (40%)
            if schedule_suggestions.get('optimization_score', 0) > 0:
                score += schedule_suggestions['optimization_score'] * 0.4

            # Puntuación por sugerencias de fechas límite (30%)
            deadline_count = len(deadline_suggestions.get('suggestions', {}))
            if deadline_count > 0:
                score += min(deadline_count * 10, 30)

            # Puntuación por análisis de time blocking (30%)
            time_blocking_effectiveness = time_blocking_analysis.get(
                'overall_effectiveness', 0
            )
            score += time_blocking_effectiveness * 0.3

            return round(score, 1)

        except Exception:
            return 0

    def get_gtd_learning_resources(self) -> list:
        """
        Obtiene recursos de aprendizaje para GTD.
        """
        return [
            {
                'title': 'Getting Things Done - David Allen',
                'type': 'book',
                'description': 'El libro fundamental de GTD',
                'url': 'https://gettingthingsdone.com/book/'
            },
            {
                'title': 'GTD Setup Guide',
                'type': 'guide',
                'description': 'Guía para implementar GTD desde cero',
                'url': '#'
            },
            {
                'title': 'Weekly Review Checklist',
                'type': 'template',
                'description': 'Plantilla para revisiones semanales',
                'url': '#'
            },
            {
                'title': 'Context Definitions',
                'type': 'reference',
                'description': 'Definiciones y ejemplos de contextos GTD',
                'url': '#'
            }
        ]

    def export_gtd_data(self, user_id: int, format: str = 'json') -> dict:
        """
        Exporta datos GTD del usuario.
        """
        try:
            # Obtener todos los datos relevantes
            tasks = Task.objects.filter(user_id=user_id).values()
            projects = Project.objects.filter(user_id=user_id).values()
            inbox_items = InboxItem.objects.filter(user_id=user_id).values()

            data = {
                'tasks': list(tasks),
                'projects': list(projects),
                'inbox_items': list(inbox_items),
                'export_date': timezone.now().isoformat(),
                'user_id': user_id
            }

            if format == 'json':
                return data
            else:
                return {
                    'error': f'Formato no soportado: {format}',
                    'supported_formats': ['json']
                }

        except Exception as e:
            return {'error': str(e)}

    def get_system_health_check(self) -> dict:
        """
        Realiza chequeo de salud del sistema GTD.
        """
        try:
            health_status = {
                'overall_status': 'healthy',
                'components': {},
                'issues': [],
                'recommendations': []
            }

            # Chequear cada componente
            components = {
                'automation_engine': self.automation,
                'review_system': self.reviews,
                'analytics_engine': self.analytics,
                'calendar_integration': self.calendar,
                'metrics_engine': self.metrics
            }

            for name, component in components.items():
                try:
                    # Verificar que el componente esté funcionando
                    if hasattr(component, 'get_system_status'):
                        status = component.get_system_status()
                    else:
                        status = 'operational'

                    health_status['components'][name] = {
                        'status': status,
                        'last_check': timezone.now().isoformat()
                    }

                except Exception as e:
                    health_status['components'][name] = {
                        'status': 'error',
                        'error': str(e),
                        'last_check': timezone.now().isoformat()
                    }
                    health_status['issues'].append(f"Componente {name} con error: {str(e)}")

            # Determinar estado general
            if any(comp['status'] == 'error' for comp in health_status['components'].values()):
                health_status['overall_status'] = 'degraded'
            elif all(comp['status'] == 'operational' for comp in health_status['components'].values()):
                health_status['overall_status'] = 'healthy'
            else:
                health_status['overall_status'] = 'unknown'

            return health_status

        except Exception as e:
            return {
                'overall_status': 'error',
                'error': str(e),
                'components': {},
                'issues': [str(e)],
                'recommendations': ['Contactar soporte técnico']
            }


# Instancia global del sistema GTD
gtd_system = GTDSystem()


def get_gtd_context_processors():
    """
    Proporciona context processors para templates GTD.
    """
    def gtd_system_status(request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            return {
                'gtd_system_status': gtd_system.get_system_status(),
                'gtd_dashboard_data': gtd_system.get_dashboard_data(request.user.id),
                'gtd_config': gtd_system.config
            }
        return {
            'gtd_system_status': None,
            'gtd_dashboard_data': None,
            'gtd_config': gtd_system.config
        }

    return {
        'gtd_system_status': gtd_system_status
    }