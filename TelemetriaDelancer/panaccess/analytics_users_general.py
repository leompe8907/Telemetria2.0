"""
Módulo de análisis general de usuarios/subscribers.

Proporciona análisis agregado de todos los usuarios:
- Distribución de usuarios por nivel de actividad (segmentación)
- Estadísticas agregadas (promedios)
- Top usuarios por diferentes métricas
- Distribución temporal de usuarios activos
- Métricas de engagement (retención, churn potencial)

IMPORTANTE: Los análisis trabajan con datos de la base de datos local (MergedTelemetricOTTDelancer),
NO consultan directamente a PanAccess. Los datos se obtienen de PanAccess mediante
telemetry_fetcher.py y se almacenan localmente para análisis.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

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
    Count, Sum, Avg, Max, Min
)

from TelemetriaDelancer.models import MergedTelemetricOTTDelancer

logger = logging.getLogger(__name__)


def get_general_users_analysis(start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None,
                               n_segments: int = 5) -> Dict[str, Any]:
    """
    Análisis general de todos los usuarios/subscribers.
    
    Incluye:
    - Distribución de usuarios por nivel de actividad (segmentación)
    - Estadísticas agregadas (promedios)
    - Top usuarios por diferentes métricas
    - Distribución temporal de usuarios activos
    - Métricas de engagement (retención, churn potencial)
    
    Args:
        start_date: Fecha de inicio (opcional)
        end_date: Fecha de fin (opcional)
        n_segments: Número de segmentos para clasificar usuarios (default: 5)
    
    Returns:
        Dict con análisis completo de usuarios
    """
    queryset = MergedTelemetricOTTDelancer.objects.filter(
        subscriberCode__isnull=False,
        dataDuration__isnull=False
    )
    
    if start_date:
        queryset = queryset.filter(dataDate__gte=start_date.date())
    if end_date:
        queryset = queryset.filter(dataDate__lte=end_date.date())
    
    # Estadísticas agregadas por usuario
    user_stats = queryset.values('subscriberCode').annotate(
        total_views=Count('id'),
        total_hours=Sum('dataDuration') / 3600.0,  # Convertir segundos a horas
        unique_channels=Count('dataName', distinct=True),
        unique_devices=Count('deviceId', distinct=True),
        active_days=Count('dataDate', distinct=True),
        avg_duration=Avg('dataDuration'),
        first_activity=Min('timestamp'),
        last_activity=Max('timestamp')
    ).order_by('-total_views')
    
    total_users = user_stats.count()
    
    if total_users == 0:
        return {
            "total_users": 0,
            "message": "No hay usuarios en el período seleccionado"
        }
    
    # Convertir a lista para procesamiento
    users_list = list(user_stats)
    
    # Calcular estadísticas agregadas
    total_views_all = sum(u['total_views'] for u in users_list)
    total_hours_all = sum(float(u['total_hours'] or 0) for u in users_list)
    total_channels_all = sum(u['unique_channels'] for u in users_list)
    total_devices_all = sum(u['unique_devices'] for u in users_list)
    total_active_days_all = sum(u['active_days'] for u in users_list)
    
    # Promedios
    avg_views_per_user = total_views_all / total_users if total_users > 0 else 0
    avg_hours_per_user = total_hours_all / total_users if total_users > 0 else 0
    avg_channels_per_user = total_channels_all / total_users if total_users > 0 else 0
    avg_devices_per_user = total_devices_all / total_users if total_users > 0 else 0
    avg_active_days_per_user = total_active_days_all / total_users if total_users > 0 else 0
    
    # Segmentación por nivel de actividad (usando percentiles si Pandas está disponible)
    if PANDAS_AVAILABLE and len(users_list) > 0:
        df = pd.DataFrame(users_list)
        df['total_hours'] = df['total_hours'].fillna(0)
        df['total_views'] = df['total_views'].fillna(0)
        
        # Calcular percentiles para segmentación
        p20 = df['total_hours'].quantile(0.20)
        p40 = df['total_hours'].quantile(0.40)
        p60 = df['total_hours'].quantile(0.60)
        p80 = df['total_hours'].quantile(0.80)
        
        def classify_user(hours):
            if hours >= p80:
                return 'super_activo'
            elif hours >= p60:
                return 'activo'
            elif hours >= p40:
                return 'regular'
            elif hours >= p20:
                return 'ocasional'
            else:
                return 'inactivo'
        
        df['segment'] = df['total_hours'].apply(classify_user)
        segmentation = df['segment'].value_counts().to_dict()
    else:
        # Segmentación simple sin Pandas
        sorted_users = sorted(users_list, key=lambda x: float(x['total_hours'] or 0), reverse=True)
        segment_size = len(sorted_users) // n_segments
        
        segmentation = {
            'super_activo': len(sorted_users[:segment_size]) if segment_size > 0 else 0,
            'activo': len(sorted_users[segment_size:segment_size*2]) if segment_size > 0 else 0,
            'regular': len(sorted_users[segment_size*2:segment_size*3]) if segment_size > 0 else 0,
            'ocasional': len(sorted_users[segment_size*3:segment_size*4]) if segment_size > 0 else 0,
            'inactivo': len(sorted_users[segment_size*4:]) if segment_size > 0 else 0
        }
    
    # Top usuarios
    top_users_by_hours = sorted(users_list, key=lambda x: float(x['total_hours'] or 0), reverse=True)[:10]
    top_users_by_views = sorted(users_list, key=lambda x: x['total_views'], reverse=True)[:10]
    top_users_by_channels = sorted(users_list, key=lambda x: x['unique_channels'], reverse=True)[:10]
    
    # Distribución temporal de usuarios activos
    active_users_by_date = queryset.values('dataDate').annotate(
        unique_users=Count('subscriberCode', distinct=True)
    ).order_by('dataDate')
    
    # Calcular días totales del período
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
    
    # Métricas de engagement
    # Retención: usuarios que tienen actividad en múltiples días
    users_with_multiple_days = sum(1 for u in users_list if u['active_days'] > 1)
    retention_rate = (users_with_multiple_days / total_users * 100) if total_users > 0 else 0
    
    # Churn potencial: usuarios inactivos (última actividad hace más de 30 días)
    if end_date:
        cutoff_date = end_date.date() - timedelta(days=30)
        potential_churn = queryset.filter(
            timestamp__lt=datetime.combine(cutoff_date, datetime.min.time())
        ).values('subscriberCode').distinct().count()
    else:
        potential_churn = 0
    
    return {
        "total_users": total_users,
        "aggregate_stats": {
            "avg_views_per_user": round(avg_views_per_user, 2),
            "avg_hours_per_user": round(avg_hours_per_user, 2),
            "avg_channels_per_user": round(avg_channels_per_user, 2),
            "avg_devices_per_user": round(avg_devices_per_user, 2),
            "avg_active_days_per_user": round(avg_active_days_per_user, 2),
            "total_views_all_users": total_views_all,
            "total_hours_all_users": round(total_hours_all, 2)
        },
        "segmentation": segmentation,
        "top_users": {
            "by_hours": [
                {
                    "subscriber_code": u['subscriberCode'],
                    "total_hours": round(float(u['total_hours'] or 0), 2),
                    "total_views": u['total_views']
                }
                for u in top_users_by_hours
            ],
            "by_views": [
                {
                    "subscriber_code": u['subscriberCode'],
                    "total_views": u['total_views'],
                    "total_hours": round(float(u['total_hours'] or 0), 2)
                }
                for u in top_users_by_views
            ],
            "by_channels": [
                {
                    "subscriber_code": u['subscriberCode'],
                    "unique_channels": u['unique_channels'],
                    "total_hours": round(float(u['total_hours'] or 0), 2)
                }
                for u in top_users_by_channels
            ]
        },
        "temporal_distribution": [
            {
                "date": str(row['dataDate']),
                "active_users": row['unique_users']
            }
            for row in active_users_by_date
        ],
        "engagement_metrics": {
            "retention_rate": round(retention_rate, 2),
            "users_with_multiple_days": users_with_multiple_days,
            "potential_churn_users": potential_churn,
            "days_in_period": days_in_period
        }
    }

