# Implementación de Pandas y NumPy - Análisis Avanzados

## 📦 Instalación

Pandas y NumPy ya están incluidos en `requirements.txt`. Para instalar:

```bash
pip install -r requirements.txt
```

O solo las librerías de análisis:
```bash
pip install pandas numpy
```

---

## 🎯 Dónde y Cómo se Implementó

### 1. **Archivo Principal: `TelemetriaDelancer/panaccess/analytics.py`**

Este archivo contiene todas las funciones de análisis, organizadas en tres secciones:

#### **Sección 1: Análisis Simples (Django ORM)**
- `get_top_channels()` - Top canales más vistos
- `get_channel_audience()` - Audiencia por canal
- `get_peak_hours_by_channel()` - Horarios pico
- `get_average_duration_by_channel()` - Duración promedio
- `get_temporal_analysis()` - Análisis temporal
- `get_geographic_analysis()` - Análisis geográfico

**¿Por qué Django ORM?**
- Aprovecha índices de base de datos
- Muy eficiente en memoria
- No requiere cargar datos en RAM

#### **Sección 2: Análisis Complejos (Raw SQL)**
- `get_day_over_day_comparison()` - Comparación día a día
- `get_anomaly_detection()` - Detección de anomalías

**¿Por qué Raw SQL?**
- Funciones de ventana (LAG, LEAD)
- CTEs complejas
- Optimizado para PostgreSQL

#### **Sección 3: Análisis Avanzados (Pandas + NumPy)** ⭐ NUEVO

Estas son las funciones que aprovechan Pandas y NumPy:

---

## 🔬 Funciones con Pandas/NumPy

### 1. **`get_cohort_analysis_pandas()`**
**Ubicación:** Línea ~334

**¿Qué hace?**
- Analiza comportamiento de grupos de usuarios por fecha de inicio
- Calcula retención y engagement por cohorte
- Identifica patrones de uso a lo largo del tiempo

**¿Por qué Pandas?**
- Agrupaciones complejas por múltiples dimensiones
- Transformaciones de fechas avanzadas
- Cálculos de retención que requieren operaciones secuenciales

**Ejemplo de uso:**
```python
from TelemetriaDelancer.panaccess.analytics import get_cohort_analysis_pandas
from datetime import datetime, timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=90)

cohort_data = get_cohort_analysis_pandas(start_date, end_date)
# Retorna: {
#   "data": [...],  # Datos de cohortes
#   "summary": {
#     "total_cohorts": 3,
#     "total_users": 1500,
#     "avg_cohort_size": 500
#   }
# }
```

---

### 2. **`get_correlation_analysis()`**
**Ubicación:** Línea ~390

**¿Qué hace?**
- Analiza correlaciones entre variables (duración, frecuencia, canales, etc.)
- Identifica relaciones estadísticas entre métricas
- Genera matriz de correlaciones y estadísticas descriptivas

**¿Por qué Pandas/NumPy?**
- Cálculo de correlaciones de Pearson
- Operaciones matriciales eficientes
- Estadísticas descriptivas avanzadas

**Ejemplo de uso:**
```python
from TelemetriaDelancer.panaccess.analytics import get_correlation_analysis

correlations = get_correlation_analysis()
# Retorna: {
#   "correlation_matrix": {...},
#   "descriptive_stats": {...},
#   "insights": {
#     "strongest_correlation": {
#       "variable1": "total_watch_time",
#       "variable2": "unique_channels",
#       "correlation": 0.85,
#       "strength": "fuerte"
#     }
#   }
# }
```

---

### 3. **`get_time_series_analysis()`**
**Ubicación:** Línea ~460

**¿Qué hace?**
- Analiza tendencias temporales
- Calcula media móvil
- Genera pronósticos simples usando regresión lineal
- Identifica dirección de tendencia (creciente/decreciente/estable)

**¿Por qué Pandas/NumPy?**
- Manipulación de series temporales
- Cálculo de media móvil
- Regresión lineal con `np.polyfit()`
- Generación de fechas futuras para pronóstico

**Ejemplo de uso:**
```python
from TelemetriaDelancer.panaccess.analytics import get_time_series_analysis

# Análisis de un canal específico con pronóstico de 7 días
ts_analysis = get_time_series_analysis(
    channel="Canal Premium",
    forecast_days=7
)
# Retorna: {
#   "historical_data": [...],  # Datos históricos con media móvil
#   "forecast": [...],  # Pronóstico para próximos 7 días
#   "statistics": {
#     "mean": 1250.5,
#     "std": 320.2,
#     "trend_slope": 15.3,
#     "trend_direction": "creciente"
#   }
# }
```

---

### 4. **`get_user_segmentation_analysis()`**
**Ubicación:** Línea ~540

**¿Qué hace?**
- Segmenta usuarios en grupos usando K-means clustering
- Identifica diferentes tipos de usuarios (ocasionales, regulares, activos, super activos)
- Analiza características de cada segmento

**¿Por qué NumPy?**
- Implementación de K-means desde cero (sin sklearn)
- Normalización de datos (z-score)
- Cálculos de distancias euclidianas
- Agrupación eficiente

**Ejemplo de uso:**
```python
from TelemetriaDelancer.panaccess.analytics import get_user_segmentation_analysis

# Segmentar en 4 grupos
segments = get_user_segmentation_analysis(n_segments=4)
# Retorna: {
#   "segments": [
#     {
#       "segment_id": 0,
#       "segment_name": "Usuarios Ocasionales",
#       "user_count": 450,
#       "percentage": 30.0,
#       "avg_metrics": {
#         "total_watch_time": 1200.5,
#         "avg_duration": 45.2,
#         "unique_channels": 3.1,
#         "total_views": 8.5
#       }
#     },
#     ...
#   ],
#   "total_users": 1500
# }
```

---

### 5. **`get_channel_performance_matrix()`**
**Ubicación:** Línea ~620

**¿Qué hace?**
- Crea matriz de rendimiento combinando múltiples métricas
- Calcula scores normalizados (0-100) para cada canal
- Genera ranking de canales por rendimiento
- Combina views, usuarios, duración, retención

**¿Por qué Pandas?**
- Agregaciones complejas por múltiples dimensiones
- Cálculo de métricas derivadas
- Normalización y scoring
- Ranking y ordenamiento

**Ejemplo de uso:**
```python
from TelemetriaDelancer.panaccess.analytics import get_channel_performance_matrix

performance = get_channel_performance_matrix()
# Retorna: {
#   "performance_matrix": [
#     {
#       "channel": "Canal Premium",
#       "total_views": 50000,
#       "unique_users": 5000,
#       "performance_score": 95.5,
#       "rank": 1
#     },
#     ...
#   ],
#   "summary": {
#     "total_channels": 25,
#     "top_channel": "Canal Premium",
#     "avg_performance_score": 65.3
#   }
# }
```

---

## 🏗️ Arquitectura de Implementación

### Verificación de Disponibilidad

```python
# Al inicio del archivo
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("Pandas/NumPy no están instalados...")

# Función helper
def _check_pandas():
    """Verifica si pandas está disponible."""
    if not PANDAS_AVAILABLE:
        raise ImportError("Pandas y NumPy son requeridos...")
```

### Flujo de Datos

```
1. Django ORM → Carga datos filtrados (eficiente)
   ↓
2. Conversión a DataFrame → Solo campos necesarios
   ↓
3. Procesamiento con Pandas/NumPy → Análisis estadístico
   ↓
4. Conversión a Dict → Retorno compatible con Django
```

### Optimizaciones Implementadas

1. **Carga Selectiva de Datos**
   - Solo carga campos necesarios con `.values()`
   - Filtros aplicados en BD antes de cargar

2. **Procesamiento Eficiente**
   - Uso de operaciones vectorizadas de NumPy
   - Agrupaciones optimizadas de Pandas
   - Evita loops de Python cuando es posible

3. **Manejo de Memoria**
   - No carga toda la tabla en memoria
   - Procesa en chunks cuando es necesario
   - Limpia DataFrames después de usar

---

## 📊 Comparación: Con vs Sin Pandas/NumPy

### Análisis de Correlaciones

**Sin Pandas (Solo SQL):**
```sql
-- Muy complejo, requiere múltiples subconsultas
-- Difícil de mantener
-- Limitado a correlaciones simples
```

**Con Pandas:**
```python
# Simple y claro
correlation_matrix = user_stats[features].corr()
# Soporta múltiples tipos de correlación
# Fácil de extender
```

### Análisis de Cohortes

**Sin Pandas:**
- Requeriría múltiples consultas SQL complejas
- Cálculos de retención muy difíciles
- Código difícil de mantener

**Con Pandas:**
- Una función clara y mantenible
- Cálculos de retención naturales
- Fácil de extender con nuevas métricas

---

## 🚀 Uso en Endpoints API

### Ejemplo: Endpoint de Análisis

```python
# En views.py
from TelemetriaDelancer.panaccess.analytics import (
    get_correlation_analysis,
    get_time_series_analysis,
    get_user_segmentation_analysis
)

class AnalyticsView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        analysis_type = request.data.get('type')
        
        if analysis_type == 'correlation':
            result = get_correlation_analysis()
        elif analysis_type == 'time_series':
            channel = request.data.get('channel')
            result = get_time_series_analysis(channel=channel)
        elif analysis_type == 'segmentation':
            result = get_user_segmentation_analysis()
        else:
            return Response({"error": "Tipo de análisis no válido"}, 
                          status=400)
        
        return Response(result, status=200)
```

---

## ⚠️ Consideraciones Importantes

### 1. **Rendimiento**
- Pandas es más lento que SQL para agregaciones simples
- Usar solo cuando SQL no es suficiente
- Cargar solo datos necesarios

### 2. **Memoria**
- DataFrames cargan datos en RAM
- Para tablas muy grandes, considerar procesamiento en chunks
- Limpiar DataFrames después de usar

### 3. **Cuándo Usar Cada Enfoque**

| Tipo de Análisis | Enfoque Recomendado |
|-----------------|-------------------|
| Agregaciones simples | Django ORM |
| Funciones de ventana | Raw SQL |
| Correlaciones múltiples | Pandas |
| Series temporales | Pandas |
| Clustering | NumPy/Pandas |
| Cohortes complejas | Pandas |

---

## 📝 Resumen

### ✅ Implementado

1. **Pandas y NumPy agregados a requirements.txt**
2. **5 funciones avanzadas implementadas:**
   - Análisis de cohortes
   - Análisis de correlaciones
   - Análisis de series temporales
   - Segmentación de usuarios
   - Matriz de rendimiento de canales

3. **Verificación de disponibilidad** (graceful degradation)
4. **Optimizaciones de memoria y rendimiento**
5. **Documentación completa**

### 🎯 Dónde Está

- **Archivo principal:** `TelemetriaDelancer/panaccess/analytics.py`
- **Líneas:** ~330-750 (funciones con Pandas/NumPy)
- **Dependencias:** `requirements.txt` (pandas>=2.0.0, numpy>=1.24.0)

### 🔄 Próximos Pasos

1. Instalar dependencias: `pip install -r requirements.txt`
2. Probar funciones individualmente
3. Crear endpoints API para exponer análisis
4. Agregar caché para análisis frecuentes (opcional)

---

**Documento creado:** 2025-12-31  
**Última actualización:** 2025-12-31  
**Versión:** 1.0

