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
from TelemetriaDelancer.panaccess.ott_merger import merge_ott_records
from TelemetriaDelancer.exceptions import PanAccessException
from datetime import datetime, timedelta, date
import json

logger = logging.getLogger(__name__)


def _serialize_for_json(obj):
    """
    Serializa objetos para JSON, convirtiendo datetime, date y otros tipos no serializables.
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: _serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_serialize_for_json(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        return _serialize_for_json(obj.__dict__)
    else:
        return obj


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


class MergeOTTView(APIView):
    """
    Endpoint para fusionar registros OTT (actionId 7 y 8) en MergedTelemetricOTT.
    
    Fusiona el dataName de actionId=7 a actionId=8 cuando comparten el mismo dataId.
    Solo procesa registros nuevos desde el último recordId guardado.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        POST: Ejecuta el merge de registros OTT.
        
        Parámetros opcionales:
        - max_record_id: RecordId máximo ya procesado (None = usar el máximo de la BD)
        - batch_size: Tamaño del lote para guardar (default: 500)
        """
        try:
            # Obtener parámetros
            max_record_id = request.data.get('max_record_id')
            if max_record_id is not None:
                max_record_id = int(max_record_id)
            
            batch_size = int(request.data.get('batch_size', 500))
            
            logger.info(f"Merge OTT iniciado - max_record_id={max_record_id}, batch_size={batch_size}")
            
            # Ejecutar merge
            result = merge_ott_records(
                max_record_id=max_record_id,
                batch_size=batch_size
            )
            
            # Preparar respuesta
            response_data = {
                "success": True,
                "message": "Merge OTT completado exitosamente",
                "result": result
            }
            
            logger.info(f"Merge OTT completado: {result}")
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error en merge OTT: {str(e)}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": "Error en merge OTT",
                    "message": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        """
        GET: Obtiene información sobre el estado del merge OTT.
        """
        try:
            from TelemetriaDelancer.models import MergedTelemetricOTT
            from django.db.models import Max, Count
            
            # Obtener estadísticas
            max_record = MergedTelemetricOTT.objects.aggregate(Max('recordId'))['recordId__max']
            total_records = MergedTelemetricOTT.objects.count()
            
            # Distribución por actionId
            action_dist = MergedTelemetricOTT.objects.values('actionId').annotate(
                count=Count('actionId')
            ).order_by('actionId')
            
            return Response({
                "message": "Estado del merge OTT",
                "merged_table_status": {
                    "total_records": total_records,
                    "max_record_id": max_record
                },
                "actionId_distribution": list(action_dist),
                "endpoint_info": {
                    "post": "/delancer/telemetry/merge/ott/ - Ejecuta el merge",
                    "parameters": {
                        "max_record_id": "Opcional - RecordId máximo ya procesado",
                        "batch_size": "Opcional - Tamaño del lote (default: 500)"
                    }
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error en GET merge OTT: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AnalyticsView(APIView):
    """
    Endpoint para análisis generales de telemetría OTT.
    
    Retorna TODOS los análisis generales en una sola respuesta.
    Ideal para dashboards que necesitan toda la información de una vez.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        POST: Ejecuta TODOS los análisis generales.
        
        Parámetros opcionales:
        - start_date: Fecha de inicio (formato: YYYY-MM-DD)
        - end_date: Fecha de fin (formato: YYYY-MM-DD)
        - limit: Límite de resultados para top_channels (default: 20)
        - period: 'daily', 'weekly', 'monthly' (para temporal, default: 'daily')
        - forecast_days: Días a pronosticar (para time_series, default: 7)
        - n_segments: Número de segmentos (para segmentation, default: 4)
        - include_pandas_analyses: Incluir análisis que requieren Pandas (default: True)
        """
        try:
            # Parsear fechas opcionales
            start_date = None
            end_date = None
            if request.data.get('start_date'):
                start_date = datetime.fromisoformat(request.data.get('start_date'))
            if request.data.get('end_date'):
                end_date = datetime.fromisoformat(request.data.get('end_date'))
            
            # Parámetros opcionales
            limit = int(request.data.get('limit', 20))
            period = request.data.get('period', 'daily')
            forecast_days = int(request.data.get('forecast_days', 7))
            n_segments = int(request.data.get('n_segments', 4))
            include_pandas = request.data.get('include_pandas_analyses', True)
            if isinstance(include_pandas, str):
                include_pandas = include_pandas.lower() in ('true', '1', 'yes')
            
            # Importar funciones de análisis
            from TelemetriaDelancer.panaccess.analytics import (
                get_top_channels,
                get_channel_audience,
                get_peak_hours_by_channel,
                get_average_duration_by_channel,
                get_temporal_analysis,
                get_geographic_analysis,
                get_correlation_analysis,
                get_time_series_analysis,
                get_user_segmentation_analysis,
                get_channel_performance_matrix
            )
            
            logger.info("Iniciando ejecución de todos los análisis generales")
            
            # Ejecutar TODOS los análisis
            results = {
                "success": True,
                "generated_at": datetime.now().isoformat(),
                "filters": {
                    "start_date": start_date.date().isoformat() if start_date else None,
                    "end_date": end_date.date().isoformat() if end_date else None
                },
                "analyses": {}
            }
            
            # Análisis básicos (siempre disponibles)
            try:
                logger.info("Ejecutando: top_channels")
                results["analyses"]["top_channels"] = get_top_channels(
                    limit=limit,
                    start_date=start_date,
                    end_date=end_date
                )
            except Exception as e:
                logger.error(f"Error en top_channels: {e}")
                results["analyses"]["top_channels"] = {"error": str(e)}
            
            try:
                logger.info("Ejecutando: channel_audience")
                results["analyses"]["channel_audience"] = get_channel_audience(
                    start_date=start_date,
                    end_date=end_date
                )
            except Exception as e:
                logger.error(f"Error en channel_audience: {e}")
                results["analyses"]["channel_audience"] = {"error": str(e)}
            
            try:
                logger.info("Ejecutando: peak_hours")
                results["analyses"]["peak_hours"] = get_peak_hours_by_channel(
                    channel=None,
                    start_date=start_date,
                    end_date=end_date
                )
            except Exception as e:
                logger.error(f"Error en peak_hours: {e}")
                results["analyses"]["peak_hours"] = {"error": str(e)}
            
            try:
                logger.info("Ejecutando: average_duration")
                results["analyses"]["average_duration"] = get_average_duration_by_channel(
                    start_date=start_date,
                    end_date=end_date
                )
            except Exception as e:
                logger.error(f"Error en average_duration: {e}")
                results["analyses"]["average_duration"] = {"error": str(e)}
            
            try:
                logger.info("Ejecutando: temporal")
                results["analyses"]["temporal"] = get_temporal_analysis(
                    period=period,
                    start_date=start_date,
                    end_date=end_date
                )
            except Exception as e:
                logger.error(f"Error en temporal: {e}")
                results["analyses"]["temporal"] = {"error": str(e)}
            
            try:
                logger.info("Ejecutando: geographic")
                results["analyses"]["geographic"] = get_geographic_analysis(
                    start_date=start_date,
                    end_date=end_date
                )
            except Exception as e:
                logger.error(f"Error en geographic: {e}")
                results["analyses"]["geographic"] = {"error": str(e)}
            
            # Análisis avanzados (requieren Pandas)
            if include_pandas:
                try:
                    logger.info("Ejecutando: correlation")
                    results["analyses"]["correlation"] = get_correlation_analysis(
                        start_date=start_date,
                        end_date=end_date
                    )
                except ImportError as e:
                    logger.warning(f"Pandas no disponible para correlation: {e}")
                    results["analyses"]["correlation"] = {
                        "error": "Pandas no está instalado",
                        "hint": "Instala con: pip install pandas numpy"
                    }
                except Exception as e:
                    logger.error(f"Error en correlation: {e}")
                    results["analyses"]["correlation"] = {"error": str(e)}
                
                try:
                    logger.info("Ejecutando: time_series")
                    results["analyses"]["time_series"] = get_time_series_analysis(
                        channel=None,
                        start_date=start_date,
                        end_date=end_date,
                        forecast_days=forecast_days
                    )
                except ImportError as e:
                    logger.warning(f"Pandas no disponible para time_series: {e}")
                    results["analyses"]["time_series"] = {
                        "error": "Pandas no está instalado",
                        "hint": "Instala con: pip install pandas numpy"
                    }
                except Exception as e:
                    logger.error(f"Error en time_series: {e}")
                    results["analyses"]["time_series"] = {"error": str(e)}
                
                try:
                    logger.info("Ejecutando: segmentation")
                    results["analyses"]["segmentation"] = get_user_segmentation_analysis(
                        start_date=start_date,
                        end_date=end_date,
                        n_segments=n_segments
                    )
                except ImportError as e:
                    logger.warning(f"Pandas no disponible para segmentation: {e}")
                    results["analyses"]["segmentation"] = {
                        "error": "Pandas no está instalado",
                        "hint": "Instala con: pip install pandas numpy"
                    }
                except Exception as e:
                    logger.error(f"Error en segmentation: {e}")
                    results["analyses"]["segmentation"] = {"error": str(e)}
                
                try:
                    logger.info("Ejecutando: channel_performance")
                    results["analyses"]["channel_performance"] = get_channel_performance_matrix(
                        start_date=start_date,
                        end_date=end_date
                    )
                except ImportError as e:
                    logger.warning(f"Pandas no disponible para channel_performance: {e}")
                    results["analyses"]["channel_performance"] = {
                        "error": "Pandas no está instalado",
                        "hint": "Instala con: pip install pandas numpy"
                    }
                except Exception as e:
                    logger.error(f"Error en channel_performance: {e}")
                    results["analyses"]["channel_performance"] = {"error": str(e)}
            else:
                results["analyses"]["correlation"] = {"skipped": "include_pandas_analyses=False"}
                results["analyses"]["time_series"] = {"skipped": "include_pandas_analyses=False"}
                results["analyses"]["segmentation"] = {"skipped": "include_pandas_analyses=False"}
                results["analyses"]["channel_performance"] = {"skipped": "include_pandas_analyses=False"}
            
            logger.info("Todos los análisis generales completados")
            
            # Serializar resultados para JSON
            serialized_results = _serialize_for_json(results)
            
            return Response(serialized_results, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error inesperado en análisis generales: {str(e)}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": "Error inesperado",
                    "message": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        """
        GET: Información sobre el endpoint de análisis generales.
        """
        return Response({
            "message": "Análisis generales de telemetría OTT - Retorna TODOS los análisis en una sola respuesta",
            "usage": {
                "method": "POST",
                "endpoint": "/delancer/telemetry/analytics/",
                "description": "Ejecuta TODOS los análisis generales y los retorna en un solo objeto JSON",
                "optional_parameters": {
                    "start_date": "Fecha de inicio (YYYY-MM-DD) - Filtra análisis por fecha",
                    "end_date": "Fecha de fin (YYYY-MM-DD) - Filtra análisis por fecha",
                    "limit": "Límite de resultados para top_channels (default: 20)",
                    "period": "Período para temporal: 'daily', 'weekly', 'monthly' (default: 'daily')",
                    "forecast_days": "Días a pronosticar para time_series (default: 7)",
                    "n_segments": "Número de segmentos para segmentation (default: 4)",
                    "include_pandas_analyses": "Incluir análisis que requieren Pandas (default: true)"
                }
            },
            "analyses_included": {
                "top_channels": "Top canales más vistos",
                "channel_audience": "Audiencia por canal (dispositivos y usuarios únicos)",
                "peak_hours": "Horarios pico por canal",
                "average_duration": "Duración promedio por canal",
                "temporal": "Análisis temporal (diario/semanal/mensual)",
                "geographic": "Análisis geográfico por país e ISP",
                "correlation": "Análisis de correlaciones entre variables (requiere Pandas)",
                "time_series": "Análisis de series temporales con forecasting (requiere Pandas)",
                "segmentation": "Segmentación de usuarios con clustering (requiere Pandas)",
                "channel_performance": "Matriz de rendimiento de canales (requiere Pandas)"
            },
            "example": {
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "limit": 20,
                "include_pandas_analyses": true
            },
            "response_structure": {
                "success": "boolean",
                "generated_at": "timestamp",
                "filters": "filtros aplicados",
                "analyses": {
                    "top_channels": "...",
                    "channel_audience": "...",
                    "peak_hours": "...",
                    "average_duration": "...",
                    "temporal": "...",
                    "geographic": "...",
                    "correlation": "...",
                    "time_series": "...",
                    "segmentation": "...",
                    "channel_performance": "..."
                }
            }
        }, status=status.HTTP_200_OK)


class PeriodAnalysisView(APIView):
    """
    Endpoint para análisis segmentados por rango de fechas.
    
    Retorna TODOS los análisis del período en una sola respuesta.
    Ideal para dashboards que necesitan toda la información del período de una vez.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        POST: Ejecuta TODOS los análisis del período específico.
        
        Parámetros requeridos:
        - start_date: Fecha de inicio (formato: YYYY-MM-DD)
        - end_date: Fecha de fin (formato: YYYY-MM-DD)
        
        Parámetros opcionales:
        - breakdown: 'daily', 'weekly', 'monthly' (para temporal_breakdown, default: 'daily')
        - top_n_channels: Número de canales top (default: 20)
        - top_n_users: Número de usuarios top (default: 50)
        - threshold_std: Desviaciones estándar para eventos (default: 2.0)
        - include_comparison: Incluir comparación con período anterior (default: True)
        - include_pandas_analyses: Incluir análisis que requieren Pandas (default: True)
        """
        try:
            # Validar fechas requeridas
            start_date_str = request.data.get('start_date')
            end_date_str = request.data.get('end_date')
            
            if not start_date_str or not end_date_str:
                return Response(
                    {
                        "error": "start_date y end_date son requeridos",
                        "format": "YYYY-MM-DD",
                        "example": {
                            "start_date": "2025-01-01",
                            "end_date": "2025-01-07"
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                start_date = datetime.fromisoformat(start_date_str)
                end_date = datetime.fromisoformat(end_date_str)
            except ValueError as e:
                return Response(
                    {
                        "error": "Formato de fecha inválido",
                        "message": str(e),
                        "format": "YYYY-MM-DD",
                        "example": "2025-01-01"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Parámetros opcionales
            breakdown = request.data.get('breakdown', 'daily')
            top_n_channels = int(request.data.get('top_n_channels', 20))
            top_n_users = int(request.data.get('top_n_users', 50))
            threshold_std = float(request.data.get('threshold_std', 2.0))
            include_comparison = request.data.get('include_comparison', True)
            include_pandas = request.data.get('include_pandas_analyses', True)
            
            if isinstance(include_comparison, str):
                include_comparison = include_comparison.lower() in ('true', '1', 'yes')
            if isinstance(include_pandas, str):
                include_pandas = include_pandas.lower() in ('true', '1', 'yes')
            
            # Importar funciones de análisis por período
            from TelemetriaDelancer.panaccess.analytics_date_range import (
                get_period_summary,
                get_period_comparison,
                get_period_temporal_breakdown,
                get_period_channel_analysis,
                get_period_user_analysis,
                get_period_events_analysis,
                get_period_trend_analysis
            )
            
            logger.info(f"Iniciando ejecución de todos los análisis del período {start_date.date()} a {end_date.date()}")
            
            # Ejecutar TODOS los análisis
            results = {
                "success": True,
                "generated_at": datetime.now().isoformat(),
                "period": {
                    "start_date": start_date.date().isoformat(),
                    "end_date": end_date.date().isoformat(),
                    "days": (end_date.date() - start_date.date()).days + 1
                },
                "analyses": {}
            }
            
            # Resumen general
            try:
                logger.info("Ejecutando: summary")
                results["analyses"]["summary"] = get_period_summary(start_date, end_date)
            except Exception as e:
                logger.error(f"Error en summary: {e}")
                results["analyses"]["summary"] = {"error": str(e)}
            
            # Comparación con período anterior
            if include_comparison:
                try:
                    logger.info("Ejecutando: comparison")
                    results["analyses"]["comparison"] = get_period_comparison(start_date, end_date, compare_with_previous=True)
                except Exception as e:
                    logger.error(f"Error en comparison: {e}")
                    results["analyses"]["comparison"] = {"error": str(e)}
            else:
                results["analyses"]["comparison"] = {"skipped": "include_comparison=False"}
            
            # Desglose temporal
            try:
                logger.info("Ejecutando: temporal_breakdown")
                results["analyses"]["temporal_breakdown"] = get_period_temporal_breakdown(
                    start_date, end_date, breakdown=breakdown
                )
            except Exception as e:
                logger.error(f"Error en temporal_breakdown: {e}")
                results["analyses"]["temporal_breakdown"] = {"error": str(e)}
            
            # Análisis de canales
            try:
                logger.info("Ejecutando: channels")
                results["analyses"]["channels"] = get_period_channel_analysis(
                    start_date, end_date, top_n=top_n_channels
                )
            except Exception as e:
                logger.error(f"Error en channels: {e}")
                results["analyses"]["channels"] = {"error": str(e)}
            
            # Análisis de usuarios
            try:
                logger.info("Ejecutando: users")
                results["analyses"]["users"] = get_period_user_analysis(
                    start_date, end_date, top_n=top_n_users
                )
            except Exception as e:
                logger.error(f"Error en users: {e}")
                results["analyses"]["users"] = {"error": str(e)}
            
            # Análisis avanzados (requieren Pandas)
            if include_pandas:
                try:
                    logger.info("Ejecutando: events")
                    results["analyses"]["events"] = get_period_events_analysis(
                        start_date, end_date, threshold_std=threshold_std
                    )
                except ImportError as e:
                    logger.warning(f"Pandas no disponible para events: {e}")
                    results["analyses"]["events"] = {
                        "error": "Pandas no está instalado",
                        "hint": "Instala con: pip install pandas numpy"
                    }
                except Exception as e:
                    logger.error(f"Error en events: {e}")
                    results["analyses"]["events"] = {"error": str(e)}
                
                try:
                    logger.info("Ejecutando: trend")
                    results["analyses"]["trend"] = get_period_trend_analysis(start_date, end_date)
                except ImportError as e:
                    logger.warning(f"Pandas no disponible para trend: {e}")
                    results["analyses"]["trend"] = {
                        "error": "Pandas no está instalado",
                        "hint": "Instala con: pip install pandas numpy"
                    }
                except Exception as e:
                    logger.error(f"Error en trend: {e}")
                    results["analyses"]["trend"] = {"error": str(e)}
            else:
                results["analyses"]["events"] = {"skipped": "include_pandas_analyses=False"}
                results["analyses"]["trend"] = {"skipped": "include_pandas_analyses=False"}
            
            logger.info("Todos los análisis del período completados")
            
            # Serializar resultados para JSON
            serialized_results = _serialize_for_json(results)
            
            return Response(serialized_results, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.error(f"Error de validación: {str(e)}")
            return Response(
                {
                    "success": False,
                    "error": "Error de validación",
                    "message": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except ImportError as e:
            logger.error(f"Error de importación: {str(e)}")
            return Response(
                {
                    "success": False,
                    "error": "Dependencias faltantes",
                    "message": str(e),
                    "hint": "Algunos análisis requieren pandas y numpy. Instala con: pip install pandas numpy"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Error en análisis de período: {str(e)}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": "Error en análisis",
                    "message": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        """
        GET: Información sobre el endpoint de análisis por período.
        """
        return Response({
            "message": "Análisis segmentados por rango de fechas - Retorna TODOS los análisis del período en una sola respuesta",
            "usage": {
                "method": "POST",
                "endpoint": "/delancer/telemetry/period-analysis/",
                "description": "Ejecuta TODOS los análisis del período especificado y los retorna en un solo objeto JSON",
                "required_parameters": {
                    "start_date": "Fecha de inicio (YYYY-MM-DD) - OBLIGATORIO",
                    "end_date": "Fecha de fin (YYYY-MM-DD) - OBLIGATORIO"
                },
                "optional_parameters": {
                    "breakdown": "Para temporal_breakdown: 'daily', 'weekly', 'monthly' (default: 'daily')",
                    "top_n_channels": "Número de canales top (default: 20)",
                    "top_n_users": "Número de usuarios top (default: 50)",
                    "threshold_std": "Desviaciones estándar para eventos (default: 2.0)",
                    "include_comparison": "Incluir comparación con período anterior (default: true)",
                    "include_pandas_analyses": "Incluir análisis que requieren Pandas (default: true)"
                }
            },
            "analyses_included": {
                "summary": "Resumen general del período (métricas principales)",
                "comparison": "Comparación con período anterior equivalente",
                "temporal_breakdown": "Desglose temporal día por día/semana/mes",
                "channels": "Análisis detallado de canales en el período",
                "users": "Análisis de comportamiento de usuarios en el período",
                "events": "Detección de eventos y picos anómalos (requiere Pandas)",
                "trend": "Análisis de tendencia dentro del período (requiere Pandas)"
            },
            "example": {
                "start_date": "2025-01-01",
                "end_date": "2025-01-07",
                "breakdown": "daily",
                "top_n_channels": 20,
                "top_n_users": 50,
                "include_comparison": true,
                "include_pandas_analyses": true
            },
            "response_structure": {
                "success": "boolean",
                "generated_at": "timestamp",
                "period": {
                    "start_date": "fecha inicio",
                    "end_date": "fecha fin",
                    "days": "días del período"
                },
                "analyses": {
                    "summary": "...",
                    "comparison": "...",
                    "temporal_breakdown": "...",
                    "channels": "...",
                    "users": "...",
                    "events": "...",
                    "trend": "..."
                }
            }
        }, status=status.HTTP_200_OK)
