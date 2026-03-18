import requests

ENGINE_BASE_URL = 'http://localhost:8001'
ENGINE_TIMEOUT = 30

def engine_get(path):
    r = requests.get(f'{ENGINE_BASE_URL}{path}', timeout=ENGINE_TIMEOUT)
    r.raise_for_status()
    return r.json()

def engine_post(path, data=None):
    r = requests.post(
        f'{ENGINE_BASE_URL}{path}',
        json=data or {},
        timeout=ENGINE_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()

def engine_new_game(name):
    return engine_post('/api/game/new/', {'name': name})

def engine_reset(engine_id, size, num_agents, monopoly=False):
    return engine_post(f'/api/game/{engine_id}/reset/', {
        'size': size, 'num_agents': num_agents, 'monopoly': monopoly,
    })

def engine_tick(engine_id, n=1):
    return engine_post(f'/api/game/{engine_id}/tick/', {'n': n})

def engine_build(engine_id, herramienta, x, y, agente_id=None):
    return engine_post(f'/api/game/{engine_id}/build/', {
        'herramienta': herramienta, 'x': x, 'y': y, 'agente_id': agente_id,
    })

def engine_map(engine_id):
    return engine_get(f'/api/game/{engine_id}/map/')

def engine_census(engine_id):
    return engine_get(f'/api/game/{engine_id}/census/')

def engine_generate_block(engine_id, size='medium', conectar=True):
    return engine_post(f'/api/game/{engine_id}/generate_block/', {
        'size': size, 'conectar': conectar,
    })

def engine_generate_zr(engine_id):
    return engine_post(f'/api/game/{engine_id}/generate_zr_block/', {})

def engine_add_money(engine_id, cantidad=1000):
    return engine_post(f'/api/game/{engine_id}/add_money/', {'cantidad': cantidad})

def engine_tasks(engine_id):
    return engine_get(f'/api/game/{engine_id}/tasks/')