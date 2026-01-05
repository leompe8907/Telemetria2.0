"""
Mixins para vistas con cache.

Este módulo proporciona mixins para agregar funcionalidad de cache
a las vistas de la API.
"""
from django.core.cache import cache
from django.conf import settings
from rest_framework.response import Response
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class CacheMixin:
    """
    Mixin para agregar cache a las vistas de API.
    
    Usage:
        class MyView(CacheMixin, APIView):
            cache_timeout = 300  # 5 minutos
            cache_key_prefix = 'my_view'
            
            def get(self, request):
                return self.get_cached_response(request, self._get_data)
            
            def _get_data(self, request):
                # Tu lógica aquí
                return {"data": "result"}
    """
    cache_timeout = None  # None = usar CACHE_TIMEOUT_MEDIUM
    cache_key_prefix = None  # None = usar nombre de la clase
    
    def get_cache_key(self, request, *args, **kwargs):
        """
        Genera una clave de cache única para la petición.
        
        Args:
            request: Request object
            *args: Argumentos adicionales
            **kwargs: Argumentos con nombre
        
        Returns:
            Clave de cache generada
        """
        prefix = self.cache_key_prefix or self.__class__.__name__
        
        # Incluir método HTTP
        method = request.method
        
        # Incluir parámetros de query
        query_params = dict(request.query_params)
        
        # Incluir body si es POST/PUT/PATCH
        body_data = {}
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body_data = request.data
            except Exception:
                pass
        
        # Crear string para hashear
        key_parts = [
            prefix,
            method,
            json.dumps(query_params, sort_keys=True, default=str),
            json.dumps(body_data, sort_keys=True, default=str),
            json.dumps(args, sort_keys=True, default=str),
            json.dumps(kwargs, sort_keys=True, default=str),
        ]
        
        key_string = "|".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"telemetria:view:{prefix}:{key_hash}"
    
    def get_cached_response(self, request, data_func, *args, **kwargs):
        """
        Obtiene una respuesta cacheada o ejecuta la función y cachea el resultado.
        
        Args:
            request: Request object
            data_func: Función que genera los datos (se ejecuta si no hay cache)
            *args: Argumentos para data_func
            **kwargs: Argumentos con nombre para data_func
        
        Returns:
            Response con los datos (cacheados o nuevos)
        """
        # Verificar si se debe usar cache (puede ser deshabilitado con ?no_cache=1)
        use_cache = request.query_params.get('no_cache', '0') != '1'
        
        if not use_cache:
            logger.debug("Cache deshabilitado por parámetro no_cache")
            data = data_func(request, *args, **kwargs)
            return Response(data)
        
        # Generar clave de cache
        cache_key = self.get_cache_key(request, *args, **kwargs)
        
        # Intentar obtener del cache
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.debug(f"Cache HIT: {cache_key}")
            return Response(cached_data)
        
        # Cache miss - ejecutar función
        logger.debug(f"Cache MISS: {cache_key}")
        data = data_func(request, *args, **kwargs)
        
        # Guardar en cache
        timeout = self.cache_timeout or getattr(settings, 'CACHE_TIMEOUT_MEDIUM', 300)
        try:
            cache.set(cache_key, data, timeout=timeout)
            logger.debug(f"Cached response for {cache_key} (timeout: {timeout}s)")
        except Exception as e:
            logger.warning(f"Error al guardar en cache: {str(e)}")
        
        return Response(data)
    
    def wrap_with_cache(self, method_func):
        """
        Wrapper para métodos que retornan Response directamente.
        
        Usage:
            def post(self, request):
                return self.wrap_with_cache(self._post_impl)(request)
            
            def _post_impl(self, request):
                # Tu lógica aquí
                return Response(data)
        """
        def wrapper(request, *args, **kwargs):
            # Verificar si se debe usar cache
            use_cache = request.query_params.get('no_cache', '0') != '1'
            
            if not use_cache:
                logger.debug("Cache deshabilitado por parámetro no_cache")
                return method_func(request, *args, **kwargs)
            
            # Generar clave de cache
            cache_key = self.get_cache_key(request, *args, **kwargs)
            
            # Intentar obtener del cache
            cached_response_data = cache.get(cache_key)
            if cached_response_data is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return Response(cached_response_data['data'], status=cached_response_data.get('status', 200))
            
            # Cache miss - ejecutar método
            logger.debug(f"Cache MISS: {cache_key}")
            response = method_func(request, *args, **kwargs)
            
            # Extraer datos del Response para cachear
            if hasattr(response, 'data'):
                response_data = response.data
                response_status = response.status_code
            else:
                # Si no es un Response de DRF, intentar obtener contenido
                response_data = getattr(response, 'content', None)
                response_status = getattr(response, 'status_code', 200)
            
            # Guardar en cache
            timeout = self.cache_timeout or getattr(settings, 'CACHE_TIMEOUT_MEDIUM', 300)
            try:
                cache.set(cache_key, {
                    'data': response_data,
                    'status': response_status
                }, timeout=timeout)
                logger.debug(f"Cached response for {cache_key} (timeout: {timeout}s)")
            except Exception as e:
                logger.warning(f"Error al guardar en cache: {str(e)}")
            
            return response
        
        return wrapper
    
    def invalidate_cache(self, pattern=None):
        """
        Invalida el cache de esta vista.
        
        Args:
            pattern: Patrón opcional para invalidar (None = invalidar todo de esta vista)
        """
        if pattern is None:
            prefix = self.cache_key_prefix or self.__class__.__name__
            pattern = f"telemetria:view:{prefix}:*"
        
        from TelemetriaDelancer.utils.cache_utils import invalidate_cache_pattern
        return invalidate_cache_pattern(pattern)

