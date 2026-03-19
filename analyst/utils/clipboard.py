# analyst/utils/clipboard.py
import pickle
import base64
import logging
import pandas as pd
from typing import Optional, Tuple, Dict, Any, List
from django.core.cache import cache
from django.core.signing import Signer, BadSignature
from django.utils import timezone
from django.http import JsonResponse  # <-- IMPORTANTE: Agregar este import
from django.views.decorators.http import require_GET, require_POST  # <-- IMPORTANTE: Agregar estos imports

logger = logging.getLogger(__name__)

class DataFrameClipboard:
    """Utilidad para manejar DataFrames en caché (portapapeles)"""
    
    @staticmethod
    def _serialize_df(df: pd.DataFrame) -> str:
        """Serializa DataFrame usando pickle y base64"""
        try:
            return base64.b64encode(pickle.dumps(df)).decode('utf-8')
        except Exception as e:
            logger.error(f"Error serializando DataFrame: {str(e)}")
            raise
    
    @staticmethod
    def _deserialize_df(data: str) -> pd.DataFrame:
        """Deserializa DataFrame"""
        try:
            return pickle.loads(base64.b64decode(data.encode('utf-8')))
        except Exception as e:
            logger.error(f"Error deserializando DataFrame: {str(e)}")
            raise
    
    @classmethod
    def store_df(cls, request, df: pd.DataFrame, key: str = None, 
                 metadata: Dict = None, timeout: int = 3600) -> str:
        """
        Almacena un DataFrame en caché con metadata
        
        Args:
            request: Django request object
            df: Pandas DataFrame
            key: Identificador único (auto-generado si None)
            metadata: Metadatos adicionales
            timeout: Tiempo de vida en segundos
            
        Returns:
            str: Key del DataFrame almacenado
        """
        if not key:
            key = f"clip_{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
        # Asegurar session key
        if not request.session.session_key:
            request.session.save()
        
        cache_key = f"df_clip_{request.session.session_key}_{key}"
        
        # Preparar datos
        data = {
            'data': cls._serialize_df(df),
            'metadata': {
                'shape': df.shape,
                'columns': list(df.columns),
                'dtypes': {str(k): str(v) for k, v in df.dtypes.items()},
                'created_at': timezone.now().isoformat(),
                'filename': metadata.get('filename') if metadata else None,
                'model': metadata.get('model') if metadata else None,
                **(metadata or {})
            }
        }
        
        # Firmar datos
        signer = Signer()
        signed_data = signer.sign_object(data)
        
        # Guardar en caché
        cache.set(cache_key, signed_data, timeout=timeout)
        
        # Actualizar keys en sesión
        if 'clipboard_keys' not in request.session:
            request.session['clipboard_keys'] = []
        
        if key not in request.session['clipboard_keys']:
            request.session['clipboard_keys'].append(key)
            request.session.modified = True
        
        logger.info(f"DataFrame almacenado: {key} - Shape: {df.shape}")
        return key
    
    @classmethod
    def retrieve_df(cls, request, key: str) -> Tuple[Optional[pd.DataFrame], Optional[Dict]]:
        """
        Recupera un DataFrame almacenado
        
        Returns:
            Tuple[Optional[pd.DataFrame], Optional[Dict]]: (DataFrame, metadata)
        """
        if not request.session.session_key:
            return None, None
        
        cache_key = f"df_clip_{request.session.session_key}_{key}"
        signed_data = cache.get(cache_key)
        
        if not signed_data:
            logger.debug(f"Clip no encontrado: {key}")
            return None, None
        
        try:
            signer = Signer()
            data = signer.unsign_object(signed_data)
            df = cls._deserialize_df(data['data'])
            logger.debug(f"Clip recuperado: {key} - Shape: {df.shape}")
            return df, data['metadata']
        except (BadSignature, pickle.PickleError, base64.binascii.Error, KeyError) as e:
            logger.error(f"Error recuperando clip {key}: {str(e)}")
            cache.delete(cache_key)
            return None, None
    
    @classmethod
    def delete_df(cls, request, key: str) -> bool:
        """Elimina un DataFrame almacenado"""
        if not request.session.session_key:
            return False
        
        cache_key = f"df_clip_{request.session.session_key}_{key}"
        
        # Eliminar de caché
        deleted = bool(cache.delete(cache_key))
        
        # Eliminar de sesión
        if 'clipboard_keys' in request.session and key in request.session['clipboard_keys']:
            request.session['clipboard_keys'].remove(key)
            request.session.modified = True
        
        if deleted:
            logger.info(f"Clip eliminado: {key}")
        
        return deleted
    

    @classmethod
    def list_clips(cls, request) -> List[Dict]:
        """Lista todos los clips disponibles para la sesión"""
        if 'clipboard_keys' not in request.session:
            return []
        
        clips = []
        for key in request.session['clipboard_keys'][:]:  # Copia para modificación segura
            df, metadata = cls.retrieve_df(request, key)
            if df is not None and metadata:
                shape = metadata.get('shape', (0, 0))
                clips.append({
                    'key':         str(key),
                    'name':        str(key),  # alias usado por el selector JS
                    'columns':     [str(c) for c in metadata.get('columns', [])],
                    'shape':       [int(shape[0]), int(shape[1])],
                    'created_at':  str(metadata.get('created_at') or ''),
                    'filename':    str(metadata.get('filename') or ''),
                    'model':       str(metadata.get('model') or ''),
                    'description': str(metadata.get('description') or ''),
                    'rows':        int(shape[0]),
                    'cols':        int(shape[1]),
                })
            else:
                # Limpiar keys inválidas
                request.session['clipboard_keys'].remove(key)
                request.session.modified = True
        
        return clips

    
    @classmethod
    def clear_clips(cls, request) -> int:
        """Limpia todos los clips de la sesión actual"""
        count = 0
        keys = request.session.get('clipboard_keys', []).copy()
        
        for key in keys:
            if cls.delete_df(request, key):
                count += 1
        
        request.session['clipboard_keys'] = []
        request.session.modified = True
        
        logger.info(f"Portapapeles limpiado: {count} clips eliminados")
        return count