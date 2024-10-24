# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from .models import Room, Comment, Evaluation, EntranceExit, Portal
from .forms import RoomForm, EvaluationForm, EntranceExitForm, PortalForm
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail

# Vista para la página de lobby
@login_required
def lobby(request):
    page_title = 'Lobby'
    rooms = Room.objects.all()
    portals = Portal.objects.all()

    context = {
        'page_title': page_title,
        'rooms': rooms,
        'portals': portals,
    }

    return render(request, 'lobby.html', context)

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
            return HttpResponseRedirect(reverse_lazy('room_detail', kwargs={'pk': room.pk}))
    else:
        form = RoomForm()
    return render(request, 'create_room.html', {'form': form})

# Vista para mostrar los detalles de una sala

def room_detail(request, pk):
    room = get_object_or_404(Room, pk=pk)
    entrance_exits = room.entranceexit_set.all()
    portals = room.portal_set.all()

    if request.method == 'POST':
        if 'create_entrance_exit' in request.POST:
            form = EntranceExitForm(request.POST)
            if form.is_valid():
                entrance_exit = form.save(commit=False)
                entrance_exit.room = room
                entrance_exit.save()
                messages.success(request, 'Entrada/Salida creada con éxito')
                return HttpResponseRedirect(reverse_lazy('room_detail', kwargs={'pk': pk}))
        elif 'create_portal' in request.POST:
            form = PortalForm(request.POST)
            if form.is_valid():
                portal = form.save(commit=False)
                portal.room = room
                portal.save()
                messages.success(request, 'Portal creado con éxito')
                return HttpResponseRedirect(reverse_lazy('room_detail', kwargs={'pk': pk}))
        elif 'enter_room' in request.POST:
            room_id = request.POST['room_id']
            return HttpResponseRedirect(reverse_lazy('room_detail', kwargs={'pk': room_id}))

    entrance_exit_form = EntranceExitForm()
    portal_form = PortalForm()

    return render(request, 'room_detail.html', {
        'page_title': 'Room Details',
        'room': room,
        'entrance_exits': entrance_exits,
        'portals': portals,
        'entrance_exit_form': entrance_exit_form,
        'portal_form': portal_form

    })

# Vista para agregar comentarios a una sala
def room_comments(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        comment = request.POST['comment']
        room.comments.create(text=comment, user=request.user)
        messages.success(request, 'Comentario agregado con éxito')
        return HttpResponseRedirect(reverse_lazy('room_detail', kwargs={'pk': pk}))
    return render(request, 'room_comments.html', {'room': room})

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
            return HttpResponseRedirect(reverse_lazy('room_detail', kwargs={'pk': pk}))
    return render(request, 'room_evaluations.html', {'room': room, 'evaluation_form': evaluation_form})

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
    return render(request, 'entrance_exit_list.html', {'entrance_exits': entrance_exits})

# Vista para mostrar los detalles de una entrada/salida
def entrance_exit_detail(request, pk):
    entrance_exit = get_object_or_404(EntranceExit, pk=pk)
    return render(request, 'entrance_exit_detail.html', {'entrance_exit': entrance_exit})

# Vista para crear un nuevo portal
@login_required
def create_portal(request):
    if request.method == 'POST':
        form = PortalForm(request.POST)
        if form.is_valid():
            portal = form.save(commit=False)
            portal.save()
            messages.success(request, 'Portal creado con éxito')
            return HttpResponseRedirect(reverse_lazy('portal_list'))
    else:
        form = PortalForm()
    return render(request, 'create_portal.html', {'form': form})

# Vista para mostrar la lista de portales
def portal_list(request):
    portals = Portal.objects.all()
    return render(request, 'portal_list.html', {'portals': portals})

# Vista para mostrar los detalles de un portal
def portal_detail(request, pk):
    portal = get_object_or_404(Portal, pk=pk)
    return render(request, 'portal_detail.html', {'portal': portal})


def room_list(request):
    page_title = 'Room List'
    rooms = Room.objects.all()
    return render(request, 'room_list.html', {
        'page_title': page_title,
        'rooms': rooms,
        
        })