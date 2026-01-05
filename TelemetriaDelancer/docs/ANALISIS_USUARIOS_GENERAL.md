# Análisis General de Usuarios/Subscribers

## 👥 Descripción

Este módulo (`analytics_users_general.py`) proporciona un análisis agregado de todos los usuarios/subscribers del sistema. Permite obtener una visión general del comportamiento de la base de usuarios, incluyendo segmentación, estadísticas agregadas, top usuarios y métricas de engagement.

**IMPORTANTE:** Los análisis trabajan con datos de la base de datos local (`MergedTelemetricOTTDelancer`), NO consultan directamente a PanAccess. Los datos se obtienen de PanAccess mediante `telemetry_fetcher.py` y se almacenan localmente para análisis.

**Ideal para:**
- Dashboards ejecutivos con visión general de usuarios
- Análisis de segmentación de usuarios por nivel de actividad
- Identificación de usuarios top (por horas, visualizaciones, canales)
- Análisis de retención y churn potencial
- Distribución temporal de usuarios activos

---

## 🎯 Función Disponible

### **`get_general_users_analysis(start_date=None, end_date=None, n_segments=5)`**

Análisis general de todos los usuarios/subscribers.

**Parámetros:**
- `start_date` (datetime, opcional): Fecha de inicio para filtrar el análisis
- `end_date` (datetime, opcional): Fecha de fin para filtrar el análisis
- `n_segments` (int, default=5): Número de segmentos para clasificar usuarios (si Pandas no está disponible)

**Retorna:**

**Caso 1: Con usuarios en el período**
```python
{
    "total_users": 5000,  # Count distinct de subscriberCode
    "aggregate_stats": {
        "avg_views_per_user": 125.5,  # Promedio redondeado a 2 decimales
        "avg_hours_per_user": 45.2,  # Promedio redondeado a 2 decimales (calculado desde segundos)
        "avg_channels_per_user": 8.3,  # Promedio redondeado a 2 decimales
        "avg_devices_per_user": 1.8,  # Promedio redondeado a 2 decimales
        "avg_active_days_per_user": 12.5,  # Promedio redondeado a 2 decimales
        "total_views_all_users": 627500,  # Suma total de visualizaciones (int)
        "total_hours_all_users": 226000.0  # Suma total de horas (redondeado a 2 decimales)
    },
    "segmentation": {
        "super_activo": 1000,
        "activo": 1500,
        "regular": 1200,
        "ocasional": 800,
        "inactivo": 500
    },
    "top_users": {
        "by_hours": [
            {
                "subscriber_code": "USER001",  # subscriberCode
                "total_hours": 450.5,  # Redondeado a 2 decimales
                "total_views": 2500  # Total de visualizaciones
            },
            ...
        ],
        # Nota: Top 10 usuarios ordenados por total_hours descendente
        "by_views": [
            {
                "subscriber_code": "USER002",
                "total_views": 3000,
                "total_hours": 380.2  # Redondeado a 2 decimales
            },
            ...
        ],
        # Nota: Top 10 usuarios ordenados por total_views descendente
        "by_channels": [
            {
                "subscriber_code": "USER003",
                "unique_channels": 25,  # Count distinct de dataName
                "total_hours": 320.8  # Redondeado a 2 decimales
            },
            ...
        ]
        # Nota: Top 10 usuarios ordenados por unique_channels descendente
    },
    "temporal_distribution": [
        {
            "date": "2025-01-01",  # str(dataDate), formato YYYY-MM-DD
            "active_users": 3500  # Count distinct de subscriberCode ese día
        },
        {
            "date": "2025-01-02",
            "active_users": 3800
        },
        ...
    ],
    # Nota: Solo incluye días con actividad (no todos los días del período)
    # Ordenado por fecha ascendente
    "engagement_metrics": {
        "retention_rate": 75.5,  # Porcentaje: (users_with_multiple_days / total_users) * 100 (redondeado a 2 decimales)
        "users_with_multiple_days": 3750,  # Usuarios con active_days > 1
        "potential_churn_users": 500,  # Solo se calcula si se proporciona end_date
        "days_in_period": 30  # Días totales del período (calculado según filtros)
    }
}
```

**Caso 2: Sin usuarios en el período**
```python
{
    "total_users": 0,
    "message": "No hay usuarios en el período seleccionado"
}
```

**Ejemplo de uso:**
```python
from datetime import datetime
from TelemetriaDelancer.panaccess.analytics_users_general import get_general_users_analysis

# Análisis de todos los usuarios
analysis = get_general_users_analysis()

# Análisis filtrado por fecha
start = datetime(2025, 1, 1)
end = datetime(2025, 1, 31)
analysis = get_general_users_analysis(start_date=start, end_date=end)

# Con segmentación personalizada
analysis = get_general_users_analysis(
    start_date=start,
    end_date=end,
    n_segments=7
)
```

---

## 📊 Estructura de la Respuesta

### `total_users`
- **Tipo:** int
- **Descripción:** Número total de usuarios únicos en el período
- **Utilidad:** Métrica principal para entender el tamaño de la base de usuarios

### `aggregate_stats`
Estadísticas agregadas de todos los usuarios (todos los valores redondeados a 2 decimales):
- **`avg_views_per_user`**: Promedio de visualizaciones por usuario (`total_views_all / total_users`)
- **`avg_hours_per_user`**: Promedio de horas vistas por usuario (`total_hours_all / total_users`)
  - Calculado desde `dataDuration` en segundos, convertido a horas dividiendo por 3600.0
- **`avg_channels_per_user`**: Promedio de canales únicos consumidos por usuario (`total_channels_all / total_users`)
- **`avg_devices_per_user`**: Promedio de dispositivos únicos por usuario (`total_devices_all / total_users`)
- **`avg_active_days_per_user`**: Promedio de días activos por usuario (`total_active_days_all / total_users`)
- **`total_views_all_users`**: Total de visualizaciones de todos los usuarios (int, suma de Count)
- **`total_hours_all_users`**: Total de horas vistas de todos los usuarios (float, redondeado a 2 decimales)

**Notas:**
- Todos los promedios se calculan sumando las métricas individuales de cada usuario y dividiendo por el total
- Si `total_users` es 0, todos los promedios serán 0

**Utilidad:** Permite comparar el comportamiento promedio de usuarios y entender el consumo total del sistema.

### `segmentation`
Distribución de usuarios por nivel de actividad (basado en `total_hours`):
- **`super_activo`**: Usuarios más activos
  - Con Pandas: percentil 80-100 (hours >= p80)
  - Sin Pandas: top 20% de usuarios ordenados por horas
- **`activo`**: Usuarios activos
  - Con Pandas: percentil 60-80 (hours >= p60 y < p80)
  - Sin Pandas: siguiente 20% de usuarios
- **`regular`**: Usuarios regulares
  - Con Pandas: percentil 40-60 (hours >= p40 y < p60)
  - Sin Pandas: siguiente 20% de usuarios
- **`ocasional`**: Usuarios ocasionales
  - Con Pandas: percentil 20-40 (hours >= p20 y < p40)
  - Sin Pandas: siguiente 20% de usuarios
- **`inactivo`**: Usuarios menos activos
  - Con Pandas: percentil 0-20 (hours < p20)
  - Sin Pandas: últimos usuarios restantes

**Notas:**
- Si Pandas está disponible: usa percentiles reales (p20, p40, p60, p80) calculados con `quantile()`
- Si Pandas NO está disponible: divide usuarios en `n_segments` grupos iguales ordenados por horas
- La segmentación se basa en `total_hours` de cada usuario
- Todos los segmentos siempre están presentes en el diccionario (incluso con valor 0)

**Utilidad:** Permite segmentar usuarios para estrategias de marketing, retención y personalización de contenido.

### `top_users`
Listas de top usuarios por diferentes métricas (máximo 10 usuarios por lista):
- **`by_hours`**: Top 10 usuarios por horas totales vistas
  - Ordenado por `total_hours` descendente
  - Incluye: `subscriber_code`, `total_hours` (redondeado a 2 decimales), `total_views`
- **`by_views`**: Top 10 usuarios por número de visualizaciones
  - Ordenado por `total_views` descendente
  - Incluye: `subscriber_code`, `total_views`, `total_hours` (redondeado a 2 decimales)
- **`by_channels`**: Top 10 usuarios por diversidad de canales
  - Ordenado por `unique_channels` descendente
  - Incluye: `subscriber_code`, `unique_channels`, `total_hours` (redondeado a 2 decimales)

**Notas:**
- Siempre retorna máximo 10 usuarios por cada métrica (limitado con `[:10]`)
- Puede tener menos de 10 si hay menos usuarios
- Los valores de horas se redondean a 2 decimales

**Utilidad:** Identificar usuarios VIP, influencers o casos de uso extremos para análisis.

### `temporal_distribution`
Distribución de usuarios activos por fecha:
- **`date`**: Fecha del período (str, formato YYYY-MM-DD, desde `dataDate`)
- **`active_users`**: Número de usuarios únicos activos ese día (Count distinct de `subscriberCode`)

**Notas:**
- Solo incluye días con actividad (no todos los días del período)
- Ordenado por fecha ascendente
- Se calcula usando agregación de Django ORM: `values('dataDate').annotate(unique_users=Count('subscriberCode', distinct=True))`

**Utilidad:** Visualizar tendencias de activación de usuarios a lo largo del tiempo.

### `engagement_metrics`
Métricas de engagement y retención:
- **`retention_rate`**: Porcentaje de usuarios con actividad en múltiples días
  - Calculado como: `(users_with_multiple_days / total_users) * 100`
  - Redondeado a 2 decimales
  - Si `total_users` es 0, retorna 0
- **`users_with_multiple_days`**: Número de usuarios que han estado activos en más de un día
  - Calculado como: usuarios con `active_days > 1`
- **`potential_churn_users`**: Usuarios inactivos (última actividad hace más de 30 días)
  - Solo se calcula si se proporciona `end_date`
  - Calculado como: usuarios con `timestamp < (end_date - 30 días)`
  - Usa el campo `timestamp` (no `dataDate`) para determinar última actividad
  - Si no se proporciona `end_date`, retorna 0
- **`days_in_period`**: Días totales del período analizado
  - Si se proporcionan `start_date` y `end_date`: `(end_date - start_date).days + 1`
  - Si no se proporcionan fechas: `(max_date - min_date).days + 1` (desde los datos)
  - Mínimo: 1 día

**Utilidad:** Medir la salud de la base de usuarios, identificar riesgo de churn y evaluar estrategias de retención.

---

## 🎨 Casos de Uso

### 1. Dashboard Ejecutivo
Mostrar métricas clave de usuarios:
- Total de usuarios activos
- Promedio de consumo por usuario
- Tasa de retención
- Distribución por segmentos

### 2. Estrategia de Segmentación
- Identificar usuarios por nivel de actividad
- Personalizar ofertas según segmento
- Diseñar campañas de retención para usuarios ocasionales/inactivos

### 3. Análisis de Usuarios VIP
- Identificar top usuarios por diferentes métricas
- Ofrecer beneficios especiales
- Analizar comportamiento de usuarios de alto valor

### 4. Monitoreo de Engagement
- Medir retención de usuarios
- Identificar usuarios en riesgo de churn
- Evaluar efectividad de estrategias de retención

### 5. Análisis Temporal
- Visualizar tendencias de activación de usuarios
- Identificar días con mayor/menor actividad
- Planificar campañas según patrones temporales

---

## 🔧 Endpoint API

**Ruta:** `POST /delancer/telemetry/users/analysis/general/`

**Parámetros (opcionales):**
```json
{
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "n_segments": 5
}
```

**Ejemplo de respuesta:**
```json
{
    "total_users": 5000,
    "aggregate_stats": {...},
    "segmentation": {...},
    "top_users": {...},
    "temporal_distribution": [...],
    "engagement_metrics": {...}
}
```

---

## 📈 Optimizaciones

- **Django ORM optimizado:** Usa agregaciones eficientes que aprovechan índices de base de datos
- **Pandas opcional:** Si está disponible, usa percentiles para segmentación más precisa
- **Filtros opcionales:** Permite análisis global o filtrado por fecha según necesidad
- **Top N limitado:** Limita resultados de top usuarios a 10 para mejor rendimiento

---

## ⚠️ Notas Importantes

1. **Segmentación con Pandas:** 
   - Si Pandas está instalado: usa percentiles reales (p20, p40, p60, p80) calculados con `quantile()`
   - Si Pandas NO está instalado: divide usuarios en `n_segments` grupos iguales ordenados por horas
   - La segmentación se basa en `total_hours` de cada usuario
   - Todos los segmentos siempre están presentes en el diccionario

2. **Churn Potencial:** 
   - Solo se calcula si se proporciona `end_date`
   - Se consideran usuarios inactivos aquellos con `timestamp < (end_date - 30 días)`
   - Usa el campo `timestamp` (no `dataDate`) para determinar última actividad
   - Si no se proporciona `end_date`, retorna 0

3. **Rendimiento:** 
   - Para bases de datos muy grandes, considera usar filtros de fecha para mejorar el rendimiento
   - La función carga todos los usuarios en memoria para procesamiento (convierte queryset a lista)
   - Para muchos usuarios, puede ser lento sin filtros de fecha

4. **Top Usuarios:** 
   - Siempre retorna máximo 10 usuarios por cada métrica (limitado con `[:10]`)
   - Puede tener menos de 10 si hay menos usuarios
   - Los valores de horas se redondean a 2 decimales

5. **Usuario sin datos:** 
   - Si no hay usuarios en el período, retorna:
     ```python
     {
         "total_users": 0,
         "message": "No hay usuarios en el período seleccionado"
     }
     ```

6. **Base de datos local:** Todos los análisis trabajan con datos de la base de datos local (`MergedTelemetricOTTDelancer`), NO consultan directamente a PanAccess

7. **Conversión de tiempo:** 
   - Todos los tiempos se almacenan en segundos en la BD (`dataDuration`)
   - Se convierten a horas dividiendo por 3600.0
   - Todos los valores de horas se redondean a 2 decimales

8. **Cálculo de estadísticas:** 
   - Las estadísticas agregadas se calculan sumando las métricas individuales de cada usuario
   - Los promedios se calculan dividiendo las sumas por el total de usuarios
   - Todos los promedios se redondean a 2 decimales

9. **Filtros aplicados:** 
   - Solo incluye usuarios donde `subscriberCode` no es `None`
   - Si se proporcionan fechas, filtra por `dataDate >= start_date.date()` y `dataDate <= end_date.date()`

10. **Distribución temporal:** 
    - Solo incluye días con actividad (no todos los días del período)
    - Ordenado por fecha ascendente
    - Se calcula usando agregación de Django ORM

