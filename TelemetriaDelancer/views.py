from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import logging

from TelemetriaDelancer.panaccess.telemetry_fetcher import (
    fetch_telemetry_records_smart,
    save_telemetry_records,
    is_database_empty,
    get_highest_record_id
)
from TelemetriaDelancer.exceptions import PanAccessException

logger = logging.getLogger(__name__)


class TelemetrySyncView(APIView):
    """
    Endpoint único para sincronizar registros de telemetría desde PanAccess.
    
    Este endpoint descarga y guarda automáticamente los registros:
    - Si la BD está vacía: descarga un lote de registros (o max_records si se especifica)
    - Si la BD tiene registros: descarga solo los NUEVOS desde el último recordId
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        POST: Sincroniza registros de telemetría desde PanAccess.
        
        Parámetros opcionales:
        - limit: Cantidad de registros por página (default: 100, max: 1000)
        - process_timestamps: Si procesar timestamps para extraer fecha/hora (default: true)
        - batch_size: Tamaño del lote para guardar en BD (default: 100)
        """
        try:
            # Obtener parámetros
            limit = int(request.data.get('limit', 100))
            process_timestamps = request.data.get('process_timestamps', True)
            batch_size = int(request.data.get('batch_size', 100))
            
            if isinstance(process_timestamps, str):
                process_timestamps = process_timestamps.lower() in ('true', '1', 'yes')
            
            # Estado inicial de la BD
            was_empty_before = is_database_empty()
            highest_id_before = get_highest_record_id()
            
            logger.info(f"Sincronización iniciada - limit={limit}, process_timestamps={process_timestamps}, batch_size={batch_size}")
            
            # Descargar y guardar en lotes (más seguro ante interrupciones)
            total_downloaded = 0
            total_saved = 0
            total_skipped = 0
            total_errors = 0
            
            # Verificar si la BD está vacía
            if is_database_empty():
                logger.info("BD vacía - descargando y guardando TODOS los registros en lotes")
                # Descargar y guardar página por página
                offset = 0
                page_count = 0
                
                while True:
                    try:
                        page_count += 1
                        # Descargar un lote
                        from TelemetriaDelancer.panaccess.telemetry_fetcher import get_telemetry_records, extract_timestamp_details
                        
                        response = get_telemetry_records(
                            offset=offset,
                            limit=limit,
                            order_by="recordId",
                            order_dir="DESC"
                        )
                        
                        answer = response.get("answer", {})
                        records = answer.get("telemetryRecordEntries", [])
                        
                        if not records:
                            logger.info(f"No hay más registros en offset {offset}")
                            break
                        
                        # Procesar timestamps si se solicita
                        if process_timestamps:
                            records = extract_timestamp_details(records)
                        
                        total_downloaded += len(records)
                        
                        # Guardar inmediatamente este lote
                        logger.info(f"Guardando lote {page_count}: {len(records)} registros (offset={offset})")
                        save_result = save_telemetry_records(records, batch_size=batch_size)
                        total_saved += save_result['saved_records']
                        total_skipped += save_result['skipped_records']
                        total_errors += save_result['errors']
                        
                        logger.info(f"Lote {page_count} guardado: {save_result['saved_records']} guardados, {save_result['skipped_records']} omitidos")
                        
                        # Si obtuvimos menos registros que el límite, es la última página
                        if len(records) < limit:
                            break
                        
                        # Preparar siguiente página
                        offset += limit
                        
                    except Exception as e:
                        logger.error(f"Error en lote {page_count} (offset={offset}): {str(e)}", exc_info=True)
                        # Continuar con el siguiente lote en lugar de fallar completamente
                        offset += limit
                        continue
            else:
                # BD tiene registros - descargar solo los nuevos
                logger.info("BD tiene registros - descargando solo los nuevos desde el último recordId")
                records = fetch_telemetry_records_smart(
                    limit=limit,
                    process_timestamps=process_timestamps
                )
                
                total_downloaded = len(records)
                
                if records:
                    logger.info(f"Guardando {len(records)} registros nuevos en BD")
                    save_result = save_telemetry_records(records, batch_size=batch_size)
                    total_saved = save_result['saved_records']
                    total_skipped = save_result['skipped_records']
                    total_errors = save_result['errors']
            
            save_result = {
                "total_records": total_downloaded,
                "saved_records": total_saved,
                "skipped_records": total_skipped,
                "errors": total_errors
            }
            
            # Estado final de la BD
            is_empty_after = is_database_empty()
            highest_id_after = get_highest_record_id()
            
            # Preparar respuesta
            response_data = {
                "success": True,
                "message": "Sincronización completada exitosamente",
                "download": {
                    "total_records_downloaded": total_downloaded
                },
                "save": save_result,
                "database_status": {
                    "was_empty_before": was_empty_before,
                    "highest_record_id_before": highest_id_before,
                    "is_empty_after": is_empty_after,
                    "highest_record_id_after": highest_id_after
                }
            }
            
            logger.info(
                f"Sincronización completada: {total_downloaded} descargados, "
                f"{total_saved} guardados, {total_skipped} omitidos, {total_errors} errores"
            )
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except PanAccessException as e:
            logger.error(f"Error de PanAccess: {str(e)}")
            return Response(
                {
                    "success": False,
                    "error": "Error de PanAccess",
                    "message": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": "Error inesperado",
                    "message": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
