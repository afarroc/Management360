# chat/views.py
from django.shortcuts import render


def index(request):
    return render(request, "chat/index.html", {
        'pagetitle':'Chat Page',
        })


def room(request, room_name):
    return render(request, "chat/room.html", {
        "room_name": room_name,
        })

from django.shortcuts import render
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
import asyncio

from .ollama_api import generate_response

@csrf_exempt
def chat_view(request):
    if request.method == "POST":
        user_input = request.POST["user_input"]
        prompt = f"User: {user_input}\nAI:"

        async def async_chat_view():
            async for chunk in generate_response(prompt):
                yield chunk['message']['content'].replace('\n', '<br>')

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

    return render(request, "chat/assistant.html" ,{
        "pagetitle":"Chat IA"})