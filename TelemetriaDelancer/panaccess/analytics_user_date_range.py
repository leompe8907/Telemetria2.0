"""
Módulo de análisis de un usuario/subscriber en un rango de fechas específico.

Proporciona análisis detallado de un usuario en un período específico:
- Resumen del período (métricas del usuario en el rango)
- Evolución temporal (actividad día por día)
- Canales consumidos en el período
- Patrones horarios en el período
- Comparación con promedio general
- Eventos y anomalías (días con consumo anormal)

IMPORTANTE: Los análisis trabajan con datos de la base de datos local (MergedTelemetricOTTDelancer),
NO consultan directamente a PanAccess. Los datos se obtienen de PanAccess mediante
telemetry_fetcher.py y se almacenan localmente para análisis.
"""

import logging
from typing import Dict, Any
from datetime import datetime

# Importar pandas y numpy
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Pandas/NumPy no están instalados. Algunas funciones avanzadas no estarán disponibles.")

from django.db.models import (
    Count, Sum, Avg, Case, When, Value, CharField
)

from TelemetriaDelancer.models import MergedTelemetricOTTDelancer

logger = logging.getLogger(__name__)


def get_user_date_range_analysis(subscriber_code: str,
                                 start_date: datetime,
                                 end_date: datetime) -> Dict[str, Any]:
    """
    Análisis detallado de un usuario en un rango de fechas específico.
    
    Incluye:
    - Resumen del período (métricas del usuario en el rango)
    - Evolución temporal (actividad día por día)
    - Canales consumidos en el período
    - Patrones horarios en el período
    - Comparación con promedio general (si aplica)
    - Eventos y anomalías (días con consumo anormal)
    
    Args:
        subscriber_code: Código del subscriber a analizar
        start_date: Fecha de inicio (obligatorio)
        end_date: Fecha de fin (obligatorio)
    
    Returns:
        Dict con análisis completo del usuario en el período
    """
    if start_date > end_date:
        return {
            "error": "start_date debe ser anterior a end_date"
        }
    
    queryset = MergedTelemetricOTTDelancer.objects.filter(
        subscriberCode=subscriber_code,
        dataDate__gte=start_date.date(),
        dataDate__lte=end_date.date()
    )
    
    total_records = queryset.count()
    
    if total_records == 0:
        return {
            "subscriber_code": subscriber_code,
            "period": {
                "start_date": start_date.date().isoformat(),
                "end_date": end_date.date().isoformat()
            },
            "message": "No se encontraron registros para este usuario en el período seleccionado",
            "total_records": 0
        }
    
    # Resumen del período
    period_summary = queryset.aggregate(
        total_views=Count('id'),
        total_seconds=Sum('dataDuration'),
        unique_channels=Count('dataName', distinct=True),
        unique_devices=Count('deviceId', distinct=True),
        active_days=Count('dataDate', distinct=True),
        avg_duration=Avg('dataDuration')
    )
    
    total_hours = float(period_summary['total_seconds'] or 0) / 3600.0
    days_in_period = (end_date.date() - start_date.date()).days + 1
    
    # Evolución temporal - Actividad día por día
    daily_activity = queryset.values('dataDate').annotate(
        views=Count('id'),
        total_seconds=Sum('dataDuration'),
        unique_channels=Count('dataName', distinct=True)
    ).order_by('dataDate')
    
    daily_list = [
        {
            "date": str(row['dataDate']),
            "views": row['views'],
            "total_hours": round(float(row['total_seconds'] or 0) / 3600.0, 2),
            "unique_channels": row['unique_channels']
        }
        for row in daily_activity
    ]
    
    # Calcular tendencia (creciente/decreciente/estable)
    if len(daily_list) >= 2:
        first_half = daily_list[:len(daily_list)//2]
        second_half = daily_list[len(daily_list)//2:]
        
        avg_first = sum(d['total_hours'] for d in first_half) / len(first_half) if first_half else 0
        avg_second = sum(d['total_hours'] for d in second_half) / len(second_half) if second_half else 0
        
        if avg_second > avg_first * 1.1:
            trend = "creciente"
        elif avg_second < avg_first * 0.9:
            trend = "decreciente"
        else:
            trend = "estable"
    else:
        trend = "insuficiente_datos"
    
    # Canales en el período
    channels_in_period = queryset.filter(dataName__isnull=False).values('dataName').annotate(
        views=Count('id'),
        total_seconds=Sum('dataDuration'),
        unique_days=Count('dataDate', distinct=True)
    ).order_by('-views')
    
    channels_list = [
        {
            "channel": ch['dataName'],
            "views": ch['views'],
            "total_hours": round(float(ch['total_seconds'] or 0) / 3600.0, 2),
            "active_days": ch['unique_days']
        }
        for ch in channels_in_period
    ]
    
    # Patrones horarios en el período
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
    
    # Comparación con promedio general (en el mismo período)
    general_avg = MergedTelemetricOTTDelancer.objects.filter(
        dataDate__gte=start_date.date(),
        dataDate__lte=end_date.date()
    ).aggregate(
        avg_views_per_user=Count('id') / Count('subscriberCode', distinct=True),
        avg_hours_per_user=Sum('dataDuration') / 3600.0 / Count('subscriberCode', distinct=True)
    )
    
    user_views = period_summary['total_views']
    user_hours = total_hours
    avg_views = float(general_avg['avg_views_per_user'] or 0)
    avg_hours = float(general_avg['avg_hours_per_user'] or 0)
    
    comparison = {
        "user_views": user_views,
        "avg_views": round(avg_views, 2),
        "user_vs_avg_views": round((user_views / avg_views * 100) if avg_views > 0 else 0, 2),
        "user_hours": round(user_hours, 2),
        "avg_hours": round(avg_hours, 2),
        "user_vs_avg_hours": round((user_hours / avg_hours * 100) if avg_hours > 0 else 0, 2)
    }
    
    # Eventos y anomalías - Días con consumo anormalmente alto/bajo
    if len(daily_list) > 0:
        avg_daily_hours = sum(d['total_hours'] for d in daily_list) / len(daily_list)
        std_daily_hours = 0
        
        if PANDAS_AVAILABLE and len(daily_list) > 1:
            hours_array = np.array([d['total_hours'] for d in daily_list])
            std_daily_hours = float(np.std(hours_array))
        else:
            # Calcular desviación estándar manualmente
            variance = sum((d['total_hours'] - avg_daily_hours) ** 2 for d in daily_list) / len(daily_list)
            std_daily_hours = variance ** 0.5
        
        anomalies = []
        for day in daily_list:
            hours = day['total_hours']
            if std_daily_hours > 0:
                z_score = abs((hours - avg_daily_hours) / std_daily_hours)
                if z_score > 2:  # Más de 2 desviaciones estándar
                    anomalies.append({
                        "date": day['date'],
                        "total_hours": hours,
                        "type": "alto" if hours > avg_daily_hours else "bajo",
                        "z_score": round(z_score, 2)
                    })
    else:
        anomalies = []
    
    return {
        "subscriber_code": subscriber_code,
        "period": {
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "days": days_in_period
        },
        "period_summary": {
            "total_views": period_summary['total_views'],
            "total_hours": round(total_hours, 2),
            "unique_channels": period_summary['unique_channels'],
            "unique_devices": period_summary['unique_devices'],
            "active_days": period_summary['active_days'],
            "avg_duration_seconds": round(float(period_summary['avg_duration'] or 0), 2)
        },
        "temporal_evolution": {
            "daily_activity": daily_list,
            "trend": trend
        },
        "channels_in_period": channels_list,
        "time_slots_in_period": time_slots,
        "comparison_with_average": comparison,
        "anomalies": anomalies
    }

