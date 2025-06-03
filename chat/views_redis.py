from django.shortcuts import render
from django.conf import settings
import redis
from django.contrib import messages

def check_redis(request):
    try:
        redis_instance = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
        redis_instance.ping()
        info = redis_instance.info()
        
        context = {
            'status': 'connected',
            'redis_version': info['redis_version'],
            'connected_clients': info['connected_clients'],
            'used_memory_human': info['used_memory_human'],
            'redis_url': settings.REDIS_URL,
            'page_title': 'Redis Status'
        }
        
        messages.success(request, '¡Conexión a Redis exitosa!')
        return render(request, 'chat/redis_status.html', context)
        
    except redis.ConnectionError as e:
        messages.error(request, f'Error en la conexión a Redis: {str(e)}')
        return render(request, 'chat/redis_status.html', {
            'status': 'error',
            'message': str(e),
            'redis_url': settings.REDIS_URL,
            'page_title': 'Redis Status'
        })
