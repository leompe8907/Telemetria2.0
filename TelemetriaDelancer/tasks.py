"""
Tareas de Celery para sincronización y procesamiento de telemetría.

Este módulo contiene las tareas que se ejecutan periódicamente:
1. Sincronización de telemetría desde PanAccess
2. Merge de registros OTT
3. Cadena de tareas que ejecuta ambas en secuencia
"""
import logging
from celery import shared_task, chain
from django.db import transaction

from django.core.cache import cache
from datetime import datetime
from django.conf import settings

from TelemetriaDelancer.ml.constants import (
    ML_ANOMALIES_LATEST_CACHE_KEY,
    ML_FORECAST_LATEST_CACHE_KEY,
    ml_forecast_cache_key,
    ML_SEGMENTS_LATEST_CACHE_KEY,
    ml_segments_cache_key,
    ML_CHURN_LATEST_CACHE_KEY,
    ml_churn_cache_key,
)
from TelemetriaDelancer.ml.services import compute_churn_risk
from TelemetriaDelancer.ml.forecast_ml import train_ridge, predict_next_days

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def sync_telemetry_task(self):
    """
    Tarea Celery para sincronizar telemetría desde PanAccess.
    
    Descarga los registros nuevos y los guarda en la base de datos.
    Si falla, se reintentará hasta 3 veces.
    
    Returns:
        dict: Resultado de la sincronización con estadísticas
    """
    try:
        from TelemetriaDelancer.panaccess.telemetry_fetcher import (
            fetch_telemetry_records_smart,
            save_telemetry_records,
            is_database_empty,
            get_highest_record_id
        )
        
        logger.info("🔄 [CELERY] Iniciando sincronización periódica de telemetría...")
        
        # Estado inicial
        was_empty_before = is_database_empty()
        highest_id_before = get_highest_record_id()
        
        # Descargar registros nuevos
        records = fetch_telemetry_records_smart(
            limit=1000,
            process_timestamps=True
        )
        
        total_downloaded = len(records)
        
        if records:
            # Guardar en BD
            result = save_telemetry_records(records, batch_size=500)
            
            logger.info(
                f"✅ [CELERY] Sincronización completada: "
                f"{result['saved_records']} guardados, "
                f"{result['skipped_records']} omitidos, "
                f"{result['errors']} errores"
            )
            
            return {
                'success': True,
                'task': 'sync_telemetry',
                'total_downloaded': total_downloaded,
                'saved_records': result['saved_records'],
                'skipped_records': result['skipped_records'],
                'errors': result['errors'],
                'was_empty_before': was_empty_before,
                'highest_id_before': highest_id_before,
                'highest_id_after': get_highest_record_id()
            }
        else:
            logger.info("ℹ️ [CELERY] No hay registros nuevos para sincronizar")
            return {
                'success': True,
                'task': 'sync_telemetry',
                'total_downloaded': 0,
                'saved_records': 0,
                'skipped_records': 0,
                'errors': 0,
                'message': 'No hay registros nuevos'
            }
            
    except Exception as e:
        logger.error(
            f"❌ [CELERY] Error en sincronización periódica: {str(e)}",
            exc_info=True
        )
        
        # Reintentar si no hemos alcanzado el máximo
        if self.request.retries < self.max_retries:
            logger.warning(
                f"🔄 [CELERY] Reintentando sincronización "
                f"({self.request.retries + 1}/{self.max_retries})..."
            )
            raise self.retry(exc=e, countdown=60)  # Reintentar en 60 segundos
        
        # Si falló después de todos los reintentos
        logger.error(
            f"❌ [CELERY] Sincronización falló después de {self.max_retries} intentos"
        )
        return {
            'success': False,
            'task': 'sync_telemetry',
            'error': str(e),
            'retries': self.request.retries
        }


@shared_task(bind=True, max_retries=3)
def merge_ott_task(self, sync_result=None):
    """
    Tarea Celery para hacer merge de registros OTT.
    
    Fusiona los registros OTT (actionId 7 y 8) y los guarda en MergedTelemetricOTTDelancer.
    Esta tarea puede recibir el resultado de la tarea de sincronización anterior.
    
    Args:
        sync_result: Resultado de la tarea de sincronización (opcional)
    
    Returns:
        dict: Resultado del merge con estadísticas
    """
    try:
        from TelemetriaDelancer.panaccess.ott_merger import merge_ott_records
        
        logger.info("🔄 [CELERY] Iniciando merge OTT periódico...")
        
        # Si tenemos resultado de sincronización, podemos usar el highest_id_after
        max_record_id = None
        if sync_result and isinstance(sync_result, dict):
            highest_id_after = sync_result.get('highest_id_after')
            if highest_id_after:
                max_record_id = highest_id_after
                logger.info(
                    f"📊 [CELERY] Usando highest_id_after de sincronización: {max_record_id}"
                )
        
        # Ejecutar merge
        result = merge_ott_records(
            max_record_id=max_record_id,  # None = procesa todos los nuevos
            batch_size=500
        )
        
        logger.info(
            f"✅ [CELERY] Merge OTT completado: "
            f"{result['merged_records']} fusionados, "
            f"{result['saved_records']} guardados, "
            f"{result['skipped_records']} sin dataName, "
            f"{result['errors']} errores"
        )
        
        return {
            'success': True,
            'task': 'merge_ott',
            'total_processed': result['total_processed'],
            'merged_records': result['merged_records'],
            'saved_records': result['saved_records'],
            'skipped_records': result['skipped_records'],
            'errors': result['errors']
        }
        
    except Exception as e:
        logger.error(
            f"❌ [CELERY] Error en merge OTT periódico: {str(e)}",
            exc_info=True
        )
        
        # Reintentar si no hemos alcanzado el máximo
        if self.request.retries < self.max_retries:
            logger.warning(
                f"🔄 [CELERY] Reintentando merge OTT "
                f"({self.request.retries + 1}/{self.max_retries})..."
            )
            raise self.retry(exc=e, countdown=60)  # Reintentar en 60 segundos
        
        # Si falló después de todos los reintentos
        logger.error(
            f"❌ [CELERY] Merge OTT falló después de {self.max_retries} intentos"
        )
        return {
            'success': False,
            'task': 'merge_ott',
            'error': str(e),
            'retries': self.request.retries
        }


@shared_task
def sync_and_merge_telemetry_chain():
    """
    Tarea principal que ejecuta sincronización y merge en secuencia.
    
    Usa Celery chains para ejecutar:
    1. sync_telemetry_task (primero)
    2. merge_ott_task (después, usando el resultado de la primera)
    
    Esta es la tarea que se programa en el beat schedule.
    """
    logger.info("🚀 [CELERY] Iniciando cadena de tareas: Sync → Merge OTT")
    
    # Crear cadena de tareas
    # La tarea 2 recibirá el resultado de la tarea 1 como argumento
    workflow = chain(
        sync_telemetry_task.s(),
        merge_ott_task.s()
    )
    
    # Ejecutar la cadena de forma asíncrona
    result = workflow.apply_async()
    
    logger.info(f"📋 [CELERY] Cadena de tareas iniciada con ID: {result.id}")
    
    return {
        'success': True,
        'task': 'sync_and_merge_chain',
        'chain_id': result.id,
        'message': 'Cadena de tareas iniciada'
    }


@shared_task(bind=True, max_retries=2)
def compute_anomalies_task(self, threshold_std: float = 3.0, start_date: str | None = None, end_date: str | None = None):
    """
    Calcula anomalías y guarda el resultado “latest” en cache (Redis si está configurado).

    Args:
        threshold_std: Umbral en desviaciones estándar para marcar anomalías.
        start_date: YYYY-MM-DD opcional
        end_date: YYYY-MM-DD opcional
    """
    try:
        from TelemetriaDelancer.panaccess.analytics import get_anomaly_detection

        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        logger.info(
            "🔎 [CELERY] Calculando anomalías (threshold_std=%s, start_date=%s, end_date=%s)",
            threshold_std,
            start_date,
            end_date,
        )

        anomalies = get_anomaly_detection(
            threshold_std=float(threshold_std),
            start_date=start_dt,
            end_date=end_dt,
        )

        payload = {
            "success": True,
            "generated_at": datetime.now().isoformat(),
            "filters": {
                "threshold_std": float(threshold_std),
                "start_date": start_dt.date().isoformat() if start_dt else None,
                "end_date": end_dt.date().isoformat() if end_dt else None,
            },
            "data": anomalies,
        }

        cache.set(
            ML_ANOMALIES_LATEST_CACHE_KEY,
            payload,
            timeout=getattr(settings, "CACHE_TIMEOUT_ANALYTICS", 1800),
        )

        logger.info("✅ [CELERY] Anomalías calculadas y cacheadas (key=%s)", ML_ANOMALIES_LATEST_CACHE_KEY)

        return {"success": True, "task": "compute_anomalies", "count": len(anomalies)}
    except Exception as e:
        logger.error("❌ [CELERY] Error calculando anomalías: %s", str(e), exc_info=True)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        return {"success": False, "task": "compute_anomalies", "error": str(e)}


@shared_task(bind=True, max_retries=2)
def compute_forecast_task(
    self,
    channel: str | None = None,
    forecast_days: int = 7,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """
    Precomputa forecasting y lo guarda en cache por canal/horizonte.

    Nota: usa `get_time_series_analysis()` (requiere Pandas/NumPy según analytics.py).
    """
    try:
        from TelemetriaDelancer.panaccess.analytics import get_time_series_analysis

        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        logger.info(
            "📈 [CELERY] Calculando forecast (channel=%s, forecast_days=%s, start_date=%s, end_date=%s)",
            channel,
            forecast_days,
            start_date,
            end_date,
        )

        forecast = get_time_series_analysis(
            channel=channel,
            start_date=start_dt,
            end_date=end_dt,
            forecast_days=int(forecast_days),
        )

        payload = {
            "success": True,
            "generated_at": datetime.now().isoformat(),
            "filters": {
                "channel": channel,
                "forecast_days": int(forecast_days),
                "start_date": start_dt.date().isoformat() if start_dt else None,
                "end_date": end_dt.date().isoformat() if end_dt else None,
            },
            "data": forecast,
        }

        key = ml_forecast_cache_key(channel=channel, forecast_days=int(forecast_days))
        timeout = getattr(settings, "CACHE_TIMEOUT_ANALYTICS", 1800)
        cache.set(key, payload, timeout=timeout)
        cache.set(ML_FORECAST_LATEST_CACHE_KEY, payload, timeout=timeout)

        logger.info("✅ [CELERY] Forecast cacheado (key=%s)", key)
        return {"success": True, "task": "compute_forecast", "cache_key": key}
    except ImportError as e:
        # Pandas/NumPy no instalados
        logger.warning("⚠️ [CELERY] Forecast requiere Pandas/NumPy: %s", str(e))
        return {"success": False, "task": "compute_forecast", "error": "PANDAS_REQUIRED", "message": str(e)}
    except Exception as e:
        logger.error("❌ [CELERY] Error calculando forecast: %s", str(e), exc_info=True)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        return {"success": False, "task": "compute_forecast", "error": str(e)}


@shared_task(bind=True, max_retries=1)
def train_forecast_models_task(self, channels: list[str] | None = None, window_days: int = 180, alpha: float = 1.0):
    """
    Entrena modelos Ridge por canal y los persiste a disco.
    Diseñado para ejecutarse en background (no en request).
    """
    try:
        if not channels:
            # Por defecto, entrenar un set pequeño de canales top (para no sobrecargar)
            from TelemetriaDelancer.panaccess.analytics import get_top_channels
            top = get_top_channels(limit=10)
            channels = [x["channel"] for x in top if x.get("channel")]

        results = []
        for ch in channels:
            try:
                results.append(train_ridge(channel=ch, window_days=int(window_days), alpha=float(alpha)))
            except Exception as e:
                results.append({"channel": ch, "success": False, "error": str(e)})

        return {"success": True, "task": "train_forecast_models", "results": results}
    except Exception as e:
        logger.error("❌ [CELERY] Error entrenando modelos forecast: %s", str(e), exc_info=True)
        return {"success": False, "task": "train_forecast_models", "error": str(e)}


@shared_task(bind=True, max_retries=1)
def score_forecast_models_task(self, channels: list[str] | None = None, horizon_days: int = 7, window_days: int = 180):
    """
    Genera predicciones y las publica en cache (por canal/horizonte).
    """
    try:
        if not channels:
            from TelemetriaDelancer.panaccess.analytics import get_top_channels
            top = get_top_channels(limit=10)
            channels = [x["channel"] for x in top if x.get("channel")]

        timeout = getattr(settings, "CACHE_TIMEOUT_ANALYTICS", 1800)
        out = []
        for ch in channels:
            try:
                preds = predict_next_days(channel=ch, horizon_days=int(horizon_days), window_days=int(window_days))
                payload = {
                    "success": True,
                    "generated_at": datetime.now().isoformat(),
                    "filters": {
                        "channel": ch,
                        "forecast_days": int(horizon_days),
                        "model": "ridge_v1",
                        "window_days": int(window_days),
                    },
                    "data": {"forecast": preds, "channel": ch},
                }
                key = ml_forecast_cache_key(channel=ch, forecast_days=int(horizon_days))
                cache.set(key, payload, timeout=timeout)
                cache.set(ML_FORECAST_LATEST_CACHE_KEY, payload, timeout=timeout)
                out.append({"channel": ch, "cache_key": key, "count": len(preds)})
            except Exception as e:
                out.append({"channel": ch, "success": False, "error": str(e)})

        return {"success": True, "task": "score_forecast_models", "results": out}
    except Exception as e:
        logger.error("❌ [CELERY] Error haciendo scoring forecast: %s", str(e), exc_info=True)
        return {"success": False, "task": "score_forecast_models", "error": str(e)}


@shared_task(bind=True, max_retries=2)
def compute_segments_task(self, n_segments: int = 4, window_days: int = 30):
    """
    Precomputa segmentación K-means y la guarda en cache.
    Requiere Pandas/NumPy según `get_user_segmentation_analysis()`.
    """
    try:
        from datetime import timedelta
        from TelemetriaDelancer.panaccess.analytics import get_user_segmentation_analysis

        n_segments = int(n_segments)
        window_days = int(window_days)
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=window_days)

        logger.info(
            "🧩 [CELERY] Calculando segmentación (n_segments=%s, window_days=%s)",
            n_segments,
            window_days,
        )

        segments = get_user_segmentation_analysis(
            start_date=start_dt,
            end_date=end_dt,
            n_segments=n_segments,
        )

        payload = {
            "success": True,
            "generated_at": datetime.now().isoformat(),
            "filters": {
                "n_segments": n_segments,
                "window_days": window_days,
                "start_date": start_dt.date().isoformat(),
                "end_date": end_dt.date().isoformat(),
            },
            "data": segments,
        }

        key = ml_segments_cache_key(n_segments=n_segments, window_days=window_days)
        timeout = getattr(settings, "CACHE_TIMEOUT_ANALYTICS", 1800)
        cache.set(key, payload, timeout=timeout)
        cache.set(ML_SEGMENTS_LATEST_CACHE_KEY, payload, timeout=timeout)

        logger.info("✅ [CELERY] Segmentación cacheada (key=%s)", key)
        return {"success": True, "task": "compute_segments", "cache_key": key}
    except ImportError as e:
        logger.warning("⚠️ [CELERY] Segmentación requiere Pandas/NumPy: %s", str(e))
        return {"success": False, "task": "compute_segments", "error": "PANDAS_REQUIRED", "message": str(e)}
    except Exception as e:
        logger.error("❌ [CELERY] Error calculando segmentación: %s", str(e), exc_info=True)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        return {"success": False, "task": "compute_segments", "error": str(e)}


@shared_task(bind=True, max_retries=2)
def compute_churn_task(self, window_days: int = 14, min_views: int = 3):
    """
    Precomputa churn/riesgo (heurístico) y lo guarda en cache.
    No requiere dependencias extra.
    """
    try:
        window_days = int(window_days)
        min_views = int(min_views)

        logger.info("🧯 [CELERY] Calculando churn risk (window_days=%s, min_views=%s)", window_days, min_views)

        data = compute_churn_risk(window_days=window_days, min_views=min_views)
        payload = {
            "success": True,
            "generated_at": datetime.now().isoformat(),
            "filters": {"window_days": window_days, "min_views": min_views},
            "data": data,
        }

        key = ml_churn_cache_key(window_days=window_days)
        timeout = getattr(settings, "CACHE_TIMEOUT_ANALYTICS", 1800)
        cache.set(key, payload, timeout=timeout)
        cache.set(ML_CHURN_LATEST_CACHE_KEY, payload, timeout=timeout)

        logger.info("✅ [CELERY] Churn risk cacheado (key=%s)", key)
        return {"success": True, "task": "compute_churn", "cache_key": key}
    except Exception as e:
        logger.error("❌ [CELERY] Error calculando churn: %s", str(e), exc_info=True)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        return {"success": False, "task": "compute_churn", "error": str(e)}

