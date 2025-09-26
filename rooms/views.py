# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from .models import Room, Comment, Evaluation, EntranceExit, Portal, RoomObject, PlayerProfile
from .forms import RoomForm, EvaluationForm, EntranceExitForm, PortalForm
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from rest_framework.decorators import api_view
from .exceptions import RoomManagerError
from django.http import Http404
from django.db.models import Q  # Import for search functionality
from django.utils import timezone
from datetime import timedelta

# Ensure Room refers to the model, not overridden
from .models import Room  # Ensure this import is not shadowed

@login_required
def lobby(request):
    # Secciones dinámicas
    sections = [
        {
            'title': 'Recent Rooms',
            'url_name': 'rooms:room_list',
            'detail_url_name': 'rooms:room_detail',
            'icon': 'bi-house',
            'items': Room.objects.all().order_by('-created_at')[:5]
        },
        # Puedes agregar más secciones aquí si lo necesitas
    ]

    # Estadísticas rápidas
    stats = [
        {
            'title': 'Total Rooms',
            'value': Room.objects.count(),
            'icon': 'bi-house-door',
            'trend': 12,
            'trend_color': 'success',
            'period': 'This month'
        },
        # Puedes agregar más estadísticas aquí si lo necesitas
    ]

    # Filtros rápidos para la búsqueda
    quick_filters = ['Available', 'Recently Added', 'Popular']

    # Actividad reciente
    recent_activities = get_recent_activities()

    context = {
        'page_title': 'Lobby',
        'sections': sections,
        'stats': stats,
        'quick_filters': quick_filters,
        'recent_activities': recent_activities,
    }
    return render(request, 'rooms/lobby.html', context)

@login_required
def register_presence(request):
    """Registra la presencia del usuario como disponible y lo ingresa a una habitación inicial"""
    player_profile, created = PlayerProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'energy': 100,
            'productivity': 50,
            'social': 50,
            'position_x': 0,
            'position_y': 0
        }
    )

    # Cambiar estado a disponible
    player_profile.state = 'AVAILABLE'
    player_profile.energy = 100  # Resetear energía al registrarse

    # Encontrar habitación inicial (primera habitación pública disponible)
    initial_room = Room.objects.filter(permissions='public').first()
    if not initial_room:
        # Si no hay habitaciones públicas, crear una habitación de lobby por defecto
        initial_room, room_created = Room.objects.get_or_create(
            name='Lobby Principal',
            defaults={
                'description': 'Habitación principal para nuevos usuarios',
                'owner': request.user,
                'permissions': 'public',
                'room_type': 'LOUNGE'
            }
        )

    player_profile.current_room = initial_room
    player_profile.save()

    messages.success(request, f'Te has registrado como disponible y entrado al {initial_room.name}')
    return redirect('rooms:room_detail', pk=initial_room.pk)

# Vista para crear una nueva sala
@login_required
def create_room(request):
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            room = form.save(commit=False)
            room.owner = request.user
            room.creator = request.user
            room.save()
            messages.success(request, 'Sala creada con éxito')
            cache.set('room_{}'.format(room.pk), room)
            return HttpResponseRedirect(reverse_lazy('lobby'))  # Redirect to the lobby
    else:
        form = RoomForm()
    context = {
        'form': form,
        'page_title': 'Crear Nueva Habitación',
        'is_edit': False
    }

    return render(request, 'rooms/room_form.html', context)

# Vista para mostrar los detalles de una sala
def room_detail(request, pk):
    try:
        logger.debug(f"Fetching details for room with ID {pk}.")
        room = get_object_or_404(Room, pk=pk)
        logger.debug(f"Room with ID {pk} found: {room.name}.")
        try:
            room_image_url = room.image.url if room.image and room.image.name else None
        except ValueError as e:
            logger.warning(f"Room with ID {pk} has no associated image: {str(e)}")
            room_image_url = None  # Set to None if no image is associated

        # Use a default image if no image is available
        if not room_image_url:
            room_image_url = '/static/images/default-room.jpg'  # Path to the default image

        # Debugging URL generation
        detail_url = reverse_lazy('rooms:room_detail', kwargs={'pk': pk})
        logger.debug(f"Generated URL for room_detail: {detail_url}")

        # Verificar si la sala tiene entradas/salidas y portales asociados
        entrance_exits = room.entrance_exits.all() if hasattr(room, 'entrance_exits') else []  # Manejar caso sin relación
        portals = room.portals.all() if hasattr(room, 'portals') else []  # Updated to use 'portals' attribute

        if request.method == 'POST':
            if 'create_entrance_exit' in request.POST:
                form = EntranceExitForm(request.POST)
                if form.is_valid():
                    entrance_exit = form.save(commit=False)
                    entrance_exit.room = room
                    entrance_exit.save()
                    messages.success(request, 'Entrada/Salida creada con éxito')
                    return HttpResponseRedirect(reverse_lazy('rooms:room_detail', kwargs={'pk': pk}))
            elif 'create_portal' in request.POST:
                form = PortalForm(request.POST)
                if form.is_valid():
                    portal = form.save(commit=False)
                    portal.room = room
                    portal.save()
                    messages.success(request, 'Portal creado con éxito')
                    return HttpResponseRedirect(reverse_lazy('rooms:room_detail', kwargs={'pk': pk}))
            elif 'enter_room' in request.POST:
                room_id = request.POST['room_id']
                return HttpResponseRedirect(reverse_lazy('rooms:room_detail', kwargs={'pk': room_id}))

        entrance_exit_form = EntranceExitForm()
        portal_form = PortalForm()

        logger.debug("Rendering the room_detail view with the prepared context.")
        # Asegurarse de que los datos se pasen correctamente al contexto
        return render(request, 'rooms/room_detail.html', {
            'page_title': 'Room Details',
            'room': room,
            'room_image_url': room_image_url,  # Pass the image URL (default or actual)
            'entrance_exits': entrance_exits,  # Confirmar que contiene datos
            'portals': portals,  # Confirmar que contiene datos
            'entrance_exit_form': entrance_exit_form,
            'portal_form': portal_form
        })
    except Http404:
        logger.warning(f"Room with ID {pk} not found in the database.")
        return JsonResponse({'detail': 'No Room matches the given query.'}, status=404)
    except Exception as e:
        logger.error(f"Unexpected error in room_detail: {str(e)}", exc_info=True)
        return JsonResponse({'detail': 'An unexpected error occurred.'}, status=500)

# Vista para renderizar habitación en 3D
def room_3d_view(request, pk):
    """
    Vista para mostrar una habitación renderizada en 3D isométrico
    """
    room = get_object_or_404(Room, pk=pk)

    # Generar SVG del renderizado 3D
    svg_content = generate_room_3d_svg(room)

    context = {
        'room': room,
        'svg_content': svg_content,
        'page_title': f'Vista 3D - {room.name}'
    }

    return render(request, 'rooms/room_3d.html', context)

@login_required
def edit_room(request, pk):
    """Vista para editar una habitación existente"""
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"=== INICIO EDIT_ROOM: pk={pk}, user={request.user.username}, method={request.method} ===")

    try:
        room = get_object_or_404(Room, pk=pk)
        logger.info(f"Room encontrada: {room.name} (owner: {room.owner.username})")
    except Exception as e:
        logger.error(f"Error obteniendo room: {e}")
        raise

    # Verificar permisos - solo el owner o administradores pueden editar
    has_permission = request.user == room.owner or request.user in room.administrators.all()
    logger.info(f"Permisos: user={request.user.username}, owner={room.owner.username}, administrators={[admin.username for admin in room.administrators.all()]}, has_permission={has_permission}")

    if not has_permission:
        logger.warning(f"Usuario {request.user.username} no tiene permisos para editar room {room.name}")
        messages.error(request, 'No tienes permisos para editar esta habitación.')
        return redirect('rooms:room_detail', pk=pk)

    if request.method == 'POST':
        logger.info("=== PROCESANDO POST REQUEST ===")
        logger.info(f"POST data keys: {list(request.POST.keys())}")
        logger.info(f"FILES data keys: {list(request.FILES.keys())}")

        try:
            form = RoomForm(request.POST, request.FILES, instance=room, user=request.user)
            logger.info(f"Formulario creado. Campos: {list(form.fields.keys())}")
            logger.info(f"Formulario inicial válido: {form.is_bound and not form.errors}")

            # Verificar validación del formulario
            is_valid = form.is_valid()
            logger.info(f"form.is_valid(): {is_valid}")

            if not is_valid:
                logger.error("=== ERRORES DE VALIDACIÓN ===")
                logger.error(f"form.errors: {dict(form.errors)}")
                logger.error(f"form.non_field_errors: {form.non_field_errors()}")

                # Log detallado de cada campo con error
                for field_name, field_errors in form.errors.items():
                    logger.error(f"Campo '{field_name}': {field_errors}")
                    if field_name in form.fields:
                        field_value = form.data.get(field_name, 'NO_VALUE')
                        logger.error(f"  Valor enviado: {field_value}")
                        logger.error(f"  Tipo de campo: {type(form.fields[field_name])}")

            if is_valid:
                logger.info("=== INTENTANDO GUARDAR ===")
                try:
                    # Intentar guardar sin commit primero para ver si hay errores de modelo
                    room_instance = form.save(commit=False)
                    logger.info(f"save(commit=False) exitoso. Room instance: {room_instance}")

                    # Verificar campos del modelo antes de guardar
                    logger.info("=== VERIFICANDO CAMPOS DEL MODELO ===")
                    for field in room_instance._meta.fields:
                        value = getattr(room_instance, field.name, None)
                        logger.info(f"  {field.name}: {value} (tipo: {type(value)})")

                    # Ahora guardar realmente
                    room_saved = form.save()
                    logger.info(f"form.save() exitoso. Room guardada: {room_saved.name}")

                    # Limpiar cache si existe
                    from django.core.cache import cache
                    cache_key = f'room_{room_saved.pk}'
                    cache.delete(cache_key)
                    logger.info(f"Cache limpiado para key: {cache_key}")

                    messages.success(request, f'Habitación "{room_saved.name}" actualizada exitosamente.')
                    logger.info("=== REDIRECCIÓN EXITOSA ===")
                    return redirect('rooms:room_detail', pk=pk)

                except Exception as save_error:
                    logger.error(f"=== ERROR DURANTE GUARDADO ===")
                    logger.error(f"Error: {save_error}")
                    logger.error(f"Error type: {type(save_error)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")

                    # Agregar error al formulario para mostrar al usuario
                    form.add_error(None, f"Error al guardar: {str(save_error)}")

            else:
                logger.warning("Formulario no válido, mostrando errores al usuario")

        except Exception as form_error:
            logger.error(f"=== ERROR CREANDO FORMULARIO ===")
            logger.error(f"Error: {form_error}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            form = RoomForm(instance=room, user=request.user)

    else:
        logger.info("=== CREANDO FORMULARIO GET ===")
        form = RoomForm(instance=room, user=request.user)
        logger.info(f"Formulario GET creado exitosamente")

    context = {
        'form': form,
        'room': room,
        'page_title': f'Editar - {room.name}',
        'is_edit': True,
        'room_count': Room.objects.count(),
        'active_rooms': Room.objects.filter(is_active=True).count()
    }

    logger.info(f"=== RENDERIZANDO TEMPLATE: rooms/room_edit_alerts.html ===")
    return render(request, 'rooms/room_edit_alerts.html', context)

# Vista para agregar comentarios a una sala
def room_comments(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        comment = request.POST['comment']
        room.comments.create(text=comment, user=request.user)
        messages.success(request, 'Comentario agregado con éxito')
        return HttpResponseRedirect(reverse_lazy('rooms:room_detail', kwargs={'pk': pk}))
    # Asegurarse de que la plantilla 'rooms/room_comments.html' exista
    return render(request, 'rooms/room_comments.html', {'room': room})

# Vista para agregar evaluaciones a una sala
def room_evaluations(request, pk):
    room = get_object_or_404(Room, pk=pk)
    evaluation_form = EvaluationForm()
    if request.method == 'POST':
        evaluation_form = EvaluationForm(request.POST)
        if evaluation_form.is_valid():
            evaluation = evaluation_form.save(commit=False)
            evaluation.user = request.user
            evaluation.room = room
            evaluation.save()
            messages.success(request, 'Evaluación agregada con éxito')
            return HttpResponseRedirect(reverse_lazy('rooms:room_detail', kwargs={'pk': pk}))
    # Asegurarse de que la plantilla 'rooms/room_evaluations.html' exista
    return render(request, 'rooms/room_evaluations.html', {'room': room, 'evaluation_form': evaluation_form})

# Vista para crear una nueva entrada/salida
@login_required
def create_entrance_exit(request):
    if request.method == 'POST':
        form = EntranceExitForm(request.POST)
        if form.is_valid():
            entrance_exit = form.save(commit=False)
            entrance_exit.save()
            messages.success(request, 'Entrada/Salida creada con éxito')
            return HttpResponseRedirect(reverse_lazy('entrance_exit_list'))
    else:
        form = EntranceExitForm()
    return render(request, 'create_entrance_exit.html', {'form': form})

# Vista para mostrar la lista de entradas/salidas
def entrance_exit_list(request):
    entrance_exits = EntranceExit.objects.all()
    return render(request, 'rooms/entrance_exit_list.html', {'entrance_exits': entrance_exits})  # Updated path

# Vista para mostrar los detalles de una entrada/salida
def entrance_exit_detail(request, pk):
    entrance_exit = get_object_or_404(EntranceExit, pk=pk)
    return render(request, 'rooms/entrance_exit_detail.html', {'entrance_exit': entrance_exit})  # Asegúrate de que esta plantilla exista

# Vista para crear un nuevo portal
@login_required
def create_portal(request):
    if request.method == 'POST':
        form = PortalForm(request.POST)
        if form.is_valid():
            portal = form.save(commit=False)
            portal.last_used = timezone.now()  # Establecer la fecha de último uso
            portal.save()
            messages.success(request, 'Portal creado con éxito')
            return HttpResponseRedirect(reverse_lazy('portal_list'))
    else:
        form = PortalForm()
    
    return render(request, 'rooms/portal_create.html', {
        'form': form,
        'page_title': 'Crear Nuevo Portal'
    })

# Vista para mostrar la lista de portales
def portal_list(request):
    portals = Portal.objects.all()
    return render(request, 'rooms/portal_list.html', {'portals': portals})

# Vista para mostrar los detalles de un portal
def portal_detail(request, pk):
    portal = get_object_or_404(Portal, pk=pk)
    return render(request, 'rooms/portal_detail.html', {'portal': portal})

# Vista para mostrar la lista de portales
def portal_list(request):
    portals = Portal.objects.all()
    return render(request, 'rooms/portal_list.html', {'portals': portals})

# Vista para mostrar los detalles de un portal
def portal_detail(request, pk):
    portal = get_object_or_404(Portal, pk=pk)
    return render(request, 'rooms/portal_detail.html', {'portal': portal})

# Vista para mostrar la lista de salas
def room_list(request):
    logger.debug("Fetching all rooms from the database.")
    # Verificar si la sesión está activa
    if not request.user.is_authenticated:
        logger.warning("User not authenticated. Redirecting to login.")
        return redirect('login')    
    
    page_title = 'Lista de Salas'
    rooms = Room.objects.all()  # Obtener todas las salas desde la base de datos
    # Verificar si hay salas disponibles
    if not rooms.exists():
        logger.warning("No rooms found in the database.")
        messages.info(request, 'No hay salas disponibles en este momento.')
    else:
        logger.debug(f"Rooms count: {rooms.count()}")
        
    return render(request, 'rooms/room_list.html', {
        'page_title': page_title,
        'rooms': rooms,  # Pasar las salas al contexto
    })

@api_view(['GET'])
def room_search(request):
    query = request.GET.get('q', '')
    rooms = Room.objects.filter(Q(name__icontains=query) | Q(description__icontains=query))
    return render(request, 'rooms/room_search.html', {'rooms': rooms, 'query': query})

import json
import logging
import requests
import math
from requests.adapters import HTTPAdapter, Retry
from django.conf import settings
from django.db import transaction
from django.db.models import Exists, OuterRef, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.generics import ListCreateAPIView
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from .models import Message, Room, RoomMember, Outbox, CDC
from .serializers import MessageSerializer, RoomSearchSerializer, RoomSerializer, RoomMemberSerializer

logger = logging.getLogger(__name__)

def process_message_command(content, user):
    """Procesa comandos enviados como mensajes"""
    if not content.startswith('/'):
        return None

    command = content[1:].strip().lower().split()
    if not command:
        return None

    cmd = command[0]
    args = command[1:]

    try:
        player = user.player_profile
    except PlayerProfile.DoesNotExist:
        return "No tienes un perfil de jugador. Regístrate primero."

    if cmd == 'work':
        player.state = 'WORKING'
        player.productivity += 5
        player.energy -= 10
        player.save()
        return f"Has empezado a trabajar. Productividad: {player.productivity}, Energía: {player.energy}"

    elif cmd == 'rest':
        player.state = 'RESTING'
        player.energy = min(100, player.energy + 20)
        player.save()
        return f"Estás descansando. Energía: {player.energy}"

    elif cmd == 'social':
        player.state = 'SOCIALIZING'
        player.social += 5
        player.energy -= 5
        player.save()
        return f"Estás socializando. Social: {player.social}, Energía: {player.energy}"

    elif cmd == 'disconnect':
        player.state = 'DISCONNECTED'
        player.save()
        return "Te has desconectado."

    elif cmd == 'move' and args:
        direction = args[0].upper()
        success = player.move_to_room(direction)
        if success:
            return f"Te has movido al {direction} hacia {player.current_room.name}"
        else:
            return "No puedes moverte en esa dirección."

    elif cmd == 'status':
        return f"Estado: {player.get_state_display()}, Energía: {player.energy}, Productividad: {player.productivity}, Social: {player.social}"

    else:
        return f"Comando desconocido: {cmd}. Comandos disponibles: /work, /rest, /social, /disconnect, /move <direction>, /status"


def project_isometric(x, y, z, scale=10):
    """
    Proyecta coordenadas 3D a 2D usando proyección isométrica (perspectiva caballero)
    """
    # Ángulos isométricos: 30 grados
    cos30 = math.cos(math.radians(30))
    sin30 = math.sin(math.radians(30))

    # Proyección isométrica
    screen_x = (x - y) * cos30 * scale
    screen_y = ((x + y) * sin30 - z) * scale

    return screen_x, screen_y


def generate_room_3d_svg(room, canvas_width=800, canvas_height=600):
    """
    Genera SVG para renderizar una habitación en 3D isométrico
    """
    scale = 8  # Escala para ajustar el tamaño

    # Calcular el centro del canvas
    center_x = canvas_width // 2
    center_y = canvas_height // 2

    # Proyectar los 8 vértices del cuboide
    vertices = []
    for dx in [0, room.length]:
        for dy in [0, room.width]:
            for dz in [0, room.height]:
                x, y = project_isometric(dx, dy, dz, scale)
                vertices.append((x, y))

    # Ajustar posición al centro del canvas
    min_x = min(v[0] for v in vertices)
    max_x = max(v[0] for v in vertices)
    min_y = min(v[1] for v in vertices)
    max_y = max(v[1] for v in vertices)

    offset_x = center_x - (min_x + max_x) // 2
    offset_y = center_y - (min_y + max_y) // 2

    # Aplicar offset
    vertices = [(x + offset_x, y + offset_y) for x, y in vertices]

    # Definir las caras del cuboide (índices de vértices)
    faces = [
        # Frente (z=0)
        [0, 1, 3, 2],
        # Derecha (y=width)
        [1, 5, 7, 3],
        # Atrás (x=length)
        [4, 5, 7, 6],
        # Izquierda (y=0)
        [0, 2, 6, 4],
        # Superior (z=height)
        [2, 3, 7, 6],
        # Inferior (z=0, pero desde arriba)
        [0, 1, 5, 4]
    ]

    # Usar colores del objeto habitación con variaciones para cada cara
    base_color = room.color_primary
    accent_color = room.color_secondary

    # Crear variaciones de color para diferentes caras
    colors = [
        base_color,  # Frente
        accent_color,  # Derecha
        base_color,  # Atrás
        accent_color,  # Izquierda
        base_color,  # Superior
        accent_color,  # Inferior
    ]

    svg_parts = []
    svg_parts.append(f'<svg width="{canvas_width}" height="{canvas_height}" xmlns="http://www.w3.org/2000/svg">')

    # Dibujar fondo
    svg_parts.append(f'<rect width="100%" height="100%" fill="#f5f5f5"/>')

    # Dibujar caras (ordenadas por profundidad para efecto 3D)
    for i, face_indices in enumerate(faces):
        points = []
        for idx in face_indices:
            vx, vy = vertices[idx]
            points.append(f"{vx},{vy}")
        points_str = " ".join(points)

        svg_parts.append(f'<polygon points="{points_str}" fill="{colors[i]}" stroke="#1976d2" stroke-width="1"/>')

    # Dibujar aristas
    edges = [
        (0, 1), (1, 3), (3, 2), (2, 0),  # Base inferior
        (4, 5), (5, 7), (7, 6), (6, 4),  # Base superior
        (0, 4), (1, 5), (2, 6), (3, 7)   # Aristas verticales
    ]

    for edge in edges:
        x1, y1 = vertices[edge[0]]
        x2, y2 = vertices[edge[1]]
        svg_parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#0d47a1" stroke-width="2"/>')

    # Agregar texto con información de la habitación
    svg_parts.append(f'<text x="20" y="30" font-family="Arial" font-size="16" fill="#000">Habitación: {room.name}</text>')
    svg_parts.append(f'<text x="20" y="50" font-family="Arial" font-size="12" fill="#666">Dimensiones: {room.length}×{room.width}×{room.height}</text>')
    svg_parts.append(f'<text x="20" y="70" font-family="Arial" font-size="12" fill="#666">Posición: ({room.x}, {room.y}, {room.z})</text>')

    svg_parts.append('</svg>')

    return '\n'.join(svg_parts)

class RoomListViewSet(ListModelMixin, GenericViewSet):
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.request.user.pk
        logger.debug(f"Fetching rooms for user_id: {user_id}")
        queryset = Room.objects.annotate(
            member_count=Count('members__id')  # Changed from 'memberships__id' to 'members__id'
        ).filter(
            members__id=user_id  # Changed from 'memberships__user_id' to 'members__id'
        ).select_related('last_message', 'last_message__user').order_by('-bumped_at')
        logger.debug(f"Queryset: {queryset.query}")
        return queryset


class RoomDetailViewSet(RetrieveModelMixin, GenericViewSet):
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Room.objects.annotate(
            member_count=Count('members')  # Changed from 'memberships' to 'members'
        ).filter(members__id=self.request.user.pk)  # Changed from 'memberships__user_id' to 'members__id'


class RoomSearchViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSearchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        user_membership = RoomMember.objects.filter(
            room=OuterRef('pk'),
            user=user
        )
        return Room.objects.annotate(
            is_member=Exists(user_membership)
        ).order_by('name')


class CentrifugoMixin:
    # A helper method to return the list of channels for all current members of specific room.
    # So that the change in the room may be broadcasted to all the members.
    def get_room_member_channels(self, room_id):
        members = RoomMember.objects.filter(room_id=room_id).values_list('user', flat=True)
        return [f'personal:{user_id}' for user_id in members]

    def broadcast_room(self, room_id, broadcast_payload):
        # Using Centrifugo HTTP API is the simplest way to send real-time message, and usually
        # it provides the best latency. The trade-off here is that error here may result in
        # lost real-time event. Depending on the application requirements this may be fine or not.  
        def broadcast():
            session = requests.Session()
            retries = Retry(total=1, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
            session.mount('http://', HTTPAdapter(max_retries=retries))
            try:
                session.post(
                    settings.CENTRIFUGO_HTTP_API_ENDPOINT + '/api/broadcast',
                    data=json.dumps(broadcast_payload),
                    headers={
                        'Content-type': 'application/json', 
                        'X-API-Key': settings.CENTRIFUGO_HTTP_API_KEY,
                        'X-Centrifugo-Error-Mode': 'transport'
                    }
                )
            except requests.exceptions.RequestException as e:
                logging.error(e)

        if settings.CENTRIFUGO_BROADCAST_MODE == 'api':
            # We need to use on_commit here to not send notification to Centrifugo before
            # changes applied to the database. Since we are inside transaction.atomic block
            # broadcast will happen only after successful transaction commit.
            transaction.on_commit(broadcast)

        elif settings.CENTRIFUGO_BROADCAST_MODE == 'outbox':
            # In outbox case we can set partition for parallel processing, but
            # it must be in predefined range and match Centrifugo PostgreSQL
            # consumer configuration.
            partition = hash(room_id)%settings.CENTRIFUGU_OUTBOX_PARTITIONS
            # Creating outbox object inside transaction will guarantee that Centrifugo will
            # process the command at some point. In normal conditions – almost instantly.
            Outbox.objects.create(method='broadcast', payload=broadcast_payload, partition=partition)

        elif settings.CENTRIFUGO_BROADCAST_MODE == 'cdc':
            # In cdc case Debezium will use this field for setting Kafka partition.
            # We should not prepare proper partition ourselves in this case.
            partition = hash(room_id)
            # Creating outbox object inside transaction will guarantee that Centrifugo will
            # process the command at some point. In normal conditions – almost instantly. In this
            # app Debezium will perform CDC and send outbox events to Kafka, event will be then
            # consumed by Centrifugo. The advantages here is that Debezium reads WAL changes and
            # has a negligible overhead on database performance. And most efficient partitioning.
            # The trade-off is that more hops add more real-time event delivery latency. May be
            # still instant enough though.
            CDC.objects.create(method='broadcast', payload=broadcast_payload, partition=partition)

        elif settings.CENTRIFUGO_BROADCAST_MODE == 'api_cdc':
            if len(broadcast_payload['channels']) <= 1000000:
                # We only use low-latency broadcast over API for not too big rooms, it's possible
                # to adjust as required of course.
                transaction.on_commit(broadcast)

            partition = hash(room_id)
            CDC.objects.create(method='broadcast', payload=broadcast_payload, partition=partition)

        else:
            raise ValueError(f'unknown CENTRIFUGO_BROADCAST_MODE: {settings.CENTRIFUGO_BROADCAST_MODE}')


class MessageListCreateAPIView(ListCreateAPIView, CentrifugoMixin):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        room_id = self.kwargs['room_id']
        get_object_or_404(RoomMember, user=self.request.user, room_id=room_id)
        return Message.objects.filter(
            room_id=room_id).prefetch_related('user', 'room').order_by('-created_at')

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        room_id = self.kwargs['room_id']
        room = Room.objects.select_for_update().get(id=room_id)
        room.increment_version()
        channels = self.get_room_member_channels(room_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(room=room, user=request.user)
        room.last_message = obj
        room.bumped_at = timezone.now()
        room.save()

        # Procesar comandos si el mensaje es un comando
        command_response = process_message_command(obj.content, request.user)
        if command_response:
            # Crear mensaje de sistema con la respuesta del comando
            system_message = Message.objects.create(
                room=room,
                content=command_response,
                message_type='system'
            )
            room.last_message = system_message
            room.save()

            # Broadcast del mensaje de comando
            broadcast_payload = {
                'channels': channels,
                'data': {
                    'type': 'message_added',
                    'body': MessageSerializer(system_message).data
                },
                'idempotency_key': f'message_{system_message.id}'
            }
            self.broadcast_room(room_id, broadcast_payload)

        # Broadcast del mensaje original
        broadcast_payload = {
            'channels': channels,
            'data': {
                'type': 'message_added',
                'body': serializer.data
            },
            'idempotency_key': f'message_{serializer.data["id"]}'
        }
        self.broadcast_room(room_id, broadcast_payload)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class JoinRoomView(APIView, CentrifugoMixin):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, room_id):
        room = Room.objects.select_for_update().get(id=room_id)
        room.increment_version()
        if RoomMember.objects.filter(user=request.user, room=room).exists():
            return Response({"message": "already a member"}, status=status.HTTP_409_CONFLICT)
        obj, _ = RoomMember.objects.get_or_create(user=request.user, room=room)
        channels = self.get_room_member_channels(room_id)
        obj.room.member_count = len(channels)
        body = RoomMemberSerializer(obj).data

        broadcast_payload = {
            'channels': channels,
            'data': {
                'type': 'user_joined',
                'body': body
            },
            'idempotency_key': f'user_joined_{obj.pk}'
        }
        self.broadcast_room(room_id, broadcast_payload)
        return Response(body, status=status.HTTP_200_OK)


class LeaveRoomView(APIView, CentrifugoMixin):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, room_id):
        room = Room.objects.select_for_update().get(id=room_id)
        room.increment_version()
        channels = self.get_room_member_channels(room_id)
        obj = get_object_or_404(RoomMember, user=request.user, room=room)
        obj.room.member_count = len(channels) - 1
        pk = obj.pk
        obj.delete()
        body = RoomMemberSerializer(obj).data

        broadcast_payload = {
            'channels': channels,
            'data': {
                'type': 'user_left',
                'body': body
            },
            'idempotency_key': f'user_left_{pk}'
        }
        self.broadcast_room(room_id, broadcast_payload)
        return Response(body, status=status.HTTP_200_OK)
    
@api_view(['POST'])
def player_move(request, direction):
    player = request.user.player_profile
    success = player.move_to_room(direction)
    return Response({"success": success, "current_room": player.current_room.name})

@api_view(['POST'])
def interact_with_object(request, object_id):
    obj = get_object_or_404(RoomObject, pk=object_id)
    result = obj.interact(request.user.player_profile)
    return Response(result)

@api_view(['GET'])
def room_detail_view(request, pk):
    """
    API view to retrieve details of a specific room.
    """
    try:
        room = get_object_or_404(Room, pk=pk)
        data = {
            'id': room.id,
            'name': room.name,
            'description': room.description,
            'created_at': room.created_at,
            'updated_at': room.updated_at,
        }
        return JsonResponse(data, status=200)
    except Http404:
        logger.warning(f"Room with ID {pk} not found.")
        return JsonResponse({'detail': 'No Room matches the given query.'}, status=404)

def get_recent_activities(limit=5):
    """
    Get recent activities across the system.
    Returns a list of activity dictionaries with user, action, timestamp, icon, and color.
    """
    activities = []
    now = timezone.now()
    past_24h = now - timedelta(hours=24)

    # Get recent room creations
    recent_rooms = Room.objects.filter(
        created_at__gte=past_24h
    ).select_related('creator')[:limit]

    for room in recent_rooms:
        if room.creator:  # Check if creator exists
            activities.append({
                'user': room.creator.username,
                'action': f'created room "{room.name}"',
                'timestamp': room.created_at,
                'icon': 'bi-house-add',
                'color': 'success'
            })

    # Only add portal activities if Portal has created_at field
    if hasattr(Portal, 'created_at'):
        recent_portals = Portal.objects.filter(
            created_at__gte=past_24h
        ).select_related('room')[:limit]

        for portal in recent_portals:
            # Defensive: check if portal.room and portal.room.creator exist
            user = getattr(getattr(portal.room, 'creator', None), 'username', None)
            if user:
                activities.append({
                    'user': user,
                    'action': f'created portal in {portal.room.name}',
                    'timestamp': portal.created_at,
                    'icon': 'bi-door-open',
                    'color': 'info'
                })

    # Sort all activities by timestamp
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    return activities[:limit]
    
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import PlayerProfile, Room, EntranceExit, RoomConnection
from django.http import JsonResponse

@login_required
def navigate_room(request, direction):
    """
    Vista para manejar la navegación entre habitaciones
    """
    player = request.user.player_profile
    
    if not player.current_room:
        return JsonResponse({
            'success': False,
            'message': 'No estás en ninguna habitación actualmente'
        }, status=400)
    
    # Intentar mover al jugador
    success = player.move_to_room(direction)
    
    if success:
        new_room = player.current_room
        entrance = new_room.entrance_exits.filter(face=direction.opposite()).first()
        
        # Obtener información de la nueva habitación
        room_info = {
            'id': new_room.id,
            'name': new_room.name,
            'description': new_room.description,
            'image_url': new_room.get_image_url() or '/static/images/default-room.jpg',
            'connections': get_available_exits(new_room),
            'objects': list(new_room.room_objects.values('id', 'name', 'object_type', 'position_x', 'position_y')),
            'entrance_position': {
                'x': entrance.position_x if entrance else new_room.length // 2,
                'y': entrance.position_y if entrance else new_room.width // 2
            } if entrance else None
        }
        
        return JsonResponse({
            'success': True,
            'message': f'Te has movido a {new_room.name}',
            'room': room_info
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'No hay conexión disponible en esa dirección'
        }, status=400)

def get_available_exits(room):
    """
    Obtiene las salidas disponibles de una habitación
    """
    exits = []
    for entrance in room.entrance_exits.filter(enabled=True):
        if entrance.connection:
            exits.append({
                'direction': entrance.face,
                'to_room': entrance.connection.to_room.name,
                'to_room_id': entrance.connection.to_room.id,
                'energy_cost': entrance.connection.energy_cost
            })
    return exits

@login_required
def room_view(request, room_id=None):
    """Vista principal para mostrar una habitación"""
    player = request.user.player_profile
    
    # Si no se especifica room_id, usar la actual
    room = player.current_room if room_id is None else get_object_or_404(Room, id=room_id)
    
    # Actualizar habitación del jugador si es diferente
    if player.current_room != room:
        player.current_room = room
        player.save()
    
    return JsonResponse({
        'room': {
            'id': room.id,
            'name': room.name,
            'description': room.description,
            'image_url': room.get_image_url() or '/static/default-room.jpg'
        },
        'exits': player.get_available_exits(),
        'player': {
            'energy': player.energy,
            'position': [player.position_x, player.position_y]
        }
    })

@login_required
def navigate(request):
    """Maneja la navegación entre habitaciones"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    player = request.user.player_profile
    exit_type = request.POST.get('exit_type')
    exit_id = request.POST.get('exit_id')
    
    if not exit_type or not exit_id:
        return JsonResponse({'error': 'Faltan parámetros'}, status=400)
    
    if player.use_exit(exit_type, exit_id):
        return JsonResponse({
            'success': True,
            'new_room': {
                'id': player.current_room.id,
                'name': player.current_room.name
            },
            'energy': player.energy,
            'position': [player.position_x, player.position_y]
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'No se puede usar esta salida'
        }, status=400)

@login_required
def room_delete(request, pk):
    """Vista para eliminar una habitación"""
    room = get_object_or_404(Room, pk=pk)

    # Verificar permisos
    if not room.can_user_manage(request.user):
        messages.error(request, 'No tienes permisos para eliminar esta habitación.')
        return redirect('rooms:room_detail', pk=pk)

    if request.method == 'POST':
        room_name = room.name
        room.delete()
        messages.success(request, f'La habitación "{room_name}" ha sido eliminada exitosamente.')
        return redirect('rooms:room_list')

    # Si es GET, mostrar confirmación
    return render(request, 'rooms/room_confirm_delete.html', {'room': room})

@login_required
def create_room_complete(request):
    """Vista para crear una habitación completa con todas las opciones"""
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            room = form.save(commit=False)
            room.owner = request.user
            room.creator = request.user
            room.save()
            messages.success(request, f'Habitación "{room.name}" creada exitosamente.')
            return redirect('rooms:room_detail', pk=room.pk)
    else:
        form = RoomForm(user=request.user)

    context = {
        'form': form,
        'page_title': 'Crear Habitación Completa',
        'is_edit': False,
        'room_count': Room.objects.count(),
        'active_rooms': Room.objects.filter(is_active=True).count()
    }

    return render(request, 'rooms/room_form_complete.html', context)

@login_required
def edit_room_complete(request, pk):
    """Vista para editar una habitación completa con todas las opciones"""
    room = get_object_or_404(Room, pk=pk)

    # Verificar permisos
    if not room.can_user_manage(request.user):
        messages.error(request, 'No tienes permisos para editar esta habitación.')
        return redirect('rooms:room_detail', pk=pk)

    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES, instance=room, user=request.user)
        if form.is_valid():
            room = form.save()
            messages.success(request, f'Habitación "{room.name}" actualizada exitosamente.')
            return redirect('rooms:room_detail', pk=pk)
    else:
        form = RoomForm(instance=room, user=request.user)

    context = {
        'form': form,
        'room': room,
        'page_title': f'Editar Completo - {room.name}',
        'is_edit': True,
        'room_count': Room.objects.count(),
        'active_rooms': Room.objects.filter(is_active=True).count()
    }

    return render(request, 'rooms/room_form_complete.html', context)