from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import logging

from TelemetriaDelancer.utils.telemetry_fetcher import (
    fetch_telemetry_records_smart,
    get_telemetry_records,
    fetch_all_telemetry_records,
    fetch_telemetry_records_until,
    is_database_empty,
    get_highest_record_id,
    save_telemetry_records
)
from TelemetriaDelancer.exceptions import PanAccessException

logger = logging.getLogger(__name__)


class TestTelemetryFetch(APIView):
    """
    Endpoint de prueba para obtener registros de telemetría desde PanAccess.
    
    Este endpoint permite probar las diferentes funciones de obtención de registros.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        GET: Obtiene información sobre el estado de la BD y opciones disponibles.
        """
        try:
            is_empty = is_database_empty()
            highest_id = get_highest_record_id()
            
            return Response({
                "message": "Endpoint de prueba para obtener telemetría",
                "database_status": {
                    "is_empty": is_empty,
                    "highest_record_id": highest_id
                },
                "available_endpoints": {
                    "smart": "/delancer/telemetry/test/smart/ - Descarga inteligente (recomendado)",
                    "all": "/delancer/telemetry/test/all/ - Descarga todos los registros",
                    "new": "/delancer/telemetry/test/new/ - Descarga solo registros nuevos",
                    "page": "/delancer/telemetry/test/page/?offset=0&limit=100 - Obtiene una página"
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error en GET TestTelemetryFetch: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        POST: Ejecuta la descarga inteligente de registros.
        
        Parámetros opcionales:
        - limit: Cantidad de registros por página (default: 1000, max: 1000)
        - process_timestamps: Si procesar timestamps (default: true)
        """
        try:
            limit = int(request.data.get('limit', 1000))
            process_timestamps = request.data.get('process_timestamps', True)
            
            if isinstance(process_timestamps, str):
                process_timestamps = process_timestamps.lower() in ('true', '1', 'yes')
            
            logger.info(f"🚀 Iniciando descarga inteligente - limit={limit}, process_timestamps={process_timestamps}")
            
            # Verificar estado inicial de la BD
            was_empty_before = is_database_empty()
            highest_id_before = get_highest_record_id()
            
            # Ejecutar descarga inteligente
            records = fetch_telemetry_records_smart(
                limit=limit,
                process_timestamps=process_timestamps
            )
            
            # Guardar registros en la base de datos
            save_result = None
            if records:
                logger.info(f"💾 Guardando {len(records)} registros en la BD...")
                save_result = save_telemetry_records(records, batch_size=500)
                logger.info(f"✅ Guardado completado: {save_result}")
            
            # Preparar respuesta
            response_data = {
                "success": True,
                "message": "Registros descargados y guardados exitosamente",
                "download": {
                    "total_records_downloaded": len(records),
                    "sample_records": records[:3] if records else []  # Primeros 3 como muestra
                },
                "save": save_result if save_result else {
                    "total_records": 0,
                    "saved_records": 0,
                    "skipped_records": 0,
                    "errors": 0
                },
                "database_status": {
                    "was_empty_before": was_empty_before,
                    "highest_record_id_before": highest_id_before,
                    "is_empty_after": is_database_empty(),
                    "highest_record_id_after": get_highest_record_id()
                }
            }
            
            # Si hay registros, mostrar información del primero y último
            if records:
                first_record = records[0]
                last_record = records[-1]
                response_data["record_range"] = {
                    "first_record_id": first_record.get("recordId"),
                    "last_record_id": last_record.get("recordId"),
                    "first_timestamp": first_record.get("timestamp"),
                    "last_timestamp": last_record.get("timestamp")
                }
            
            logger.info(f"✅ Proceso completado: {len(records)} descargados, {save_result['saved_records'] if save_result else 0} guardados")
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except PanAccessException as e:
            logger.error(f"❌ Error de PanAccess: {str(e)}")
            return Response(
                {
                    "success": False,
                    "error": "Error de PanAccess",
                    "message": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"💥 Error inesperado: {str(e)}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": "Error inesperado",
                    "message": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TestTelemetryFetchAll(APIView):
    """
    Endpoint para obtener TODOS los registros de telemetría.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        POST: Descarga todos los registros disponibles.
        """
        try:
            limit = int(request.data.get('limit', 1000))
            max_records = request.data.get('max_records')
            if max_records:
                max_records = int(max_records)
            
            process_timestamps = request.data.get('process_timestamps', True)
            if isinstance(process_timestamps, str):
                process_timestamps = process_timestamps.lower() in ('true', '1', 'yes')
            
            logger.info(f"🚀 Descargando TODOS los registros - limit={limit}, max_records={max_records}")
            
            records = fetch_all_telemetry_records(
                limit=limit,
                max_records=max_records,
                process_timestamps=process_timestamps
            )
            
            return Response({
                "success": True,
                "message": "Todos los registros obtenidos",
                "total_records": len(records),
                "sample_records": records[:3] if records else []
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=True)
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TestTelemetryFetchNew(APIView):
    """
    Endpoint para obtener solo los registros nuevos.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        POST: Descarga solo los registros nuevos desde el último recordId.
        """
        try:
            limit = int(request.data.get('limit', 1000))
            highest_record_id = request.data.get('highest_record_id')
            
            # Si no se proporciona, obtener de la BD
            if not highest_record_id:
                highest_record_id = get_highest_record_id()
                if not highest_record_id:
                    return Response({
                        "success": False,
                        "error": "No hay recordId en la BD y no se proporcionó uno"
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                highest_record_id = int(highest_record_id)
            
            process_timestamps = request.data.get('process_timestamps', True)
            if isinstance(process_timestamps, str):
                process_timestamps = process_timestamps.lower() in ('true', '1', 'yes')
            
            logger.info(f"🚀 Descargando registros nuevos desde recordId {highest_record_id}")
            
            records = fetch_telemetry_records_until(
                highest_record_id=highest_record_id,
                limit=limit,
                process_timestamps=process_timestamps
            )
            
            return Response({
                "success": True,
                "message": "Registros nuevos obtenidos",
                "total_records": len(records),
                "from_record_id": highest_record_id,
                "sample_records": records[:3] if records else []
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=True)
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TestTelemetryFetchPage(APIView):
    """
    Endpoint para obtener una página específica de registros.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        GET: Obtiene una página de registros.
        
        Parámetros de query:
        - offset: Índice de inicio (default: 0)
        - limit: Cantidad de registros (default: 100, max: 1000)
        - order_by: Campo para ordenar (default: recordId)
        - order_dir: Dirección (ASC o DESC, default: DESC)
        """
        try:
            offset = int(request.query_params.get('offset', 0))
            limit = int(request.query_params.get('limit', 100))
            order_by = request.query_params.get('order_by', 'recordId')
            order_dir = request.query_params.get('order_dir', 'DESC')
            
            logger.info(f"📄 Obteniendo página - offset={offset}, limit={limit}")
            
            response = get_telemetry_records(
                offset=offset,
                limit=limit,
                order_by=order_by,
                order_dir=order_dir
            )
            
            answer = response.get("answer", {})
            records = answer.get("telemetryRecordEntries", [])
            
            return Response({
                "success": True,
                "message": "Página de registros obtenida",
                "offset": offset,
                "limit": limit,
                "total_in_page": len(records),
                "records": records[:10] if len(records) > 10 else records,  # Máximo 10 en respuesta
                "has_more": len(records) == limit
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=True)
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
