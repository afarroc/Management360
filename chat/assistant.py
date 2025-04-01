import asyncio, aiohttp, json, sys

async def enviar_solicitud(pregunta):
    async with aiohttp.ClientSession() as session:
        async with session.post('http://192.168.18.49:11434/api/generate', json={
            "model": "deepseek-r1:1.5b",
            "format": "json",
            "stream": "false",


        }) as respuesta:
            async for linea in respuesta.content:
                if linea:
                    json_linea = json.loads(linea.decode('utf-8'))
                    if 'message' in json_linea:
                        print(json_linea['message']['content'], end='', flush=True)

if __name__ == "__main__":
    pregunta = sys.argv[1]
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(enviar_solicitud(pregunta))
    loop.close()
