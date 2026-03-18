from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .models import Game
from . import services as engine

@login_required
def index(request):
    games = Game.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'simcity/index.html', {'games': games})

@login_required
def new_game(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    body = json.loads(request.body)
    name = body.get('name', 'Mi ciudad')
    engine_data = engine.engine_new_game(name)
    game = Game.objects.create(
        name=name,
        created_by=request.user,
        engine_game_id=engine_data['id'],
    )
    return JsonResponse({'success': True, 'id': game.id})

@login_required
def game_map(request, game_id):
    game = get_object_or_404(Game, pk=game_id, created_by=request.user)
    data = engine.engine_map(game.engine_game_id)
    return JsonResponse(data)

@login_required
@require_POST
def tick(request, game_id):
    game = get_object_or_404(Game, pk=game_id, created_by=request.user)
    body = json.loads(request.body)
    data = engine.engine_tick(game.engine_game_id, body.get('n', 1))
    game.map_data = data.get('map', game.map_data)
    game.money = data.get('money', game.money)
    game.save()
    return JsonResponse(data)

@login_required
@require_POST
def build(request, game_id):
    game = get_object_or_404(Game, pk=game_id, created_by=request.user)
    body = json.loads(request.body)
    data = engine.engine_build(
        game.engine_game_id,
        body.get('herramienta'),
        int(body.get('x', 0)),
        int(body.get('y', 0)),
        body.get('agente_id'),
    )
    if data.get('map'):
        game.map_data = data['map']
    if data.get('money') is not None:
        game.money = data['money']
    game.save()
    return JsonResponse(data)

@login_required
@require_POST
def reset(request, game_id):
    game = get_object_or_404(Game, pk=game_id, created_by=request.user)
    body = json.loads(request.body)
    data = engine.engine_reset(
        game.engine_game_id,
        body.get('size', 64),
        body.get('num_agents', 3),
        body.get('monopoly', False),
    )
    game.map_data = data.get('map_data', game.map_data)
    game.money = data.get('money', game.money)
    game.save()
    return JsonResponse(data)

@login_required
@require_POST
def generate_block(request, game_id):
    game = get_object_or_404(Game, pk=game_id, created_by=request.user)
    body = json.loads(request.body)
    data = engine.engine_generate_block(
        game.engine_game_id,
        body.get('size', 'medium'),
        body.get('conectar', True),
    )
    if data.get('map'):
        game.map_data = data['map']
    game.save()
    return JsonResponse(data)

@login_required
def census(request, game_id):
    game = get_object_or_404(Game, pk=game_id, created_by=request.user)
    return JsonResponse(engine.engine_census(game.engine_game_id))

@login_required
def task_status(request, game_id):
    game = get_object_or_404(Game, pk=game_id, created_by=request.user)
    return JsonResponse(engine.engine_tasks(game.engine_game_id))

@login_required
def list_games(request):
    games = Game.objects.filter(created_by=request.user).order_by('-created_at').values(
        'id', 'name', 'money', 'size', 'created_at'
    )
    return JsonResponse(list(games), safe=False)

@login_required
@require_POST
def delete_game(request, game_id):
    game = get_object_or_404(Game, pk=game_id, created_by=request.user)
    game.delete()
    return JsonResponse({'success': True})

# En simcity/views.py — agregar esta vista
@login_required
@require_POST
def add_money(request, game_id):
    game = get_object_or_404(Game, pk=game_id, created_by=request.user)
    body = json.loads(request.body)
    data = engine.engine_add_money(game.engine_game_id, body.get('cantidad', 1000))
    game.money = data.get('money', game.money)
    game.save()
    return JsonResponse(data)