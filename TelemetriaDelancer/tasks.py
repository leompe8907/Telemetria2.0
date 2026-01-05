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

