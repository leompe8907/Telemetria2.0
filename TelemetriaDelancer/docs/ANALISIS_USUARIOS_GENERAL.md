# Análisis General de Usuarios/Subscribers

## 👥 Descripción

Este módulo (`analytics_users_general.py`) proporciona un análisis agregado de todos los usuarios/subscribers del sistema. Permite obtener una visión general del comportamiento de la base de usuarios, incluyendo segmentación, estadísticas agregadas, top usuarios y métricas de engagement.

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
```python
{
    "total_users": 5000,
    "aggregate_stats": {
        "avg_views_per_user": 125.5,
        "avg_hours_per_user": 45.2,
        "avg_channels_per_user": 8.3,
        "avg_devices_per_user": 1.8,
        "avg_active_days_per_user": 12.5,
        "total_views_all_users": 627500,
        "total_hours_all_users": 226000.0
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
                "subscriber_code": "USER001",
                "total_hours": 450.5,
                "total_views": 2500
            },
            ...
        ],
        "by_views": [
            {
                "subscriber_code": "USER002",
                "total_views": 3000,
                "total_hours": 380.2
            },
            ...
        ],
        "by_channels": [
            {
                "subscriber_code": "USER003",
                "unique_channels": 25,
                "total_hours": 320.8
            },
            ...
        ]
    },
    "temporal_distribution": [
        {
            "date": "2025-01-01",
            "active_users": 3500
        },
        {
            "date": "2025-01-02",
            "active_users": 3800
        },
        ...
    ],
    "engagement_metrics": {
        "retention_rate": 75.5,
        "users_with_multiple_days": 3750,
        "potential_churn_users": 500,
        "days_in_period": 30
    }
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
Estadísticas agregadas de todos los usuarios:
- **`avg_views_per_user`**: Promedio de visualizaciones por usuario
- **`avg_hours_per_user`**: Promedio de horas vistas por usuario
- **`avg_channels_per_user`**: Promedio de canales únicos consumidos por usuario
- **`avg_devices_per_user`**: Promedio de dispositivos únicos por usuario
- **`avg_active_days_per_user`**: Promedio de días activos por usuario
- **`total_views_all_users`**: Total de visualizaciones de todos los usuarios
- **`total_hours_all_users`**: Total de horas vistas de todos los usuarios

**Utilidad:** Permite comparar el comportamiento promedio de usuarios y entender el consumo total del sistema.

### `segmentation`
Distribución de usuarios por nivel de actividad:
- **`super_activo`**: Usuarios en el percentil 80-100 (más activos)
- **`activo`**: Usuarios en el percentil 60-80
- **`regular`**: Usuarios en el percentil 40-60
- **`ocasional`**: Usuarios en el percentil 20-40
- **`inactivo`**: Usuarios en el percentil 0-20 (menos activos)

**Utilidad:** Permite segmentar usuarios para estrategias de marketing, retención y personalización de contenido.

### `top_users`
Listas de top usuarios por diferentes métricas:
- **`by_hours`**: Top 10 usuarios por horas totales vistas
- **`by_views`**: Top 10 usuarios por número de visualizaciones
- **`by_channels`**: Top 10 usuarios por diversidad de canales

**Utilidad:** Identificar usuarios VIP, influencers o casos de uso extremos para análisis.

### `temporal_distribution`
Distribución de usuarios activos por fecha:
- **`date`**: Fecha del período
- **`active_users`**: Número de usuarios únicos activos ese día

**Utilidad:** Visualizar tendencias de activación de usuarios a lo largo del tiempo.

### `engagement_metrics`
Métricas de engagement y retención:
- **`retention_rate`**: Porcentaje de usuarios con actividad en múltiples días
- **`users_with_multiple_days`**: Número de usuarios que han estado activos en más de un día
- **`potential_churn_users`**: Usuarios inactivos (última actividad hace más de 30 días)
- **`days_in_period`**: Días totales del período analizado

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

1. **Segmentación con Pandas:** Si Pandas está instalado, la segmentación usa percentiles reales. Si no, usa división simple por segmentos.

2. **Churn Potencial:** Solo se calcula si se proporciona `end_date`. Se consideran usuarios inactivos aquellos con última actividad hace más de 30 días.

3. **Rendimiento:** Para bases de datos muy grandes, considera usar filtros de fecha para mejorar el rendimiento.

4. **Top Usuarios:** Siempre retorna máximo 10 usuarios por cada métrica para mantener el rendimiento.

