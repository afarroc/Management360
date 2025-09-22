"""
Utilidades avanzadas para el sistema GTD (Getting Things Done)
Incluye clasificación automática, patrones de aprendizaje y análisis de productividad.
"""

from django.utils import timezone
from datetime import datetime, timedelta
from .models import Task, Project, InboxItem, GTDClassificationPattern, GTDLearningEntry
import re
from collections import Counter
import json
from typing import Dict, List, Tuple, Optional


class GTDAutomationEngine:
    """
    Motor de automatización inteligente para GTD.
    Proporciona clasificación automática, sugerencias y análisis de patrones.
    """

    def __init__(self):
        self.patterns = self._load_patterns()
        self.learning_data = self._load_learning_data()

    def _load_patterns(self) -> Dict[str, List[str]]:
        """Carga patrones de clasificación desde la base de datos."""
        patterns = {
            'contexts': ['trabajo', 'casa', 'computadora', 'recados', 'teléfono', 'email', 'reunión'],
            'priorities': ['alta', 'media', 'baja'],
            'keywords': {
                'urgent': ['urgente', 'asap', 'inmediato', 'crítico', 'deadline', 'hoy'],
                'waiting': ['esperar', 'waiting for', 'pendiente de', 'respuesta', 'feedback'],
                'meeting': ['reunión', 'meeting', 'cita', 'llamada', 'conferencia'],
                'email': ['email', 'correo', 'responder', 'enviar'],
                'research': ['investigar', 'research', 'estudiar', 'analizar', 'review'],
                'planning': ['planear', 'planificar', 'estrategia', 'objetivos', 'metas'],
                'communication': ['llamar', 'escribir', 'contactar', 'mensaje', 'chat'],
                'errands': ['comprar', 'ir a', 'recoger', 'entregar', 'pagar'],
                'home': ['casa', 'hogar', 'familia', 'personal', 'mantenimiento'],
                'computer': ['computadora', 'software', 'programar', 'desarrollar', 'sistema']
            }
        }

        # Cargar patrones desde la base de datos
        try:
            db_patterns = GTDClassificationPattern.objects.all()
            for pattern in db_patterns:
                if pattern.category not in patterns:
                    patterns[pattern.category] = []
                patterns[pattern.category].append(pattern.keyword.lower())
        except:
            pass  # Si hay error, usar patrones por defecto

        return patterns

    def _load_learning_data(self) -> Dict:
        """Carga datos de aprendizaje para mejorar clasificaciones."""
        try:
            entries = GTDLearningEntry.objects.all()
            learning_data = {
                'user_patterns': {},
                'context_frequency': Counter(),
                'priority_frequency': Counter(),
                'success_patterns': []
            }

            for entry in entries:
                if entry.user_id not in learning_data['user_patterns']:
                    learning_data['user_patterns'][entry.user_id] = {
                        'contexts': Counter(),
                        'priorities': Counter(),
                        'keywords': Counter()
                    }

                learning_data['user_patterns'][entry.user_id]['contexts'][entry.context] += 1
                learning_data['user_patterns'][entry.user_id]['priorities'][entry.priority] += 1

                if entry.metadata:
                    metadata = json.loads(entry.metadata)
                    for keyword in metadata.get('keywords', []):
                        learning_data['user_patterns'][entry.user_id]['keywords'][keyword] += 1

            return learning_data
        except:
            return {
                'user_patterns': {},
                'context_frequency': Counter(),
                'priority_frequency': Counter(),
                'success_patterns': []
            }

    def classify_inbox_item(self, description: str, user_id: Optional[int] = None) -> Dict:
        """
        Clasifica automáticamente un elemento del inbox.
        Retorna sugerencias de contexto, prioridad y etiquetas.
        """
        description_lower = description.lower()

        # Análisis de contexto
        context = self._classify_context(description_lower)

        # Análisis de prioridad
        priority = self._classify_priority(description_lower)

        # Extracción de etiquetas
        tags = self._extract_tags(description_lower)

        # Análisis de tiempo requerido
        time_estimate = self._estimate_time(description_lower)

        # Análisis de energía requerida
        energy_level = self._classify_energy(description_lower)

        # Sugerencia de fecha límite
        due_date_suggestion = self._suggest_due_date(description_lower)

        # Aprendizaje personalizado
        if user_id and user_id in self.learning_data['user_patterns']:
            user_patterns = self.learning_data['user_patterns'][user_id]
            context = self._refine_with_user_patterns(context, user_patterns)
            priority = self._refine_with_user_patterns(priority, user_patterns)

        return {
            'context': context,
            'priority': priority,
            'tags': tags,
            'time_estimate': time_estimate,
            'energy_level': energy_level,
            'due_date_suggestion': due_date_suggestion,
            'confidence': self._calculate_confidence(description_lower)
        }

    def _classify_context(self, text: str) -> str:
        """Clasifica el contexto de una tarea."""
        context_scores = {}

        for context, keywords in self.patterns['keywords'].items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    score += 1
            if score > 0:
                context_scores[context] = score

        if not context_scores:
            return 'trabajo'  # Contexto por defecto

        # Encontrar el contexto con más coincidencias
        best_context = max(context_scores, key=context_scores.get)

        # Mapear contextos a las opciones disponibles
        context_mapping = {
            'meeting': 'trabajo',
            'email': 'computadora',
            'communication': 'teléfono',
            'research': 'computadora',
            'planning': 'trabajo',
            'errands': 'recados',
            'home': 'casa',
            'computer': 'computadora'
        }

        return context_mapping.get(best_context, 'trabajo')

    def _classify_priority(self, text: str) -> str:
        """Clasifica la prioridad de una tarea."""
        if any(word in text for word in self.patterns['keywords']['urgent']):
            return 'alta'

        # Buscar indicadores de prioridad media
        medium_indicators = ['importante', 'pronto', 'esta semana', 'mañana']
        if any(indicator in text for indicator in medium_indicators):
            return 'media'

        return 'baja'

    def _extract_tags(self, text: str) -> List[str]:
        """Extrae etiquetas relevantes del texto."""
        tags = []
        for category, keywords in self.patterns['keywords'].items():
            for keyword in keywords:
                if keyword in text and category not in ['urgent', 'waiting']:
                    tags.append(category)

        # Eliminar duplicados y limitar a 5 etiquetas
        return list(set(tags))[:5]

    def _estimate_time(self, text: str) -> str:
        """Estima el tiempo requerido para completar la tarea."""
        time_patterns = {
            '5_minutos': ['rápido', '5 minutos', 'minutos', 'breve'],
            '15_minutos': ['15 minutos', 'corto', 'rápido'],
            '30_minutos': ['30 minutos', 'media hora'],
            '1_hora': ['1 hora', 'hora'],
            '2_horas': ['2 horas', 'pocas horas'],
            'medio_dia': ['medio día', 'mañana', 'tarde'],
            'dia_completo': ['día completo', 'todo el día', 'jornada']
        }

        for time_category, patterns in time_patterns.items():
            if any(pattern in text for pattern in patterns):
                return time_category

        return '30_minutos'  # Estimación por defecto

    def _classify_energy(self, text: str) -> str:
        """Clasifica el nivel de energía requerido."""
        high_energy = ['creativo', 'innovar', 'diseñar', 'planear', 'estratégico']
        low_energy = ['revisar', 'responder', 'archivar', 'organizar', 'rutina']

        if any(word in text for word in high_energy):
            return 'alta'
        elif any(word in text for word in low_energy):
            return 'baja'

        return 'media'

    def _suggest_due_date(self, text: str) -> Optional[datetime]:
        """Sugiere una fecha límite basada en el texto."""
        today = timezone.now().date()

        if 'hoy' in text:
            return today
        elif 'mañana' in text:
            return today + timedelta(days=1)
        elif 'esta semana' in text:
            days_to_friday = (4 - today.weekday()) % 7
            return today + timedelta(days=days_to_friday)
        elif 'próxima semana' in text:
            days_to_next_monday = (7 - today.weekday()) % 7
            return today + timedelta(days=days_to_next_monday + 7)
        elif 'este mes' in text:
            # Último día del mes actual
            next_month = today.replace(day=28) + timedelta(days=4)
            return next_month - timedelta(days=next_month.day - 1)

        return None

    def _refine_with_user_patterns(self, current_value: str, user_patterns: Dict) -> str:
        """Refina la clasificación usando patrones de aprendizaje del usuario."""
        # Si el usuario tiene preferencias claras, usarlas
        if user_patterns['contexts'] or user_patterns['priorities']:
            # Por simplicidad, usar el patrón más frecuente del usuario
            if user_patterns['contexts']:
                most_common_context = user_patterns['contexts'].most_common(1)[0][0]
                return most_common_context

        return current_value

    def _calculate_confidence(self, text: str) -> float:
        """Calcula el nivel de confianza de la clasificación."""
        confidence = 0.5  # Confianza base

        # Aumentar confianza si hay palabras clave claras
        keyword_matches = 0
        for keywords in self.patterns['keywords'].values():
            for keyword in keywords:
                if keyword in text:
                    keyword_matches += 1

        confidence += min(keyword_matches * 0.1, 0.4)  # Máximo +0.4

        # Aumentar confianza si el texto es específico
        if len(text.split()) > 5:
            confidence += 0.1

        return min(confidence, 1.0)  # Máximo 1.0

    def learn_from_task(self, task: Task, user_id: int):
        """Aprende de una tarea completada para mejorar futuras clasificaciones."""
        try:
            # Extraer palabras clave del título y descripción
            text = f"{task.title} {task.description or ''}".lower()
            keywords = []

            for category, keyword_list in self.patterns['keywords'].items():
                for keyword in keyword_list:
                    if keyword in text:
                        keywords.append(keyword)

            # Crear entrada de aprendizaje
            learning_entry = GTDLearningEntry.objects.create(
                user_id=user_id,
                context=task.context,
                priority=task.priority,
                metadata=json.dumps({
                    'keywords': keywords,
                    'task_id': task.id,
                    'completed_at': timezone.now().isoformat()
                })
            )

            # Actualizar datos de aprendizaje en memoria
            if user_id not in self.learning_data['user_patterns']:
                self.learning_data['user_patterns'][user_id] = {
                    'contexts': Counter(),
                    'priorities': Counter(),
                    'keywords': Counter()
                }

            self.learning_data['user_patterns'][user_id]['contexts'][task.context] += 1
            self.learning_data['user_patterns'][user_id]['priorities'][task.priority] += 1

            for keyword in keywords:
                self.learning_data['user_patterns'][user_id]['keywords'][keyword] += 1

        except Exception as e:
            print(f"Error learning from task: {e}")

    def get_productivity_insights(self, user_id: int) -> Dict:
        """Proporciona insights de productividad basados en patrones."""
        if user_id not in self.learning_data['user_patterns']:
            return {
                'most_used_context': 'trabajo',
                'most_used_priority': 'media',
                'productivity_score': 0,
                'suggestions': ['Completa más tareas para obtener insights personalizados']
            }

        user_patterns = self.learning_data['user_patterns'][user_id]

        # Calcular contexto más usado
        most_used_context = 'trabajo'
        if user_patterns['contexts']:
            most_used_context = user_patterns['contexts'].most_common(1)[0][0]

        # Calcular prioridad más usada
        most_used_priority = 'media'
        if user_patterns['priorities']:
            most_used_priority = user_patterns['priorities'].most_common(1)[0][0]

        # Calcular puntuación de productividad (simple)
        total_tasks = sum(user_patterns['contexts'].values())
        productivity_score = min(total_tasks * 5, 100)  # Máximo 100

        # Generar sugerencias
        suggestions = []
        if most_used_context == 'trabajo' and user_patterns['contexts']['casa'] == 0:
            suggestions.append('Considera equilibrar trabajo y vida personal')

        if most_used_priority == 'alta' and user_patterns['priorities']['alta'] > total_tasks * 0.7:
            suggestions.append('Muchas tareas de alta prioridad - considera delegar algunas')

        return {
            'most_used_context': most_used_context,
            'most_used_priority': most_used_priority,
            'productivity_score': productivity_score,
            'suggestions': suggestions
        }


# Instancia global del motor GTD
gtd_engine = GTDAutomationEngine()


def process_inbox_item_automatically(inbox_item: InboxItem, user_id: int) -> Dict:
    """
    Procesa automáticamente un elemento del inbox usando el motor GTD.
    """
    classification = gtd_engine.classify_inbox_item(inbox_item.description, user_id)

    return {
        'inbox_item': inbox_item,
        'classification': classification,
        'suggested_action': 'create_task' if classification['confidence'] > 0.6 else 'review_required'
    }


def suggest_next_actions(user_id: int) -> List[Dict]:
    """
    Sugiere próximas acciones basadas en el contexto actual del usuario.
    """
    try:
        # Obtener tareas pendientes ordenadas por prioridad y contexto
        tasks = Task.objects.filter(
            status__in=['pending', 'in_progress'],
            user_id=user_id
        ).order_by('-priority', 'created_at')[:10]

        suggestions = []

        for task in tasks:
            suggestion = {
                'task': task,
                'reason': '',
                'urgency': 'medium'
            }

            # Determinar razón de la sugerencia
            if task.priority == 'high':
                suggestion['reason'] = 'Alta prioridad'
                suggestion['urgency'] = 'high'
            elif task.context == 'work' and timezone.now().hour < 12:
                suggestion['reason'] = 'Contexto de trabajo - mañana'
                suggestion['urgency'] = 'medium'
            elif task.due_date and task.due_date <= timezone.now().date() + timedelta(days=1):
                suggestion['reason'] = 'Fecha límite próxima'
                suggestion['urgency'] = 'high'
            else:
                suggestion['reason'] = 'Próxima en la lista'
                suggestion['urgency'] = 'low'

            suggestions.append(suggestion)

        return suggestions

    except Exception as e:
        print(f"Error suggesting next actions: {e}")
        return []


def generate_weekly_review_data(user_id: int) -> Dict:
    """
    Genera datos para la revisión semanal GTD.
    """
    try:
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)

        # Estadísticas de la semana
        tasks_completed = Task.objects.filter(
            user_id=user_id,
            status='done',
            updated_at__range=[start_date, end_date]
        ).count()

        tasks_created = Task.objects.filter(
            user_id=user_id,
            created_at__range=[start_date, end_date]
        ).count()

        # Contextos más usados
        contexts_used = Task.objects.filter(
            user_id=user_id,
            created_at__range=[start_date, end_date]
        ).values('context').annotate(count=Count('context')).order_by('-count')

        # Proyectos activos
        active_projects = Project.objects.filter(
            user_id=user_id,
            status='active'
        ).count()

        # Insights del motor GTD
        insights = gtd_engine.get_productivity_insights(user_id)

        return {
            'period': f"{start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')}",
            'tasks_completed': tasks_completed,
            'tasks_created': tasks_created,
            'contexts_used': list(contexts_used[:5]),
            'active_projects': active_projects,
            'productivity_score': insights['productivity_score'],
            'most_used_context': insights['most_used_context'],
            'most_used_priority': insights['most_used_priority'],
            'suggestions': insights['suggestions']
        }

    except Exception as e:
        print(f"Error generating weekly review: {e}")
        return {
            'period': 'Esta semana',
            'tasks_completed': 0,
            'tasks_created': 0,
            'contexts_used': [],
            'active_projects': 0,
            'productivity_score': 0,
            'most_used_context': 'trabajo',
            'most_used_priority': 'media',
            'suggestions': ['Error al generar revisión semanal']
        }