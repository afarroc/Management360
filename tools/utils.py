import pandas as pd
import pickle
import base64
from django.core.cache import cache
from django.core.signing import Signer, BadSignature
from django.utils import timezone

def calcular_trafico_intensidad(calls, average_handling_time):
    """
    Calculate traffic intensity in Erlangs
    Args:
        calls: Number of calls
        average_handling_time: Average handling time in minutes
    Returns:
        Traffic intensity in Erlangs
    """
    call_minutes = calls * average_handling_time
    call_hours = call_minutes / 60
    return call_hours

class DataFrameClipboard:
    @staticmethod
    def _serialize_df(df):
        """Serialize DataFrame using pickle and base64"""
        return base64.b64encode(pickle.dumps(df)).decode('utf-8')
    
    @staticmethod
    def _deserialize_df(data):
        """Deserialize DataFrame"""
        return pickle.loads(base64.b64decode(data.encode('utf-8')))
    
    @classmethod
    def store_df(cls, request, df, key=None, metadata=None, timeout=3600):
        """
        Store a DataFrame in cache with metadata
        Args:
            request: Django request object
            df: Pandas DataFrame
            key: Unique identifier (auto-generated if None)
            metadata: Additional metadata dictionary
            timeout: Time to live in seconds
        Returns:
            Cache key used for storage
        """
        if not key:
            key = f"clip_{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
        session_key = request.session.session_key
        if not session_key:
            request.session.save()
            session_key = request.session.session_key
            
        cache_key = f"df_clip_{session_key}_{key}"
        
        data = {
            'data': cls._serialize_df(df),
            'metadata': {
                'shape': df.shape,
                'columns': list(df.columns),
                'dtypes': {str(k): str(v) for k, v in df.dtypes.items()},
                'created_at': timezone.now().isoformat(),
                **(metadata or {})
            }
        }
        
        signer = Signer()
        signed_data = signer.sign_object(data)
        
        cache.set(cache_key, signed_data, timeout=timeout)
        
        # Update session clipboard keys
        if 'clipboard_keys' not in request.session:
            request.session['clipboard_keys'] = []
        
        if key not in request.session['clipboard_keys']:
            request.session['clipboard_keys'].append(key)
            request.session.modified = True
            
        return key
    
    @classmethod
    def retrieve_df(cls, request, key):
        """
        Retrieve a stored DataFrame
        Args:
            request: Django request object
            key: Key used when storing
        Returns:
            Tuple of (DataFrame, metadata) or (None, None) if not found
        """
        session_key = request.session.session_key
        cache_key = f"df_clip_{session_key}_{key}"
        
        signed_data = cache.get(cache_key)
        if not signed_data:
            return None, None
            
        try:
            signer = Signer()
            data = signer.unsign_object(signed_data)
            return cls._deserialize_df(data['data']), data['metadata']
        except (BadSignature, AttributeError, pickle.PickleError, base64.binascii.Error) as e:
            cache.delete(cache_key)
            return None, None
    
    @classmethod
    def delete_df(cls, request, key):
        """
        Delete a stored DataFrame
        Args:
            request: Django request object
            key: Key to delete
        Returns:
            bool: True if deleted, False if not found
        """
        session_key = request.session.session_key
        cache_key = f"df_clip_{session_key}_{key}"
        
        # Remove from cache
        deleted = bool(cache.delete(cache_key))
        
        # Remove from session keys if present
        if 'clipboard_keys' in request.session and key in request.session['clipboard_keys']:
            request.session['clipboard_keys'].remove(key)
            request.session.modified = True
            
        return deleted
    
    @classmethod
    def list_clips(cls, request):
        """
        List all available clips for the session
        Args:
            request: Django request object
        Returns:
            List of clip keys with their metadata
        """
        if 'clipboard_keys' not in request.session:
            return []
            
        clips = []
        for key in request.session['clipboard_keys']:
            _, metadata = cls.retrieve_df(request, key)
            if metadata:
                clips.append({
                    'key': key,
                    'columns': metadata.get('columns', []),
                    'shape': metadata.get('shape', (0, 0)),
                    'created_at': metadata.get('created_at')
                })
                
        return clips
    
    @classmethod
    def clear_clips(cls, request):
        """
        Clear all clips for the current session
        Args:
            request: Django request object
        Returns:
            int: Number of clips deleted
        """
        count = 0
        if 'clipboard_keys' in request.session:
            for key in request.session['clipboard_keys']:
                if cls.delete_df(request, key):
                    count += 1
                    
        request.session['clipboard_keys'] = []
        request.session.modified = True
        return count