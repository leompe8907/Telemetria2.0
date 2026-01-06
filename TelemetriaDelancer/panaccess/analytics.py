"""
Módulo de análisis para telemetría OTT.

Este módulo proporciona funciones de análisis optimizadas que aprovechan:
- Django ORM para consultas eficientes (usa índices de BD)
- MySQL/MariaDB para análisis complejos (Raw SQL cuando es necesario)
- Pandas y NumPy para análisis estadísticos avanzados (opcional)

IMPORTANTE: Los análisis trabajan con datos de la base de datos local (MergedTelemetricOTTDelancer),
NO consultan directamente a PanAccess. Los datos se obtienen de PanAccess mediante
telemetry_fetcher.py y se almacenan localmente para análisis.

Estrategia:
1. Análisis simples → Django ORM (rápido, eficiente, aprovecha índices)
2. Análisis complejos → Raw SQL optimizado para MySQL/MariaDB (CTEs, funciones de ventana)
3. Análisis estadísticos avanzados → Pandas + NumPy (correlaciones, forecasting, etc.)
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

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
    Count, Sum, Avg, Max, Min, Q, F, 
    Value, IntegerField, FloatField, CharField,
    Case, When
)
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, Extract
from django.db import connection

from TelemetriaDelancer.models import MergedTelemetricOTTDelancer

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


# ============================================================================
# ANÁLISIS DE CONSUMO POR CANAL (Django ORM - Optimizado)
# ============================================================================

def get_top_channels(limit: int = 10, start_date: Optional[datetime] = None, 
                     end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Top canales más vistos.
    
    Usa Django ORM con agregaciones optimizadas que aprovechan índices.
    """
    queryset = MergedTelemetricOTTDelancer.objects.filter(
        dataName__isnull=False
    )
    
    # Filtros opcionales por fecha
    if start_date:
        queryset = queryset.filter(dataDate__gte=start_date.date())
    if end_date:
        queryset = queryset.filter(dataDate__lte=end_date.date())
    
    # Calcular total para porcentajes
    total_views = queryset.count()
    
    # Agregación optimizada
    results = queryset.values('dataName').annotate(
        total_views=Count('id'),
        percentage=Value(0.0, output_field=FloatField())  # Se calcula después
    ).order_by('-total_views')[:limit]
    
    # Convertir a lista y calcular porcentajes
    result_list = []
    for item in results:
        percentage = (item['total_views'] / total_views * 100) if total_views > 0 else 0
        result_list.append({
            'channel': item['dataName'],
            'total_views': item['total_views'],
            'percentage': round(percentage, 2)
        })
    
    return result_list


def get_channel_audience(start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Análisis de audiencia por canal (dispositivos y usuarios únicos).
    
    Incluye total de horas vistas por canal.
    Usa Django ORM con agregaciones que aprovechan índices compuestos.
    """
    queryset = MergedTelemetricOTTDelancer.objects.filter(
        dataName__isnull=False
    )
    
    if start_date:
        queryset = queryset.filter(dataDate__gte=start_date.date())
    if end_date:
        queryset = queryset.filter(dataDate__lte=end_date.date())
    
    # Agregación optimizada con múltiples COUNT DISTINCT y suma de horas
    results = queryset.values('dataName').annotate(
        unique_devices=Count('deviceId', distinct=True),
        unique_users=Count('subscriberCode', distinct=True),
        total_views=Count('id'),
        total_watch_time=Sum('dataDuration')  # Total de horas vistas
    ).order_by('-total_views')
    
    # Convertir a lista y calcular horas (dataDuration está en segundos, convertir a horas)
    result_list = []
    for item in results:
        total_hours = (item['total_watch_time'] or 0) / 3600  # Convertir segundos a horas
        result_list.append({
            'dataName': item['dataName'],
            'unique_devices': item['unique_devices'],
            'unique_users': item['unique_users'],
            'total_views': item['total_views'],
            'total_watch_time': round(total_hours, 2)  # Horas con 2 decimales
        })
    
    return result_list


def get_peak_hours_by_channel(channel: Optional[str] = None,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Horarios pico por canal.
    
    Usa Django ORM con truncamiento de hora para agrupación eficiente.
    """
    queryset = MergedTelemetricOTTDelancer.objects.filter(
        dataName__isnull=False,
        timeDate__isnull=False
    )
    
    if channel:
        queryset = queryset.filter(dataName=channel)
    if start_date:
        queryset = queryset.filter(dataDate__gte=start_date.date())
    if end_date:
        queryset = queryset.filter(dataDate__lte=end_date.date())
    
    # Agrupar por canal y hora
    results = queryset.values('dataName', 'timeDate').annotate(
        views=Count('id')
    ).order_by('dataName', '-views')
    
    return list(results)


def get_average_duration_by_channel(start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Duración promedio por canal.
    
    Usa Django ORM con agregaciones que aprovechan índices.
    """
    queryset = MergedTelemetricOTTDelancer.objects.filter(
        dataName__isnull=False,
        dataDuration__isnull=False
    )
    
    if start_date:
        queryset = queryset.filter(dataDate__gte=start_date.date())
    if end_date:
        queryset = queryset.filter(dataDate__lte=end_date.date())
    
    results = queryset.values('dataName').annotate(
        avg_duration=Avg('dataDuration'),
        total_views=Count('id'),
        total_watch_time=Sum('dataDuration')
    ).order_by('-avg_duration')
    
    # Convertir tiempos de segundos a horas
    result_list = []
    for item in results:
        avg_duration_hours = (item['avg_duration'] or 0) / 3600  # Convertir segundos a horas
        total_watch_time_hours = (item['total_watch_time'] or 0) / 3600  # Convertir segundos a horas
        result_list.append({
            'dataName': item['dataName'],
            'avg_duration': round(avg_duration_hours, 2),  # Duración promedio en horas
            'total_views': item['total_views'],
            'total_watch_time': round(total_watch_time_hours, 2)  # Tiempo total en horas
        })
    
    return result_list


# ============================================================================
# ANÁLISIS TEMPORAL (Django ORM con funciones de fecha)
# ============================================================================

def get_temporal_analysis(period: str = 'daily',
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Análisis temporal (diario, semanal, mensual).
    
    Usa Django ORM con funciones de truncamiento de fecha optimizadas.
    Compatible con MySQL/MariaDB (usando Django ORM) y SQLite (usando Raw SQL como fallback).
    """
    queryset = MergedTelemetricOTTDelancer.objects.filter(
        dataDate__isnull=False
    )
    
    if start_date:
        queryset = queryset.filter(dataDate__gte=start_date.date())
    if end_date:
        queryset = queryset.filter(dataDate__lte=end_date.date())
    
    # Para SQLite, usar Raw SQL para todos los períodos (TruncDate también falla en SQLite)
    if connection.vendor == 'sqlite':
        # Usar Raw SQL para SQLite
        if period == 'daily':
            query = """
            SELECT 
                date(dataDate) as period,
                COUNT(*) as views
            FROM merged_telemetric_ott
            WHERE dataDate IS NOT NULL
            """
        elif period == 'weekly':
            # SQLite: usar strftime para semana
            query = """
            SELECT 
                strftime('%%Y-W%%W', dataDate) as period,
                COUNT(*) as views
            FROM merged_telemetric_ott
            WHERE dataDate IS NOT NULL
            """
        else:  # monthly
            # SQLite: usar strftime para mes
            query = """
            SELECT 
                strftime('%%Y-%%m', dataDate) as period,
                COUNT(*) as views
            FROM merged_telemetric_ott
            WHERE dataDate IS NOT NULL
            """
        
        params = []
        if start_date:
            query += " AND dataDate >= ?"
            params.append(start_date.date().isoformat())
        if end_date:
            query += " AND dataDate <= ?"
            params.append(end_date.date().isoformat())
        
        query += " GROUP BY period ORDER BY period"
        
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return results
    
    # Para MySQL/MariaDB y PostgreSQL, usar Django ORM (más eficiente)
    if period == 'daily':
        queryset = queryset.annotate(period=TruncDate('dataDate'))
    elif period == 'weekly':
        queryset = queryset.annotate(period=TruncWeek('dataDate'))
    elif period == 'monthly':
        queryset = queryset.annotate(period=TruncMonth('dataDate'))
    else:
        raise ValueError(f"Período no válido: {period}. Use 'daily', 'weekly' o 'monthly'")
    
    results = queryset.values('period').annotate(
        views=Count('id')
    ).order_by('period')
    
    return list(results)


# ============================================================================
# ANÁLISIS AVANZADOS (Raw SQL optimizado para MySQL 8.0+/MariaDB 10.2+)
# ============================================================================

def get_day_over_day_comparison(start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Comparación día a día con funciones de ventana.
    
    Usa Raw SQL con CTEs y funciones de ventana (LAG).
    Requiere MySQL 8.0+ o MariaDB 10.2+ para funciones de ventana.
    Compatible con SQLite para desarrollo (con limitaciones).
    """
    query = """
    WITH daily_stats AS (
        SELECT 
            dataDate,
            COUNT(*) as daily_views
        FROM merged_telemetric_ott
        WHERE dataDate IS NOT NULL
    """
    
    params = []
    if start_date:
        query += " AND dataDate >= %s"
        params.append(start_date.date())
    if end_date:
        query += " AND dataDate <= %s"
        params.append(end_date.date())
    
    query += """
        GROUP BY dataDate
    )
    SELECT 
        dataDate,
        daily_views,
        LAG(daily_views) OVER (ORDER BY dataDate) as previous_day_views,
        daily_views - LAG(daily_views) OVER (ORDER BY dataDate) as day_over_day_change
    FROM daily_stats
    ORDER BY dataDate DESC
    """
    
    with connection.cursor() as cursor:
        # Django maneja automáticamente los parámetros según el vendor (%s para MySQL/PostgreSQL, ? para SQLite)
        # Para MySQL 8.0+ y MariaDB 10.2+, las funciones de ventana (LAG) están disponibles
        # Para versiones anteriores, esta consulta fallará - usar Django ORM como alternativa
        try:
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error ejecutando consulta con funciones de ventana: {str(e)}")
            logger.warning("Las funciones de ventana requieren MySQL 8.0+ o MariaDB 10.2+")
            raise
    
    return results


def get_anomaly_detection(threshold_std: float = 3.0,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Detección de anomalías usando desviación estándar.
    
    Usa Raw SQL con CTEs para calcular estadísticas.
    Compatible con MySQL/MariaDB (usa STDDEV_POP o STDDEV según vendor).
    """
    query = """
    WITH daily_counts AS (
        SELECT 
            dataDate,
            COUNT(*) as daily_views
        FROM merged_telemetric_ott
        WHERE dataDate IS NOT NULL
    """
    
    params = []
    if start_date:
        query += " AND dataDate >= %s"
        params.append(start_date.date())
    if end_date:
        query += " AND dataDate <= %s"
        params.append(end_date.date())
    
    query += """
        GROUP BY dataDate
    ),
    stats AS (
        SELECT 
            AVG(daily_views) as avg_views,
            STDDEV_POP(daily_views) as stddev_views
        FROM daily_counts
    )
    SELECT 
        dc.dataDate,
        dc.daily_views,
        s.avg_views as average_views,
        s.stddev_views as standard_deviation,
        ROUND((dc.daily_views - s.avg_views) / NULLIF(s.stddev_views, 0), 2) as z_score
    FROM daily_counts dc
    CROSS JOIN stats s
    WHERE dc.daily_views > (s.avg_views + %s * s.stddev_views)
    ORDER BY dc.daily_views DESC
    """
    
    params.append(threshold_std)
    
    with connection.cursor() as cursor:
        # Ajustar función de desviación estándar según el vendor de BD
        if connection.vendor == 'sqlite':
            # SQLite usa STDDEV
            query = query.replace('STDDEV_POP', 'STDDEV')
        elif connection.vendor == 'mysql':
            # MySQL 8.0+ soporta STDDEV_POP, pero para compatibilidad usar STDDEV_SAMP
            # STDDEV_SAMP es equivalente a STDDEV_POP para muestras grandes
            query = query.replace('STDDEV_POP', 'STDDEV_SAMP')
        
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return results


# ============================================================================
# ANÁLISIS POR FRANJAS HORARIAS
# ============================================================================

def get_time_slot_analysis(start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Análisis de consumo por franjas horarias.
    
    Divide el consumo en 4 franjas:
    - Madrugada: 00:00 - 05:59
    - Mañana: 06:00 - 11:59
    - Tarde: 12:00 - 17:59
    - Noche: 18:00 - 23:59
    
    Retorna total de horas vistas en cada franja horaria.
    
    Args:
        start_date: Fecha de inicio (opcional)
        end_date: Fecha de fin (opcional)
    
    Returns:
        Dict con consumo por franja horaria
    """
    # Base queryset para contar TODOS los registros (sin filtrar por timeDate/dataDuration)
    base_queryset = MergedTelemetricOTTDelancer.objects.all()
    
    if start_date:
        base_queryset = base_queryset.filter(dataDate__gte=start_date.date())
    if end_date:
        base_queryset = base_queryset.filter(dataDate__lte=end_date.date())
    
    # Para calcular horas, necesitamos filtrar por timeDate y dataDuration
    queryset_for_hours = base_queryset.filter(
        timeDate__isnull=False,
        dataDuration__isnull=False
    )
    
    # timeDate es un IntegerField que contiene la hora directamente (0-23)
    # No necesitamos extraer la hora, solo usar el campo directamente
    
    # Usar Django ORM con Case/When para clasificar por franja horaria (para horas)
    queryset_for_hours = queryset_for_hours.annotate(
        time_slot=Case(
            When(timeDate__gte=0, timeDate__lte=5, then=Value('madrugada')),
            When(timeDate__gte=6, timeDate__lte=11, then=Value('mañana')),
            When(timeDate__gte=12, timeDate__lte=17, then=Value('tarde')),
            default=Value('noche'),
            output_field=CharField()
        )
    )
    
    # Calcular horas por franja
    hours_results = queryset_for_hours.values('time_slot').annotate(
        total_seconds=Sum('dataDuration')
    ).order_by('time_slot')
    
    # Para contar visualizaciones, usar TODOS los registros con timeDate (sin filtrar dataDuration)
    queryset_for_views = base_queryset.filter(timeDate__isnull=False).annotate(
        time_slot=Case(
            When(timeDate__gte=0, timeDate__lte=5, then=Value('madrugada')),
            When(timeDate__gte=6, timeDate__lte=11, then=Value('mañana')),
            When(timeDate__gte=12, timeDate__lte=17, then=Value('tarde')),
            default=Value('noche'),
            output_field=CharField()
        )
    )
    
    views_results = queryset_for_views.values('time_slot').annotate(
        total_views=Count('id')
    ).order_by('time_slot')
    
    # Formatear resultados
    time_slots = {
        'madrugada': {'total_hours': 0, 'total_views': 0},
        'mañana': {'total_hours': 0, 'total_views': 0},
        'tarde': {'total_hours': 0, 'total_views': 0},
        'noche': {'total_hours': 0, 'total_views': 0}
    }
    
    # Procesar horas
    for row in hours_results:
        slot = row['time_slot']
        total_seconds = float(row['total_seconds'] or 0)
        total_hours = total_seconds / 3600
        time_slots[slot]['total_hours'] = round(total_hours, 2)
    
    # Procesar visualizaciones
    for row in views_results:
        slot = row['time_slot']
        time_slots[slot]['total_views'] = row['total_views']
    
    # Calcular totales
    total_all_hours = sum(slot['total_hours'] for slot in time_slots.values())
    total_all_views = sum(slot['total_views'] for slot in time_slots.values())
    
    return {
        'time_slots': time_slots,
        'summary': {
            'total_hours': round(total_all_hours, 2),
            'total_views': total_all_views
        }
    }


# ============================================================================
# RESUMEN GENERAL DE ANÁLISIS
# ============================================================================

def get_general_summary(start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Resumen general con métricas principales.
    
    Incluye:
    - Total de horas vistas
    - Número de usuarios/subscribers activos
    - Total de visualizaciones
    - Dispositivos únicos
    - Canales únicos
    
    Args:
        start_date: Fecha de inicio (opcional)
        end_date: Fecha de fin (opcional)
    
    Returns:
        Dict con resumen general
    """
    queryset = MergedTelemetricOTTDelancer.objects.all()
    
    if start_date:
        queryset = queryset.filter(dataDate__gte=start_date.date())
    if end_date:
        queryset = queryset.filter(dataDate__lte=end_date.date())
    
    # Métricas generales
    total_views = queryset.count()
    unique_users = queryset.filter(subscriberCode__isnull=False).values('subscriberCode').distinct().count()
    unique_devices = queryset.filter(deviceId__isnull=False).values('deviceId').distinct().count()
    unique_channels = queryset.filter(dataName__isnull=False).values('dataName').distinct().count()
    
    # Total de horas vistas (dataDuration está en segundos)
    duration_stats = queryset.filter(dataDuration__isnull=False).aggregate(
        total_seconds=Sum('dataDuration')
    )
    
    total_seconds = float(duration_stats['total_seconds'] or 0)
    total_hours = total_seconds / 3600  # Convertir segundos a horas
    
    return {
        'total_views': total_views,
        'active_users': unique_users,  # Usuarios/subscribers activos
        'unique_devices': unique_devices,
        'unique_channels': unique_channels,
        'total_watch_time': round(total_hours, 2)  # Total de horas vistas
    }


# ============================================================================
# ANÁLISIS GEOGRÁFICO (Django ORM)
# ============================================================================

def get_geographic_analysis(start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Análisis geográfico por país e ISP.
    
    Usa Django ORM con agregaciones optimizadas.
    """
    queryset = MergedTelemetricOTTDelancer.objects.filter(
        whoisCountry__isnull=False
    )
    
    if start_date:
        queryset = queryset.filter(dataDate__gte=start_date.date())
    if end_date:
        queryset = queryset.filter(dataDate__lte=end_date.date())
    
    results = queryset.values('whoisCountry', 'whoisIsp').annotate(
        total_views=Count('id'),
        unique_devices=Count('deviceId', distinct=True),
        unique_users=Count('subscriberCode', distinct=True)
    ).order_by('-total_views')
    
    return list(results)


# ============================================================================
# ANÁLISIS CON PANDAS (Opcional - Solo para análisis complejos)
# ============================================================================

# ============================================================================
# ANÁLISIS CON PANDAS Y NUMPY (Análisis Estadísticos Avanzados)
# ============================================================================

def get_cohort_analysis_pandas(start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Análisis de cohortes usando Pandas.
    
    Analiza el comportamiento de grupos de usuarios por fecha de inicio,
    calculando retención y engagement por cohorte.
    
    Returns:
        Dict con datos de cohortes incluyendo:
        - cohort_month: Mes de inicio de la cohorte
        - period: Período de análisis
        - unique_users: Usuarios únicos en ese período
        - unique_channels: Canales únicos consumidos
        - total_watch_time: Tiempo total de visualización
    """
    _check_pandas()
    
    # Cargar solo los datos necesarios (no toda la tabla)
    queryset = MergedTelemetricOTTDelancer.objects.filter(
        subscriberCode__isnull=False,
        timestamp__isnull=False
    )
    
    if start_date:
        queryset = queryset.filter(dataDate__gte=start_date.date())
    if end_date:
        queryset = queryset.filter(dataDate__lte=end_date.date())
    
    # Convertir a DataFrame (solo campos necesarios)
    df = pd.DataFrame(list(
        queryset.values('subscriberCode', 'timestamp', 'dataName', 'dataDuration')
    ))
    
    if df.empty:
        return {"message": "No hay datos para el análisis de cohortes", "data": []}
    
    # Análisis de cohortes con Pandas
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['cohort_month'] = df.groupby('subscriberCode')['timestamp'].transform('min').dt.to_period('M')
    df['period'] = df['timestamp'].dt.to_period('M')
    
    cohort_data = df.groupby(['cohort_month', 'period']).agg({
        'subscriberCode': 'nunique',
        'dataName': 'nunique',
        'dataDuration': 'sum'
    }).reset_index()
    
    # Calcular retención (usuarios activos en período vs. cohorte inicial)
    cohort_sizes = df.groupby('cohort_month')['subscriberCode'].nunique()
    cohort_data['cohort_size'] = cohort_data['cohort_month'].map(cohort_sizes)
    cohort_data['retention_rate'] = (
        cohort_data['subscriberCode'] / cohort_data['cohort_size'] * 100
    ).round(2)
    
    return {
        "data": cohort_data.to_dict('records'),
        "summary": {
            "total_cohorts": len(cohort_sizes),
            "total_users": cohort_sizes.sum(),
            "avg_cohort_size": cohort_sizes.mean().round(2)
        }
    }


def get_correlation_analysis(start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Análisis de correlaciones entre variables usando Pandas y NumPy.
    
    Analiza correlaciones entre:
    - Duración de visualización vs. número de canales
    - Frecuencia de uso vs. tiempo total de visualización
    - Horario vs. duración promedio
    
    Returns:
        Dict con matriz de correlaciones y análisis estadístico
    """
    _check_pandas()
    
    queryset = MergedTelemetricOTTDelancer.objects.filter(
        subscriberCode__isnull=False,
        dataDuration__isnull=False,
        dataName__isnull=False
    )
    
    if start_date:
        queryset = queryset.filter(dataDate__gte=start_date.date())
    if end_date:
        queryset = queryset.filter(dataDate__lte=end_date.date())
    
    # Cargar datos necesarios
    df = pd.DataFrame(list(
        queryset.values(
            'subscriberCode', 'dataDuration', 'dataName', 
            'dataDate', 'timeDate'
        )
    ))
    
    if df.empty or len(df) < 10:
        return {"message": "Datos insuficientes para análisis de correlación"}
    
    # Preparar datos para análisis
    df['dataDate'] = pd.to_datetime(df['dataDate'])
    df['hour'] = pd.to_datetime(df['timeDate']).dt.hour if 'timeDate' in df.columns else None
    
    # Agregar por usuario
    user_stats = df.groupby('subscriberCode').agg({
        'dataDuration': ['sum', 'mean', 'count'],
        'dataName': 'nunique',
        'hour': 'mean' if 'hour' in df.columns else None
    }).reset_index()
    
    user_stats.columns = ['subscriberCode', 'total_watch_time', 'avg_duration', 
                         'total_views', 'unique_channels', 'avg_hour']
    
    # Convertir tiempos de segundos a horas
    user_stats['total_watch_time'] = user_stats['total_watch_time'] / 3600.0
    user_stats['avg_duration'] = user_stats['avg_duration'] / 3600.0
    
    # Calcular correlaciones
    numeric_cols = ['total_watch_time', 'avg_duration', 'total_views', 'unique_channels']
    if 'avg_hour' in user_stats.columns:
        numeric_cols.append('avg_hour')
    
    correlation_matrix = user_stats[numeric_cols].corr()
    
    # Estadísticas descriptivas
    stats = user_stats[numeric_cols].describe()
    
    return {
        "correlation_matrix": correlation_matrix.to_dict(),
        "descriptive_stats": stats.to_dict(),
        "sample_size": len(user_stats),
        "insights": {
            "strongest_correlation": _get_strongest_correlation(correlation_matrix),
            "watch_time_vs_channels": correlation_matrix.loc['total_watch_time', 'unique_channels'],
            "views_vs_duration": correlation_matrix.loc['total_views', 'avg_duration']
        }
    }


def _get_strongest_correlation(corr_matrix: pd.DataFrame) -> Dict[str, Any]:
    """Encuentra la correlación más fuerte (excluyendo diagonal)."""
    corr_matrix = corr_matrix.copy()
    np.fill_diagonal(corr_matrix.values, 0)  # Excluir diagonal
    
    max_corr = corr_matrix.abs().max().max()
    max_idx = corr_matrix.abs().stack().idxmax()
    
    return {
        "variable1": max_idx[0],
        "variable2": max_idx[1],
        "correlation": float(corr_matrix.loc[max_idx[0], max_idx[1]]),
        "strength": "fuerte" if abs(corr_matrix.loc[max_idx[0], max_idx[1]]) > 0.7 else 
                   "moderada" if abs(corr_matrix.loc[max_idx[0], max_idx[1]]) > 0.4 else "débil"
    }


def _simple_kmeans(X: np.ndarray, n_clusters: int, max_iters: int = 100) -> np.ndarray:
    """
    Implementación simple de K-means usando solo NumPy.
    
    Args:
        X: Datos normalizados (n_samples, n_features)
        n_clusters: Número de clusters
        max_iters: Máximo de iteraciones
    
    Returns:
        Array con etiquetas de cluster para cada muestra
    """
    n_samples, n_features = X.shape
    
    # Inicializar centroides aleatoriamente
    np.random.seed(42)
    centroids = X[np.random.choice(n_samples, n_clusters, replace=False)]
    
    for _ in range(max_iters):
        # Asignar puntos al centroide más cercano
        distances = np.sqrt(((X - centroids[:, np.newaxis])**2).sum(axis=2))
        labels = np.argmin(distances, axis=0)
        
        # Actualizar centroides
        new_centroids = np.array([X[labels == k].mean(axis=0) for k in range(n_clusters)])
        
        # Verificar convergencia
        if np.allclose(centroids, new_centroids):
            break
        
        centroids = new_centroids
    
    return labels


def get_time_series_analysis(channel: Optional[str] = None,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None,
                            forecast_days: int = 7) -> Dict[str, Any]:
    """
    Análisis de series temporales con forecasting usando Pandas y NumPy.
    
    Analiza tendencias temporales y genera pronósticos simples usando
    media móvil y tendencia lineal.
    
    Args:
        channel: Canal específico (None = todos)
        start_date: Fecha de inicio
        end_date: Fecha de fin
        forecast_days: Días a pronosticar
    
    Returns:
        Dict con datos históricos, tendencia y pronóstico
    """
    _check_pandas()
    
    queryset = MergedTelemetricOTTDelancer.objects.filter(
        dataDate__isnull=False
    )
    
    if channel:
        queryset = queryset.filter(dataName=channel)
    if start_date:
        queryset = queryset.filter(dataDate__gte=start_date.date())
    if end_date:
        queryset = queryset.filter(dataDate__lte=end_date.date())
    
    # Cargar datos diarios
    df = pd.DataFrame(list(
        queryset.values('dataDate', 'id')
    ))
    
    if df.empty:
        return {"message": "No hay datos para análisis de series temporales"}
    
    df['dataDate'] = pd.to_datetime(df['dataDate'])
    daily_views = df.groupby('dataDate').size().reset_index(name='views')
    daily_views = daily_views.sort_values('dataDate')
    
    # Calcular media móvil (7 días)
    daily_views['moving_avg_7d'] = daily_views['views'].rolling(window=7, min_periods=1).mean()
    
    # Calcular tendencia lineal simple
    x = np.arange(len(daily_views))
    y = daily_views['views'].values
    
    # Regresión lineal simple
    coeffs = np.polyfit(x, y, 1)
    trend_line = np.poly1d(coeffs)
    daily_views['trend'] = trend_line(x)
    
    # Pronóstico simple (extrapolación de tendencia)
    last_date = daily_views['dataDate'].max()
    forecast_dates = pd.date_range(
        start=last_date + timedelta(days=1),
        periods=forecast_days,
        freq='D'
    )
    
    forecast_x = np.arange(len(daily_views), len(daily_views) + forecast_days)
    forecast_values = trend_line(forecast_x)
    
    forecast_df = pd.DataFrame({
        'dataDate': forecast_dates,
        'forecast': forecast_values,
        'moving_avg_forecast': daily_views['moving_avg_7d'].iloc[-1]  # Última media móvil
    })
    
    # Estadísticas
    stats = {
        "mean": float(daily_views['views'].mean()),
        "std": float(daily_views['views'].std()),
        "trend_slope": float(coeffs[0]),  # Pendiente de la tendencia
        "trend_direction": "creciente" if coeffs[0] > 0 else "decreciente" if coeffs[0] < 0 else "estable"
    }
    
    return {
        "historical_data": daily_views.to_dict('records'),
        "forecast": forecast_df.to_dict('records'),
        "statistics": stats,
        "channel": channel or "Todos los canales"
    }


def get_user_segmentation_analysis(start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None,
                                  n_segments: int = 4) -> Dict[str, Any]:
    """
    Segmentación de usuarios usando K-means clustering (NumPy).
    
    Segmenta usuarios en grupos basados en:
    - Frecuencia de uso (total de views)
    - Tiempo total de visualización
    - Diversidad de canales
    - Duración promedio por sesión
    
    Returns:
        Dict con segmentos de usuarios y sus características
    """
    _check_pandas()
    
    queryset = MergedTelemetricOTTDelancer.objects.filter(
        subscriberCode__isnull=False
    )
    
    if start_date:
        queryset = queryset.filter(dataDate__gte=start_date.date())
    if end_date:
        queryset = queryset.filter(dataDate__lte=end_date.date())
    
    # Cargar datos de usuarios
    df = pd.DataFrame(list(
        queryset.values('subscriberCode', 'dataDuration', 'dataName', 'dataDate')
    ))
    
    if df.empty or len(df) < n_segments:
        return {"message": "Datos insuficientes para segmentación"}
    
    # Agregar métricas por usuario
    user_metrics = df.groupby('subscriberCode').agg({
        'dataDuration': ['sum', 'mean'],
        'dataName': 'nunique',
        'dataDate': 'count'
    }).reset_index()
    
    user_metrics.columns = ['subscriberCode', 'total_watch_time', 'avg_duration',
                           'unique_channels', 'total_views']
    
    # Convertir tiempos de segundos a horas
    user_metrics['total_watch_time'] = user_metrics['total_watch_time'] / 3600.0
    user_metrics['avg_duration'] = user_metrics['avg_duration'] / 3600.0
    
    # Normalizar datos para clustering (usando NumPy)
    features = ['total_watch_time', 'avg_duration', 'unique_channels', 'total_views']
    X = user_metrics[features].values
    
    # Normalizar manualmente (z-score)
    X_mean = np.mean(X, axis=0)
    X_std = np.std(X, axis=0)
    X_std[X_std == 0] = 1  # Evitar división por cero
    X_scaled = (X - X_mean) / X_std
    
    # K-means simple con NumPy (implementación básica)
    user_metrics['segment'] = _simple_kmeans(X_scaled, n_segments)
    
    # Características de cada segmento
    segment_summary = user_metrics.groupby('segment')[features].agg(['mean', 'std']).round(2)
    
    # Asignar nombres descriptivos a segmentos
    segment_names = {
        0: "Usuarios Ocasionales",
        1: "Usuarios Regulares",
        2: "Usuarios Activos",
        3: "Usuarios Super Activos"
    }
    
    segment_info = []
    for seg_id in range(n_segments):
        seg_data = user_metrics[user_metrics['segment'] == seg_id]
        
        # Calcular totales del segmento (suma, no promedio)
        total_watch_time_segment = seg_data['total_watch_time'].sum()
        total_views_segment = seg_data['total_views'].sum()
        
        # Calcular avg_duration como total_watch_time / total_views
        avg_duration_segment = total_watch_time_segment / total_views_segment if total_views_segment > 0 else 0
        
        segment_info.append({
            "segment_id": seg_id,
            "segment_name": segment_names.get(seg_id, f"Segmento {seg_id}"),
            "user_count": len(seg_data),
            "percentage": round(len(seg_data) / len(user_metrics) * 100, 2),
            "avg_metrics": {
                "total_watch_time": round(float(total_watch_time_segment), 2),  # Suma total del segmento
                "total_views": int(total_views_segment),  # Suma total del segmento
                "avg_duration": round(avg_duration_segment, 2),  # total_watch_time / total_views
                "unique_channels": float(seg_data['unique_channels'].mean())  # Promedio de canales únicos por usuario
            }
        })
    
    return {
        "segments": segment_info,
        "total_users": len(user_metrics),
        "features_used": features
    }


def get_channel_performance_matrix(start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Matriz de rendimiento de canales usando Pandas.
    
    Crea una matriz que combina múltiples métricas:
    - Views totales
    - Usuarios únicos
    - Duración promedio
    - Tasa de retención
    
    Returns:
        Dict con matriz de rendimiento y ranking
    """
    _check_pandas()
    
    queryset = MergedTelemetricOTTDelancer.objects.filter(
        dataName__isnull=False
    )
    
    if start_date:
        queryset = queryset.filter(dataDate__gte=start_date.date())
    if end_date:
        queryset = queryset.filter(dataDate__lte=end_date.date())
    
    # Cargar datos
    df = pd.DataFrame(list(
        queryset.values('dataName', 'subscriberCode', 'deviceId', 'dataDuration', 'dataDate')
    ))
    
    if df.empty:
        return {"message": "No hay datos para matriz de rendimiento"}
    
    # Calcular métricas por canal
    channel_metrics = df.groupby('dataName').agg({
        'dataName': 'count',  # Total views
        'subscriberCode': 'nunique',  # Usuarios únicos
        'deviceId': 'nunique',  # Dispositivos únicos
        'dataDuration': ['sum', 'mean'],  # Tiempo total y promedio
        'dataDate': 'nunique'  # Días activos
    }).reset_index()
    
    channel_metrics.columns = ['channel', 'total_views', 'unique_users', 'unique_devices',
                                'total_watch_time', 'avg_duration', 'active_days']
    
    # Convertir tiempos de segundos a horas
    channel_metrics['total_watch_time'] = channel_metrics['total_watch_time'] / 3600.0
    channel_metrics['avg_duration'] = channel_metrics['avg_duration'] / 3600.0
    
    # Calcular métricas derivadas
    channel_metrics['views_per_user'] = (
        channel_metrics['total_views'] / channel_metrics['unique_users']
    ).round(2)
    
    channel_metrics['watch_time_per_user'] = (
        channel_metrics['total_watch_time'] / channel_metrics['unique_users']
    ).round(2)
    
    # Normalizar para scoring (0-100)
    for col in ['total_views', 'unique_users', 'total_watch_time', 'avg_duration']:
        max_val = channel_metrics[col].max()
        if max_val > 0:
            channel_metrics[f'{col}_score'] = (
                channel_metrics[col] / max_val * 100
            ).round(2)
    
    # Score total (promedio de scores normalizados)
    score_cols = [col for col in channel_metrics.columns if col.endswith('_score')]
    channel_metrics['performance_score'] = channel_metrics[score_cols].mean(axis=1).round(2)
    
    # Ranking
    channel_metrics = channel_metrics.sort_values('performance_score', ascending=False)
    channel_metrics['rank'] = range(1, len(channel_metrics) + 1)
    
    return {
        "performance_matrix": channel_metrics.to_dict('records'),
        "summary": {
            "total_channels": len(channel_metrics),
            "top_channel": channel_metrics.iloc[0]['channel'] if len(channel_metrics) > 0 else None,
            "avg_performance_score": float(channel_metrics['performance_score'].mean())
        }
    }


# ============================================================================
# FUNCIÓN HELPER PARA DETERMINAR QUÉ ENFOQUE USAR
# ============================================================================

def get_analysis_strategy(analysis_type: str) -> str:
    """
    Determina qué estrategia usar para cada tipo de análisis.
    
    Returns:
        'orm': Usar Django ORM
        'sql': Usar Raw SQL optimizado
        'pandas': Usar Pandas (opcional)
    """
    strategies = {
        # Análisis simples - Django ORM
        'top_channels': 'orm',
        'channel_audience': 'orm',
        'peak_hours': 'orm',
        'average_duration': 'orm',
        'temporal': 'orm',
        'geographic': 'orm',
        
        # Análisis complejos - Raw SQL
        'day_over_day': 'sql',
        'anomaly_detection': 'sql',
        'trend_analysis': 'sql',
        
        # Análisis estadísticos avanzados - Pandas (opcional)
        'cohort_analysis': 'pandas',
        'correlation_analysis': 'pandas',
        'time_series_forecast': 'pandas',
    }
    
    return strategies.get(analysis_type, 'orm')

