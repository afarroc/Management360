
import os
from dotenv import load_dotenv
import aiohttp
import asyncio
import logging
from typing import AsyncGenerator
import json


# Cargar variables de entorno
load_dotenv()

# Configuración del cliente y logging
# Forzar localhost:11434 ya que la variable de entorno del sistema puede estar mal configurada
OLLAMA_HOST = 'http://localhost:11434'
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Semáforo para limitar conexiones concurrentes
semaphore = asyncio.Semaphore(2)

# Configuración del modelo desde .env
MODEL_CONFIG = {
    'model': os.getenv('OLLAMA_MODEL', 'deepseek-r1:8b'),
    'options': {
        'temperature': float(os.getenv('OLLAMA_TEMPERATURE', 0.7)),
        'num_ctx': int(os.getenv('OLLAMA_NUM_CTX', 2048)),
        'repeat_penalty': float(os.getenv('OLLAMA_REPEAT_PENALTY', 1.1)),
        'top_k': int(os.getenv('OLLAMA_TOP_K', 40)),
        'top_p': float(os.getenv('OLLAMA_TOP_P', 0.9)),
    }
}

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
                async with aiohttp.ClientSession() as session:
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

        except aiohttp.ClientError as e:
            logger.error(f"Connection error: {e}")
            print(f"[OLLAMA][ERROR] Connection error: {e}")
            yield {'message': {'content': 'Error de conexión con el servidor de modelos. Intente nuevamente.'}}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print(f"[OLLAMA][ERROR] Unexpected error: {e}")
            yield {'message': {'content': f'Lo siento, ocurrió un error al procesar tu solicitud. ({e})'}}

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

# Función de interfaz pública
async def generate_response(messages: list, conversation_id: str = None) -> AsyncGenerator[dict, None]:
    """
    Interfaz pública para generación de respuestas
    Args:
        messages: Lista de mensajes en formato {'role': 'user|assistant', 'content': 'texto'}
        conversation_id: ID opcional para conversaciones persistentes
    
    Returns:
        AsyncGenerator que produce chunks de la respuesta
    """
    async for chunk in conversation_manager.generate_response(messages, conversation_id):
        yield chunk