"""
Módulo de análisis segmentado por rango de fechas.

Este módulo proporciona análisis específicos para períodos de tiempo definidos
por el usuario (desde día X hasta día Y), incluyendo:
- Análisis detallados del período seleccionado
- Comparaciones con períodos anteriores
- Tendencias dentro del rango
- Segmentación temporal del período
- Análisis de eventos y picos

Todas las funciones requieren start_date y end_date como parámetros obligatorios.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal

# Importar pandas y numpy
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from django.db.models import (
    Count, Sum, Avg, Max, Min, Q, F,
    Value, IntegerField, FloatField
)
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, Extract
from django.db import connection

from TelemetriaDelancer.models import MergedTelemetricOTT

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER: Verificar disponibilidad de Pandas
# ============================================================================

def _check_pandas():
    """Verifica si pandas está disponible, lanza excepción si no."""
    if not PANDAS_AVAILABLE:
        raise ImportError(
            "Pandas y NumPy son requeridos para esta función. "
            "Instala con: pip install pandas numpy"
        )


def _validate_date_range(start_date: datetime, end_date: datetime):
    """Valida que el rango de fechas sea válido."""
    if start_date > end_date:
        raise ValueError("start_date debe ser anterior a end_date")
    if (end_date - start_date).days > 365:
        logger.warning(f"Rango de fechas muy amplio: {(end_date - start_date).days} días")


# ============================================================================
# ANÁLISIS GENERAL DEL PERÍODO
# ============================================================================

def get_period_summary(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    Resumen general del período seleccionado.
    
    Proporciona un resumen completo con todas las métricas principales
    del período desde start_date hasta end_date.
    
    Args:
        start_date: Fecha de inicio del período (obligatorio)
        end_date: Fecha de fin del período (obligatorio)
    
    Returns:
        Dict con resumen completo del período incluyendo:
        - Total de visualizaciones
        - Usuarios únicos
        - Dispositivos únicos
        - Canales únicos
        - Tiempo total de visualización
        - Duración promedio
        - Top canales
        - Distribución por día
    """
    _validate_date_range(start_date, end_date)
    
    queryset = MergedTelemetricOTT.objects.filter(
        dataDate__gte=start_date.date(),
        dataDate__lte=end_date.date()
    )
    
    # Métricas generales
    total_views = queryset.count()
    unique_users = queryset.values('subscriberCode').distinct().count()
    unique_devices = queryset.values('deviceId').distinct().count()
    unique_channels = queryset.filter(dataName__isnull=False).values('dataName').distinct().count()
    
    # Métricas de tiempo
    duration_stats = queryset.filter(dataDuration__isnull=False).aggregate(
        total_watch_time=Sum('dataDuration'),
        avg_duration=Avg('dataDuration'),
        max_duration=Max('dataDuration'),
        min_duration=Min('dataDuration')
    )
    
    # Top 10 canales del período
    top_channels = queryset.filter(dataName__isnull=False).values('dataName').annotate(
        views=Count('id'),
        unique_users=Count('subscriberCode', distinct=True)
    ).order_by('-views')[:10]
    
    # Distribución por día
    daily_distribution = queryset.values('dataDate').annotate(
        views=Count('id')
    ).order_by('dataDate')
    
    # Días del período
    days_in_period = (end_date.date() - start_date.date()).days + 1
    
    # Convertir total_watch_time de segundos a horas
    total_watch_time_seconds = float(duration_stats['total_watch_time'] or 0)
    total_watch_time_hours = total_watch_time_seconds / 3600.0
    
    return {
        "period": {
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "days": days_in_period
        },
        "metrics": {
            "total_views": total_views,
            "unique_users": unique_users,
            "unique_devices": unique_devices,
            "unique_channels": unique_channels,
            "total_watch_time_seconds": total_watch_time_seconds,
            "total_watch_time_hours": round(total_watch_time_hours, 2),
            "avg_duration": float(duration_stats['avg_duration'] or 0),
            "max_duration": float(duration_stats['max_duration'] or 0),
            "min_duration": float(duration_stats['min_duration'] or 0),
            "avg_views_per_day": round(total_views / days_in_period, 2) if days_in_period > 0 else 0
        },
        "top_channels": list(top_channels),
        "daily_distribution": list(daily_distribution)
    }


# ============================================================================
# ANÁLISIS COMPARATIVO CON PERÍODO ANTERIOR
# ============================================================================

def get_period_comparison(start_date: datetime, end_date: datetime,
                         compare_with_previous: bool = True) -> Dict[str, Any]:
    """
    Compara el período seleccionado con el período anterior equivalente.
    
    Si compare_with_previous=True, compara con el período anterior de la misma duración.
    Por ejemplo, si seleccionas 7 días, compara con los 7 días anteriores.
    
    Args:
        start_date: Fecha de inicio del período actual
        end_date: Fecha de fin del período actual
        compare_with_previous: Si True, compara con período anterior
    
    Returns:
        Dict con métricas del período actual y comparación con período anterior
    """
    _validate_date_range(start_date, end_date)
    
    # Período actual
    current_period = get_period_summary(start_date, end_date)
    
    if not compare_with_previous:
        return {
            "current_period": current_period,
            "comparison": None
        }
    
    # Calcular período anterior (misma duración)
    period_days = (end_date.date() - start_date.date()).days + 1
    previous_end_date = start_date - timedelta(days=1)
    previous_start_date = previous_end_date - timedelta(days=period_days - 1)
    
    # Período anterior
    previous_period = get_period_summary(previous_start_date, previous_end_date)
    
    # Calcular cambios porcentuales
    current_views = current_period['metrics']['total_views']
    previous_views = previous_period['metrics']['total_views']
    
    views_change = ((current_views - previous_views) / previous_views * 100) if previous_views > 0 else 0
    
    current_users = current_period['metrics']['unique_users']
    previous_users = previous_period['metrics']['unique_users']
    
    users_change = ((current_users - previous_users) / previous_users * 100) if previous_users > 0 else 0
    
    current_watch_time = current_period['metrics']['total_watch_time']
    previous_watch_time = previous_period['metrics']['total_watch_time']
    
    watch_time_change = ((current_watch_time - previous_watch_time) / previous_watch_time * 100) if previous_watch_time > 0 else 0
    
    return {
        "current_period": current_period,
        "previous_period": previous_period,
        "comparison": {
            "period_days": period_days,
            "previous_start_date": previous_start_date.date().isoformat(),
            "previous_end_date": previous_end_date.date().isoformat(),
            "changes": {
                "views": {
                    "absolute": current_views - previous_views,
                    "percentage": round(views_change, 2),
                    "trend": "aumento" if views_change > 0 else "disminución" if views_change < 0 else "estable"
                },
                "users": {
                    "absolute": current_users - previous_users,
                    "percentage": round(users_change, 2),
                    "trend": "aumento" if users_change > 0 else "disminución" if users_change < 0 else "estable"
                },
                "watch_time": {
                    "absolute": current_watch_time - previous_watch_time,
                    "percentage": round(watch_time_change, 2),
                    "trend": "aumento" if watch_time_change > 0 else "disminución" if watch_time_change < 0 else "estable"
                }
            }
        }
    }


# ============================================================================
# ANÁLISIS TEMPORAL DETALLADO DEL PERÍODO
# ============================================================================

def get_period_temporal_breakdown(start_date: datetime, end_date: datetime,
                                  breakdown: str = 'daily') -> Dict[str, Any]:
    """
    Desglose temporal detallado del período seleccionado.
    
    Analiza el período día por día, semana por semana o mes por mes,
    mostrando tendencias y patrones dentro del rango.
    
    Args:
        start_date: Fecha de inicio
        end_date: Fecha de fin
        breakdown: 'daily', 'weekly', o 'monthly'
    
    Returns:
        Dict con desglose temporal y estadísticas
    """
    _validate_date_range(start_date, end_date)
    
    queryset = MergedTelemetricOTT.objects.filter(
        dataDate__gte=start_date.date(),
        dataDate__lte=end_date.date(),
        dataDate__isnull=False
    )
    
    # Para SQLite, usar Raw SQL para todos los períodos (TruncDate también falla en SQLite)
    if connection.vendor == 'sqlite':
        # Usar Raw SQL para SQLite
        if breakdown == 'daily':
            query = """
            SELECT 
                date(dataDate) as period,
                COUNT(*) as views,
                COUNT(DISTINCT subscriberCode) as unique_users,
                COUNT(DISTINCT deviceId) as unique_devices,
                SUM(dataDuration) as total_watch_time,
                AVG(dataDuration) as avg_duration
            FROM merged_telemetric_ott
            WHERE dataDate >= ? AND dataDate <= ? AND dataDate IS NOT NULL
            GROUP BY period
            ORDER BY period
            """
        elif breakdown == 'weekly':
            query = """
            SELECT 
                strftime('%%Y-W%%W', dataDate) as period,
                COUNT(*) as views,
                COUNT(DISTINCT subscriberCode) as unique_users,
                COUNT(DISTINCT deviceId) as unique_devices,
                SUM(dataDuration) as total_watch_time,
                AVG(dataDuration) as avg_duration
            FROM merged_telemetric_ott
            WHERE dataDate >= ? AND dataDate <= ? AND dataDate IS NOT NULL
            GROUP BY period
            ORDER BY period
            """
        else:  # monthly
            query = """
            SELECT 
                strftime('%%Y-%%m', dataDate) as period,
                COUNT(*) as views,
                COUNT(DISTINCT subscriberCode) as unique_users,
                COUNT(DISTINCT deviceId) as unique_devices,
                SUM(dataDuration) as total_watch_time,
                AVG(dataDuration) as avg_duration
            FROM merged_telemetric_ott
            WHERE dataDate >= ? AND dataDate <= ? AND dataDate IS NOT NULL
            GROUP BY period
            ORDER BY period
            """
        
        with connection.cursor() as cursor:
            cursor.execute(query, [start_date.date().isoformat(), end_date.date().isoformat()])
            columns = [col[0] for col in cursor.description]
            temporal_list = [dict(zip(columns, row)) for row in cursor.fetchall()]
    else:
        # Para PostgreSQL, usar Django ORM
        if breakdown == 'daily':
            queryset = queryset.annotate(period=TruncDate('dataDate'))
        elif breakdown == 'weekly':
            queryset = queryset.annotate(period=TruncWeek('dataDate'))
        elif breakdown == 'monthly':
            queryset = queryset.annotate(period=TruncMonth('dataDate'))
        else:
            raise ValueError(f"breakdown debe ser 'daily', 'weekly' o 'monthly'")
        
        # Agregaciones por período
        temporal_data = queryset.values('period').annotate(
            views=Count('id'),
            unique_users=Count('subscriberCode', distinct=True),
            unique_devices=Count('deviceId', distinct=True),
            total_watch_time=Sum('dataDuration'),
            avg_duration=Avg('dataDuration')
        ).order_by('period')
        
        temporal_list = list(temporal_data)
    
    # Calcular estadísticas
    if temporal_list:
        views_list = [item['views'] for item in temporal_list]
        users_list = [item['unique_users'] for item in temporal_list]
        
        stats = {
            "views": {
                "mean": round(sum(views_list) / len(views_list), 2),
                "std": round(float(np.std(views_list)) if PANDAS_AVAILABLE else 0, 2),
                "min": min(views_list),
                "max": max(views_list),
                "trend": "creciente" if views_list[-1] > views_list[0] else "decreciente" if views_list[-1] < views_list[0] else "estable"
            },
            "users": {
                "mean": round(sum(users_list) / len(users_list), 2),
                "min": min(users_list),
                "max": max(users_list)
            }
        }
    else:
        stats = {}
    
    return {
        "period": {
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "breakdown": breakdown
        },
        "temporal_data": temporal_list,
        "statistics": stats
    }


# ============================================================================
# ANÁLISIS DE CANALES EN EL PERÍODO
# ============================================================================

def get_period_channel_analysis(start_date: datetime, end_date: datetime,
                               top_n: int = 20) -> Dict[str, Any]:
    """
    Análisis detallado de canales en el período seleccionado.
    
    Analiza rendimiento, audiencia y engagement de cada canal
    específicamente en el rango de fechas seleccionado.
    
    Args:
        start_date: Fecha de inicio
        end_date: Fecha de fin
        top_n: Número de canales top a retornar
    
    Returns:
        Dict con análisis de canales del período
    """
    _validate_date_range(start_date, end_date)
    
    queryset = MergedTelemetricOTT.objects.filter(
        dataDate__gte=start_date.date(),
        dataDate__lte=end_date.date(),
        dataName__isnull=False
    )
    
    total_period_views = queryset.count()
    
    # Análisis por canal
    channel_analysis = queryset.values('dataName').annotate(
        total_views=Count('id'),
        unique_users=Count('subscriberCode', distinct=True),
        unique_devices=Count('deviceId', distinct=True),
        total_watch_time=Sum('dataDuration'),
        avg_duration=Avg('dataDuration'),
        active_days=Count('dataDate', distinct=True)
    ).order_by('-total_views')[:top_n]
    
    # Calcular porcentajes y métricas derivadas
    channel_list = []
    for channel in channel_analysis:
        percentage = (channel['total_views'] / total_period_views * 100) if total_period_views > 0 else 0
        views_per_user = (channel['total_views'] / channel['unique_users']) if channel['unique_users'] > 0 else 0
        
        channel_list.append({
            **channel,
            "percentage": round(percentage, 2),
            "views_per_user": round(views_per_user, 2),
            "watch_time_per_user": round(
                (channel['total_watch_time'] or 0) / channel['unique_users'] if channel['unique_users'] > 0 else 0,
                2
            )
        })
    
    return {
        "period": {
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat()
        },
        "total_channels": queryset.values('dataName').distinct().count(),
        "total_period_views": total_period_views,
        "channels": channel_list
    }


# ============================================================================
# ANÁLISIS DE USUARIOS EN EL PERÍODO
# ============================================================================

def get_period_user_analysis(start_date: datetime, end_date: datetime,
                            top_n: int = 50) -> Dict[str, Any]:
    """
    Análisis de comportamiento de usuarios en el período seleccionado.
    
    Identifica usuarios más activos, patrones de consumo y engagement
    específicamente en el rango de fechas.
    
    Args:
        start_date: Fecha de inicio
        end_date: Fecha de fin
        top_n: Número de usuarios top a retornar
    
    Returns:
        Dict con análisis de usuarios del período
    """
    _validate_date_range(start_date, end_date)
    
    queryset = MergedTelemetricOTT.objects.filter(
        dataDate__gte=start_date.date(),
        dataDate__lte=end_date.date(),
        subscriberCode__isnull=False
    )
    
    # Análisis por usuario
    user_analysis = queryset.values('subscriberCode').annotate(
        total_views=Count('id'),
        unique_channels=Count('dataName', distinct=True),
        unique_devices=Count('deviceId', distinct=True),
        total_watch_time=Sum('dataDuration'),
        avg_duration=Avg('dataDuration'),
        active_days=Count('dataDate', distinct=True),
        first_view_date=Min('dataDate'),
        last_view_date=Max('dataDate')
    ).order_by('-total_views')[:top_n]
    
    # Calcular métricas derivadas
    user_list = []
    for user in user_analysis:
        days_in_period = (end_date.date() - start_date.date()).days + 1
        activity_rate = (user['active_days'] / days_in_period * 100) if days_in_period > 0 else 0
        
        user_list.append({
            **user,
            "activity_rate": round(activity_rate, 2),
            "avg_views_per_day": round(
                user['total_views'] / user['active_days'] if user['active_days'] > 0 else 0,
                2
            )
        })
    
    return {
        "period": {
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat()
        },
        "total_users": queryset.values('subscriberCode').distinct().count(),
        "top_users": user_list
    }


# ============================================================================
# ANÁLISIS DE EVENTOS Y PICOS EN EL PERÍODO (Pandas)
# ============================================================================

def get_period_events_analysis(start_date: datetime, end_date: datetime,
                               threshold_std: float = 2.0) -> Dict[str, Any]:
    """
    Identifica eventos y picos anómalos dentro del período seleccionado.
    
    Usa Pandas para detectar días con consumo inusualmente alto o bajo
    comparado con el promedio del período.
    
    Args:
        start_date: Fecha de inicio
        end_date: Fecha de fin
        threshold_std: Desviaciones estándar para considerar un evento (default: 2.0)
    
    Returns:
        Dict con eventos detectados y análisis de anomalías
    """
    _check_pandas()
    _validate_date_range(start_date, end_date)
    
    queryset = MergedTelemetricOTT.objects.filter(
        dataDate__gte=start_date.date(),
        dataDate__lte=end_date.date(),
        dataDate__isnull=False
    )
    
    # Cargar datos diarios
    df = pd.DataFrame(list(
        queryset.values('dataDate', 'id', 'dataName', 'subscriberCode')
    ))
    
    if df.empty:
        return {"message": "No hay datos en el período seleccionado"}
    
    df['dataDate'] = pd.to_datetime(df['dataDate'])
    
    # Agregar por día
    daily_stats = df.groupby('dataDate').agg({
        'id': 'count',
        'dataName': 'nunique',
        'subscriberCode': 'nunique'
    }).reset_index()
    daily_stats.columns = ['date', 'views', 'unique_channels', 'unique_users']
    
    # Calcular estadísticas
    mean_views = daily_stats['views'].mean()
    std_views = daily_stats['views'].std()
    
    # Identificar eventos (picos y valles)
    daily_stats['z_score'] = (daily_stats['views'] - mean_views) / std_views if std_views > 0 else 0
    daily_stats['is_peak'] = daily_stats['z_score'] > threshold_std
    daily_stats['is_valley'] = daily_stats['z_score'] < -threshold_std
    
    # Eventos detectados
    peaks = daily_stats[daily_stats['is_peak']].sort_values('views', ascending=False)
    valleys = daily_stats[daily_stats['is_valley']].sort_values('views', ascending=True)
    
    return {
        "period": {
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat()
        },
        "statistics": {
            "mean_daily_views": round(float(mean_views), 2),
            "std_daily_views": round(float(std_views), 2),
            "total_days": len(daily_stats),
            "threshold_std": threshold_std
        },
        "peaks": peaks.to_dict('records') if not peaks.empty else [],
        "valleys": valleys.to_dict('records') if not valleys.empty else [],
        "daily_data": daily_stats.to_dict('records')
    }


# ============================================================================
# ANÁLISIS DE TENDENCIA DENTRO DEL PERÍODO (Pandas)
# ============================================================================

def get_period_trend_analysis(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    Análisis de tendencia dentro del período seleccionado.
    
    Identifica si el consumo está creciendo, decreciendo o estable
    dentro del rango de fechas, usando regresión lineal.
    
    Args:
        start_date: Fecha de inicio
        end_date: Fecha de fin
    
    Returns:
        Dict con análisis de tendencia y pronóstico
    """
    _check_pandas()
    _validate_date_range(start_date, end_date)
    
    queryset = MergedTelemetricOTT.objects.filter(
        dataDate__gte=start_date.date(),
        dataDate__lte=end_date.date(),
        dataDate__isnull=False
    )
    
    # Cargar datos diarios
    df = pd.DataFrame(list(
        queryset.values('dataDate', 'id')
    ))
    
    if df.empty:
        return {"message": "No hay datos en el período seleccionado"}
    
    df['dataDate'] = pd.to_datetime(df['dataDate'])
    daily_views = df.groupby('dataDate').size().reset_index(name='views')
    daily_views = daily_views.sort_values('dataDate')
    
    # Calcular tendencia lineal
    x = np.arange(len(daily_views))
    y = daily_views['views'].values
    
    # Regresión lineal
    coeffs = np.polyfit(x, y, 1)
    slope = coeffs[0]  # Pendiente
    intercept = coeffs[1]
    
    # Calcular R² (coeficiente de determinación)
    trend_line = np.poly1d(coeffs)
    y_pred = trend_line(x)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    # Determinar dirección de tendencia
    if slope > 0:
        trend_direction = "creciente"
        trend_strength = "fuerte" if abs(slope) > np.std(y) * 0.1 else "moderada" if abs(slope) > np.std(y) * 0.05 else "débil"
    elif slope < 0:
        trend_direction = "decreciente"
        trend_strength = "fuerte" if abs(slope) > np.std(y) * 0.1 else "moderada" if abs(slope) > np.std(y) * 0.05 else "débil"
    else:
        trend_direction = "estable"
        trend_strength = "estable"
    
    # Calcular cambio total en el período
    first_day_views = daily_views['views'].iloc[0]
    last_day_views = daily_views['views'].iloc[-1]
    total_change = last_day_views - first_day_views
    percentage_change = (total_change / first_day_views * 100) if first_day_views > 0 else 0
    
    return {
        "period": {
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "days": len(daily_views)
        },
        "trend": {
            "direction": trend_direction,
            "strength": trend_strength,
            "slope": round(float(slope), 2),
            "r_squared": round(float(r_squared), 4),
            "interpretation": f"Tendencia {trend_direction} {trend_strength}"
        },
        "change": {
            "first_day_views": int(first_day_views),
            "last_day_views": int(last_day_views),
            "absolute_change": int(total_change),
            "percentage_change": round(percentage_change, 2)
        },
        "daily_data": daily_views.to_dict('records')
    }


# ============================================================================
# ANÁLISIS COMPLETO DEL PERÍODO (Función Principal)
# ============================================================================

def get_complete_period_analysis(start_date: datetime, end_date: datetime,
                                include_comparison: bool = True,
                                include_events: bool = True) -> Dict[str, Any]:
    """
    Análisis completo del período seleccionado.
    
    Combina todos los análisis en un solo reporte completo.
    Esta es la función principal para obtener un análisis exhaustivo
    del rango de fechas seleccionado.
    
    Args:
        start_date: Fecha de inicio (obligatorio)
        end_date: Fecha de fin (obligatorio)
        include_comparison: Incluir comparación con período anterior
        include_events: Incluir análisis de eventos (requiere Pandas)
    
    Returns:
        Dict con análisis completo del período
    """
    _validate_date_range(start_date, end_date)
    
    logger.info(f"Generando análisis completo para período {start_date.date()} a {end_date.date()}")
    
    # Resumen general
    summary = get_period_summary(start_date, end_date)
    
    # Comparación con período anterior
    comparison = None
    if include_comparison:
        try:
            comparison = get_period_comparison(start_date, end_date)
        except Exception as e:
            logger.warning(f"Error en comparación: {e}")
    
    # Análisis temporal
    temporal_daily = get_period_temporal_breakdown(start_date, end_date, breakdown='daily')
    
    # Análisis de canales
    channels = get_period_channel_analysis(start_date, end_date, top_n=20)
    
    # Análisis de usuarios
    users = get_period_user_analysis(start_date, end_date, top_n=50)
    
    # Análisis de tendencia
    trend = None
    try:
        trend = get_period_trend_analysis(start_date, end_date)
    except Exception as e:
        logger.warning(f"Error en análisis de tendencia: {e}")
    
    # Análisis de eventos
    events = None
    if include_events:
        try:
            events = get_period_events_analysis(start_date, end_date)
        except Exception as e:
            logger.warning(f"Error en análisis de eventos: {e}")
    
    return {
        "period": {
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "days": (end_date.date() - start_date.date()).days + 1
        },
        "summary": summary,
        "comparison": comparison,
        "temporal_breakdown": temporal_daily,
        "channels": channels,
        "users": users,
        "trend": trend,
        "events": events,
        "generated_at": datetime.now().isoformat()
    }

