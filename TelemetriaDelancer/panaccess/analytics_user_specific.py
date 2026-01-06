"""
Módulo de análisis de un usuario/subscriber específico.

Proporciona análisis detallado de un usuario individual:
- Perfil del usuario (métricas generales)
- Comportamiento de consumo (canales, horarios, dispositivos)
- Patrones temporales (día de semana, hora del día)
- Estadísticas del usuario

IMPORTANTE: Los análisis trabajan con datos de la base de datos local (MergedTelemetricOTTDelancer),
NO consultan directamente a PanAccess. Los datos se obtienen de PanAccess mediante
telemetry_fetcher.py y se almacenan localmente para análisis.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from django.db.models import (
    Count, Sum, Avg, Max, Min, Case, When, Value, CharField
)

from TelemetriaDelancer.models import MergedTelemetricOTTDelancer

logger = logging.getLogger(__name__)


def get_user_analysis(subscriber_code: str,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Análisis detallado de un usuario/subscriber específico.
    
    Incluye:
    - Perfil del usuario (métricas generales)
    - Comportamiento de consumo (canales, horarios, dispositivos)
    - Patrones temporales (día de semana, hora del día)
    - Estadísticas del usuario
    
    Args:
        subscriber_code: Código del subscriber a analizar
        start_date: Fecha de inicio (opcional, para filtrar)
        end_date: Fecha de fin (opcional, para filtrar)
    
    Returns:
        Dict con análisis completo del usuario
    """
    queryset = MergedTelemetricOTTDelancer.objects.filter(
        subscriberCode=subscriber_code
    )
    
    if start_date:
        queryset = queryset.filter(dataDate__gte=start_date.date())
    if end_date:
        queryset = queryset.filter(dataDate__lte=end_date.date())
    
    total_records = queryset.count()
    
    if total_records == 0:
        return {
            "subscriber_code": subscriber_code,
            "message": "No se encontraron registros para este usuario",
            "total_records": 0
        }
    
    # Perfil del usuario
    profile = queryset.aggregate(
        total_views=Count('id'),
        total_seconds=Sum('dataDuration'),
        unique_channels=Count('dataName', distinct=True),
        unique_devices=Count('deviceId', distinct=True),
        active_days=Count('dataDate', distinct=True),
        avg_duration=Avg('dataDuration'),
        first_activity=Min('timestamp'),
        last_activity=Max('timestamp')
    )
    
    total_hours = float(profile['total_seconds'] or 0) / 3600.0
    
    # Calcular días totales
    if start_date and end_date:
        days_in_period = (end_date.date() - start_date.date()).days + 1
    else:
        date_range = queryset.aggregate(
            min_date=Min('dataDate'),
            max_date=Max('dataDate')
        )
        if date_range['min_date'] and date_range['max_date']:
            days_in_period = (date_range['max_date'] - date_range['min_date']).days + 1
        else:
            days_in_period = 1
    
    # Comportamiento de consumo - Top canales
    top_channels = queryset.filter(dataName__isnull=False).values('dataName').annotate(
        views=Count('id'),
        total_seconds=Sum('dataDuration'),
        unique_days=Count('dataDate', distinct=True)
    ).order_by('-views')[:10]
    
    top_channels_list = [
        {
            "channel": ch['dataName'],
            "views": ch['views'],
            "total_hours": round(float(ch['total_seconds'] or 0) / 3600.0, 2),
            "active_days": ch['unique_days']
        }
        for ch in top_channels
    ]
    
    # Horarios preferidos (franjas horarias)
    time_slot_analysis = queryset.filter(timeDate__isnull=False).annotate(
        time_slot=Case(
            When(timeDate__gte=0, timeDate__lte=5, then=Value('madrugada')),
            When(timeDate__gte=6, timeDate__lte=11, then=Value('mañana')),
            When(timeDate__gte=12, timeDate__lte=17, then=Value('tarde')),
            default=Value('noche'),
            output_field=CharField()
        )
    ).values('time_slot').annotate(
        total_seconds=Sum('dataDuration'),
        total_views=Count('id')
    ).order_by('-total_seconds')
    
    time_slots = {
        'madrugada': {'total_hours': 0, 'total_views': 0},
        'mañana': {'total_hours': 0, 'total_views': 0},
        'tarde': {'total_hours': 0, 'total_views': 0},
        'noche': {'total_hours': 0, 'total_views': 0}
    }
    
    for row in time_slot_analysis:
        slot = row['time_slot']
        total_seconds = float(row['total_seconds'] or 0)
        total_hours = total_seconds / 3600.0
        time_slots[slot] = {
            'total_hours': round(total_hours, 2),
            'total_views': row['total_views']
        }
    
    # Dispositivos utilizados
    devices = queryset.filter(deviceId__isnull=False).values('deviceId').annotate(
        views=Count('id'),
        total_seconds=Sum('dataDuration')
    ).order_by('-views')
    
    devices_list = [
        {
            "device_id": dev['deviceId'],
            "views": dev['views'],
            "total_hours": round(float(dev['total_seconds'] or 0) / 3600.0, 2)
        }
        for dev in devices
    ]
    
    # Patrones temporales - Actividad por hora del día
    hourly_activity = queryset.filter(timeDate__isnull=False).values('timeDate').annotate(
        views=Count('id'),
        total_seconds=Sum('dataDuration')
    ).order_by('timeDate')
    
    hourly_list = [
        {
            "hour": row['timeDate'],
            "views": row['views'],
            "total_hours": round(float(row['total_seconds'] or 0) / 3600.0, 2)
        }
        for row in hourly_activity
    ]
    
    # Estadísticas del usuario
    avg_hours_per_active_day = total_hours / profile['active_days'] if profile['active_days'] > 0 else 0
    avg_views_per_active_day = profile['total_views'] / profile['active_days'] if profile['active_days'] > 0 else 0
    avg_session_duration_seconds = float(profile['avg_duration'] or 0)
    avg_session_duration_hours = avg_session_duration_seconds / 3600.0  # Convertir a horas
    frequency = (profile['active_days'] / days_in_period * 100) if days_in_period > 0 else 0
    
    return {
        "subscriber_code": subscriber_code,
        "profile": {
            "total_views": profile['total_views'],
            "total_hours": round(total_hours, 2),
            "unique_channels": profile['unique_channels'],
            "unique_devices": profile['unique_devices'],
            "active_days": profile['active_days'],
            "first_activity": profile['first_activity'].isoformat() if profile['first_activity'] else None,
            "last_activity": profile['last_activity'].isoformat() if profile['last_activity'] else None
        },
        "consumption_behavior": {
            "top_channels": top_channels_list,
            "preferred_time_slots": time_slots,
            "devices_used": devices_list
        },
        "temporal_patterns": {
            "hourly_activity": hourly_list
        },
        "user_statistics": {
            "avg_hours_per_active_day": round(avg_hours_per_active_day, 2),
            "avg_views_per_active_day": round(avg_views_per_active_day, 2),
            "avg_session_duration": round(avg_session_duration_hours, 2),  # Convertido a horas
            "frequency_percentage": round(frequency, 2),
            "days_in_period": days_in_period
        }
    }

