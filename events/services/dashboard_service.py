"""
Dashboard Service Module

Este módulo contiene servicios para manejar la lógica del dashboard root
de manera más organizada y mantenible.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q, Count
from django.utils import timezone
from django.conf import settings
import smtplib

from ..models import InboxItem, User

logger = logging.getLogger(__name__)


class RootFilters:
    """Clase para manejar filtros del dashboard root con validación robusta"""

    VALID_STATUS_FILTERS = ['all', 'processed', 'unprocessed']
    VALID_CONTENT_TYPES = ['all', 'email', 'call', 'chat']
    VALID_PRIORITIES = ['all', 'alta', 'media', 'baja']
    VALID_SORT_FIELDS = ['created_at', 'updated_at', 'title', 'priority']
    VALID_SORT_ORDERS = ['asc', 'desc']

    def __init__(self, search_query: str = '', status_filter: str = 'all',
                 user_filter: str = 'all', date_from: str = '', date_to: str = '',
                 content_type: str = 'all', priority_filter: str = 'all',
                 sort_by: str = 'created_at', sort_order: str = 'desc',
                 items_per_page: int = 20, page: int = 1):

        self.search_query = search_query.strip()
        self.status_filter = self._validate_choice(status_filter, self.VALID_STATUS_FILTERS)
        self.user_filter = user_filter
        self.date_from = self._parse_date(date_from)
        self.date_to = self._parse_date(date_to)
        self.content_type = self._validate_choice(content_type, self.VALID_CONTENT_TYPES)
        self.priority_filter = self._validate_choice(priority_filter, self.VALID_PRIORITIES)
        self.sort_by = self._validate_choice(sort_by, self.VALID_SORT_FIELDS)
        self.sort_order = self._validate_choice(sort_order, self.VALID_SORT_ORDERS)
        self.items_per_page = max(1, min(items_per_page, 100))  # Entre 1 y 100
        self.page = max(1, page)

    @classmethod
    def from_request(cls, request) -> 'RootFilters':
        """Crear instancia desde request con validación"""
        try:
            return cls(
                search_query=request.GET.get('search', ''),
                status_filter=request.GET.get('status', 'all'),
                user_filter=request.GET.get('user', 'all'),
                date_from=request.GET.get('date_from', ''),
                date_to=request.GET.get('date_to', ''),
                content_type=request.GET.get('content_type', 'all'),
                priority_filter=request.GET.get('priority', 'all'),
                sort_by=request.GET.get('sort', 'created_at'),
                sort_order=request.GET.get('order', 'desc'),
                items_per_page=int(request.GET.get('per_page', 20)),
                page=int(request.GET.get('page', 1)),
            )
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing filters from request: {e}")
            # Retornar filtros por defecto en caso de error
            return cls()

    def _validate_choice(self, value: str, valid_choices: list) -> str:
        """Validar que el valor esté en las opciones válidas"""
        return value if value in valid_choices else valid_choices[0]

    def _parse_date(self, date_str: str) -> Optional[datetime.date]:
        """Parsear fecha con validación"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            logger.warning(f"Invalid date format: {date_str}")
            return None

    def get_ordering(self) -> str:
        """Obtener string de ordenamiento para Django"""
        field = self.sort_by
        if self.sort_order == 'desc':
            field = f'-{field}'
        return field

    def apply_to_queryset(self, queryset):
        """Aplicar filtros a un queryset de manera optimizada"""

        # Filtro de estado
        if self.status_filter == 'processed':
            queryset = queryset.filter(is_processed=True)
        elif self.status_filter == 'unprocessed':
            queryset = queryset.filter(is_processed=False)

        # Filtro de usuario
        if self.user_filter != 'all':
            queryset = queryset.filter(created_by_id=self.user_filter)

        # Filtros de fecha
        if self.date_from:
            queryset = queryset.filter(created_at__date__gte=self.date_from)
        if self.date_to:
            queryset = queryset.filter(created_at__date__lte=self.date_to)

        # Filtro de tipo de contenido
        if self.content_type != 'all':
            if self.content_type == 'email':
                queryset = queryset.filter(
                    Q(description__icontains='@') | Q(context__icontains='email')
                )
            elif self.content_type == 'call':
                queryset = queryset.filter(
                    Q(title__icontains='llamada') | Q(title__icontains='call')
                )
            elif self.content_type == 'chat':
                queryset = queryset.filter(
                    Q(title__icontains='chat') | Q(context__icontains='chat')
                )

        # Filtro de prioridad
        if self.priority_filter != 'all':
            queryset = queryset.filter(priority=self.priority_filter)

        # Búsqueda global
        if self.search_query:
            queryset = queryset.filter(
                Q(title__icontains=self.search_query) |
                Q(description__icontains=self.search_query) |
                Q(context__icontains=self.search_query) |
                Q(created_by__username__icontains=self.search_query)
            )

        return queryset.order_by(self.get_ordering())


class RootDashboardService:
    """Servicio principal para el dashboard root"""

    def __init__(self, user, request):
        self.user = user
        self.request = request
        self.filters = RootFilters.from_request(request)

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Obtener todos los datos del dashboard de manera optimizada"""

        # Logging para auditoría
        logger.info(f"User {self.user.username} accessing root dashboard with filters: {self.filters.__dict__}")

        return {
            'user_info': self._get_user_info(),
            'profile_info': self._get_profile_info(),
            'player_info': self._get_player_info(),
            'user_role': self._get_user_role(),
            'role_badge_class': self._get_role_badge_class(),
            'cx_email_items': self._get_inbox_items_page(),
            'cx_stats': self._get_inbox_stats(),
            'email_backend_info': self._get_email_backend_info(),
            'all_inbox_items': self._get_all_inbox_items_page(),
            'users_for_filter': self._get_users_for_filter(),
            'current_page': self.filters.page,
            'total_pages': self._get_total_pages(),
            'has_filters': self._has_active_filters(),
            'search_query': self.filters.search_query,
            'status_filter': self.filters.status_filter,
            'user_filter': self.filters.user_filter,
            'date_from': self.filters.date_from.isoformat() if self.filters.date_from else '',
            'date_to': self.filters.date_to.isoformat() if self.filters.date_to else '',
            'content_type': self.filters.content_type,
            'priority_filter': self.filters.priority_filter,
            'sort_by': self.filters.sort_by,
            'sort_order': self.filters.sort_order,
            'items_per_page': self.filters.items_per_page,
        }

    def _get_user_info(self) -> Dict[str, Any]:
        """Obtener información básica del usuario"""
        return {
            'username': self.user.username,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'email': self.user.email,
            'date_joined': self.user.date_joined,
            'last_login': self.user.last_login,
            'is_staff': self.user.is_staff,
            'is_superuser': self.user.is_superuser,
            'is_active': self.user.is_active,
        }

    def _get_profile_info(self) -> Dict[str, Any]:
        """Obtener información del perfil del usuario"""
        profile_info = {}
        if hasattr(self.user, 'profile') and self.user.cv:
            profile_info = {
                'role': getattr(self.user.cv, 'role', None),
                'profession': getattr(self.user.cv, 'profession', None),
                'bio': getattr(self.user.cv, 'bio', None),
            }
        return profile_info

    def _get_user_role(self) -> str:
        """Determinar el rol del usuario para display"""
        if hasattr(self.user, 'profile') and self.user.cv:
            role = getattr(self.user.cv, 'role', None)
            if role == 'SU':
                return 'Super Usuario'
            elif role == 'ADMIN':
                return 'Administrador'
            elif role == 'GTD_ANALYST':
                return 'Analista GTD'
            elif role:
                return f'Usuario {role}'
        return 'Usuario Regular'

    def _get_role_badge_class(self) -> str:
        """Obtener clase CSS para el badge del rol"""
        if hasattr(self.user, 'profile') and self.user.cv:
            role = getattr(self.user.cv, 'role', None)
            if role == 'SU':
                return 'danger'
            elif role == 'ADMIN':
                return 'warning'
            elif role == 'GTD_ANALYST':
                return 'info'
        return 'primary'

    def _get_player_info(self) -> Dict[str, Any]:
        """Obtener información del perfil de jugador"""
        player_info = {}
        if hasattr(self.user, 'player_profile') and self.user.player_profile:
            player_profile = self.user.player_profile
            player_info = {
                'current_room': player_profile.current_room.name if player_profile.current_room else None,
                'energy': player_profile.energy,
                'productivity': player_profile.productivity,
                'social': player_profile.social,
                'position_x': player_profile.position_x,
                'position_y': player_profile.position_y,
            }
        return player_info

    def _get_inbox_items_page(self):
        """Obtener página de items del inbox CX con optimización"""
        cache_key = f"cx_inbox_{self.user.id}_{hash(str(self.filters.__dict__))}"
        cached_data = cache.get(cache_key)

        if cached_data is None:
            # Consulta optimizada
            base_queryset = InboxItem.objects.filter(
                user_context__source='cx_email'
            ).select_related('created_by', 'assigned_to')

            # Aplicar filtros
            filtered_queryset = self.filters.apply_to_queryset(base_queryset)

            # Paginación
            paginator = Paginator(filtered_queryset, self.filters.items_per_page)
            page = paginator.get_page(self.filters.page)

            cached_data = page
            cache.set(cache_key, cached_data, 300)  # 5 minutos

        return cached_data

    def _get_inbox_stats(self) -> Dict[str, int]:
        """Obtener estadísticas del inbox con caché optimizado"""
        cache_key = f"cx_stats_{self.user.id}_{self.filters.user_filter}_{self.filters.date_from}_{self.filters.date_to}"
        stats = cache.get(cache_key)

        if stats is None:
            base_queryset = InboxItem.objects.filter(user_context__source='cx_email')

            # Aplicar filtros relevantes para estadísticas
            if self.filters.user_filter != 'all':
                base_queryset = base_queryset.filter(created_by_id=self.filters.user_filter)
            if self.filters.date_from:
                base_queryset = base_queryset.filter(created_at__date__gte=self.filters.date_from)
            if self.filters.date_to:
                base_queryset = base_queryset.filter(created_at__date__lte=self.filters.date_to)

            stats = base_queryset.aggregate(
                total=Count('id'),
                processed=Count('id', filter=Q(is_processed=True)),
                unprocessed=Count('id', filter=Q(is_processed=False)),
                today=Count('id', filter=Q(created_at__date=timezone.now().date()))
            )

            cache.set(cache_key, stats, 60)  # 1 minuto para estadísticas

        return stats

    def _get_email_backend_info(self) -> Dict[str, Any]:
        """Obtener información del backend de email"""
        info = {
            'backend': getattr(settings, 'EMAIL_BACKEND', 'No configurado'),
            'host': getattr(settings, 'EMAIL_HOST', 'No configurado'),
            'port': getattr(settings, 'EMAIL_PORT', 'No configurado'),
            'use_tls': getattr(settings, 'EMAIL_USE_TLS', False),
            'host_user': getattr(settings, 'EMAIL_HOST_USER', 'No configurado'),
            'reception_enabled': getattr(settings, 'EMAIL_RECEPTION_ENABLED', False),
            'imap_host': getattr(settings, 'EMAIL_IMAP_HOST', 'No configurado'),
            'imap_port': getattr(settings, 'EMAIL_IMAP_PORT', 'No configurado'),
            'cx_domains': getattr(settings, 'CX_EMAIL_DOMAINS', []),
            'cx_keywords': getattr(settings, 'CX_KEYWORDS', []),
        }

        # Probar conectividad SMTP
        smtp_status = 'Desconocido'
        try:
            if info['host'] != 'No configurado' and info['port'] != 'No configurado':
                server = smtplib.SMTP(info['host'], info['port'], timeout=5)
                server.ehlo()
                if info['use_tls']:
                    server.starttls()
                    server.ehlo()
                server.quit()
                smtp_status = 'Conectado'
            else:
                smtp_status = 'No configurado'
        except Exception as e:
            smtp_status = f'Error: {str(e)}'

        info['smtp_status'] = smtp_status
        return info

    def _get_all_inbox_items_page(self):
        """Obtener página de todos los items del inbox"""
        # Similar a CX pero sin filtro de fuente
        base_queryset = InboxItem.objects.select_related('created_by')
        filtered_queryset = self.filters.apply_to_queryset(base_queryset)

        paginator = Paginator(filtered_queryset, self.filters.items_per_page)
        return paginator.get_page(self.filters.page)

    def _get_users_for_filter(self):
        """Obtener usuarios para el filtro con caché"""
        cache_key = 'root_users_for_filter'
        users = cache.get(cache_key)

        if users is None:
            users = User.objects.filter(
                Q(inboxitem__isnull=False) |
                Q(authorized_inbox_items__isnull=False) |
                Q(classified_inbox_items__isnull=False) |
                Q(assigned_inbox_items__isnull=False)
            ).distinct().order_by('username')[:50]
            cache.set(cache_key, users, 1800)  # 30 minutos

        return users

    def _get_total_pages(self) -> int:
        """Obtener número total de páginas"""
        try:
            return self._get_inbox_items_page().paginator.num_pages
        except:
            return 1

    def _has_active_filters(self) -> bool:
        """Verificar si hay filtros activos"""
        return any([
            self.filters.search_query,
            self.filters.status_filter != 'all',
            self.filters.user_filter != 'all',
            self.filters.date_from,
            self.filters.date_to,
            self.filters.content_type != 'all',
            self.filters.priority_filter != 'all'
        ])