# chat/views.py
from django.shortcuts import render
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import asyncio
import json
from .ollama_api import generate_response
 

@csrf_exempt
def chat_view(request):
    if request.method == "POST":
        user_input = request.POST["user_input"]
        chat_history = json.loads(request.POST.get("chat_history", "[]"))
        
        # Construir el historial de mensajes para Ollama
        messages = []
        for msg in chat_history:
            if msg['sender'] == 'user':
                messages.append({"role": "user", "content": msg['content']})
            else:
                messages.append({"role": "assistant", "content": msg['content']})
        
        # Agregar el nuevo mensaje del usuario
        messages.append({"role": "user", "content": user_input})

        async def async_chat_view():
            async for chunk in generate_response(messages):
                yield chunk['message']['content'].replace('\n', '   ')

        async def stream():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            async_generator = async_chat_view()
            while True:
                try:
                    chunk = await async_generator.asend(None)
                    yield chunk
                except StopAsyncIteration:
                    break

        return StreamingHttpResponse(stream(), content_type='text/event-stream charset=utf-8')

    return render(request, "chat/assistant.html", {
        "pagetitle": "Chat IA",
        "initial_history": json.dumps([])
    })

@csrf_exempt
def clear_chat(request):
    if request.method == "POST":
        try:
            # Limpiar el historial en el servidor (si es necesario)
            return JsonResponse({
                "status": "success",
                "message": "Chat limpiado correctamente"
            })
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    return JsonResponse({
        "status": "error",
        "message": "Método no permitido"
    }, status=405)

def index(request):
    return render(request, "chat/index.html", {
        'pagetitle':'Chat Page',
    })

def chatroom(request, room_name):
    return render(request, "chat/room.html", {
        "room_name": room_name,
    })