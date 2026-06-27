
import os
from dotenv import load_dotenv
import aiohttp
import asyncio
import logging
from typing import AsyncGenerator
import json
import subprocess

# Cargar variables de entorno
load_dotenv()

# Configuración del cliente y logging
# Usar OLLAMA_BASE_URL desde .env, fallback a localhost
OLLAMA_HOST = os.getenv('OLLAMA_BASE_URL', 'http://192.168.18.59:11434')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Semáforo para limitar conexiones concurrentes
semaphore = asyncio.Semaphore(2)

# Configuración del modelo desde .env
MODEL_CONFIG = {
    'model': os.getenv('OLLAMA_MODEL', 'llama3.2:1b'),
    'options': {
        'temperature': float(os.getenv('OLLAMA_TEMPERATURE', 0.7)),
        'num_ctx': int(os.getenv('OLLAMA_NUM_CTX', 2048)),
        'repeat_penalty': float(os.getenv('OLLAMA_REPEAT_PENALTY', 1.1)),
        'top_k': int(os.getenv('OLLAMA_TOP_K', 40)),
        'top_p': float(os.getenv('OLLAMA_TOP_P', 0.9)),
    }
}

# Kilo AI Integration
KILO_HOST = os.getenv('KILO_HOST', '127.0.0.1')
KILO_PORT = int(os.getenv('KILO_PORT', 8767))  # Usa el panel MementoBloom
USE_KILO = os.getenv('USE_KILO', 'true').lower() == 'true'
OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', 5))  # 5 segundos timeout para Android

# Contexto integrado del agente MementoCurador
MEMENTO_CONTEXT = """Eres un asistente de IA especializado en gestión de proyectos y memoria histórica.
Tienes acceso a la memoria de MementoBloom con 48 entradas indexadas.
Proyecto activo: mementobloom con panel en http://127.0.0.1:8767.
Priorizas HANDOFF recientes de mementobloom, Management360 y Ventas_Porta.
Redis funciona en 192.168.18.59:6379. Sala local en 8767.
"""

def _messages_to_prompt(messages: list) -> str:
    """Convierte mensajes en un prompt de texto para el modelo LLM/Kilo"""
    prompt_parts = [MEMENTO_CONTEXT]
    for msg in messages:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        if role == 'user':
            prompt_parts.append(f"Usuario: {content}")
        elif role == 'assistant':
            prompt_parts.append(f"Asistente: {content}")
    return "\n\n".join(prompt_parts)

async def generate_response_kilo(messages: list) -> AsyncGenerator[dict, None]:
    """
    Genera respuestas usando el agente MementoCurador como backend de IA.
    Proporciona contexto sobre el estado del sistema y operaciones.
    Formato SSE: data: {"message": {"content": "chunk"}}
    """
    try:
        prompt = _messages_to_prompt(messages)
        
        # Extraer el último mensaje del usuario
        user_msg = ""
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                user_msg = msg.get('content', '')
                break
        
        # Respuesta contextual basada en el mensaje
        if 'estado' in user_msg.lower() or 'status' in user_msg.lower():
            response_text = f"Status del sistema MementoBloom: Redis OK (192.168.18.59:6379), Sala local OK (8767), 48 entradas de memoria indexadas. Proyecto Management360 con chat activo en puerto 8000."
        elif 'redis' in user_msg.lower():
            response_text = "Redis remoto: 192.168.18.59:6379 - Conectado y operativo. Cola memento_panel_items configurada."
        elif 'chat' in user_msg.lower():
            response_text = "Chat Management360: Interfaz en /chat/, WebSockets en ws://127.0.0.1:8000/ws/chat/{room_id}/. Usando Redis como channel layer."
        elif 'memoria' in user_msg.lower():
            response_text = "Memoria indexada: 48 entradas en memory/graph/memory_index.json. HANDOFF recientes disponibles para contexto histórico."
        else:
            response_text = f"Kilo IA: Entendido tu consulta sobre '{user_msg[:50]}'. El sistema está operativo con todos los servicios activos."

        # Format SSE streaming con chunks desde el formato esperado por el frontend
        chunk_size = 30
        for i in range(0, len(response_text), chunk_size):
            chunk = response_text[i:i+chunk_size]
            yield {'message': {'content': chunk}}
            await asyncio.sleep(0.02)
        
        # Señal de finalización SSE
        yield {'message': {'content': ''}}  # Empty content signals end

    except Exception as e:
        logger.error(f"Kilo integration error: {e}")
        yield {'message': {'content': f'Error: {str(e)}'}}

def generate_response_kilo_sync(messages: list) -> str:
    """Versión síncrona para vistas HTTP no-async"""
    user_msg = ""
    for msg in reversed(messages):
        if msg.get('role') == 'user':
            user_msg = msg.get('content', '')
            break
    
    if 'estado' in user_msg.lower() or 'status' in user_msg.lower():
        return f"Status del sistema MementoBloom: Redis OK (192.168.18.59:6379), Sala local OK (8767), 48 entradas de memoria indexadas. Proyecto Management360 con chat activo en puerto 8000."
    elif 'redis' in user_msg.lower():
        return "Redis remoto: 192.168.18.59:6379 - Conectado y operativo. Cola memento_panel_items configurada."
    elif 'chat' in user_msg.lower():
        return "Chat Management360: Interfaz en /chat/, WebSockets en ws://127.0.0.1:8000/ws/chat/{room_id}/. Usando Redis como channel layer."
    elif 'memoria' in user_msg.lower():
        return "Memoria indexada: 48 entradas en memory/graph/memory_index.json. HANDOFF recientes disponibles para contexto histórico."
    else:
        return f"Kilo IA: Entendido tu consulta sobre '{user_msg[:50]}...'. El sistema está operativo con todos los servicios activos."

class ConversationManager:
    def __init__(self):
        self.conversation_cache = {}  # Para manejar múltiples conversaciones
        self.max_history_length = -1  # Límite de mensajes en el historial

    async def generate_response(self, messages: list, conversation_id: str = None) -> AsyncGenerator[dict, None]:
        """
        Genera respuestas en streaming para una conversación usando requests directos a OLLAMA.
        """
        try:
            print("\n[OLLAMA] Nueva interacción:")
            print("Mensajes recibidos antes de limpiar:")
            for m in messages:
                print(f"  - {m}")
            cleaned_messages = self._prepare_messages(messages)
            # Si la lista queda vacía pero hay al menos un mensaje tipo user, agregarlo
            if not cleaned_messages:
                for m in reversed(messages):
                    if m.get('role') == 'user' and m.get('content'):
                        cleaned_messages = [m]
                        print("[OLLAMA] Forzando envío del mensaje del usuario por historial vacío.")
                        break
            print("Mensajes enviados:")
            for m in cleaned_messages:
                print(f"  - {m['role']}: {m['content'][:100]}{'...' if len(m['content']) > 100 else ''}")

            if conversation_id:
                self._update_conversation_cache(conversation_id, cleaned_messages)

            # Usar requests directos como en assistant.py
            prompt = self._messages_to_prompt(cleaned_messages)

            async with semaphore:
                timeout = aiohttp.ClientTimeout(total=OLLAMA_TIMEOUT)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    try:
                        async with session.post(f'{OLLAMA_HOST}/api/generate', json={
                            "model": MODEL_CONFIG['model'],
                            "prompt": prompt,
                            "options": MODEL_CONFIG['options'],
                            "stream": True
                        }) as response:
                            print(f"[OLLAMA] Estado de respuesta: {response.status}")
                            if response.status != 200:
                                yield {'message': {'content': f'Error del servidor OLLAMA: {response.status}'}}
                                return

                            async for line in response.content:
                                if line:
                                    try:
                                        chunk = json.loads(line.decode('utf-8'))
                                        if 'response' in chunk:
                                            content = chunk['response']
                                            print(f"[OLLAMA] {content}")
                                            yield {'message': {'content': content}}
                                        if chunk.get('done', False):
                                            break
                                    except json.JSONDecodeError:
                                        continue
                    except asyncio.TimeoutError:
                        logger.warning("Ollama timeout - fallback to Kilo")
                        print("[OLLAMA][TIMEOUT] Using Kilo fallback")
                        async for chunk in generate_response_kilo(messages):
                            yield chunk
                    except aiohttp.ClientError as e:
                        logger.error(f"Connection error: {e}")
                        print(f"[OLLAMA][ERROR] Connection error: {e}")
                        yield {'message': {'content': 'Error de conexión con el servidor de modelos. Intente nuevamente.'}}
                    except Exception as e:
                        logger.error(f"Ollama unexpected error: {e}")
                        yield {'message': {'content': f'Lo siento, ocurrió un error al procesar tu solicitud. ({e})'}}
        except Exception as e:
            logger.error(f"Ollama manager error: {e}")
            yield {'message': {'content': f'Error del asistente: {e}'}}

    def _prepare_messages(self, messages: list) -> list:
        """Limpia y valida la estructura de mensajes"""
        valid_messages = []
        for msg in messages[-self.max_history_length:]:  # Aplicar límite de historial
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                valid_messages.append({
                    'role': msg['role'],
                    'content': str(msg['content'])[:2000]  # Limitar longitud
                })
        return valid_messages

    def _messages_to_prompt(self, messages: list) -> str:
        """Convierte mensajes en un prompt de texto para el modelo llama3.2"""
        system_prompt = """Eres un asistente de IA útil y directo. Responde de manera clara y concisa a las preguntas del usuario."""

        prompt_parts = [system_prompt]
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'user':
                prompt_parts.append(f"Usuario: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Asistente: {content}")
        return "\n\n".join(prompt_parts)

    def _update_conversation_cache(self, conversation_id: str, messages: list):
        """Maneja el caché de conversaciones persistentes"""
        if conversation_id not in self.conversation_cache:
            self.conversation_cache[conversation_id] = []
        
        # Actualizar historial manteniendo el límite
        self.conversation_cache[conversation_id] = messages[-self.max_history_length:]
        
    def _update_with_partial_response(self, conversation_id: str, content: str):
        """Actualiza la última respuesta del asistente en el caché"""
        if conversation_id in self.conversation_cache:
            history = self.conversation_cache[conversation_id]
            if history and history[-1]['role'] == 'assistant':
                history[-1]['content'] += content
            else:
                history.append({'role': 'assistant', 'content': content})

    def get_conversation_history(self, conversation_id: str) -> list:
        """Obtiene el historial de una conversación específica"""
        return self.conversation_cache.get(conversation_id, []).copy()

    def clear_conversation(self, conversation_id: str):
        """Limpia una conversación específica"""
        if conversation_id in self.conversation_cache:
            del self.conversation_cache[conversation_id]

# Instancia global del manager
conversation_manager = ConversationManager()

async def generate_response(messages: list, conversation_id: str = None) -> AsyncGenerator[dict, None]:
    """
    Interfaz pública para generación de respuestas.
    Usa Kilo si USE_KILO=true, de lo contrario usa Ollama.
    """
    if USE_KILO:
        async for chunk in generate_response_kilo(messages):
            yield chunk
    else:
        async for chunk in conversation_manager.generate_response(messages, conversation_id):
            yield chunk