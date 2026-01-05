"""
Vistas de health check y monitoreo del sistema.

Este módulo proporciona endpoints para verificar el estado del sistema,
incluyendo base de datos, Redis, Celery y PanAccess.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import logging
from datetime import datetime
import time

from django.db import connection
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Endpoint básico de health check.
    
    Retorna el estado general del sistema.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        GET: Verifica el estado básico del sistema.
        
        Returns:
            Response con estado del sistema
        """
        return Response({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "TelemetriaDelancer API",
            "version": "1.0.0"
        }, status=status.HTTP_200_OK)


class DetailedHealthCheckView(APIView):
    """
    Endpoint detallado de health check.
    
    Verifica el estado de todos los componentes del sistema:
    - Base de datos
    - Redis/Cache
    - Celery (si está disponible)
    - PanAccess (conexión)
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        GET: Verifica el estado detallado de todos los componentes.
        
        Returns:
            Response con estado detallado de cada componente
        """
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "TelemetriaDelancer API",
            "version": "1.0.0",
            "components": {}
        }
        
        overall_healthy = True
        
        # 1. Verificar Base de Datos
        db_status = self._check_database()
        health_status["components"]["database"] = db_status
        if not db_status["healthy"]:
            overall_healthy = False
        
        # 2. Verificar Redis/Cache
        cache_status = self._check_cache()
        health_status["components"]["cache"] = cache_status
        if not cache_status["healthy"]:
            overall_healthy = False
        
        # 3. Verificar Celery
        celery_status = self._check_celery()
        health_status["components"]["celery"] = celery_status
        if not celery_status["healthy"]:
            overall_healthy = False
        
        # 4. Verificar PanAccess
        panaccess_status = self._check_panaccess()
        health_status["components"]["panaccess"] = panaccess_status
        if not panaccess_status["healthy"]:
            overall_healthy = False
        
        # 5. Estadísticas generales
        health_status["statistics"] = self._get_statistics()
        
        # Determinar estado general
        health_status["status"] = "healthy" if overall_healthy else "degraded"
        
        http_status = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(health_status, status=http_status)
    
    def _check_database(self):
        """Verifica la conexión a la base de datos."""
        try:
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            response_time = (time.time() - start_time) * 1000  # en milisegundos
            
            # Obtener información de la base de datos
            db_name = connection.settings_dict.get('NAME', 'unknown')
            db_host = connection.settings_dict.get('HOST', 'unknown')
            
            return {
                "healthy": True,
                "status": "connected",
                "response_time_ms": round(response_time, 2),
                "database": db_name,
                "host": db_host,
                "message": "Base de datos conectada correctamente"
            }
        except Exception as e:
            logger.error(f"Error verificando base de datos: {str(e)}", exc_info=True)
            return {
                "healthy": False,
                "status": "disconnected",
                "error": str(e),
                "message": "Error al conectar con la base de datos"
            }
    
    def _check_cache(self):
        """Verifica la conexión a Redis/Cache."""
        try:
            start_time = time.time()
            # Intentar escribir y leer del cache
            test_key = "health_check_test"
            test_value = f"test_{int(time.time())}"
            
            cache.set(test_key, test_value, timeout=10)
            retrieved_value = cache.get(test_key)
            cache.delete(test_key)
            
            response_time = (time.time() - start_time) * 1000  # en milisegundos
            
            if retrieved_value == test_value:
                return {
                    "healthy": True,
                    "status": "connected",
                    "response_time_ms": round(response_time, 2),
                    "backend": settings.CACHES.get('default', {}).get('BACKEND', 'unknown'),
                    "message": "Cache/Redis funcionando correctamente"
                }
            else:
                return {
                    "healthy": False,
                    "status": "error",
                    "message": "Cache no retornó el valor esperado"
                }
        except Exception as e:
            logger.error(f"Error verificando cache: {str(e)}", exc_info=True)
            return {
                "healthy": False,
                "status": "disconnected",
                "error": str(e),
                "message": "Error al conectar con Redis/Cache"
            }
    
    def _check_celery(self):
        """Verifica el estado de Celery."""
        try:
            from celery import current_app
            from celery.result import AsyncResult
            
            # Verificar si hay workers activos
            inspect = current_app.control.inspect()
            active_workers = inspect.active()
            
            if active_workers is None:
                return {
                    "healthy": False,
                    "status": "no_workers",
                    "message": "No hay workers de Celery activos"
                }
            
            worker_count = len(active_workers) if active_workers else 0
            
            # Obtener estadísticas de Celery
            stats = inspect.stats()
            
            return {
                "healthy": True,
                "status": "running",
                "workers": worker_count,
                "active_tasks": sum(len(tasks) for tasks in active_workers.values()) if active_workers else 0,
                "stats": stats if stats else {},
                "message": f"Celery funcionando con {worker_count} worker(s) activo(s)"
            }
        except ImportError:
            return {
                "healthy": False,
                "status": "not_configured",
                "message": "Celery no está configurado"
            }
        except Exception as e:
            logger.error(f"Error verificando Celery: {str(e)}", exc_info=True)
            return {
                "healthy": False,
                "status": "error",
                "error": str(e),
                "message": "Error al verificar estado de Celery"
            }
    
    def _check_panaccess(self):
        """Verifica la conexión con PanAccess."""
        try:
            from TelemetriaDelancer.server.panaccess_singleton import get_panaccess
            
            start_time = time.time()
            panaccess = get_panaccess()
            
            # Verificar si hay sesión activa
            has_session = panaccess.client.session_id is not None
            
            # Intentar verificar la sesión (sin hacer login si no hay)
            if has_session:
                try:
                    from TelemetriaDelancer.utils.auth import logged_in
                    is_valid = logged_in(panaccess.client.session_id)
                    response_time = (time.time() - start_time) * 1000
                    
                    return {
                        "healthy": True,
                        "status": "connected",
                        "response_time_ms": round(response_time, 2),
                        "session_active": True,
                        "session_valid": is_valid,
                        "message": "PanAccess conectado y sesión activa" if is_valid else "PanAccess conectado pero sesión inválida"
                    }
                except Exception as e:
                    logger.warning(f"Error verificando sesión PanAccess: {str(e)}")
                    return {
                        "healthy": True,  # No es crítico si la sesión no es válida
                        "status": "connected",
                        "session_active": True,
                        "session_valid": False,
                        "message": "PanAccess conectado pero no se pudo verificar sesión"
                    }
            else:
                return {
                    "healthy": True,  # No es crítico si no hay sesión activa
                    "status": "not_authenticated",
                    "session_active": False,
                    "message": "PanAccess configurado pero sin sesión activa"
                }
        except Exception as e:
            logger.error(f"Error verificando PanAccess: {str(e)}", exc_info=True)
            return {
                "healthy": False,
                "status": "error",
                "error": str(e),
                "message": "Error al verificar estado de PanAccess"
            }
    
    def _get_statistics(self):
        """Obtiene estadísticas generales del sistema."""
        try:
            from TelemetriaDelancer.models import (
                TelemetryRecordEntryDelancer,
                MergedTelemetricOTTDelancer
            )
            from django.db.models import Count, Max
            
            # Estadísticas de registros
            total_records = TelemetryRecordEntryDelancer.objects.count()
            max_record_id = TelemetryRecordEntryDelancer.objects.aggregate(Max('recordId'))['recordId__max']
            
            # Estadísticas de OTT merged
            total_ott_merged = MergedTelemetricOTTDelancer.objects.count()
            
            # Último registro
            last_record = TelemetryRecordEntryDelancer.objects.order_by('-timestamp').first()
            last_timestamp = last_record.timestamp.isoformat() if last_record and last_record.timestamp else None
            
            return {
                "total_records": total_records,
                "max_record_id": max_record_id,
                "total_ott_merged": total_ott_merged,
                "last_record_timestamp": last_timestamp
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}", exc_info=True)
            return {
                "error": "No se pudieron obtener estadísticas",
                "details": str(e)
            }


class MetricsView(APIView):
    """
    Endpoint para obtener métricas del sistema.
    
    Proporciona información detallada sobre el rendimiento y uso del sistema.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        GET: Obtiene métricas del sistema.
        
        Returns:
            Response con métricas del sistema
        """
        try:
            from TelemetriaDelancer.models import (
                TelemetryRecordEntryDelancer,
                MergedTelemetricOTTDelancer
            )
            from django.db.models import Count, Max, Min, Avg
            from datetime import datetime, timedelta
            
            # Métricas de registros
            total_records = TelemetryRecordEntryDelancer.objects.count()
            
            # Registros por actionId
            records_by_action = TelemetryRecordEntryDelancer.objects.values('actionId').annotate(
                count=Count('actionId')
            ).order_by('-count')[:10]
            
            # Registros en las últimas 24 horas
            yesterday = datetime.now() - timedelta(days=1)
            recent_records = TelemetryRecordEntryDelancer.objects.filter(
                timestamp__gte=yesterday
            ).count()
            
            # Estadísticas de OTT
            total_ott = MergedTelemetricOTTDelancer.objects.count()
            
            # Último registro
            last_record = TelemetryRecordEntryDelancer.objects.order_by('-timestamp').first()
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "records": {
                    "total": total_records,
                    "last_24h": recent_records,
                    "by_action": list(records_by_action),
                    "last_record": {
                        "record_id": last_record.recordId if last_record else None,
                        "timestamp": last_record.timestamp.isoformat() if last_record and last_record.timestamp else None
                    }
                },
                "ott_merged": {
                    "total": total_ott
                },
                "database": {
                    "name": connection.settings_dict.get('NAME', 'unknown'),
                    "host": connection.settings_dict.get('HOST', 'unknown')
                }
            }
            
            return Response(metrics, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas: {str(e)}", exc_info=True)
            return Response(
                {
                    "error": "Error al obtener métricas",
                    "message": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

