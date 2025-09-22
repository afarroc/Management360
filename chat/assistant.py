import asyncio, aiohttp, json, sys

semaforo_api = asyncio.Semaphore(2)  # Limita a 2 conexiones concurrentes (ajustable)

async def enviar_solicitud(pregunta):
    print("[LOG] Conectando a http://localhost:11434/api/generate con modelo deepseek-r1:8b")
    print(f"[LOG] Pregunta enviada: {pregunta}")
    async with semaforo_api:
        async with aiohttp.ClientSession() as session:
            async with session.post('http://localhost:11434/api/generate', json={
            "model": "deepseek-r1:8b",
            "prompt": pregunta,
            "format": "json",
            "stream": False
            }) as respuesta:
                print(f"[LOG] Estado de la respuesta: {respuesta.status}")
                print(f"[LOG] Headers de la respuesta: {dict(respuesta.headers)}")
                total_chunks = 0
                total_chars = 0
                async for linea in respuesta.content:
                    if linea:
                        try:
                            json_linea = json.loads(linea.decode('utf-8'))
                            print(f"[LOG] Respuesta recibida: {json_linea}")
                            if 'message' in json_linea:
                                content = json_linea['message']['content']
                                print(content, end='', flush=True)
                                total_chunks += 1
                                total_chars += len(content)
                        except Exception as e:
                            print(f"[LOG] Error procesando la línea: {e}")
                print(f"\n[LOG] Total de fragmentos recibidos: {total_chunks}")
                print(f"[LOG] Total de caracteres recibidos: {total_chars}")

if __name__ == "__main__":
    pregunta = sys.argv[1]
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(enviar_solicitud(pregunta))
    loop.close()
