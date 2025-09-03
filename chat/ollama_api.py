from ollama import AsyncClient
import logging
from typing import AsyncGenerator
import json

# Configuración del cliente y logging
client = AsyncClient(host='localhost:11434')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración del modelo
MODEL_CONFIG = {
    'model': 'deepseek-r1:8b',
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
        Genera respuestas en streaming para una conversación, con manejo de estado y caché.
        Emite fragmentos de pensamiento (<|thought|>...<|endofthought|>) y respuesta normal.
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
                        cleaned_messages = [{
                            'role': 'user',
                            'content': str(m.get('content'))[:2000]
                        }]
                        print("[OLLAMA] Forzando envío del mensaje del usuario por historial vacío.")
                        break
            print("Mensajes enviados:")
            for m in cleaned_messages:
                print(f"  - {m['role']}: {m['content'][:100]}{'...' if len(m['content']) > 100 else ''}")
            if conversation_id:
                self._update_conversation_cache(conversation_id, cleaned_messages)
            generation_config = {**MODEL_CONFIG, 'messages': cleaned_messages}
            total_tokens = 0
            thought_mode = False
            async for chunk in await client.chat(**generation_config, stream=True):
                if chunk and chunk.get('message', {}).get('content'):
                    content = chunk['message']['content']
                    print(f"[OLLAMA] {content}")
                    idx_thought_start = content.find('<think>')
                    idx_thought_end = content.find('</think>')
                    while content:
                        if not thought_mode and idx_thought_start != -1:
                            # Emitir lo anterior como respuesta normal
                            before_thought = content[:idx_thought_start]
                            if before_thought:
                                yield {'message': {'content': before_thought}}
                            content = content[idx_thought_start+7:]
                            thought_mode = True
                            idx_thought_start = -1
                            idx_thought_end = content.find('</think>')
                            continue
                        if thought_mode:
                            if idx_thought_end != -1:
                                # Pensamiento final
                                thought_text = content[:idx_thought_end]
                                if thought_text:
                                    yield {'message': {'content': f'<|thought|>{thought_text}'}}
                                yield {'message': {'content': '<|endofthought|>'}}
                                content = content[idx_thought_end+8:]
                                thought_mode = False
                                idx_thought_start = content.find('<think>')
                                idx_thought_end = content.find('</think>')
                                continue
                            else:
                                # Pensamiento parcial
                                if content:
                                    yield {'message': {'content': f'<|thought|>{content}'}}
                                content = ''
                                break
                        # Si no hay etiquetas, todo es texto normal
                        if content:
                            yield {'message': {'content': content}}
                            content = ''
            print(f"[OLLAMA] Total de tokens generados: {total_tokens}\n")
        except ConnectionError as e:
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