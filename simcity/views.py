from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .models import Game
from . import services as engine
from .services import EngineUnavailableError


def _engine_error(e):
    return JsonResponse(
        {'success': False, 'error': str(e)},
        status=503,
    )


@login_required
def index(request):
    games = Game.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'simcity/index.html', {'games': games})


@login_required
def new_game(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    try:
        body = json.loads(request.body)
        name = body.get('name', 'Mi ciudad')
        engine_data = engine.engine_new_game(name)
        game = Game.objects.create(
            name=name,
            created_by=request.user,
            engine_game_id=engine_data['id'],
        )
        return JsonResponse({'success': True, 'id': game.id})
    except EngineUnavailableError as e:
        return _engine_error(e)


@login_required
def game_map(request, game_id):
    game = get_object_or_404(Game, pk=game_id, created_by=request.user)
    try:
        data = engine.engine_map(game.engine_game_id)
        return JsonResponse(data)
    except EngineUnavailableError as e:
        return _engine_error(e)


@login_required
@require_POST
def tick(request, game_id):
    game = get_object_or_404(Game, pk=game_id, created_by=request.user)
    try:
        body = json.loads(request.body)
        data = engine.engine_tick(game.engine_game_id, body.get('n', 1))
        game.map_data = data.get('map', game.map_data)
        game.money = data.get('money', game.money)
        game.save()
        return JsonResponse(data)
    except EngineUnavailableError as e:
        return _engine_error(e)


@login_required
@require_POST
def build(request, game_id):
    game = get_object_or_404(Game, pk=game_id, created_by=request.user)
    try:
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
    except EngineUnavailableError as e:
        return _engine_error(e)


@login_required
@require_POST
def reset(request, game_id):
    game = get_object_or_404(Game, pk=game_id, created_by=request.user)
    try:
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
    except EngineUnavailableError as e:
        return _engine_error(e)


@login_required
@require_POST
def generate_block(request, game_id):
    game = get_object_or_404(Game, pk=game_id, created_by=request.user)
    try:
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
    except EngineUnavailableError as e:
        return _engine_error(e)


@login_required
@require_POST
def generate_zr_block(request, game_id):
    """SC-1: View para el bloque residencial ZR 10×10 (32×32 tiles)."""
    game = get_object_or_404(Game, pk=game_id, created_by=request.user)
    try:
        data = engine.engine_generate_zr(game.engine_game_id)
        if data.get('map'):
            game.map_data = data['map']
        game.save()
        return JsonResponse(data)
    except EngineUnavailableError as e:
        return _engine_error(e)


@login_required
def census(request, game_id):
    game = get_object_or_404(Game, pk=game_id, created_by=request.user)
    try:
        return JsonResponse(engine.engine_census(game.engine_game_id))
    except EngineUnavailableError as e:
        return _engine_error(e)


@login_required
def task_status(request, game_id):
    game = get_object_or_404(Game, pk=game_id, created_by=request.user)
    try:
        return JsonResponse(engine.engine_tasks(game.engine_game_id))
    except EngineUnavailableError as e:
        return _engine_error(e)


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


@login_required
@require_POST
def add_money(request, game_id):
    game = get_object_or_404(Game, pk=game_id, created_by=request.user)
    try:
        body = json.loads(request.body)
        data = engine.engine_add_money(game.engine_game_id, body.get('cantidad', 1000))
        game.money = data.get('money', game.money)
        game.save()
        return JsonResponse(data)
    except EngineUnavailableError as e:
        return _engine_error(e)

@login_required
@require_POST
def export_to_analyst(request, game_id):
    import uuid as _uuid
    import pickle, base64
    import pandas as pd
    from analyst.models import StoredDataset

    game = get_object_or_404(Game, pk=game_id, created_by=request.user)

    ZONE_LABELS = {
        range(64,  207): 'road',
        range(208, 223): 'wire',
        range(240, 249): 'residential_empty',
        range(249, 261): 'residential',
        range(423, 432): 'commercial_empty',
        range(432, 444): 'commercial',
        range(612, 621): 'industrial_empty',
        range(621, 633): 'industrial',
        range(745, 760): 'coal_plant',
    }

    def zone_label(base):
        for rng, label in ZONE_LABELS.items():
            if base in rng:
                return label
        return 'terrain' if base == 0 else 'other'

    rows = []
    map_data = game.map_data
    size = len(map_data)

    for x in range(size):
        for y in range(size):
            tile = map_data[x][y]
            if tile == 0:
                continue
            base      = tile & 0x3FF
            has_power = bool(tile & 0x8000)
            has_road  = bool(tile & 0x2000)
            rows.append({
                'x': x, 'y': y, 'tile': base,
                'zone_type': zone_label(base),
                'has_power': has_power,
                'has_road':  has_road,
                'money':     game.money,
                'game_name': game.name,
                'game_id':   game.id,
            })

    if not rows:
        return JsonResponse({'success': False, 'error': 'El mapa está vacío'}, status=400)

    import pandas as pd
    df = pd.DataFrame(rows)
    blob = base64.b64encode(pickle.dumps(df)).decode('utf-8')
    dataset_id = _uuid.uuid4()
    cache_key  = f'stored_dataset_{dataset_id}'

    from analyst.models import StoredDataset
    ds = StoredDataset.objects.create(
        id=dataset_id, name=f'SimCity — {game.name}',
        description=f'Exportado desde SimCity · partida #{game.id} · {len(rows)} tiles · ${game.money} fondos',
        cache_key=cache_key, rows=len(df), col_count=len(df.columns),
        columns=list(df.columns), dtype_map={c: str(df[c].dtype) for c in df.columns},
        source_file=f'simcity/game/{game.id}', data_blob=blob, created_by=request.user,
    )
    return JsonResponse({
        'success': True, 'dataset_id': str(ds.id),
        'name': ds.name, 'rows': ds.rows, 'columns': ds.columns,
        'analyst_url': f'/analyst/datasets/{ds.id}/preview/',
    })
