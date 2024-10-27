from django.shortcuts import render


# Create your views here.
def lobby(request):
    page_title = 'lobby'
    return render(request, 'lobby/lobby.html', {
        "page_title":page_title,
        })


from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from .models import Room
from .forms import RoomForm
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail

@login_required
def create_room(request):
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            room = form.save(commit=False)
            room.owner = request.user
            room.creator = request.user
            room.save()
            messages.success(request, 'Sala creada con exito')
            cache.set('room_{}'.format(room.pk), room)

            return HttpResponseRedirect(reverse_lazy('room_detail', kwargs={'pk': room.pk}))
    else:
        form = RoomForm()

    return render(request, 'create_room.html', {'form': form})

def room_detail(request, pk):
    room = cache.get('room_{}'.format(pk))
    if room is None:
        room = get_object_or_404(Room, pk=pk)
        cache.set('room_{}'.format(pk), room)
    return render(request, 'room_detail.html', {'room': room})

def room_comments(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        comment = request.POST['comment']
        room.comments.create(text=comment, user=request.user)
        messages.success(request, 'Comentario agregado con exito')
        return HttpResponseRedirect(reverse_lazy('room_detail', kwargs={'pk': pk}))
    return render(request, 'room_comments.html', {'room': room})

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
            messages.success(request, 'Evaluacion agregada con exito')
            return HttpResponseRedirect(reverse_lazy('room_detail', kwargs={'pk': pk}))
    return render(request, 'room_evaluations.html', {'room': room, 'evaluation_form': evaluation_form})