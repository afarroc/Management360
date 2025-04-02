from ollama import AsyncClient
import logging
from typing import AsyncGenerator
import json

# Configuración del cliente y logging
client = AsyncClient(host='192.168.18.49:11434')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración del modelo
MODEL_CONFIG = {
    'model': 'deepseek-r1:1.5b',
    'options': {
        'temperature': 0.7,
        'num_ctx': 2048,
        'repeat_penalty': 1.1,
        'top_k': 40,
        'top_p': 0.9
    }
}

class ConversationManager:
    def __init__(self):
        self.conversation_cache = {}  # Para manejar múltiples conversaciones
        self.max_history_length = -1  # Límite de mensajes en el historial

    async def generate_response(self, messages: list, conversation_id: str = None) -> AsyncGenerator[dict, None]:
        """
        Genera respuestas en streaming para una conversación, con manejo de estado y caché
        """
        try:
            # Validar y preparar mensajes
            cleaned_messages = self._prepare_messages(messages)
            
            # Si hay conversation_id, manejar historial persistente
            if conversation_id:
                self._update_conversation_cache(conversation_id, cleaned_messages)
            
            # Configuración específica para esta generación
            generation_config = {**MODEL_CONFIG, 'messages': cleaned_messages}
            
            # Stream de respuesta
            async for chunk in await client.chat(**generation_config, stream=True):
                if chunk and chunk.get('message', {}).get('content'):
                    yield chunk
                    
                    # Actualizar caché con cada chunk si es conversación persistente
                    if conversation_id:
                        self._update_with_partial_response(conversation_id, chunk['message']['content'])
                        
        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
            yield {'message': {'content': 'Error de conexión con el servidor de modelos. Intente nuevamente.'}}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            yield {'message': {'content': 'Lo siento, ocurrió un error al procesar tu solicitud.'}}

    def _prepare_messages(self, messages: list) -> list:
        """Limpia y valida la estructura de mensajes"""
        valid_messages = []
        for msg in messages[-self.max_history_length:]:  # Aplicar límite de historial
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                valid_messages.append({
                    'role': msg['role'],
                    'content': str(msg['content'])[:2000]  # Limitar longitud
                })
        return valid_messages or [{'role': 'user', 'content': 'Hola'}]

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