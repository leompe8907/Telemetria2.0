# Guía de Gráficas para Análisis de Telemetría OTT

Este documento lista todos los análisis disponibles y las gráficas recomendadas para visualizar cada uno.

---

## 📊 ANÁLISIS GENERALES

### 1. **`get_top_channels`** ✅ GRAFICABLE

**Datos:** Lista de canales con `total_views` y `percentage`

**Gráficas recomendadas:**
- **Gráfica de barras horizontal** (Top 10 canales por visualizaciones)
- **Gráfica de pastel** (Distribución porcentual de visualizaciones)
- **Gráfica de barras vertical** (Comparación de visualizaciones)

**Ejemplo de datos:**
```json
[
  {"channel": "Canal A", "total_views": 5000, "percentage": 25.5},
  {"channel": "Canal B", "total_views": 4000, "percentage": 20.4}
]
```

---

### 2. **`get_channel_audience`** ✅ GRAFICABLE

**Datos:** Lista de canales con `unique_devices`, `unique_users`, `total_views`, `total_hours`

**Gráficas recomendadas:**
- **Gráfica de barras agrupadas** (Dispositivos vs. Usuarios por canal)
- **Gráfica de líneas duales** (Visualizaciones y horas por canal)
- **Gráfica de burbujas** (Eje X: usuarios, Eje Y: horas, Tamaño: visualizaciones)
- **Heatmap** (Canales vs. Métricas: usuarios, dispositivos, horas)

**Ejemplo de datos:**
```json
[
  {
    "dataName": "Canal A",
    "unique_devices": 500,
    "unique_users": 450,
    "total_views": 5000,
    "total_hours": 2500.5
  }
]
```

---

### 3. **`get_peak_hours_by_channel`** ✅ GRAFICABLE

**Datos:** Lista con `dataName`, `timeDate` (0-23), `views`

**Gráficas recomendadas:**
- **Heatmap** (Canales en filas, Horas 0-23 en columnas, Color: visualizaciones)
- **Gráfica de líneas múltiples** (Una línea por canal, horas en X, visualizaciones en Y)
- **Gráfica de área apilada** (Horas en X, visualizaciones apiladas por canal)

**Ejemplo de datos:**
```json
[
  {"dataName": "Canal A", "timeDate": 20, "views": 500},
  {"dataName": "Canal A", "timeDate": 21, "views": 600}
]
```

---

### 4. **`get_average_duration_by_channel`** ✅ GRAFICABLE

**Datos:** Lista de canales con `avg_duration`, `total_views`, `total_watch_time`

**Gráficas recomendadas:**
- **Gráfica de barras** (Duración promedio por canal)
- **Gráfica de dispersión** (Eje X: visualizaciones, Eje Y: duración promedio)
- **Gráfica de barras agrupadas** (Duración promedio vs. Total de horas)

**Ejemplo de datos:**
```json
[
  {
    "dataName": "Canal A",
    "avg_duration": 1800.5,
    "total_views": 5000,
    "total_watch_time": 9000000
  }
]
```

---

### 5. **`get_temporal_analysis`** ✅ GRAFICABLE

**Datos:** Lista con `period` (fecha/semana/mes) y `views`

**Gráficas recomendadas:**
- **Gráfica de líneas** (Tendencia temporal de visualizaciones)
- **Gráfica de área** (Visualizaciones acumuladas en el tiempo)
- **Gráfica de barras** (Visualizaciones por período)

**Ejemplo de datos:**
```json
[
  {"period": "2025-01-01", "views": 5000},
  {"period": "2025-01-02", "views": 5200}
]
```

---

### 6. **`get_time_slot_analysis`** ✅ GRAFICABLE

**Datos:** Objeto con `time_slots` (madrugada, mañana, tarde, noche) y `summary`

**Gráficas recomendadas:**
- **Gráfica de pastel** (Distribución de horas por franja horaria)
- **Gráfica de barras** (Comparación de horas y visualizaciones por franja)
- **Gráfica de dona** (Distribución porcentual de consumo)

**Ejemplo de datos:**
```json
{
  "time_slots": {
    "madrugada": {"total_hours": 50.2, "total_views": 120},
    "mañana": {"total_hours": 80.5, "total_views": 200},
    "tarde": {"total_hours": 150.3, "total_views": 400},
    "noche": {"total_hours": 169.5, "total_views": 530}
  }
}
```

---

### 7. **`get_geographic_analysis`** ✅ GRAFICABLE

**Datos:** Lista con `whoisCountry`, `whoisIsp`, `total_views`, `unique_devices`, `unique_users`

**Gráficas recomendadas:**
- **Mapa de calor geográfico** (Países con intensidad según visualizaciones)
- **Gráfica de barras** (Top países por visualizaciones)
- **Gráfica de barras agrupadas** (Países vs. Métricas: usuarios, dispositivos, visualizaciones)
- **Gráfica de treemap** (Países e ISPs anidados)

**Ejemplo de datos:**
```json
[
  {
    "whoisCountry": "MX",
    "whoisIsp": "ISP1",
    "total_views": 5000,
    "unique_devices": 500,
    "unique_users": 450
  }
]
```

---

### 8. **`get_time_series_analysis`** ✅ GRAFICABLE

**Datos:** `historical_data` (fecha, views, moving_avg_7d, trend) y `forecast` (fecha, forecast)

**Gráficas recomendadas:**
- **Gráfica de líneas múltiples** (Datos históricos, media móvil, tendencia, pronóstico)
- **Gráfica de área con pronóstico** (Área histórica + línea de pronóstico)
- **Gráfica de líneas con bandas de confianza** (Si se calculan)

**Ejemplo de datos:**
```json
{
  "historical_data": [
    {"dataDate": "2025-01-01", "views": 5000, "moving_avg_7d": 4800, "trend": 4900}
  ],
  "forecast": [
    {"dataDate": "2025-02-01", "forecast": 5500}
  ]
}
```

---

### 9. **`get_user_segmentation_analysis`** ✅ GRAFICABLE

**Datos:** Lista de `segments` con métricas promedio

**Gráficas recomendadas:**
- **Gráfica de barras** (Distribución de usuarios por segmento)
- **Gráfica de pastel** (Porcentaje de usuarios por segmento)
- **Gráfica de radar** (Métricas promedio de cada segmento)
- **Gráfica de barras agrupadas** (Comparación de métricas entre segmentos)

**Ejemplo de datos:**
```json
{
  "segments": [
    {
      "segment_name": "Usuarios Super Activos",
      "user_count": 1000,
      "percentage": 20.0,
      "avg_metrics": {
        "total_watch_time": 500.5,
        "avg_duration": 1800.2,
        "unique_channels": 15.5,
        "total_views": 2000.0
      }
    }
  ]
}
```

---

### 10. **`get_channel_performance_matrix`** ✅ GRAFICABLE

**Datos:** Lista de canales con múltiples métricas y `performance_score`

**Gráficas recomendadas:**
- **Heatmap** (Canales vs. Métricas normalizadas)
- **Gráfica de barras** (Performance score por canal)
- **Gráfica de dispersión** (Eje X: usuarios, Eje Y: horas, Color: performance_score)
- **Tabla de calor** (Matriz de rendimiento)

**Ejemplo de datos:**
```json
{
  "performance_matrix": [
    {
      "channel": "Canal A",
      "total_views": 5000,
      "unique_users": 500,
      "performance_score": 85.5,
      "rank": 1
    }
  ]
}
```

---

### 11. **`get_correlation_analysis`** ✅ GRAFICABLE

**Datos:** `correlation_matrix` (matriz de correlaciones)

**Gráficas recomendadas:**
- **Heatmap de correlación** (Matriz de correlaciones con colores)
- **Gráfica de dispersión** (Pares de variables con mayor correlación)
- **Gráfica de red** (Variables conectadas por correlación)

**Ejemplo de datos:**
```json
{
  "correlation_matrix": {
    "total_watch_time": {
      "unique_channels": 0.75,
      "total_views": 0.85
    }
  }
}
```

---

### 12. **`get_general_summary`** ⚠️ PARCIALMENTE GRAFICABLE

**Datos:** Métricas agregadas (números simples)

**Gráficas recomendadas:**
- **Tarjetas/KPIs** (Mostrar números grandes)
- **Gráfica de indicadores** (Gauges para porcentajes)
- **No requiere gráfica compleja** (Solo visualización de métricas)

---

## 📅 ANÁLISIS POR RANGO DE FECHAS

### 13. **`get_period_summary`** ✅ GRAFICABLE

**Datos:** `metrics`, `top_channels`, `daily_distribution`

**Gráficas recomendadas:**
- **KPIs/Tarjetas** (Métricas principales)
- **Gráfica de líneas** (`daily_distribution` - visualizaciones por día)
- **Gráfica de barras** (`top_channels` - top canales del período)

---

### 14. **`get_period_comparison`** ✅ GRAFICABLE

**Datos:** Comparación entre período actual y anterior con cambios

**Gráficas recomendadas:**
- **Gráfica de barras agrupadas** (Período actual vs. anterior)
- **Gráfica de líneas duales** (Tendencia de ambos períodos)
- **Gráfica de indicadores de cambio** (Flechas arriba/abajo con porcentajes)
- **Gráfica de barras apiladas** (Comparación lado a lado)

**Ejemplo de datos:**
```json
{
  "current_period": {"total_views": 50000},
  "previous_period": {"total_views": 45000},
  "comparison": {
    "changes": {
      "views": {
        "absolute": 5000,
        "percentage": 10.0,
        "trend": "aumento"
      }
    }
  }
}
```

---

### 15. **`get_period_temporal_breakdown`** ✅ GRAFICABLE

**Datos:** Desglose temporal (diario/semanal/mensual) con múltiples métricas

**Gráficas recomendadas:**
- **Gráfica de líneas múltiples** (Varias métricas en el tiempo)
- **Gráfica de área apilada** (Métricas apiladas)
- **Gráfica de barras agrupadas** (Métricas por período)

---

### 16. **`get_period_channel_analysis`** ✅ GRAFICABLE

**Datos:** Lista de canales con métricas del período

**Gráficas recomendadas:**
- **Gráfica de barras horizontal** (Top canales por visualizaciones)
- **Gráfica de barras agrupadas** (Múltiples métricas por canal)
- **Gráfica de burbujas** (Usuarios vs. Horas, tamaño: visualizaciones)

---

### 17. **`get_period_user_analysis`** ✅ GRAFICABLE

**Datos:** Top usuarios del período con métricas

**Gráficas recomendadas:**
- **Gráfica de barras** (Top usuarios por visualizaciones/horas)
- **Gráfica de dispersión** (Visualizaciones vs. Horas por usuario)
- **Tabla interactiva** (Lista de usuarios con ordenamiento)

---

### 18. **`get_period_events_analysis`** ✅ GRAFICABLE

**Datos:** Eventos/anomalías detectados con fechas y métricas

**Gráficas recomendadas:**
- **Gráfica de líneas con marcadores** (Tendencia con puntos destacados para eventos)
- **Gráfica de barras** (Eventos por tipo: alto/bajo)
- **Gráfica de dispersión temporal** (Fecha vs. Valor, color por tipo de evento)

---

### 19. **`get_period_trend_analysis`** ✅ GRAFICABLE

**Datos:** Tendencias calculadas (creciente/decreciente/estable)

**Gráficas recomendadas:**
- **Gráfica de líneas con tendencia** (Datos + línea de tendencia)
- **Gráfica de área** (Tendencia suavizada)
- **Indicadores de tendencia** (Flechas y porcentajes de cambio)

---

## 👥 ANÁLISIS DE USUARIOS

### 20. **`get_general_users_analysis`** ✅ GRAFICABLE

**Datos:** `segmentation`, `top_users`, `temporal_distribution`, `engagement_metrics`

**Gráficas recomendadas:**
- **Gráfica de pastel** (`segmentation` - distribución por nivel de actividad)
- **Gráfica de barras** (`top_users.by_hours` - top usuarios por horas)
- **Gráfica de líneas** (`temporal_distribution` - usuarios activos por fecha)
- **Gráfica de barras agrupadas** (`top_users` - comparación por métricas)
- **Indicadores/KPIs** (`engagement_metrics` - retención, churn)

**Ejemplo de datos:**
```json
{
  "segmentation": {
    "super_activo": 1000,
    "activo": 1500,
    "regular": 1200,
    "ocasional": 800,
    "inactivo": 500
  },
  "temporal_distribution": [
    {"date": "2025-01-01", "active_users": 3500}
  ]
}
```

---

### 21. **`get_user_analysis`** ✅ GRAFICABLE

**Datos:** `profile`, `consumption_behavior`, `temporal_patterns`, `user_statistics`

**Gráficas recomendadas:**
- **KPIs/Tarjetas** (`profile` - métricas principales)
- **Gráfica de barras** (`consumption_behavior.top_channels` - canales favoritos)
- **Gráfica de pastel** (`consumption_behavior.preferred_time_slots` - distribución horaria)
- **Gráfica de barras** (`consumption_behavior.devices_used` - dispositivos)
- **Gráfica de líneas** (`temporal_patterns.hourly_activity` - actividad por hora 0-23)
- **Gráfica de radar** (`user_statistics` - múltiples métricas en un gráfico)

**Ejemplo de datos:**
```json
{
  "consumption_behavior": {
    "top_channels": [
      {"channel": "Canal A", "views": 350, "total_hours": 180.5}
    ],
    "preferred_time_slots": {
      "noche": {"total_hours": 169.5, "total_views": 530}
    }
  },
  "temporal_patterns": {
    "hourly_activity": [
      {"hour": 20, "views": 50, "total_hours": 15.5}
    ]
  }
}
```

---

### 22. **`get_user_date_range_analysis`** ✅ GRAFICABLE

**Datos:** `temporal_evolution`, `channels_in_period`, `time_slots_in_period`, `comparison_with_average`, `anomalies`

**Gráficas recomendadas:**
- **Gráfica de líneas** (`temporal_evolution.daily_activity` - evolución día por día)
- **Gráfica de barras** (`channels_in_period` - canales consumidos en el período)
- **Gráfica de pastel** (`time_slots_in_period` - distribución por franjas horarias)
- **Gráfica de barras agrupadas** (`comparison_with_average` - usuario vs. promedio)
- **Gráfica de líneas con marcadores** (`anomalies` - días anómalos destacados)
- **Indicador de tendencia** (`temporal_evolution.trend` - creciente/decreciente/estable)

**Ejemplo de datos:**
```json
{
  "temporal_evolution": {
    "daily_activity": [
      {"date": "2025-01-01", "views": 30, "total_hours": 12.5}
    ],
    "trend": "creciente"
  },
  "anomalies": [
    {
      "date": "2025-01-15",
      "total_hours": 25.5,
      "type": "alto",
      "z_score": 2.5
    }
  ]
}
```

---

## 📋 RESUMEN POR TIPO DE GRÁFICA

### **Gráficas de Barras** (Más comunes)
- Top canales
- Top usuarios
- Comparaciones período actual vs. anterior
- Distribución por segmentos
- Canales favoritos de usuario

### **Gráficas de Líneas** (Tendencias temporales)
- Análisis temporal (diario/semanal/mensual)
- Evolución de usuarios activos
- Series temporales con pronóstico
- Actividad diaria de usuario
- Comparación de períodos

### **Gráficas de Pastel/Donut** (Distribuciones)
- Segmentación de usuarios
- Distribución por franjas horarias
- Distribución de canales (porcentajes)

### **Heatmaps** (Datos multidimensionales)
- Horarios pico por canal (canales × horas)
- Matriz de correlaciones
- Matriz de rendimiento de canales
- Análisis geográfico

### **Gráficas de Dispersión/Burbujas** (Relaciones)
- Usuarios vs. Canales (burbujas)
- Visualizaciones vs. Duración
- Correlaciones entre variables

### **Gráficas de Área** (Acumulación)
- Visualizaciones acumuladas en el tiempo
- Consumo por franjas horarias apilado

### **Gráficas de Radar** (Múltiples métricas)
- Segmentos de usuarios
- Perfil completo de usuario

### **Mapas Geográficos** (Ubicación)
- Distribución por países
- Mapa de calor geográfico

---

## 🎯 RECOMENDACIONES GENERALES

1. **Para Dashboards Ejecutivos:**
   - KPIs/Tarjetas grandes
   - Gráficas de líneas (tendencias)
   - Gráficas de pastel (distribuciones)
   - Gráficas de barras (comparaciones)

2. **Para Análisis Detallados:**
   - Heatmaps (datos multidimensionales)
   - Gráficas de dispersión (relaciones)
   - Gráficas de líneas múltiples (comparaciones)

3. **Para Análisis de Usuarios:**
   - Gráficas de barras (top usuarios)
   - Gráficas de pastel (segmentación)
   - Gráficas de líneas (evolución temporal)
   - Gráficas de radar (perfil completo)

4. **Para Análisis Temporales:**
   - Gráficas de líneas (tendencias)
   - Gráficas de área (acumulación)
   - Gráficas de barras (comparación por período)

---

## ⚠️ NOTAS IMPORTANTES

- **Todas las gráficas deben ser interactivas** (zoom, filtros, tooltips)
- **Usar colores consistentes** para las mismas categorías
- **Incluir leyendas y etiquetas** claras
- **Permitir exportación** de gráficas (PNG, PDF)
- **Responsive design** para móviles y tablets
- **Considerar accesibilidad** (colores, contraste, texto alternativo)

