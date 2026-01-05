"""
Módulo para obtener registros de telemetría desde PanAccess.

Este módulo proporciona funciones para consultar getListOfTelemetryRecords
usando el singleton de PanAccess, con manejo inteligente de descarga
y procesamiento de timestamps.

FLUJO DE DATOS:
1. PanAccess API → getListOfTelemetryRecords() → Obtiene datos de PanAccess
2. Los datos se procesan y guardan en TelemetryRecordEntryDelancer (BD local)
3. Los análisis trabajan con la BD local, NO consultan PanAccess directamente

IMPORTANTE: Este módulo es el ÚNICO punto de contacto con PanAccess para obtener datos.
Los módulos de análisis (analytics.py, etc.) trabajan exclusivamente con la BD local.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from TelemetriaDelancer.server.panaccess_singleton import get_panaccess
from TelemetriaDelancer.models import TelemetryRecordEntryDelancer
from TelemetriaDelancer.exceptions import PanAccessException

logger = logging.getLogger(__name__)


# ============================================================================
# FUNCIONES DE VALIDACIÓN DE BASE DE DATOS
# ============================================================================

def is_database_empty() -> bool:
    """
    Verifica si la base de datos está vacía.
    
    Returns:
        True si no hay registros en la BD, False si hay registros
    """
    return not TelemetryRecordEntryDelancer.objects.exists()


def get_highest_record_id() -> Optional[int]:
    """
    Obtiene el recordId más alto (más reciente) de la base de datos.
    
    Returns:
        El recordId más alto, o None si la BD está vacía
    """
    highest_record = TelemetryRecordEntryDelancer.objects.order_by('-recordId').first()
    return highest_record.recordId if highest_record else None


# ============================================================================
# FUNCIONES DE PROCESAMIENTO DE TIMESTAMP
# ============================================================================

def get_time_date(timestamp: str) -> int:
    """
    Extrae la hora de un timestamp.
    
    Args:
        timestamp: String con formato "YYYY-MM-DD HH:MM:SS"
    
    Returns:
        Hora del día (0-23)
    
    Raises:
        ValueError: Si el formato del timestamp es inválido
    """
    try:
        data = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        return data.hour
    except ValueError as e:
        logger.error(f"Error al parsear timestamp para hora: {timestamp} - {str(e)}")
        raise


def get_data_date(timestamp: str) -> str:
    """
    Extrae la fecha de un timestamp.
    
    Args:
        timestamp: String con formato "YYYY-MM-DD HH:MM:SS"
    
    Returns:
        Fecha en formato ISO (YYYY-MM-DD)
    
    Raises:
        ValueError: Si el formato del timestamp es inválido
    """
    try:
        data = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        return data.date().isoformat()
    except ValueError as e:
        logger.error(f"Error al parsear timestamp para fecha: {timestamp} - {str(e)}")
        raise


def extract_timestamp_details(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extrae detalles del timestamp (fecha y hora) y los añade a cada registro.
    
    Modifica los registros in-place agregando los campos:
    - dataDate: Fecha en formato ISO (YYYY-MM-DD)
    - timeDate: Hora del día (0-23)
    
    Args:
        data: Lista de diccionarios con registros de telemetría
    
    Returns:
        Lista de registros con dataDate y timeDate agregados
    """
    for record in data:
        try:
            timestamp = record.get("timestamp")
            if timestamp:
                record["dataDate"] = get_data_date(timestamp)
                record["timeDate"] = get_time_date(timestamp)
            else:
                record["dataDate"] = None
                record["timeDate"] = None
        except (ValueError, KeyError) as e:
            logger.debug(f"Error procesando timestamp recordId {record.get('recordId', 'N/A')}: {e}")
            record["dataDate"] = None
            record["timeDate"] = None
    
    return data


# ============================================================================
# FUNCIONES DE OBTENCIÓN DE REGISTROS DESDE PANACCESS
# ============================================================================

def get_telemetry_records(
    offset: int = 0,
    limit: int = 100,
    order_by: str = "recordId",
    order_dir: str = "DESC"
) -> Dict[str, Any]:
    """
    Obtiene una lista de registros de telemetría desde PanAccess.
    
    Usa el singleton de PanAccess que maneja automáticamente:
    - La sesión (sessionId)
    - El refresco de sesión si expira
    - Reintentos en caso de errores
    
    Args:
        offset: Índice para empezar la recuperación (usado para paginación)
        limit: Cantidad máxima de items a recibir (máximo 1000, se ajusta automáticamente)
        order_by: Campo para ordenar
        order_dir: Dirección del ordenamiento ('ASC' o 'DESC')
    
    Returns:
        Diccionario con la respuesta de PanAccess
    
    Raises:
        PanAccessException: Si hay algún error en la llamada
        ValueError: Si los parámetros son inválidos
    """
    # Validar parámetros
    if limit > 1000:
        logger.debug(f"Limit ajustado de {limit} a 1000 (máximo permitido)")
        limit = 1000
    
    if limit <= 0:
        raise ValueError("limit debe ser mayor a 0")
    
    if offset < 0:
        raise ValueError("offset debe ser mayor o igual a 0")
    
    if order_dir not in ('ASC', 'DESC'):
        raise ValueError("order_dir debe ser 'ASC' o 'DESC'")
    
    # Campos válidos para ordenamiento
    valid_order_fields = [
        "recordId", "subscriberCode", "deviceId", "smartcardId", "anonymized",
        "actionId", "actionKey", "date", "timestamp", "manual", "reaonId",
        "reasonKey", "dataNetId", "dataTsId", "dataSeviceId", "dataId",
        "dataName", "dataPrice", "dataDuration", "whoisCountry", "whoisIsp",
        "ipId", "ip", "profileId", "created"
    ]
    
    if order_by not in valid_order_fields:
        raise ValueError(
            f"order_by debe ser uno de: {', '.join(valid_order_fields)}"
        )
    
    # Preparar parámetros
    parameters = {
        "offset": offset,
        "limit": limit,
        "orderBy": order_by,
        "orderDir": order_dir
    }
    
    logger.debug(f"Obteniendo registros - offset={offset}, limit={limit}")
    
    try:
        # Obtener el singleton (maneja sesión automáticamente)
        panaccess = get_panaccess()
        
        logger.info(f"Llamando a PanAccess getListOfTelemetryRecords (offset={offset}, limit={limit})...")
        
        # Llamar a PanAccess usando el singleton
        try:
            response = panaccess.call(
                func_name="getListOfTelemetryRecords",
                parameters=parameters,
                timeout=120
            )
            logger.info(f"Respuesta recibida de PanAccess exitosamente")
        except Exception as e:
            logger.error(f"Error en llamada a PanAccess: {str(e)}", exc_info=True)
            raise
        
        # Verificar si la llamada fue exitosa
        if not response.get("success"):
            error_message = response.get("errorMessage", "Error desconocido")
            logger.error(f"❌ Error al obtener registros: {error_message}")
            raise PanAccessException(f"Error en getListOfTelemetryRecords: {error_message}")
        
        # Extraer datos
        answer = response.get("answer", {})
        records = answer.get("telemetryRecordEntries", [])
        
        logger.debug(f"Obtenidos {len(records)} registros")
        
        return response
        
    except PanAccessException:
        raise
    except Exception as e:
        logger.error(f"💥 Error inesperado al obtener registros: {str(e)}", exc_info=True)
        raise PanAccessException(f"Error inesperado: {str(e)}")


def fetch_all_telemetry_records(
    limit: int = 100,
    order_by: str = "recordId",
    order_dir: str = "DESC",
    max_records: Optional[int] = None,
    process_timestamps: bool = True
) -> List[Dict[str, Any]]:
    """
    Obtiene TODOS los registros de telemetría con paginación automática.
    
    Esta función maneja la paginación automáticamente, haciendo múltiples
    llamadas hasta obtener todos los registros disponibles.
    
    Args:
        limit: Cantidad de registros por página (máximo 1000)
        order_by: Campo para ordenar
        order_dir: Dirección del ordenamiento ('ASC' o 'DESC')
        max_records: Límite máximo de registros a obtener (None = todos)
        process_timestamps: Si True, procesa timestamps para extraer fecha/hora
    
    Returns:
        Lista con todos los registros de telemetría (con dataDate y timeDate si process_timestamps=True)
    
    Raises:
        PanAccessException: Si hay algún error en las llamadas
    """
    all_records = []
    offset = 0
    
    logger.info(f"Iniciando descarga completa (limit={limit})")
    
    page_count = 0
    while True:
        try:
            page_count += 1
            logger.debug(f"Obteniendo página {page_count} (offset={offset}, limit={limit})")
            
            # Obtener página actual
            response = get_telemetry_records(
                offset=offset,
                limit=limit,
                order_by=order_by,
                order_dir=order_dir
            )
            
            answer = response.get("answer", {})
            records = answer.get("telemetryRecordEntries", [])
            
            logger.debug(f"Página {page_count}: obtenidos {len(records)} registros")
            
            if not records:
                logger.info(f"No hay más registros en página {page_count}")
                break
            
            # Procesar timestamps si se solicita
            if process_timestamps:
                records = extract_timestamp_details(records)
            
            # Agregar registros a la lista
            all_records.extend(records)
            
            # Log cada 1,000 registros para ver progreso más frecuente
            if len(all_records) % 1000 == 0:
                logger.info(f"Progreso: {len(all_records)} registros descargados ({page_count} páginas)")
            
            # Verificar si alcanzamos el máximo
            if max_records and len(all_records) >= max_records:
                all_records = all_records[:max_records]
                break
            
            # Si obtuvimos menos registros que el límite, es la última página
            if len(records) < limit:
                break
            
            # Preparar siguiente página
            offset += limit
            
        except PanAccessException as e:
            logger.error(f"❌ Error al obtener registros en offset {offset}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"💥 Error inesperado: {str(e)}", exc_info=True)
            raise PanAccessException(f"Error inesperado: {str(e)}")
    
    logger.info(f"Descarga completa: {len(all_records)} registros totales descargados")
    return all_records


def fetch_telemetry_records_until(
    highest_record_id: int,
    limit: int = 100,
    order_by: str = "recordId",
    order_dir: str = "DESC",
    process_timestamps: bool = True
) -> List[Dict[str, Any]]:
    """
    Obtiene registros de telemetría hasta un recordId específico.
    
    Útil para obtener solo los registros nuevos que no están en la base de datos.
    Se detiene cuando encuentra el recordId objetivo.
    
    Args:
        highest_record_id: El recordId más alto que ya tienes en la BD
        limit: Cantidad de registros por página (máximo 1000)
        order_by: Campo para ordenar (debe ser 'recordId' para esta función)
        order_dir: Dirección del ordenamiento ('DESC' recomendado)
        process_timestamps: Si True, procesa timestamps para extraer fecha/hora
    
    Returns:
        Lista con los registros nuevos (recordId > highest_record_id)
    
    Raises:
        PanAccessException: Si hay algún error en las llamadas
        ValueError: Si los parámetros son inválidos
    """
    if order_by != "recordId":
        logger.debug(f"order_by debería ser 'recordId', usando '{order_by}'")
    
    all_records = []
    offset = 0
    found_target = False
    
    logger.info(f"Descargando registros nuevos desde recordId {highest_record_id}")
    
    while not found_target:
        try:
            # Obtener página actual
            response = get_telemetry_records(
                offset=offset,
                limit=limit,
                order_by=order_by,
                order_dir=order_dir
            )
            
            answer = response.get("answer", {})
            records = answer.get("telemetryRecordEntries", [])
            
            if not records:
                break
            
            # Procesar timestamps si se solicita
            if process_timestamps:
                records = extract_timestamp_details(records)
            
            # Procesar registros de esta página
            for record in records:
                record_id = record.get("recordId")
                
                # Si encontramos el recordId objetivo, parar
                if record_id == highest_record_id:
                    found_target = True
                    break
                
                # Solo agregar registros con recordId mayor al objetivo
                if record_id and record_id > highest_record_id:
                    all_records.append(record)
                elif record_id and record_id <= highest_record_id:
                    # Si el recordId es menor o igual, ya pasamos el objetivo
                    if order_dir == "DESC":
                        found_target = True
                        break
            
            # Si obtuvimos menos registros que el límite, es la última página
            if len(records) < limit:
                break
            
            # Si encontramos el objetivo, parar
            if found_target:
                break
            
            # Preparar siguiente página
            offset += limit
            
        except PanAccessException as e:
            logger.error(f"❌ Error al obtener registros en offset {offset}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"💥 Error inesperado: {str(e)}", exc_info=True)
            raise PanAccessException(f"Error inesperado: {str(e)}")
    
    logger.info(f"Descarga completa: {len(all_records)} registros nuevos")
    return all_records


# ============================================================================
# FUNCIÓN INTELIGENTE DE DESCARGA
# ============================================================================

def fetch_telemetry_records_smart(
    limit: int = 100,
    process_timestamps: bool = True
) -> List[Dict[str, Any]]:
    """
    Función inteligente que decide automáticamente qué descargar:
    - Si la BD está vacía: descarga TODOS los registros en lotes de 'limit'
    - Si la BD tiene registros: descarga solo los NUEVOS desde el último recordId
    
    Args:
        limit: Cantidad de registros por página (default: 100, máximo 1000)
        process_timestamps: Si True, procesa timestamps para extraer fecha/hora
    
    Returns:
        Lista con los registros obtenidos (con dataDate y timeDate si process_timestamps=True)
    
    Raises:
        PanAccessException: Si hay algún error en las llamadas
    """
    # Verificar si la BD está vacía
    if is_database_empty():
        logger.info(f"BD vacía - descargando TODOS los registros en lotes de {limit}")
        return fetch_all_telemetry_records(
            limit=limit,
            process_timestamps=process_timestamps
        )
    else:
        # Obtener el último recordId
        highest_record_id = get_highest_record_id()
        
        if highest_record_id is None:
            logger.warning("BD no vacía pero sin recordId - descargando todos los registros")
            return fetch_all_telemetry_records(
                limit=limit,
                process_timestamps=process_timestamps
            )
        
        logger.info(f"Descargando registros nuevos desde recordId {highest_record_id}")
        return fetch_telemetry_records_until(
            highest_record_id=highest_record_id,
            limit=limit,
            process_timestamps=process_timestamps
        )


# ============================================================================
# FUNCIÓN PARA GUARDAR REGISTROS EN LA BASE DE DATOS
# ============================================================================

def save_telemetry_records(
    records: List[Dict[str, Any]],
    batch_size: int = 500
) -> Dict[str, Any]:
    """
    Guarda registros de telemetría en la base de datos.
    
    Convierte los diccionarios de PanAccess a objetos TelemetryRecordEntry
    y los guarda usando bulk_create para eficiencia.
    
    Args:
        records: Lista de diccionarios con registros de telemetría
        batch_size: Tamaño del lote para bulk_create (default: 500)
    
    Returns:
        Diccionario con estadísticas del guardado:
        {
            "total_records": int,
            "saved_records": int,
            "skipped_records": int,
            "errors": int
        }
    """
    from django.db import transaction
    from django.core.exceptions import ValidationError
    
    if not records:
        return {
            "total_records": 0,
            "saved_records": 0,
            "skipped_records": 0,
            "errors": 0
        }
    
    logger.info(f"Guardando {len(records)} registros en BD")
    
    # Obtener recordIds existentes para evitar duplicados
    existing_record_ids = set(
        TelemetryRecordEntryDelancer.objects.filter(
            recordId__in=[r.get("recordId") for r in records if r.get("recordId")]
        ).values_list('recordId', flat=True)
    )
    
    saved_count = 0
    skipped_count = 0
    error_count = 0
    telemetry_objects = []
    
    for record in records:
        try:
            record_id = record.get("recordId")
            
            # Saltar si ya existe
            if record_id and record_id in existing_record_ids:
                skipped_count += 1
                continue
            
            # Convertir timestamp de string a datetime
            timestamp = None
            if record.get("timestamp"):
                try:
                    timestamp = datetime.strptime(record["timestamp"], "%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    logger.debug(f"Timestamp inválido recordId {record_id}")
            
            # Convertir dataDate de string a date
            data_date = None
            if record.get("dataDate"):
                try:
                    if isinstance(record["dataDate"], str):
                        data_date = datetime.strptime(record["dataDate"], "%Y-%m-%d").date()
                    else:
                        data_date = record["dataDate"]
                except (ValueError, TypeError):
                    logger.debug(f"dataDate inválido recordId {record_id}")
            
            # Crear objeto del modelo
            telemetry_obj = TelemetryRecordEntryDelancer(
                actionId=record.get("actionId"),
                actionKey=record.get("actionKey"),
                anonymized=record.get("anonymized"),
                data=record.get("data"),
                dataDuration=record.get("dataDuration"),
                dataId=record.get("dataId"),
                dataName=record.get("dataName"),
                dataNetId=record.get("dataNetId"),
                dataPrice=record.get("dataPrice"),
                dataSeviceId=record.get("dataSeviceId"),
                dataTsId=record.get("dataTsId"),
                date=record.get("date"),
                deviceId=record.get("deviceId"),
                ip=record.get("ip"),
                ipId=record.get("ipId"),
                manual=record.get("manual"),
                profileId=record.get("profileId"),
                reaonId=record.get("reaonId"),
                reasonKey=record.get("reasonKey"),
                recordId=record_id,
                smartcardId=record.get("smartcardId"),
                subscriberCode=record.get("subscriberCode"),
                timestamp=timestamp,
                dataDate=data_date,
                timeDate=record.get("timeDate"),
                whoisCountry=record.get("whoisCountry"),
                whoisIsp=record.get("whoisIsp"),
            )
            
            telemetry_objects.append(telemetry_obj)
            
            # Guardar en lotes
            if len(telemetry_objects) >= batch_size:
                with transaction.atomic():
                    TelemetryRecordEntryDelancer.objects.bulk_create(
                        telemetry_objects,
                        ignore_conflicts=True
                    )
                saved_count += len(telemetry_objects)
                # Log cada 10,000 registros para no saturar
                if saved_count % 10000 == 0:
                    logger.debug(f"Progreso guardado: {saved_count}/{len(records)}")
                telemetry_objects = []
                
        except Exception as e:
            error_count += 1
            logger.error(f"❌ Error procesando registro {record.get('recordId', 'N/A')}: {str(e)}")
            continue
    
    # Guardar registros restantes
    if telemetry_objects:
        try:
            with transaction.atomic():
                TelemetryRecordEntryDelancer.objects.bulk_create(
                    telemetry_objects,
                    ignore_conflicts=True
                )
            saved_count += len(telemetry_objects)
        except Exception as e:
            error_count += len(telemetry_objects)
            logger.error(f"❌ Error guardando último lote: {str(e)}")
    
    result = {
        "total_records": len(records),
        "saved_records": saved_count,
        "skipped_records": skipped_count,
        "errors": error_count
    }
    
    logger.info(f"Guardado: {saved_count} guardados, {skipped_count} omitidos, {error_count} errores")
    
    return result

