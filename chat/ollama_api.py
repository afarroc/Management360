from ollama import AsyncClient

client = AsyncClient(host='192.168.18.40:11434')

async def generate_response(prompt):
    stream = await client.chat(
        model='gemma2:2b', 
        messages=[
            {
                'role': 'user',
                'content': "Eres un asistente de Analista de datos y responderás solo en español."
                },
            {
                "role": "assistant",
                "content": "De acuerdo, soy un asistente de Analista de datos y responderé solo en español"
                },
            {
                "role": "user",
                "content": prompt
                }
                ],
        stream=True,
        options= {
            "temperature": 0.1,
          },

    )
    async for chunk in stream:
        print(chunk)
        yield chunk