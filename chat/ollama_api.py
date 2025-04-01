from ollama import AsyncClient

client = AsyncClient(host='192.168.18.49:11434')
async def generate_response(messages):
    try:
        stream = await client.chat(
            model='deepseek-r1:1.5b', 
            messages=messages,
            stream=True,
            options={
                "temperature": 0.7,
                "num_ctx": 2048  # Aumentar el contexto si es necesario
            },
        )
        async for chunk in stream:
            if chunk.get('message') and chunk['message'].get('content'):
                yield chunk
    except Exception as e:
        print(f"Error in generate_response: {e}")
        yield {'message': {'content': 'Lo siento, ocurrió un error al procesar tu solicitud.'}}