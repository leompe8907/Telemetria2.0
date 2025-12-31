# Análisis Segmentado por Rango de Fechas

## 📅 Descripción

Este módulo (`analytics_date_range.py`) proporciona análisis específicos para períodos de tiempo definidos por el usuario. A diferencia del módulo general de análisis, **todas las funciones requieren rangos de fechas obligatorios** y están optimizadas para análisis comparativos y detallados de períodos específicos.

---

## 🎯 Funciones Disponibles

### 1. **`get_period_summary(start_date, end_date)`**

Resumen general del período seleccionado.

**Parámetros:**
- `start_date` (datetime, obligatorio): Fecha de inicio
- `end_date` (datetime, obligatorio): Fecha de fin

**Retorna:**
```python
{
    "period": {
        "start_date": "2025-01-01",
        "end_date": "2025-01-07",
        "days": 7
    },
    "metrics": {
        "total_views": 50000,
        "unique_users": 5000,
        "unique_devices": 4500,
        "unique_channels": 25,
        "total_watch_time": 125000.5,
        "avg_duration": 45.2,
        "avg_views_per_day": 7142.86
    },
    "top_channels": [...],
    "daily_distribution": [...]
}
```

**Ejemplo de uso:**
```python
from datetime import datetime
from TelemetriaDelancer.panaccess.analytics_date_range import get_period_summary

start = datetime(2025, 1, 1)
end = datetime(2025, 1, 7)
summary = get_period_summary(start, end)
```

---

### 2. **`get_period_comparison(start_date, end_date, compare_with_previous=True)`**

Compara el período seleccionado con el período anterior equivalente.

**Parámetros:**
- `start_date` (datetime, obligatorio)
- `end_date` (datetime, obligatorio)
- `compare_with_previous` (bool, default=True): Comparar con período anterior

**Retorna:**
```python
{
    "current_period": {...},  # Resumen del período actual
    "previous_period": {...},  # Resumen del período anterior
    "comparison": {
        "period_days": 7,
        "previous_start_date": "2024-12-25",
        "previous_end_date": "2024-12-31",
        "changes": {
            "views": {
                "absolute": 5000,
                "percentage": 10.0,
                "trend": "aumento"
            },
            "users": {...},
            "watch_time": {...}
        }
    }
}
```

**Ejemplo de uso:**
```python
from TelemetriaDelancer.panaccess.analytics_date_range import get_period_comparison

comparison = get_period_comparison(start, end)
# Compara automáticamente con los 7 días anteriores
```

---

### 3. **`get_period_temporal_breakdown(start_date, end_date, breakdown='daily')`**

Desglose temporal detallado del período (día por día, semana por semana, o mes por mes).

**Parámetros:**
- `start_date` (datetime, obligatorio)
- `end_date` (datetime, obligatorio)
- `breakdown` (str): 'daily', 'weekly', o 'monthly'

**Retorna:**
```python
{
    "period": {
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "breakdown": "daily"
    },
    "temporal_data": [
        {
            "period": "2025-01-01",
            "views": 5000,
            "unique_users": 500,
            "total_watch_time": 12500.5,
            "avg_duration": 45.2
        },
        ...
    ],
    "statistics": {
        "views": {
            "mean": 5200.5,
            "std": 320.2,
            "min": 4500,
            "max": 6000,
            "trend": "creciente"
        }
    }
}
```

**Ejemplo de uso:**
```python
from TelemetriaDelancer.panaccess.analytics_date_range import get_period_temporal_breakdown

# Análisis día por día
daily = get_period_temporal_breakdown(start, end, breakdown='daily')

# Análisis semana por semana
weekly = get_period_temporal_breakdown(start, end, breakdown='weekly')
```

---

### 4. **`get_period_channel_analysis(start_date, end_date, top_n=20)`**

Análisis detallado de canales en el período seleccionado.

**Parámetros:**
- `start_date` (datetime, obligatorio)
- `end_date` (datetime, obligatorio)
- `top_n` (int, default=20): Número de canales top

**Retorna:**
```python
{
    "period": {...},
    "total_channels": 25,
    "total_period_views": 50000,
    "channels": [
        {
            "dataName": "Canal Premium",
            "total_views": 10000,
            "unique_users": 2000,
            "unique_devices": 1800,
            "total_watch_time": 25000.5,
            "avg_duration": 50.2,
            "active_days": 7,
            "percentage": 20.0,
            "views_per_user": 5.0,
            "watch_time_per_user": 12.5
        },
        ...
    ]
}
```

---

### 5. **`get_period_user_analysis(start_date, end_date, top_n=50)`**

Análisis de comportamiento de usuarios en el período.

**Parámetros:**
- `start_date` (datetime, obligatorio)
- `end_date` (datetime, obligatorio)
- `top_n` (int, default=50): Número de usuarios top

**Retorna:**
```python
{
    "period": {...},
    "total_users": 5000,
    "top_users": [
        {
            "subscriberCode": "USER123",
            "total_views": 150,
            "unique_channels": 10,
            "unique_devices": 2,
            "total_watch_time": 5000.5,
            "avg_duration": 45.2,
            "active_days": 7,
            "activity_rate": 100.0,
            "avg_views_per_day": 21.43
        },
        ...
    ]
}
```

---

### 6. **`get_period_events_analysis(start_date, end_date, threshold_std=2.0)`** ⚠️ Requiere Pandas

Identifica eventos y picos anómalos dentro del período.

**Parámetros:**
- `start_date` (datetime, obligatorio)
- `end_date` (datetime, obligatorio)
- `threshold_std` (float, default=2.0): Desviaciones estándar para considerar evento

**Retorna:**
```python
{
    "period": {...},
    "statistics": {
        "mean_daily_views": 7142.86,
        "std_daily_views": 500.2,
        "total_days": 7,
        "threshold_std": 2.0
    },
    "peaks": [
        {
            "date": "2025-01-05",
            "views": 10000,
            "z_score": 5.71,
            "unique_channels": 25,
            "unique_users": 2000
        }
    ],
    "valleys": [...],
    "daily_data": [...]
}
```

---

### 7. **`get_period_trend_analysis(start_date, end_date)`** ⚠️ Requiere Pandas

Análisis de tendencia dentro del período usando regresión lineal.

**Parámetros:**
- `start_date` (datetime, obligatorio)
- `end_date` (datetime, obligatorio)

**Retorna:**
```python
{
    "period": {...},
    "trend": {
        "direction": "creciente",
        "strength": "fuerte",
        "slope": 150.5,
        "r_squared": 0.85,
        "interpretation": "Tendencia creciente fuerte"
    },
    "change": {
        "first_day_views": 5000,
        "last_day_views": 8000,
        "absolute_change": 3000,
        "percentage_change": 60.0
    },
    "daily_data": [...]
}
```

---

### 8. **`get_complete_period_analysis(start_date, end_date, include_comparison=True, include_events=True)`** ⭐ FUNCIÓN PRINCIPAL

Análisis completo del período que combina todos los análisis.

**Parámetros:**
- `start_date` (datetime, obligatorio)
- `end_date` (datetime, obligatorio)
- `include_comparison` (bool, default=True): Incluir comparación
- `include_events` (bool, default=True): Incluir análisis de eventos

**Retorna:**
```python
{
    "period": {...},
    "summary": {...},  # Resumen general
    "comparison": {...},  # Comparación con período anterior
    "temporal_breakdown": {...},  # Desglose temporal
    "channels": {...},  # Análisis de canales
    "users": {...},  # Análisis de usuarios
    "trend": {...},  # Análisis de tendencia
    "events": {...},  # Análisis de eventos
    "generated_at": "2025-12-31T12:00:00"
}
```

**Ejemplo de uso:**
```python
from TelemetriaDelancer.panaccess.analytics_date_range import get_complete_period_analysis

# Análisis completo de una semana
complete = get_complete_period_analysis(start, end)
```

---

## 📝 Ejemplos de Uso Completos

### Ejemplo 1: Análisis de una Semana Específica

```python
from datetime import datetime
from TelemetriaDelancer.panaccess.analytics_date_range import get_complete_period_analysis

# Analizar la primera semana de enero
start = datetime(2025, 1, 1)
end = datetime(2025, 1, 7)

analysis = get_complete_period_analysis(start, end)

print(f"Total de visualizaciones: {analysis['summary']['metrics']['total_views']}")
print(f"Usuarios únicos: {analysis['summary']['metrics']['unique_users']}")
print(f"Tendencia: {analysis['trend']['trend']['direction']}")
```

### Ejemplo 2: Comparar Dos Períodos

```python
from datetime import datetime, timedelta
from TelemetriaDelancer.panaccess.analytics_date_range import get_period_comparison

# Período actual (última semana)
end = datetime.now()
start = end - timedelta(days=6)

comparison = get_period_comparison(start, end)

if comparison['comparison']:
    changes = comparison['comparison']['changes']
    print(f"Cambio en visualizaciones: {changes['views']['percentage']}%")
    print(f"Tendencia: {changes['views']['trend']}")
```

### Ejemplo 3: Identificar Días con Picos

```python
from datetime import datetime
from TelemetriaDelancer.panaccess.analytics_date_range import get_period_events_analysis

start = datetime(2025, 1, 1)
end = datetime(2025, 1, 31)

events = get_period_events_analysis(start, end)

print(f"Días con picos: {len(events['peaks'])}")
for peak in events['peaks']:
    print(f"  {peak['date']}: {peak['views']} visualizaciones (z-score: {peak['z_score']:.2f})")
```

---

## 🔄 Diferencia con `analytics.py`

| Característica | `analytics.py` | `analytics_date_range.py` |
|---------------|----------------|---------------------------|
| **Rango de fechas** | Opcional | Obligatorio |
| **Enfoque** | Análisis generales | Análisis de períodos específicos |
| **Comparaciones** | Limitadas | Comparación automática con período anterior |
| **Eventos** | No incluido | Detección de picos y valles |
| **Tendencias** | Series temporales generales | Tendencias dentro del período |
| **Uso principal** | Análisis generales | Reportes de períodos específicos |

---

## ⚠️ Notas Importantes

1. **Rango de fechas obligatorio**: Todas las funciones requieren `start_date` y `end_date`
2. **Validación automática**: Se valida que `start_date < end_date`
3. **Pandas requerido**: Algunas funciones requieren Pandas/NumPy (se indica en la documentación)
4. **Rendimiento**: Para rangos muy amplios (>365 días), se muestra advertencia
5. **Comparación automática**: `get_period_comparison` calcula automáticamente el período anterior equivalente

---

## 🚀 Integración con API

Puedes crear endpoints REST para exponer estos análisis:

```python
# En views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
from TelemetriaDelancer.panaccess.analytics_date_range import get_complete_period_analysis

class PeriodAnalysisView(APIView):
    def post(self, request):
        start_str = request.data.get('start_date')
        end_str = request.data.get('end_date')
        
        start = datetime.fromisoformat(start_str)
        end = datetime.fromisoformat(end_str)
        
        analysis = get_complete_period_analysis(start, end)
        return Response(analysis)
```

---

**Documento creado:** 2025-12-31  
**Última actualización:** 2025-12-31  
**Versión:** 1.0

