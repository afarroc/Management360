# chat/views.py
from django.shortcuts import render
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import asyncio
import json
from .ollama_api import generate_response


@login_required
@csrf_exempt
def chat_view(request):
    if request.method == "POST":
        try:
            # Get user input safely
            user_input = request.POST.get("user_input", "").strip()
            if not user_input:
                return JsonResponse({"error": "Empty message"}, status=400)
                
            chat_history = json.loads(request.POST.get("chat_history", "[]"))
            
            # Validate and prepare message history
            messages = []
            for msg in chat_history:
                if not isinstance(msg, dict):
                    continue
                if msg.get('sender') == 'user':
                    messages.append({"role": "user", "content": str(msg.get('content', ''))})
                else:
                    messages.append({"role": "assistant", "content": str(msg.get('content', ''))})
            
            messages.append({"role": "user", "content": user_input})

            async def stream_generator():
                try:
                    async for chunk in generate_response(messages):
                        content = chunk.get('message', {}).get('content', '')
                        yield content.replace('\n', '   ')
                except Exception as e:
                    yield f"[ERROR: {str(e)}]"

            response = StreamingHttpResponse(
                stream_generator(),
                content_type='text/event-stream; charset=utf-8'
            )
            response['Cache-Control'] = 'no-cache'
            return response

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid chat history format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return render(request, "chat/assistant.html", {
        "pagetitle": "Chat IA",
        "initial_history": json.dumps([])
    })


@login_required
@csrf_exempt
def clear_chat(request):
    if request.method == "POST":
        try:
            # Add any server-side cleanup logic here
            return JsonResponse({
                "status": "success",
                "message": "Chat cleared successfully"
            })
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    return JsonResponse({
        "status": "error",
        "message": "Method not allowed"
    }, status=405)


@login_required
def index(request):
    return render(request, "chat/index.html", {
        'pagetitle': 'Chat Page',
    })


@login_required
def chatroom(request, room_name):
    if not room_name or not str(room_name).isdigit():
        return JsonResponse({"error": "Invalid room ID"}, status=400)
        
    return render(request, "chat/room.html", {
        "room_name": room_name,
    })