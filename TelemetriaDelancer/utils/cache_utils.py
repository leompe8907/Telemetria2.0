"""
Utilidades para cache de consultas frecuentes.

Este módulo proporciona decoradores y funciones para cachear
resultados de consultas y análisis que se ejecutan frecuentemente.
"""
from functools import wraps
from django.core.cache import cache
from django.conf import settings
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


def cache_key_from_params(prefix, *args, **kwargs):
    """
    Genera una clave de cache a partir de parámetros.
    
    Args:
        prefix: Prefijo para la clave
        *args: Argumentos posicionales
        **kwargs: Argumentos con nombre
    
    Returns:
        Clave de cache generada
    """
    # Convertir args y kwargs a string para hashear
    key_parts = [prefix]
    
    # Agregar args
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        elif arg is None:
            key_parts.append('None')
        else:
            # Para objetos complejos, usar su representación
            try:
                key_parts.append(json.dumps(arg, sort_keys=True, default=str))
            except (TypeError, ValueError):
                key_parts.append(str(hash(str(arg))))
    
    # Agregar kwargs ordenados
    for key, value in sorted(kwargs.items()):
        if isinstance(value, (str, int, float, bool)):
            key_parts.append(f"{key}:{value}")
        elif value is None:
            key_parts.append(f"{key}:None")
        else:
            try:
                key_parts.append(f"{key}:{json.dumps(value, sort_keys=True, default=str)}")
            except (TypeError, ValueError):
                key_parts.append(f"{key}:{str(hash(str(value)))}")
    
    # Crear hash de la clave completa
    key_string = "|".join(key_parts)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    
    return f"telemetria:{prefix}:{key_hash}"


def cached_result(timeout=None, key_prefix=None):
    """
    Decorador para cachear resultados de funciones.
    
    Args:
        timeout: Tiempo de expiración en segundos (None = usar default)
        key_prefix: Prefijo para la clave de cache (None = usar nombre de función)
    
    Usage:
        @cached_result(timeout=300, key_prefix='analytics')
        def get_analytics(start_date, end_date):
            # ... código ...
            return result
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave de cache
            prefix = key_prefix or func.__name__
            cache_key = cache_key_from_params(prefix, *args, **kwargs)
            
            # Intentar obtener del cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_value
            
            # Cache miss - ejecutar función
            logger.debug(f"Cache MISS: {cache_key}")
            result = func(*args, **kwargs)
            
            # Guardar en cache
            timeout_value = timeout or getattr(settings, 'CACHE_TIMEOUT_MEDIUM', 300)
            try:
                cache.set(cache_key, result, timeout=timeout_value)
                logger.debug(f"Cached result for {cache_key} (timeout: {timeout_value}s)")
            except Exception as e:
                logger.warning(f"Error al guardar en cache: {str(e)}")
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern):
    """
    Invalida todas las claves de cache que coincidan con un patrón.
    
    Args:
        pattern: Patrón de clave a invalidar (ej: 'telemetria:analytics:*')
    
    Note:
        Esta función requiere django-redis para funcionar correctamente.
        Con otros backends, puede no funcionar completamente.
    """
    try:
        from django_redis import get_redis_connection
        
        redis_client = get_redis_connection("default")
        
        # Buscar todas las claves que coincidan
        keys = redis_client.keys(f"{pattern}*")
        
        if keys:
            redis_client.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache keys matching pattern: {pattern}")
            return len(keys)
        else:
            logger.debug(f"No cache keys found matching pattern: {pattern}")
            return 0
    except ImportError:
        logger.warning("django-redis no está instalado, no se puede invalidar por patrón")
        return 0
    except Exception as e:
        logger.error(f"Error invalidando cache: {str(e)}")
        return 0


def clear_all_cache():
    """
    Limpia todo el cache del sistema.
    
    Returns:
        True si se limpió correctamente, False en caso contrario
    """
    try:
        cache.clear()
        logger.info("Cache cleared successfully")
        return True
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return False


def get_cache_info(key):
    """
    Obtiene información sobre una clave de cache.
    
    Args:
        key: Clave de cache
    
    Returns:
        Diccionario con información de la clave o None si no existe
    """
    try:
        value = cache.get(key)
        if value is not None:
            return {
                "exists": True,
                "type": type(value).__name__,
                "size": len(str(value)) if isinstance(value, (str, list, dict)) else None
            }
        else:
            return {"exists": False}
    except Exception as e:
        logger.error(f"Error obteniendo info de cache: {str(e)}")
        return None

