# Documentación de Estructura de Respuesta - Análisis de Telemetría OTT

## 📋 Propósito del Documento

Este documento explica en detalle la estructura de respuesta de los endpoints de análisis de telemetría OTT, describiendo cada objeto, parámetro, tipo de información y su utilidad para dashboards y presentaciones ejecutivas.

---

## 🎯 Endpoints Disponibles

### 1. **Análisis Generales** 
**Endpoint:** `POST /delancer/telemetry/analytics/`

Retorna todos los análisis generales en una sola respuesta. Ideal para dashboards que necesitan una visión completa del sistema.

### 2. **Análisis por Período**
**Endpoint:** `POST /delancer/telemetry/period-analysis/`

Retorna todos los análisis de un período específico (desde fecha X hasta fecha Y). Ideal para reportes comparativos y análisis de períodos específicos.

---

## 📊 Estructura de Respuesta - Análisis Generales

### Estructura Principal

```json
{
  "success": true,
  "generated_at": "2025-12-31T12:00:00",
  "filters": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-31"
  },
  "analyses": {
    "general_summary": {...},
    "top_channels": [...],
    "channel_audience": [...],
    "peak_hours": [...],
    "average_duration": [...],
    "temporal": [...],
    "geographic": [...],
    "time_slot_analysis": {...},
    "correlation": {...},
    "time_series": {...},
    "segmentation": {...},
    "channel_performance": [...]
  }
}
```

---

## 📈 Análisis Detallados

### 1. **general_summary** - Resumen General del Sistema

**¿Qué es?**
Resumen ejecutivo con las métricas principales del sistema completo.

**Estructura:**
```json
{
  "total_views": 500000,
  "active_users": 50000,
  "unique_devices": 45000,
  "unique_channels": 25,
  "total_watch_time_seconds": 4500000,
  "total_watch_time_hours": 1250.0
}
```

**Parámetros Explicados:**

| Parámetro                  | Tipo    | Descripción                                                     | Utilidad Dashboard                                                                                                          |
|----------------------------|---------|-----------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| `total_views`              | Integer | Total de visualizaciones/reproducciones en el período           | **KPI Principal**: Muestra el volumen total de consumo. Útil para mostrar en tarjetas grandes en el dashboard principal.    |
| `active_users`             | Integer | Número de usuarios/subscribers únicos que consumieron contenido | **Engagement**: Indica cuántos usuarios están activos. Comparar con total de suscriptores para calcular tasa de activación. |
| `unique_devices`           | Integer | Dispositivos únicos que consumieron contenido                   | **Penetración**: Muestra diversidad de dispositivos. Útil para entender si usuarios usan múltiples dispositivos.            |
| `unique_channels`          | Integer | Cantidad de canales diferentes consumidos                       | **Diversidad**: Indica variedad de contenido disponible y consumido.                                                        |
| `total_watch_time_seconds` | Float   | Tiempo total de visualización en segundos                       | **Métrica Técnica**: Para cálculos internos.                                                                                |
| `total_watch_time_hours`   | Float   | Tiempo total de visualización en horas                          | **KPI Clave**: Muestra horas totales consumidas. Útil para calcular promedio por usuario y comparar con objetivos.          |

**Utilidad para Junta Directiva:**
- **Dashboard Principal**: Mostrar estas métricas en tarjetas grandes (KPIs)
- **Tendencias**: Comparar con períodos anteriores para mostrar crecimiento
- **ROI**: Calcular valor por hora consumida vs. costo de contenido
- **Engagement**: `active_users / total_suscriptores` = tasa de activación

---

### 2. **top_channels** - Ranking de Canales Más Vistos

**¿Qué es?**
Lista ordenada de los N canales más populares con su participación porcentual.

**Estructura:**
```json
[
  {
    "channel": "Canal Premium",
    "total_views": 50000,
    "percentage": 25.5
  },
  {
    "channel": "Canal Deportes",
    "total_views": 35000,
    "percentage": 17.8
  }
]
```

**Parámetros Explicados:**

| Parámetro     | Tipo    | Descripción                                   | Utilidad Dashboard                                                                                 |
|---------------|---------|-----------------------------------------------|----------------------------------------------------------------------------------------------------|
| `channel`     | String  | Nombre del canal                              | **Etiqueta**: Identificación del canal en gráficos y tablas.                                       |
| `total_views` | Integer | Total de visualizaciones del canal            | **Volumen**: Muestra popularidad absoluta. Útil para gráficos de barras horizontales.              |
| `percentage`  | Float   | Porcentaje de participación respecto al total | **Proporción**: Muestra cuota de mercado del canal. Útil para gráficos de torta o barras apiladas. |

**Utilidad para Junta Directiva:**
- **Gráfico de Barras**: Top 10 canales ordenados por `total_views`
- **Gráfico de Torta**: Distribución porcentual usando `percentage`
- **Estrategia de Contenido**: Identificar canales estrella para negociaciones
- **Inversión**: Enfocar recursos en canales con mayor `percentage`

---

### 3. **channel_audience** - Análisis de Audiencia por Canal

**¿Qué es?**
Análisis detallado de cada canal mostrando audiencia (usuarios y dispositivos únicos) y tiempo total consumido.

**Estructura:**
```json
[
  {
    "dataName": "Canal Premium",
    "unique_devices": 4500,
    "unique_users": 5000,
    "total_views": 50000,
    "total_watch_time": 125000.5,
    "total_hours": 34.72
  }
]
```

**Parámetros Explicados:**

| Parámetro          | Tipo    | Descripción                                            | Utilidad Dashboard                                                                                             |
|--------------------|---------|--------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| `dataName`         | String  | Nombre del canal                                       | **Identificación**: Nombre del canal para tablas y gráficos.                                                   |
| `unique_devices`   | Integer | Dispositivos únicos que consumieron este canal         | **Alcance**: Muestra penetración del canal. Útil para entender diversidad de dispositivos por canal.           |
| `unique_users`     | Integer | Usuarios/subscribers únicos que consumieron este canal | **Audiencia Real**: Muestra cuántos usuarios únicos tiene cada canal. Útil para calcular engagement por canal. |
| `total_views`      | Integer | Total de visualizaciones del canal                     | **Volumen**: Muestra actividad total del canal.                                                                |
| `total_watch_time` | Float   | Tiempo total consumido en segundos                     | **Métrica Técnica**: Para cálculos internos.                                                                   |
| `total_hours`      | Float   | Tiempo total consumido en horas                        | **Consumo**: Muestra horas totales por canal. Útil para calcular promedio de horas por usuario.                |

**Utilidad para Junta Directiva:**
- **Tabla Comparativa**: Mostrar todos los canales con estas métricas
- **Gráfico de Dispersión**: `unique_users` vs `total_hours` para identificar canales con alto engagement
- **Análisis de Valor**: `total_hours / unique_users` = horas promedio por usuario (métrica de calidad)
- **Estrategia**: Canales con muchos `unique_users` pero pocas `total_hours` = oportunidad de mejora

---

### 4. **peak_hours** - Horarios Pico por Canal

**¿Qué es?**
Identifica las horas del día con mayor consumo para cada canal.

**Estructura:**
```json
[
  {
    "dataName": "Canal Premium",
    "timeDate": 20,
    "views": 5000
  },
  {
    "dataName": "Canal Premium",
    "timeDate": 21,
    "views": 4500
  }
]
```

**Parámetros Explicados:**

| Parámetro  | Tipo    | Descripción                 | Utilidad Dashboard                                                |
|------------|---------|-----------------------------|-------------------------------------------------------------------|
| `dataName` | String  | Nombre del canal            | **Filtro**: Permite agrupar por canal.                            |
| `timeDate` | Integer | Hora del día (0-23)         | **Eje X**: Hora del día. Útil para gráficos de líneas temporales. |
| `views`    | Integer | Visualizaciones en esa hora | **Eje Y**: Volumen de consumo. Útil para identificar picos.       |

**Utilidad para Junta Directiva:**
- **Gráfico de Líneas**: Mostrar consumo por hora del día (0-23)
- **Heatmap**: Hora vs Canal para identificar patrones
- **Programación**: Optimizar horarios de estrenos y contenido premium
- **Recursos**: Asignar ancho de banda/CDN según demanda horaria

---

### 5. **average_duration** - Duración Promedio por Canal

**¿Qué es?**
Tiempo promedio de visualización por canal, indicando retención de audiencia.

**Estructura:**
```json
[
  {
    "dataName": "Canal Premium",
    "avg_duration": 45.2,
    "total_views": 50000,
    "total_watch_time": 2260000.0
  }
]
```

**Parámetros Explicados:**

| Parámetro | Tipo | Descripción | Utilidad Dashboard |
|-----------|------|-------------|-------------------|
| `dataName` | String | Nombre del canal | **Identificación**: Nombre del canal. |
| `avg_duration` | Float | Duración promedio en segundos | **Retención**: Muestra cuánto tiempo promedio ve el usuario. Mayor = mejor retención. |
| `total_views` | Integer | Total de visualizaciones | **Contexto**: Para calcular porcentajes y ratios. |
| `total_watch_time` | Float | Tiempo total consumido en segundos | **Volumen Total**: Para cálculos adicionales. |

**Utilidad para Junta Directiva:**
- **Gráfico de Barras**: Canales ordenados por `avg_duration`
- **Métrica de Calidad**: Mayor `avg_duration` = mejor contenido/engagement
- **Comparación**: Comparar con duración promedio del contenido para ver si usuarios ven completo
- **Estrategia**: Canales con baja `avg_duration` = oportunidad de mejora en contenido

---

### 6. **temporal** - Análisis Temporal

**¿Qué es?**
Evolución del consumo a lo largo del tiempo (diario, semanal o mensual).

**Estructura:**
```json
[
  {
    "period": "2025-01-01",
    "views": 5000
  },
  {
    "period": "2025-01-02",
    "views": 5200
  }
]
```

**Parámetros Explicados:**

| Parámetro | Tipo | Descripción | Utilidad Dashboard |
|-----------|------|-------------|-------------------|
| `period` | String/Date | Período de tiempo (día, semana o mes) | **Eje X**: Fecha/período. Útil para gráficos de líneas temporales. |
| `views` | Integer | Visualizaciones en ese período | **Eje Y**: Volumen de consumo. Muestra tendencias y patrones. |

**Utilidad para Junta Directiva:**
- **Gráfico de Líneas Temporales**: Mostrar evolución del consumo
- **Tendencias**: Identificar crecimiento, estacionalidad, días especiales
- **Forecasting**: Base para predicciones futuras
- **Comparación**: Comparar con períodos anteriores (año anterior, mes anterior)

---

### 7. **geographic** - Análisis Geográfico

**¿Qué es?**
Distribución del consumo por país e ISP (proveedor de internet).

**Estructura:**
```json
[
  {
    "whoisCountry": "CO",
    "whoisIsp": "ISP Principal",
    "total_views": 250000,
    "unique_devices": 25000,
    "unique_users": 30000
  }
]
```

**Parámetros Explicados:**

| Parámetro | Tipo | Descripción | Utilidad Dashboard |
|-----------|------|-------------|-------------------|
| `whoisCountry` | String | Código de país (ISO) | **Geografía**: País de origen del consumo. Útil para mapas y gráficos geográficos. |
| `whoisIsp` | String | Proveedor de internet | **Infraestructura**: ISP del usuario. Útil para identificar problemas de conectividad por ISP. |
| `total_views` | Integer | Visualizaciones desde ese país/ISP | **Volumen**: Muestra distribución geográfica del consumo. |
| `unique_devices` | Integer | Dispositivos únicos | **Alcance**: Penetración por región. |
| `unique_users` | Integer | Usuarios únicos | **Audiencia**: Base de usuarios por región. |

**Utilidad para Junta Directiva:**
- **Mapa de Calor Geográfico**: Mostrar consumo por país
- **Expansión**: Identificar mercados con potencial de crecimiento
- **Infraestructura**: Optimizar CDN y servidores según distribución geográfica
- **Localización**: Identificar necesidad de contenido localizado

---

### 8. **time_slot_analysis** - Análisis por Franjas Horarias

**¿Qué es?**
Distribución del consumo en 4 franjas horarias del día.

**Estructura:**
```json
{
  "time_slots": {
    "madrugada": {
      "total_seconds": 180000,
      "total_hours": 50.0,
      "total_views": 1000
    },
    "mañana": {
      "total_seconds": 720000,
      "total_hours": 200.0,
      "total_views": 5000
    },
    "tarde": {
      "total_seconds": 1260000,
      "total_hours": 350.0,
      "total_views": 8000
    },
    "noche": {
      "total_seconds": 2340000,
      "total_hours": 650.0,
      "total_views": 12000
    }
  },
  "summary": {
    "total_hours": 1250.0,
    "total_views": 26000
  }
}
```

**Parámetros Explicados:**

| Parámetro | Tipo | Descripción | Utilidad Dashboard |
|-----------|------|-------------|-------------------|
| `time_slots` | Object | Objeto con 4 franjas horarias | **Estructura**: Contiene datos de cada franja. |
| `madrugada` | Object | Consumo de 00:00 a 05:59 | **Franja 1**: Horas de menor consumo típico. |
| `mañana` | Object | Consumo de 06:00 a 11:59 | **Franja 2**: Horas de consumo moderado. |
| `tarde` | Object | Consumo de 12:00 a 17:59 | **Franja 3**: Horas de consumo alto. |
| `noche` | Object | Consumo de 18:00 a 23:59 | **Franja 4**: Horas de mayor consumo típico. |
| `total_seconds` | Float | Tiempo total en segundos | **Métrica Técnica**: Para cálculos. |
| `total_hours` | Float | Tiempo total en horas | **KPI**: Horas consumidas en esa franja. Útil para gráficos de barras comparativas. |
| `total_views` | Integer | Visualizaciones en esa franja | **Volumen**: Cantidad de reproducciones. |
| `summary.total_hours` | Float | Total de horas de todas las franjas | **Resumen**: Total general para validación. |
| `summary.total_views` | Integer | Total de visualizaciones | **Resumen**: Total general para validación. |

**Utilidad para Junta Directiva:**
- **Gráfico de Barras**: Comparar las 4 franjas horarias
- **Gráfico de Torta**: Distribución porcentual por franja
- **Programación**: Optimizar horarios de estrenos según franja con mayor consumo
- **Recursos**: Asignar capacidad de servidor según demanda por franja
- **Marketing**: Enfocar campañas publicitarias en franjas de mayor consumo

---

### 9. **correlation** - Análisis de Correlaciones

**¿Qué es?**
Identifica relaciones estadísticas entre diferentes variables (duración, frecuencia, canales, etc.).

**Estructura:**
```json
{
  "correlation_matrix": {
    "total_watch_time": {
      "total_watch_time": 1.0,
      "avg_duration": 0.85,
      "total_views": 0.92,
      "unique_channels": 0.78
    }
  },
  "descriptive_stats": {...},
  "insights": {
    "strongest_correlation": {
      "variable1": "total_watch_time",
      "variable2": "total_views",
      "correlation": 0.92,
      "strength": "fuerte"
    }
  }
}
```

**Parámetros Explicados:**

| Parámetro | Tipo | Descripción | Utilidad Dashboard |
|-----------|------|-------------|-------------------|
| `correlation_matrix` | Object | Matriz de correlaciones entre variables | **Análisis Avanzado**: Muestra qué variables están relacionadas. Valores entre -1 y 1. |
| `descriptive_stats` | Object | Estadísticas descriptivas (media, desviación, etc.) | **Contexto**: Estadísticas básicas de las variables. |
| `strongest_correlation` | Object | Correlación más fuerte encontrada | **Insight Clave**: Relación más importante. Útil para identificar drivers de consumo. |
| `correlation` | Float | Valor de correlación (-1 a 1) | **Fuerza**: 0.7+ = fuerte, 0.4-0.7 = moderada, <0.4 = débil. |
| `strength` | String | "fuerte", "moderada", "débil" | **Interpretación**: Descripción fácil de entender. |

**Utilidad para Junta Directiva:**
- **Heatmap de Correlaciones**: Visualizar matriz de correlaciones
- **Insights Estratégicos**: Identificar qué factores impulsan el consumo
- **Optimización**: Enfocar esfuerzos en variables con alta correlación positiva
- **Predicción**: Usar correlaciones fuertes para predecir comportamiento

---

### 10. **time_series** - Análisis de Series Temporales

**¿Qué es?**
Análisis de tendencias temporales con pronóstico futuro usando regresión lineal.

**Estructura:**
```json
{
  "historical_data": [
    {
      "dataDate": "2025-01-01",
      "views": 5000,
      "moving_avg_7d": 4800,
      "trend": 4950
    }
  ],
  "forecast": [
    {
      "dataDate": "2025-02-01",
      "forecast": 5500,
      "moving_avg_forecast": 5200
    }
  ],
  "statistics": {
    "mean": 5000.5,
    "std": 320.2,
    "trend_slope": 15.3,
    "trend_direction": "creciente"
  }
}
```

**Parámetros Explicados:**

| Parámetro | Tipo | Descripción | Utilidad Dashboard |
|-----------|------|-------------|-------------------|
| `historical_data` | Array | Datos históricos día por día | **Línea Base**: Datos reales para comparar con pronóstico. |
| `dataDate` | String | Fecha del registro | **Eje X**: Fecha en gráficos temporales. |
| `views` | Integer | Visualizaciones reales | **Datos Reales**: Para comparar con pronóstico. |
| `moving_avg_7d` | Float | Media móvil de 7 días | **Suavizado**: Elimina ruido y muestra tendencia suave. Útil para líneas de tendencia. |
| `trend` | Float | Línea de tendencia calculada | **Tendencia**: Muestra dirección general (creciente/decreciente). |
| `forecast` | Array | Pronóstico para días futuros | **Predicción**: Valores proyectados. Útil para planificación. |
| `trend_slope` | Float | Pendiente de la tendencia | **Velocidad**: Muestra qué tan rápido crece/decrece. |
| `trend_direction` | String | "creciente", "decreciente", "estable" | **Interpretación**: Dirección fácil de entender. |

**Utilidad para Junta Directiva:**
- **Gráfico de Líneas con Pronóstico**: Mostrar datos históricos + pronóstico futuro
- **Planificación**: Usar pronóstico para planificar recursos y contenido
- **Alertas**: Si tendencia es decreciente, activar estrategias de retención
- **Objetivos**: Comparar pronóstico con objetivos para ajustar estrategias

---

### 11. **segmentation** - Segmentación de Usuarios

**¿Qué es?**
Agrupa usuarios en segmentos basados en comportamiento (frecuencia, duración, diversidad).

**Estructura:**
```json
{
  "segments": [
    {
      "segment_id": 0,
      "segment_name": "Usuarios Ocasionales",
      "user_count": 450,
      "percentage": 30.0,
      "avg_metrics": {
        "total_watch_time": 1200.5,
        "avg_duration": 45.2,
        "unique_channels": 3.1,
        "total_views": 8.5
      }
    }
  ],
  "total_users": 1500
}
```

**Parámetros Explicados:**

| Parámetro | Tipo | Descripción | Utilidad Dashboard |
|-----------|------|-------------|-------------------|
| `segments` | Array | Lista de segmentos identificados | **Segmentación**: Grupos de usuarios con comportamiento similar. |
| `segment_id` | Integer | ID numérico del segmento | **Identificación**: Para referencias técnicas. |
| `segment_name` | String | Nombre descriptivo del segmento | **Etiqueta**: "Ocasionales", "Regulares", "Activos", "Super Activos". |
| `user_count` | Integer | Cantidad de usuarios en el segmento | **Tamaño**: Muestra cuántos usuarios hay en cada segmento. |
| `percentage` | Float | Porcentaje del total | **Proporción**: Muestra distribución de usuarios. Útil para gráficos de torta. |
| `avg_metrics` | Object | Métricas promedio del segmento | **Características**: Describe comportamiento típico del segmento. |
| `total_watch_time` | Float | Tiempo promedio consumido | **Engagement**: Muestra nivel de engagement del segmento. |
| `avg_duration` | Float | Duración promedio por sesión | **Calidad**: Muestra retención promedio. |
| `unique_channels` | Float | Canales únicos promedio | **Diversidad**: Muestra variedad de consumo. |
| `total_views` | Float | Visualizaciones promedio | **Frecuencia**: Muestra actividad promedio. |

**Utilidad para Junta Directiva:**
- **Gráfico de Torta**: Distribución de usuarios por segmento
- **Tabla Comparativa**: Comparar métricas entre segmentos
- **Estrategias Personalizadas**: Crear estrategias específicas para cada segmento
- **Conversión**: Identificar cómo convertir "Ocasionales" a "Activos"
- **Retención**: Enfocar esfuerzos en segmentos de alto valor

---

### 12. **channel_performance** - Matriz de Rendimiento de Canales

**¿Qué es?**
Matriz que combina múltiples métricas para crear un score de rendimiento de cada canal.

**Estructura:**
```json
{
  "performance_matrix": [
    {
      "channel": "Canal Premium",
      "total_views": 50000,
      "unique_users": 5000,
      "unique_devices": 4500,
      "total_watch_time": 25000.5,
      "avg_duration": 50.2,
      "active_days": 30,
      "percentage": 20.0,
      "views_per_user": 10.0,
      "watch_time_per_user": 5.0,
      "performance_score": 95.5,
      "rank": 1
    }
  ],
  "summary": {
    "total_channels": 25,
    "top_channel": "Canal Premium",
    "avg_performance_score": 65.3
  }
}
```

**Parámetros Explicados:**

| Parámetro | Tipo | Descripción | Utilidad Dashboard |
|-----------|------|-------------|-------------------|
| `performance_matrix` | Array | Lista de canales con score de rendimiento | **Ranking Completo**: Canales ordenados por rendimiento. |
| `performance_score` | Float | Score normalizado (0-100) | **KPI Principal**: Métrica única que combina todas las demás. Mayor = mejor rendimiento. |
| `rank` | Integer | Posición en el ranking | **Ordenamiento**: 1 = mejor canal, 2 = segundo mejor, etc. |
| `views_per_user` | Float | Visualizaciones promedio por usuario | **Engagement**: Muestra frecuencia de consumo. |
| `watch_time_per_user` | Float | Horas promedio por usuario | **Valor**: Muestra valor del canal por usuario. |
| `active_days` | Integer | Días con actividad en el período | **Consistencia**: Muestra si el canal tiene consumo constante. |
| `summary.avg_performance_score` | Float | Score promedio de todos los canales | **Benchmark**: Punto de referencia para comparar canales individuales. |

**Utilidad para Junta Directiva:**
- **Tabla de Ranking**: Mostrar canales ordenados por `performance_score`
- **Gráfico de Barras**: Visualizar scores de rendimiento
- **Decisiones de Contenido**: Priorizar inversión en canales con alto `performance_score`
- **Benchmarking**: Comparar canales contra el promedio
- **Optimización**: Identificar canales con bajo score para mejorar

---

## 📅 Estructura de Respuesta - Análisis por Período

### Estructura Principal

```json
{
  "success": true,
  "generated_at": "2025-12-31T12:00:00",
  "period": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-07",
    "days": 7
  },
  "analyses": {
    "summary": {...},
    "comparison": {...},
    "temporal_breakdown": {...},
    "channels": {...},
    "users": {...},
    "events": {...},
    "trend": {...}
  }
}
```

---

## 📊 Análisis por Período Detallados

### 1. **summary** - Resumen del Período

**¿Qué es?**
Resumen ejecutivo del período específico seleccionado.

**Estructura:**
```json
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
    "max_duration": 120.5,
    "min_duration": 5.0,
    "avg_views_per_day": 7142.86
  },
  "top_channels": [...],
  "daily_distribution": [...]
}
```

**Parámetros Explicados:**

| Parámetro | Tipo | Descripción | Utilidad Dashboard |
|-----------|------|-------------|-------------------|
| `period.days` | Integer | Días del período analizado | **Contexto**: Para calcular promedios diarios. |
| `avg_views_per_day` | Float | Promedio de visualizaciones por día | **Normalización**: Permite comparar períodos de diferente duración. |
| `max_duration` | Float | Duración máxima de una sesión | **Límites**: Muestra el extremo superior. |
| `min_duration` | Float | Duración mínima de una sesión | **Límites**: Muestra el extremo inferior. |
| `daily_distribution` | Array | Distribución día por día | **Detalle**: Muestra variación diaria dentro del período. |

**Utilidad para Junta Directiva:**
- **Dashboard de Período**: Mostrar métricas principales del período seleccionado
- **Comparación**: Base para comparar con otros períodos
- **Normalización**: `avg_views_per_day` permite comparar semanas vs meses

---

### 2. **comparison** - Comparación con Período Anterior

**¿Qué es?**
Compara el período seleccionado con el período anterior equivalente (misma duración).

**Estructura:**
```json
{
  "current_period": {...},
  "previous_period": {...},
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
      "users": {
        "absolute": 500,
        "percentage": 11.1,
        "trend": "aumento"
      },
      "watch_time": {
        "absolute": 12500.5,
        "percentage": 11.1,
        "trend": "aumento"
      }
    }
  }
}
```

**Parámetros Explicados:**

| Parámetro | Tipo | Descripción | Utilidad Dashboard |
|-----------|------|-------------|-------------------|
| `current_period` | Object | Resumen del período actual | **Base**: Datos del período que se está analizando. |
| `previous_period` | Object | Resumen del período anterior | **Comparación**: Datos del período anterior equivalente. |
| `changes.absolute` | Integer/Float | Cambio absoluto (actual - anterior) | **Magnitud**: Muestra el cambio en números absolutos. |
| `changes.percentage` | Float | Cambio porcentual | **Proporción**: Muestra el cambio relativo. Más útil que absoluto. |
| `changes.trend` | String | "aumento", "disminución", "estable" | **Interpretación**: Descripción fácil de entender. Útil para indicadores visuales (verde/rojo). |

**Utilidad para Junta Directiva:**
- **Indicadores de Tendencia**: Mostrar flechas verdes/rojas según `trend`
- **Gráficos Comparativos**: Lado a lado período actual vs anterior
- **KPIs con Variación**: Mostrar métrica actual + porcentaje de cambio
- **Alertas**: Si `trend` es "disminución" significativa, activar análisis

---

### 3. **temporal_breakdown** - Desglose Temporal del Período

**¿Qué es?**
Análisis día por día, semana por semana o mes por mes dentro del período seleccionado.

**Estructura:**
```json
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
      "unique_devices": 450,
      "total_watch_time": 12500.5,
      "avg_duration": 45.2
    }
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

**Parámetros Explicados:**

| Parámetro | Tipo | Descripción | Utilidad Dashboard |
|-----------|------|-------------|-------------------|
| `temporal_data` | Array | Datos por período (día/semana/mes) | **Detalle**: Muestra evolución dentro del período. |
| `statistics.views.mean` | Float | Promedio de visualizaciones | **Línea Base**: Valor promedio para comparar días individuales. |
| `statistics.views.std` | Float | Desviación estándar | **Variabilidad**: Muestra qué tan variables son los días. Baja = consistente, Alta = variable. |
| `statistics.views.trend` | String | "creciente", "decreciente", "estable" | **Dirección**: Tendencia general dentro del período. |

**Utilidad para Junta Directiva:**
- **Gráfico de Líneas**: Mostrar evolución día por día
- **Análisis de Variabilidad**: Días con valores muy por encima/debajo del promedio
- **Tendencias Internas**: Identificar si el período muestra crecimiento o declive
- **Eventos**: Días con picos pueden indicar eventos especiales

---

### 4. **channels** - Análisis de Canales del Período

**¿Qué es?**
Análisis detallado de canales específicamente en el período seleccionado.

**Estructura:**
```json
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
    }
  ]
}
```

**Parámetros Explicados:**

| Parámetro | Tipo | Descripción | Utilidad Dashboard |
|-----------|------|-------------|-------------------|
| `total_channels` | Integer | Cantidad total de canales | **Contexto**: Muestra diversidad de oferta. |
| `total_period_views` | Integer | Total de visualizaciones del período | **Base**: Para calcular porcentajes. |
| `active_days` | Integer | Días con actividad en el período | **Consistencia**: Muestra si el canal tuvo consumo todos los días. |
| `views_per_user` | Float | Visualizaciones promedio por usuario | **Engagement**: Muestra frecuencia de consumo del canal. |
| `watch_time_per_user` | Float | Horas promedio por usuario | **Valor**: Muestra valor del canal por usuario. |

**Utilidad para Junta Directiva:**
- **Tabla de Canales del Período**: Mostrar rendimiento de canales en el período específico
- **Comparación Período vs General**: Comparar con análisis general para ver cambios
- **Estrategia Temporal**: Identificar canales que mejoran/empeoran en períodos específicos

---

### 5. **users** - Análisis de Usuarios del Período

**¿Qué es?**
Análisis de comportamiento de usuarios específicamente en el período seleccionado.

**Estructura:**
```json
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
    }
  ]
}
```

**Parámetros Explicados:**

| Parámetro | Tipo | Descripción | Utilidad Dashboard |
|-----------|------|-------------|-------------------|
| `total_users` | Integer | Total de usuarios únicos en el período | **Base**: Cantidad total de usuarios activos. |
| `top_users` | Array | Usuarios más activos | **Power Users**: Identificar usuarios de alto valor. |
| `activity_rate` | Float | Porcentaje de días activos (0-100) | **Consistencia**: 100% = activo todos los días, 50% = activo la mitad. |
| `avg_views_per_day` | Float | Visualizaciones promedio por día activo | **Intensidad**: Muestra nivel de consumo cuando el usuario está activo. |

**Utilidad para Junta Directiva:**
- **Identificar Power Users**: Usuarios con alta `activity_rate` y `total_views`
- **Programas de Fidelización**: Enfocar en usuarios con alto `activity_rate`
- **Análisis de Churn**: Usuarios con baja `activity_rate` = riesgo de abandono

---

### 6. **events** - Detección de Eventos y Picos

**¿Qué es?**
Identifica días con consumo anormalmente alto o bajo dentro del período.

**Estructura:**
```json
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

**Parámetros Explicados:**

| Parámetro | Tipo | Descripción | Utilidad Dashboard |
|-----------|------|-------------|-------------------|
| `peaks` | Array | Días con consumo anormalmente alto | **Eventos Positivos**: Días excepcionales. Identificar qué causó el pico. |
| `valleys` | Array | Días con consumo anormalmente bajo | **Problemas**: Días con bajo consumo. Investigar causas (fallos técnicos, eventos externos). |
| `z_score` | Float | Desviaciones estándar del promedio | **Significancia**: Mayor z_score = más anómalo. >3 = muy significativo. |
| `threshold_std` | Float | Umbral para considerar evento (default: 2.0) | **Configuración**: Ajustable según necesidad de sensibilidad. |

**Utilidad para Junta Directiva:**
- **Alertas Automáticas**: Notificar cuando hay picos o valles significativos
- **Análisis de Eventos**: Correlacionar picos con campañas, estrenos, eventos
- **Detección de Problemas**: Valles pueden indicar fallos técnicos o problemas
- **Optimización**: Entender qué causa picos para replicar éxito

---

### 7. **trend** - Análisis de Tendencia del Período

**¿Qué es?**
Analiza si el consumo está creciendo, decreciendo o estable dentro del período usando regresión lineal.

**Estructura:**
```json
{
  "period": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-07",
    "days": 7
  },
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

**Parámetros Explicados:**

| Parámetro | Tipo | Descripción | Utilidad Dashboard |
|-----------|------|-------------|-------------------|
| `trend.direction` | String | "creciente", "decreciente", "estable" | **Interpretación Simple**: Fácil de entender para ejecutivos. |
| `trend.strength` | String | "fuerte", "moderada", "débil" | **Intensidad**: Muestra qué tan pronunciada es la tendencia. |
| `trend.slope` | Float | Pendiente de la línea de tendencia | **Velocidad**: Muestra cuánto crece/decrece por día. |
| `trend.r_squared` | Float | Coeficiente de determinación (0-1) | **Confiabilidad**: >0.7 = tendencia confiable, <0.5 = poco confiable. |
| `change.percentage_change` | Float | Cambio porcentual del primero al último día | **Crecimiento**: Muestra crecimiento total del período. |

**Utilidad para Junta Directiva:**
- **Indicador de Tendencia**: Mostrar flecha verde/roja según dirección
- **Velocidad de Crecimiento**: `slope` muestra velocidad de cambio
- **Confianza**: `r_squared` alto = tendencia confiable para decisiones
- **Proyección**: Si tendencia es creciente, proyectar crecimiento futuro

---

## 🎯 Resumen de Utilidad por Tipo de Dashboard

### Dashboard Ejecutivo (Alta Gerencia)
**Métricas Clave:**
- `general_summary`: KPIs principales
- `top_channels`: Canales estrella
- `time_slot_analysis`: Patrones de consumo
- `comparison`: Crecimiento vs período anterior
- `trend`: Dirección del negocio

**Visualizaciones Recomendadas:**
- Tarjetas grandes con KPIs
- Gráfico de líneas con tendencia
- Gráfico de torta de canales
- Indicadores de crecimiento (verde/rojo)

---

### Dashboard Operativo (Equipo Técnico)
**Métricas Clave:**
- `channel_audience`: Detalle técnico por canal
- `geographic`: Distribución geográfica
- `events`: Detección de anomalías
- `peak_hours`: Optimización de recursos
- `temporal_breakdown`: Análisis detallado

**Visualizaciones Recomendadas:**
- Tablas detalladas
- Mapas geográficos
- Gráficos de series temporales
- Alertas de eventos

---

### Dashboard de Marketing
**Métricas Clave:**
- `segmentation`: Segmentos de usuarios
- `channel_performance`: Rendimiento de canales
- `correlation`: Factores que impulsan consumo
- `time_series`: Pronósticos
- `users`: Comportamiento de usuarios

**Visualizaciones Recomendadas:**
- Gráficos de segmentación
- Heatmaps de correlaciones
- Gráficos de pronóstico
- Análisis de cohortes

---

## 📝 Notas para Presentación a Junta Directiva

### Puntos Clave a Destacar:

1. **KPIs Principales** (`general_summary`):
   - Total de horas vistas = métrica de valor
   - Usuarios activos = métrica de engagement
   - Comparar con objetivos y períodos anteriores

2. **Tendencias** (`trend`, `comparison`):
   - Mostrar crecimiento/decrecimiento
   - Explicar factores que influyen
   - Proyecciones futuras

3. **Canales Estrella** (`top_channels`, `channel_performance`):
   - Identificar canales de mayor valor
   - Justificar inversión en contenido
   - Oportunidades de crecimiento

4. **Optimización** (`time_slot_analysis`, `peak_hours`):
   - Mostrar eficiencia operativa
   - Optimización de recursos
   - Mejoras implementadas

5. **Insights Accionables** (`correlation`, `segmentation`):
   - Factores que impulsan consumo
   - Segmentos de usuarios
   - Estrategias personalizadas

---

**Documento creado:** 2025-12-31  
**Última actualización:** 2025-12-31  
**Versión:** 1.0

