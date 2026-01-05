# Análisis de Telemetría OTT - MergedTelemetricOTTDelancer

> **Nota de Compatibilidad:** Las consultas SQL en este documento están optimizadas para **MySQL 8.0+ / MariaDB 10.2+**. Son compatibles con SQLite para desarrollo, pero funcionarán mejor en MySQL/MariaDB gracias a:
> - Mejor optimización de índices
> - Funciones de ventana (window functions) - MySQL 8.0+/MariaDB 10.2+
> - CTEs (Common Table Expressions) - MySQL 8.0+/MariaDB 10.2+
> - Mejor manejo de agregaciones complejas
> 
> **IMPORTANTE:** Los análisis trabajan con datos de la base de datos local (`MergedTelemetricOTTDelancer`),
> NO consultan directamente a PanAccess. Los datos se obtienen de PanAccess mediante `telemetry_fetcher.py`
> y se almacenan localmente para análisis eficientes.

## 📋 Índice

1. [Funciones Disponibles en `analytics.py`](#funciones-disponibles-en-analyticspy)
2. [Análisis de Consumo por Canal](#análisis-de-consumo-por-canal)
3. [Análisis Temporal](#análisis-temporal)
4. [Análisis por Dispositivo](#análisis-por-dispositivo)
5. [Análisis Geográfico](#análisis-geográfico)
6. [Análisis de Comportamiento](#análisis-de-comportamiento)
7. [Análisis Comparativos](#análisis-comparativos)
8. [Análisis Avanzados](#análisis-avanzados)
9. [Análisis de Negocio](#análisis-de-negocio)

---

## 🔧 Funciones Disponibles en `analytics.py`

Este documento explica los conceptos y tipos de análisis disponibles. Las funciones reales implementadas en `TelemetriaDelancer/panaccess/analytics.py` son:

### Funciones de Análisis por Canal

1. **`get_top_channels(limit=10, start_date=None, end_date=None)`**
   - Retorna: `List[Dict]` con `channel`, `total_views`, `percentage`
   - Implementa: [Top Canales Más Vistos](#1-top-canales-más-vistos)
   - Usa: Django ORM con agregaciones optimizadas

2. **`get_channel_audience(start_date=None, end_date=None)`**
   - Retorna: `List[Dict]` con `dataName`, `unique_devices`, `unique_users`, `total_views`, `total_watch_time`, `total_hours`
   - Implementa: [Análisis de Audiencia por Canal](#2-análisis-de-audiencia-por-canal)
   - Usa: Django ORM con COUNT DISTINCT

3. **`get_peak_hours_by_channel(channel=None, start_date=None, end_date=None)`**
   - Retorna: `List[Dict]` con `dataName`, `timeDate`, `views`
   - Implementa: [Horarios Pico por Canal](#3-horarios-pico-por-canal)
   - Usa: Django ORM con agrupación por canal y hora

4. **`get_average_duration_by_channel(start_date=None, end_date=None)`**
   - Retorna: `List[Dict]` con `dataName`, `avg_duration`, `total_views`, `total_watch_time`
   - Implementa: [Duración Promedio por Canal](#4-duración-promedio-por-canal)
   - Usa: Django ORM con AVG y SUM

### Funciones de Análisis Temporal

5. **`get_temporal_analysis(period='daily', start_date=None, end_date=None)`**
   - Parámetros: `period` puede ser `'daily'`, `'weekly'`, o `'monthly'`
   - Retorna: `List[Dict]` con `period`, `views`
   - Implementa: [Análisis por Fecha](#5-análisis-por-fecha-datadate)
   - Usa: Django ORM con `TruncDate`, `TruncWeek`, `TruncMonth` (MySQL/MariaDB) o Raw SQL (SQLite)

### Funciones de Análisis Avanzados (Raw SQL)

6. **`get_day_over_day_comparison(start_date=None, end_date=None)`**
   - Retorna: `List[Dict]` con `dataDate`, `daily_views`, `previous_day_views`, `day_over_day_change`
   - Implementa: [Comparación Temporal](#17-comparación-temporal)
   - Usa: Raw SQL con CTEs y funciones de ventana (LAG) - Requiere MySQL 8.0+ / MariaDB 10.2+
   - ⚠️ Requiere MySQL 8.0+ / MariaDB 10.2+ para funciones de ventana

7. **`get_anomaly_detection(threshold_std=3.0, start_date=None, end_date=None)`**
   - Retorna: `List[Dict]` con `dataDate`, `daily_views`, `average_views`, `standard_deviation`, `z_score`
   - Implementa: [Análisis de Anomalías](#21-análisis-de-anomalías)
   - Usa: Raw SQL con CTEs y STDDEV_POP/STDDEV_SAMP
   - ⚠️ Requiere MySQL 8.0+ / MariaDB 10.2+ (usa STDDEV_SAMP en MySQL)

### Funciones de Análisis por Franjas Horarias

8. **`get_time_slot_analysis(start_date=None, end_date=None)`**
   - Retorna: `Dict` con `time_slots` (madrugada, mañana, tarde, noche) y `summary`
   - Cada franja incluye: `total_seconds`, `total_hours` (redondeado a 2 decimales), `total_views`
   - Usa: Django ORM con `Case/When` para clasificar por franja horaria

### Funciones de Resumen General

9. **`get_general_summary(start_date=None, end_date=None)`**
   - Retorna: `Dict` con `total_views`, `active_users`, `unique_devices`, `unique_channels`, `total_watch_time_seconds`, `total_watch_time_hours`
   - Implementa: Resumen general del sistema
   - Usa: Django ORM con agregaciones

### Funciones de Análisis Geográfico

10. **`get_geographic_analysis(start_date=None, end_date=None)`**
    - Retorna: `List[Dict]` con `whoisCountry`, `whoisIsp`, `total_views`, `unique_devices`, `unique_users`
    - Implementa: [Análisis por País](#10-análisis-por-país-whoiscountry)
    - Usa: Django ORM con agrupación por país e ISP

### Funciones de Análisis Avanzados (Pandas - Opcional)

11. **`get_cohort_analysis_pandas(start_date=None, end_date=None)`**
    - ⚠️ **Requiere Pandas/NumPy**
    - Retorna: `Dict` con `data` (cohortes), `summary` (total_cohorts, total_users)
    - Implementa: [Análisis de Cohortes](#22-análisis-de-cohortes)
    - Usa: Pandas para análisis de cohortes

12. **`get_correlation_analysis(start_date=None, end_date=None)`**
    - ⚠️ **Requiere Pandas/NumPy**
    - Retorna: `Dict` con `correlation_matrix`, `descriptive_stats`, `insights`
    - Implementa: [Análisis de Correlaciones](#19-análisis-de-correlaciones)
    - Usa: Pandas para calcular matriz de correlaciones

13. **`get_time_series_analysis(channel=None, start_date=None, end_date=None, forecast_days=7)`**
    - ⚠️ **Requiere Pandas/NumPy**
    - Retorna: `Dict` con `historical_data`, `forecast`, `statistics`, `channel`
    - Implementa: [Análisis Predictivo](#20-análisis-predictivo)
    - Usa: Pandas y NumPy para forecasting con regresión lineal

14. **`get_user_segmentation_analysis(start_date=None, end_date=None, n_segments=4)`**
    - ⚠️ **Requiere Pandas/NumPy**
    - Retorna: `Dict` con `segments`, `total_users`, `features_used`
    - Implementa: Segmentación de usuarios usando K-means
    - Usa: NumPy para K-means clustering (implementación simple)

15. **`get_channel_performance_matrix(start_date=None, end_date=None)`**
    - ⚠️ **Requiere Pandas/NumPy**
    - Retorna: `Dict` con `performance_matrix`, `summary`
    - Implementa: Matriz de rendimiento de canales con scoring
    - Usa: Pandas para calcular métricas y scores normalizados

### Notas Importantes sobre las Funciones

- **Parámetros opcionales**: Todas las funciones aceptan `start_date` y `end_date` opcionales para filtrar por rango de fechas
- **Filtros aplicados**: Se filtran automáticamente registros donde los campos relevantes son `None` (ej: `dataName__isnull=False`)
- **Conversión de tiempo**: Los tiempos se almacenan en segundos (`dataDuration`) y se convierten a horas dividiendo por 3600.0
- **Redondeo**: Todos los valores de horas se redondean a 2 decimales
- **Base de datos local**: Todas las funciones trabajan con `MergedTelemetricOTTDelancer`, NO consultan PanAccess directamente
- **Compatibilidad**: Las funciones con Raw SQL requieren MySQL 8.0+ / MariaDB 10.2+ para funciones de ventana y CTEs
- **Pandas opcional**: Las funciones marcadas con ⚠️ requieren Pandas/NumPy instalados, si no están disponibles lanzan `ImportError`

---

---

## 📺 Análisis de Consumo por Canal

### 1. Top Canales Más Vistos

**¿En qué consiste?**
- Ranking de canales ordenados por número total de visualizaciones (actionId=8)
- Cálculo de porcentaje de participación de cada canal respecto al total
- Identificación de canales líderes y nichos de mercado

**¿Cómo se calcula?**
```sql
SELECT dataName, COUNT(*) as total_views, 
       (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM merged_telemetric_ott)) as percentage
FROM merged_telemetric_ott
WHERE dataName IS NOT NULL
GROUP BY dataName
ORDER BY total_views DESC
```

**Impacto:**
- **Estrategia de contenido**: Identificar qué canales generan más engagement
- **Negociaciones**: Datos para negociar mejores acuerdos con proveedores de contenido
- **Marketing**: Enfocar esfuerzos publicitarios en canales más populares
- **ROI**: Optimizar inversión en contenido basado en demanda real

---

### 2. Análisis de Audiencia por Canal

**Función implementada:** `get_channel_audience(start_date=None, end_date=None)`

**¿En qué consiste?**
- Número de dispositivos únicos que consumen cada canal
- Número de usuarios únicos (subscriberCode) por canal
- Total de horas vistas por canal
- Tasa de penetración de cada canal en la base de usuarios

**¿Cómo se calcula?**
- **Implementación:** Usa Django ORM con COUNT DISTINCT y SUM
- **Consulta equivalente:**
```sql
SELECT dataName,
       COUNT(DISTINCT deviceId) as unique_devices,
       COUNT(DISTINCT subscriberCode) as unique_users,
       COUNT(*) as total_views,
       SUM(dataDuration) as total_watch_time
FROM merged_telemetric_ott
WHERE dataName IS NOT NULL
GROUP BY dataName
ORDER BY total_views DESC
```

**Retorna:**
```python
[
    {
        "dataName": "Canal Premium",
        "unique_devices": 1800,  # Count distinct de deviceId
        "unique_users": 2000,  # Count distinct de subscriberCode
        "total_views": 10000,  # Count de registros
        "total_watch_time": 900000.0,  # En segundos
        "total_hours": 250.0  # Calculado desde segundos, redondeado a 2 decimales
    },
    ...
]
```

**Notas:**
- Ordenado por `total_views` descendente
- `total_watch_time` está en segundos, `total_hours` se calcula dividiendo por 3600.0
- Solo incluye canales donde `dataName` no es `None`

**Impacto:**
- **Diversificación**: Identificar si un canal tiene muchos views pero pocos usuarios (dependencia)
- **Crecimiento**: Canales con alto potencial de crecimiento de audiencia
- **Retención**: Canales que atraen nuevos usuarios vs. canales que retienen existentes
- **Segmentación**: Entender qué canales atraen a qué tipo de usuarios

---

### 3. Horarios Pico por Canal

**Función implementada:** `get_peak_hours_by_channel(channel=None, start_date=None, end_date=None)`

**¿En qué consiste?**
- Identificar las franjas horarias (timeDate) con mayor consumo para cada canal
- Patrones diarios de visualización por canal
- Comparación de horarios pico entre diferentes canales

**¿Cómo se calcula?**
- **Implementación:** Usa Django ORM con agrupación por canal y hora
- **Consulta equivalente:**
```sql
SELECT dataName, timeDate, COUNT(*) as views
FROM merged_telemetric_ott
WHERE dataName IS NOT NULL AND timeDate IS NOT NULL
GROUP BY dataName, timeDate
ORDER BY dataName, views DESC
```

**Retorna:**
```python
[
    {
        "dataName": "Canal Premium",
        "timeDate": 20,  # Hora del día (0-23)
        "views": 500  # Count de registros en esa hora
    },
    ...
]
```

**Notas:**
- Si se proporciona `channel`, filtra solo ese canal
- Ordenado por `dataName` y luego por `views` descendente
- Solo incluye registros donde `dataName` y `timeDate` no son `None`

**Impacto:**
- **Programación**: Optimizar horarios de programación especial
- **Publicidad**: Maximizar impacto publicitario en horarios pico
- **Recursos**: Asignar recursos de servidor/CDN según demanda horaria
- **Contenido**: Programar estrenos y contenido premium en horarios de mayor audiencia

---

### 4. Duración Promedio por Canal

**Función implementada:** `get_average_duration_by_channel(start_date=None, end_date=None)`

**¿En qué consiste?**
- Tiempo promedio de visualización (dataDuration) por canal
- Comparación de duración entre diferentes canales
- Identificación de canales con mayor retención de audiencia

**¿Cómo se calcula?**
- **Implementación:** Usa Django ORM con AVG, COUNT y SUM
- **Consulta equivalente:**
```sql
SELECT dataName,
       AVG(dataDuration) as avg_duration,
       COUNT(*) as total_views,
       SUM(dataDuration) as total_watch_time
FROM merged_telemetric_ott
WHERE dataName IS NOT NULL AND dataDuration IS NOT NULL
GROUP BY dataName
ORDER BY avg_duration DESC
```

**Retorna:**
```python
[
    {
        "dataName": "Canal Premium",
        "avg_duration": 1356.0,  # Promedio en segundos (float)
        "total_views": 10000,  # Count de registros
        "total_watch_time": 13560000.0  # Suma en segundos (float)
    },
    ...
]
```

**Notas:**
- Ordenado por `avg_duration` descendente
- `avg_duration` y `total_watch_time` están en segundos
- Solo incluye canales donde `dataName` y `dataDuration` no son `None`

**Impacto:**
- **Calidad de contenido**: Canales con mayor duración indican mejor contenido
- **Satisfacción**: Duración como indicador de satisfacción del usuario
- **Monetización**: Canales con mayor duración = más oportunidades publicitarias
- **Renovación de contenido**: Identificar canales que necesitan mejor contenido

---

## ⏰ Análisis Temporal

### 5. Análisis por Fecha (dataDate)

**Función implementada:** `get_temporal_analysis(period='daily', start_date=None, end_date=None)`

**¿En qué consiste?**
- Consumo diario, semanal y mensual de contenido OTT
- Identificación de tendencias temporales
- Comparación de consumo entre diferentes períodos (días, semanas, meses)

**¿Cómo se calcula?**
- **Implementación:** 
  - MySQL/MariaDB: Usa Django ORM con `TruncDate`, `TruncWeek`, `TruncMonth`
  - SQLite: Usa Raw SQL con `date()` y `strftime()` como fallback
- **Consulta equivalente:**
```sql
-- Diario (MySQL/MariaDB con Django ORM)
SELECT TruncDate(dataDate) as period, COUNT(*) as views
FROM merged_telemetric_ott
WHERE dataDate IS NOT NULL
GROUP BY period
ORDER BY period

-- Semanal (MySQL/MariaDB con Django ORM)
SELECT TruncWeek(dataDate) as period, COUNT(*) as views
FROM merged_telemetric_ott
WHERE dataDate IS NOT NULL
GROUP BY period
ORDER BY period

-- Mensual (MySQL/MariaDB con Django ORM)
SELECT TruncMonth(dataDate) as period, COUNT(*) as views
FROM merged_telemetric_ott
WHERE dataDate IS NOT NULL
GROUP BY period
ORDER BY period
```

**Retorna:**
```python
[
    {
        "period": "2025-01-01",  # Para daily (date object)
        "views": 5000  # Count de registros
    },
    ...
]
```

**Notas:**
- `period` puede ser `'daily'`, `'weekly'`, o `'monthly'`
- Para SQLite, usa Raw SQL como fallback (TruncDate no funciona en SQLite)
- Solo incluye registros donde `dataDate` no es `None`

**Impacto:**
- **Planificación**: Anticipar demanda en fechas específicas (festivos, eventos)
- **Capacidad**: Dimensionar infraestructura según patrones temporales
- **Marketing**: Lanzar campañas en períodos de mayor consumo
- **ROI**: Medir efectividad de campañas y promociones temporales

---

### 6. Análisis por Hora (timeDate)

**¿En qué consiste?**
- Distribución de consumo por hora del día (0-23)
- Identificación de horarios pico y valle
- Patrones de consumo según hora del día

**¿Cómo se calcula?**
```sql
SELECT timeDate, COUNT(*) as views
FROM merged_telemetric_ott
WHERE timeDate IS NOT NULL
GROUP BY timeDate
ORDER BY timeDate
```

**Impacto:**
- **Operaciones**: Optimizar recursos técnicos según demanda horaria
- **Soporte**: Prever picos de soporte técnico en horarios de mayor uso
- **Contenido**: Programar contenido según hábitos de visualización
- **Costos**: Optimizar costos de infraestructura (escalado automático)

---

### 7. Análisis de Sesiones

**¿En qué consiste?**
- Duración promedio de sesiones de visualización
- Frecuencia de cambios de canal durante una sesión
- Patrones de consumo continuo vs. consumo fragmentado

**¿Cómo se calcula?**
```sql
-- Sesiones por usuario/dispositivo
SELECT deviceId, subscriberCode,
       COUNT(*) as session_count,
       AVG(dataDuration) as avg_session_duration,
       MIN(timestamp) as first_view,
       MAX(timestamp) as last_view
FROM merged_telemetric_ott
WHERE dataDuration IS NOT NULL
GROUP BY deviceId, subscriberCode, DATE(timestamp)
```

**Impacto:**
- **UX**: Mejorar experiencia de usuario basada en patrones de sesión
- **Recomendaciones**: Sistema de recomendaciones basado en sesiones
- **Retención**: Identificar factores que aumentan duración de sesión
- **Monetización**: Más sesiones = más oportunidades de monetización

---

## 📱 Análisis por Dispositivo

### 8. Consumo por Dispositivo (deviceId)

**¿En qué consiste?**
- Identificar dispositivos más activos en consumo de contenido
- Canales preferidos por tipo de dispositivo
- Patrones de uso específicos por dispositivo

**¿Cómo se calcula?**
```sql
SELECT deviceId,
       COUNT(*) as total_views,
       COUNT(DISTINCT dataName) as unique_channels,
       AVG(dataDuration) as avg_duration
FROM merged_telemetric_ott
WHERE deviceId IS NOT NULL
GROUP BY deviceId
ORDER BY total_views DESC
```

**Impacto:**
- **Desarrollo**: Priorizar desarrollo de apps para dispositivos más usados
- **Soporte**: Enfocar soporte técnico en dispositivos problemáticos
- **Marketing**: Campañas específicas por tipo de dispositivo
- **Optimización**: Optimizar rendimiento para dispositivos más populares

---

### 9. Análisis de Usuarios (subscriberCode/smartcardId)

**¿En qué consiste?**
- Identificar usuarios más activos
- Canales preferidos por usuario individual
- Patrones de consumo personalizados

**¿Cómo se calcula?**
```sql
SELECT subscriberCode,
       COUNT(*) as total_views,
       COUNT(DISTINCT dataName) as unique_channels,
       SUM(dataDuration) as total_watch_time
FROM merged_telemetric_ott
WHERE subscriberCode IS NOT NULL
GROUP BY subscriberCode
ORDER BY total_views DESC
```

**Impacto:**
- **Personalización**: Crear perfiles de usuario para recomendaciones
- **Retención**: Identificar usuarios en riesgo de cancelación
- **Upselling**: Ofertas personalizadas basadas en preferencias
- **Satisfacción**: Medir satisfacción individual y mejorar experiencia

---

## 🌍 Análisis Geográfico

### 10. Análisis por País (whoisCountry)

**Función implementada:** `get_geographic_analysis(start_date=None, end_date=None)`

**¿En qué consiste?**
- Distribución de consumo de contenido por país e ISP
- Canales más populares por región geográfica
- Patrones de consumo regionales

**¿Cómo se calcula?**
- **Implementación:** Usa Django ORM con agrupación por país e ISP
- **Consulta equivalente:**
```sql
SELECT whoisCountry, whoisIsp,
       COUNT(*) as total_views,
       COUNT(DISTINCT deviceId) as unique_devices,
       COUNT(DISTINCT subscriberCode) as unique_users
FROM merged_telemetric_ott
WHERE whoisCountry IS NOT NULL
GROUP BY whoisCountry, whoisIsp
ORDER BY total_views DESC
```

**Retorna:**
```python
[
    {
        "whoisCountry": "US",
        "whoisIsp": "ISP Name",
        "total_views": 50000,  # Count de registros
        "unique_devices": 5000,  # Count distinct de deviceId
        "unique_users": 4500  # Count distinct de subscriberCode
    },
    ...
]
```

**Notas:**
- Agrupa por país E ISP (combinación de ambos)
- Ordenado por `total_views` descendente
- Solo incluye registros donde `whoisCountry` no es `None`

**Impacto:**
- **Expansión**: Identificar mercados con potencial de crecimiento
- **Contenido**: Adquirir contenido relevante para cada región
- **Localización**: Traducir y localizar contenido según demanda regional
- **Regulación**: Cumplir con regulaciones locales de contenido

---

### 11. Análisis por ISP (whoisIsp)

**¿En qué consiste?**
- Distribución de consumo por proveedor de internet
- Análisis de calidad de servicio por ISP
- Identificación de problemas de conectividad por proveedor

**¿Cómo se calcula?**
```sql
SELECT whoisIsp,
       COUNT(*) as total_views,
       AVG(dataDuration) as avg_duration,
       COUNT(DISTINCT deviceId) as unique_devices
FROM merged_telemetric_ott
WHERE whoisIsp IS NOT NULL
GROUP BY whoisIsp
ORDER BY total_views DESC
```

**Impacto:**
- **Partnerships**: Negociar acuerdos con ISPs principales
- **Optimización**: Optimizar CDN para ISPs específicos
- **Soporte**: Identificar problemas de calidad por ISP
- **Marketing**: Campañas conjuntas con ISPs

---

### 12. Análisis por IP

**¿En qué consiste?**
- Distribución geográfica de direcciones IP
- Detección de patrones anómalos o sospechosos
- Análisis de concentración de consumo por IP

**¿Cómo se calcula?**
```sql
SELECT ip,
       COUNT(*) as total_views,
       COUNT(DISTINCT deviceId) as unique_devices,
       whoisCountry, whoisIsp
FROM merged_telemetric_ott
WHERE ip IS NOT NULL
GROUP BY ip
ORDER BY total_views DESC
```

**Impacto:**
- **Seguridad**: Detectar uso anómalo o abusivo
- **Fraude**: Identificar posibles casos de fraude o compartir cuentas
- **Geolocalización**: Mejorar precisión de geolocalización
- **Optimización**: Optimizar routing según ubicación de IPs

---

## 🎯 Análisis de Comportamiento

### 13. Análisis de Duración (dataDuration)

**¿En qué consiste?**
- Distribución estadística de duraciones de visualización
- Identificación de sesiones cortas vs. largas
- Análisis de abandono temprano vs. visualización completa

**¿Cómo se calcula?**
```sql
SELECT 
    CASE 
        WHEN dataDuration < 60 THEN 'Menos de 1 min'
        WHEN dataDuration < 300 THEN '1-5 min'
        WHEN dataDuration < 1800 THEN '5-30 min'
        WHEN dataDuration < 3600 THEN '30-60 min'
        ELSE 'Más de 1 hora'
    END as duration_category,
    COUNT(*) as count,
    AVG(dataDuration) as avg_duration
FROM merged_telemetric_ott
WHERE dataDuration IS NOT NULL
GROUP BY duration_category
```

**Impacto:**
- **Calidad**: Duración como indicador de calidad de contenido
- **Engagement**: Medir nivel de engagement de usuarios
- **Optimización**: Mejorar contenido que tiene bajo tiempo de visualización
- **Monetización**: Contenido con mayor duración = más valor publicitario

---

### 14. Análisis de Cambios de Canal

**¿En qué consiste?**
- Frecuencia de cambios entre canales (actionId 7 → 8)
- Identificación de canales más abandonados
- Canales con mayor retención de audiencia

**¿Cómo se calcula?**
```sql
-- Canales más abandonados (actionId=8 con menor duración)
SELECT dataName,
       COUNT(*) as abandonment_count,
       AVG(dataDuration) as avg_duration_before_abandon
FROM merged_telemetric_ott
WHERE actionId = 8 AND dataDuration IS NOT NULL
GROUP BY dataName
ORDER BY abandonment_count DESC
```

**Impacto:**
- **Contenido**: Mejorar canales con alta tasa de abandono
- **Programación**: Ajustar programación de canales problemáticos
- **UX**: Mejorar experiencia para reducir cambios de canal
- **Retención**: Estrategias para aumentar retención en canales específicos

---

### 15. Análisis de Retención

**¿En qué consiste?**
- Tasa de retención por canal (usuarios que vuelven)
- Tiempo promedio antes de cambiar de canal
- Canales con mayor fidelidad de audiencia

**¿Cómo se calcula?**
```sql
-- Retención por canal (usuarios que vuelven al mismo canal)
SELECT dataName,
       COUNT(DISTINCT subscriberCode) as unique_users,
       COUNT(*) as total_views,
       COUNT(*) * 1.0 / COUNT(DISTINCT subscriberCode) as views_per_user
FROM merged_telemetric_ott
WHERE dataName IS NOT NULL AND subscriberCode IS NOT NULL
GROUP BY dataName
ORDER BY views_per_user DESC
```

**Impacto:**
- **Fidelización**: Estrategias para aumentar fidelidad a canales
- **Marketing**: Campañas de retención para canales con baja fidelidad
- **Contenido**: Invertir en contenido que genera fidelidad
- **Suscripciones**: Canales con alta retención = mejor valor de suscripción

---

## 📊 Análisis Comparativos

### 16. Comparación entre Canales

**¿En qué consiste?**
- Comparación directa de métricas entre diferentes canales
- Análisis competitivo de canales similares
- Benchmarking de rendimiento

**¿Cómo se calcula?**
```sql
SELECT dataName,
       COUNT(*) as total_views,
       AVG(dataDuration) as avg_duration,
       COUNT(DISTINCT deviceId) as unique_devices,
       COUNT(DISTINCT subscriberCode) as unique_users
FROM merged_telemetric_ott
WHERE dataName IS NOT NULL
GROUP BY dataName
ORDER BY total_views DESC
```

**Impacto:**
- **Estrategia**: Identificar canales líderes y oportunidades
- **Inversión**: Decidir dónde invertir recursos de contenido
- **Competencia**: Entender posición competitiva de cada canal
- **Negociación**: Datos para negociaciones con proveedores

---

### 17. Comparación Temporal

**Función implementada:** `get_day_over_day_comparison(start_date=None, end_date=None)`

**¿En qué consiste?**
- Comparación de consumo día a día
- Identificación de tendencias y patrones temporales
- Análisis de crecimiento o declive

**¿Cómo se calcula?**
- **Implementación:** Usa Raw SQL con CTEs y funciones de ventana (LAG)
- **Consulta equivalente:**
```sql
-- Comparación día a día (MySQL 8.0+ / MariaDB 10.2+ optimizado con CTE)
WITH daily_stats AS (
    SELECT dataDate, COUNT(*) as daily_views
    FROM merged_telemetric_ott
    WHERE dataDate IS NOT NULL
    GROUP BY dataDate
)
SELECT dataDate,
       daily_views,
       LAG(daily_views) OVER (ORDER BY dataDate) as previous_day_views,
       daily_views - LAG(daily_views) OVER (ORDER BY dataDate) as day_over_day_change
FROM daily_stats
ORDER BY dataDate DESC
```

**Retorna:**
```python
[
    {
        "dataDate": "2025-01-15",  # date object
        "daily_views": 5000,  # Count de registros ese día
        "previous_day_views": 4800,  # Count del día anterior (LAG)
        "day_over_day_change": 200  # Diferencia absoluta
    },
    ...
]
```

**Notas:**
- ⚠️ **Requiere MySQL 8.0+ / MariaDB 10.2+** para funciones de ventana (LAG)
- Compatible con SQLite para desarrollo (con limitaciones)
- Solo incluye días con actividad
- Ordenado por `dataDate` descendente

**Impacto:**
- **Tendencias**: Identificar tendencias de crecimiento o declive
- **Eventos**: Medir impacto de eventos, promociones o campañas
- **Planificación**: Anticipar demanda futura basada en tendencias
- **KPIs**: Establecer y monitorear KPIs temporales

---

### 18. Comparación por Segmentos

**¿En qué consiste?**
- Comparación de consumo entre diferentes segmentos (dispositivo, país, ISP)
- Análisis de diferencias de comportamiento entre segmentos
- Identificación de oportunidades por segmento

**¿Cómo se calcula?**
```sql
-- Comparación por país
SELECT whoisCountry,
       COUNT(*) as total_views,
       AVG(dataDuration) as avg_duration,
       COUNT(DISTINCT dataName) as unique_channels
FROM merged_telemetric_ott
WHERE whoisCountry IS NOT NULL
GROUP BY whoisCountry
ORDER BY total_views DESC
```

**Impacto:**
- **Segmentación**: Crear estrategias específicas por segmento
- **Personalización**: Personalizar experiencia por segmento
- **Marketing**: Campañas segmentadas más efectivas
- **Expansión**: Identificar segmentos con potencial de crecimiento

---

## 🔬 Análisis Avanzados

### 19. Análisis de Correlaciones

**¿En qué consiste?**
- Identificar correlaciones entre diferentes variables
- Correlación entre hora y canal preferido
- Correlación entre dispositivo y duración de visualización
- Correlación entre país y preferencias de contenido

**¿Cómo se calcula?**
```sql
-- Correlación hora-canal
SELECT timeDate, dataName, COUNT(*) as views
FROM merged_telemetric_ott
WHERE timeDate IS NOT NULL AND dataName IS NOT NULL
GROUP BY timeDate, dataName
ORDER BY timeDate, views DESC
```

**Impacto:**
- **Insights**: Descubrir patrones ocultos en los datos
- **Predicción**: Mejorar predicciones basadas en correlaciones
- **Optimización**: Optimizar múltiples variables simultáneamente
- **Estrategia**: Decisiones basadas en relaciones complejas

---

### 20. Análisis Predictivo (Series Temporales)

**Función implementada:** `get_time_series_analysis(channel=None, start_date=None, end_date=None, forecast_days=7)`

**¿En qué consiste?**
- Predicción de consumo futuro basado en patrones históricos
- Análisis de tendencias temporales con regresión lineal
- Pronóstico simple usando media móvil y extrapolación de tendencia

**¿Cómo se calcula?**
- **Implementación:** Usa Pandas y NumPy para análisis de series temporales
- **Proceso:**
  1. Agrupa datos por día (`dataDate`)
  2. Calcula media móvil de 7 días
  3. Calcula tendencia lineal usando regresión (`np.polyfit`)
  4. Genera pronóstico extrapolando la tendencia

**Retorna:**
```python
{
    "historical_data": [
        {
            "dataDate": "2025-01-01",
            "views": 5000,
            "moving_avg_7d": 4800.0,  # Media móvil de 7 días
            "trend": 4950.0  # Valor de la línea de tendencia
        },
        ...
    ],
    "forecast": [
        {
            "dataDate": "2025-01-08",
            "forecast": 5200.0,  # Pronóstico basado en tendencia
            "moving_avg_forecast": 5000.0  # Última media móvil
        },
        ...
    ],
    "statistics": {
        "mean": 5000.0,  # Promedio de visualizaciones diarias
        "std": 500.2,  # Desviación estándar
        "trend_slope": 50.5,  # Pendiente de la tendencia (cambio por día)
        "trend_direction": "creciente"  # "creciente", "decreciente", o "estable"
    },
    "channel": "Canal Premium"  # O "Todos los canales" si channel es None
}
```

**Notas:**
- ⚠️ **Requiere Pandas/NumPy** - Si no están instalados, lanza `ImportError`
- `forecast_days` por defecto es 7 (puede ajustarse)
- Si se proporciona `channel`, filtra solo ese canal
- Si no hay datos, retorna: `{"message": "No hay datos para análisis de series temporales"}`

**Impacto:**
- **Planificación**: Anticipar demanda futura
- **Inversión**: Decidir inversiones en contenido basado en predicciones
- **Recursos**: Dimensionar infraestructura según predicciones
- **Ventaja competitiva**: Anticipar tendencias del mercado

---

### 21. Análisis de Anomalías

**Función implementada:** `get_anomaly_detection(threshold_std=3.0, start_date=None, end_date=None)`

**¿En qué consiste?**
- Detección de patrones inusuales o anómalos en el consumo
- Identificación de picos anómalos de consumo
- Detección de posibles problemas técnicos o fraude

**¿Cómo se calcula?**
- **Implementación:** Usa Raw SQL con CTEs y STDDEV_POP/STDDEV_SAMP
- **Consulta equivalente:**
```sql
-- Detectar picos anómalos (consumo > threshold_std desviaciones estándar)
WITH daily_counts AS (
    SELECT dataDate, COUNT(*) as daily_views
    FROM merged_telemetric_ott
    WHERE dataDate IS NOT NULL
    GROUP BY dataDate
),
stats AS (
    SELECT 
        AVG(daily_views) as avg_views,
        STDDEV_SAMP(daily_views) as stddev_views  -- STDDEV_SAMP en MySQL
    FROM daily_counts
)
SELECT dc.dataDate, dc.daily_views,
       s.avg_views as average_views,
       s.stddev_views as standard_deviation,
       ROUND((dc.daily_views - s.avg_views) / NULLIF(s.stddev_views, 0), 2) as z_score
FROM daily_counts dc
CROSS JOIN stats s
WHERE dc.daily_views > (s.avg_views + threshold_std * s.stddev_views)
ORDER BY dc.daily_views DESC
```

**Retorna:**
```python
[
    {
        "dataDate": "2025-01-15",  # date object
        "daily_views": 10000,  # Count de registros ese día
        "average_views": 5000.0,  # Promedio de visualizaciones diarias
        "standard_deviation": 1000.0,  # Desviación estándar
        "z_score": 5.0  # Z-score redondeado a 2 decimales
    },
    ...
]
```

**Notas:**
- ⚠️ **Requiere MySQL 8.0+ / MariaDB 10.2+** para CTEs y STDDEV
- `threshold_std` por defecto es 3.0 (puede ajustarse)
- En MySQL usa `STDDEV_SAMP` (ajustado automáticamente en el código)
- En SQLite usa `STDDEV` (ajustado automáticamente en el código)
- Solo retorna días donde `z_score > threshold_std`

**Impacto:**
- **Seguridad**: Detectar uso fraudulento o abusivo
- **Calidad**: Identificar problemas técnicos rápidamente
- **Optimización**: Corregir problemas antes de que afecten a más usuarios
- **Costos**: Prevenir costos innecesarios por anomalías

---

### 22. Análisis de Cohortes

**Función implementada:** `get_cohort_analysis_pandas(start_date=None, end_date=None)`

**¿En qué consiste?**
- Análisis de comportamiento de grupos de usuarios por fecha de inicio
- Evolución del comportamiento de consumo por cohorte
- Comparación de retención entre diferentes cohortes

**¿Cómo se calcula?**
- **Implementación:** Usa Pandas para análisis de cohortes
- **Consulta equivalente (concepto):**
```sql
-- Cohortes por mes de primer uso (concepto, implementado con Pandas)
-- Se agrupa por subscriberCode y se calcula el mes de primera actividad
-- Luego se analiza comportamiento por cohorte y período
```

**Retorna:**
```python
{
    "data": [
        {
            "cohort_month": "2024-12",  # Período de la cohorte
            "period": "2025-01",  # Período de análisis
            "subscriberCode": 500,  # Usuarios únicos en ese período
            "dataName": 25,  # Canales únicos
            "dataDuration": 1250000.0,  # Tiempo total en segundos
            "cohort_size": 1000,  # Tamaño inicial de la cohorte
            "retention_rate": 50.0  # Porcentaje de retención
        },
        ...
    ],
    "summary": {
        "total_cohorts": 12,
        "total_users": 5000
    }
}
```

**Notas:**
- ⚠️ **Requiere Pandas/NumPy** - Si no están instalados, lanza `ImportError`
- Usa Pandas para agrupar usuarios por mes de primera actividad
- Calcula retención como: `(usuarios activos en período / tamaño inicial de cohorte) * 100`
- Solo incluye usuarios donde `subscriberCode` y `timestamp` no son `None`

**Impacto:**
- **Retención**: Entender cómo evoluciona la retención por cohorte
- **Adquisición**: Mejorar estrategias de adquisición basadas en cohortes
- **LTV**: Calcular valor de vida del cliente por cohorte
- **Mejora continua**: Aprender de cohortes exitosas

---

## 💼 Análisis de Negocio

### 23. Análisis de Ingresos (dataPrice)

**¿En qué consiste?**
- Cálculo de ingresos generados por canal
- Análisis de monetización por contenido
- ROI por canal o tipo de contenido

**¿Cómo se calcula?**
```sql
SELECT dataName,
       COUNT(*) as total_views,
       SUM(dataPrice) as total_revenue,
       AVG(dataPrice) as avg_price_per_view
FROM merged_telemetric_ott
WHERE dataPrice IS NOT NULL AND dataName IS NOT NULL
GROUP BY dataName
ORDER BY total_revenue DESC
```

**Impacto:**
- **Monetización**: Optimizar estrategias de monetización
- **Pricing**: Ajustar precios basado en demanda y valor percibido
- **ROI**: Medir retorno de inversión por canal
- **Decisiones**: Decidir qué contenido adquirir o producir

---

### 24. Análisis de Engagement

**¿En qué consiste?**
- Métricas de engagement por canal (tiempo total, frecuencia, retención)
- Identificación de contenido altamente engaging
- Análisis de factores que aumentan engagement

**¿Cómo se calcula?**
```sql
SELECT dataName,
       COUNT(*) as total_views,
       SUM(dataDuration) as total_watch_time,
       COUNT(DISTINCT subscriberCode) as unique_users,
       AVG(dataDuration) as avg_duration,
       COUNT(*) * 1.0 / COUNT(DISTINCT subscriberCode) as views_per_user
FROM merged_telemetric_ott
WHERE dataName IS NOT NULL
GROUP BY dataName
ORDER BY total_watch_time DESC
```

**Impacto:**
- **Contenido**: Identificar qué contenido genera más engagement
- **Estrategia**: Enfocar recursos en contenido de alto engagement
- **Retención**: Engagement alto = mayor retención de usuarios
- **Crecimiento**: Contenido engaging atrae nuevos usuarios

---

### 25. Análisis de Satisfacción

**¿En qué consiste?**
- Indicadores de satisfacción basados en duración de visualización
- Canales con mayor satisfacción de usuarios
- Factores que correlacionan con satisfacción

**¿Cómo se calcula?**
```sql
SELECT dataName,
       AVG(dataDuration) as avg_duration,
       COUNT(*) as total_views,
       COUNT(CASE WHEN dataDuration > 1800 THEN 1 END) * 100.0 / COUNT(*) as satisfaction_rate
FROM merged_telemetric_ott
WHERE dataName IS NOT NULL AND dataDuration IS NOT NULL
GROUP BY dataName
ORDER BY satisfaction_rate DESC
```

**Impacto:**
- **Calidad**: Mejorar calidad de contenido basado en satisfacción
- **Retención**: Satisfacción alta = menor churn
- **Recomendaciones**: Recomendar contenido con alta satisfacción
- **Reputación**: Construir reputación basada en satisfacción del usuario

---

## 📈 Métricas Clave Recomendadas (KPIs)

### Métricas de Consumo
- **Total de visualizaciones**: Número total de reproducciones
- **Tiempo total de visualización**: Suma de todas las duraciones
- **Duración promedio**: Tiempo promedio por sesión
- **Usuarios activos**: Dispositivos/usuarios únicos

### Métricas de Engagement
- **Sesiones por usuario**: Frecuencia de uso
- **Canales únicos por usuario**: Diversidad de consumo
- **Tasa de retención**: Porcentaje de usuarios que vuelven
- **Tiempo de sesión promedio**: Duración promedio de sesión

### Métricas de Negocio
- **Ingresos por canal**: Monetización por contenido
- **Costo por adquisición**: Costo de adquirir nuevos usuarios
- **LTV (Lifetime Value)**: Valor de vida del cliente
- **Churn rate**: Tasa de cancelación

---

## 🎯 Priorización de Análisis

### Alta Prioridad (Impacto Inmediato)
1. **Top Canales Más Vistos** - Estrategia de contenido
2. **Análisis por Fecha** - Planificación y capacidad
3. **Duración Promedio por Canal** - Calidad de contenido
4. **Análisis de Engagement** - Retención y crecimiento

### Media Prioridad (Impacto a Mediano Plazo)
5. **Horarios Pico por Canal** - Optimización de recursos
6. **Análisis por Dispositivo** - Desarrollo y soporte
7. **Análisis de Retención** - Fidelización
8. **Comparación entre Canales** - Estrategia competitiva

### Baja Prioridad (Impacto a Largo Plazo)
9. **Análisis Predictivo** - Planificación avanzada
10. **Análisis de Cohortes** - Optimización continua
11. **Análisis de Correlaciones** - Insights avanzados
12. **Análisis de Anomalías** - Seguridad y calidad

---

## 📝 Notas de Implementación

- Todos los análisis deben considerar filtros por rango de fechas
- Los análisis deben ser ejecutables de forma eficiente (usar índices)
- Considerar agregar caché para análisis frecuentes
- Implementar paginación para resultados grandes
- Exportar resultados a formatos estándar (CSV, JSON, Excel)

---

## 🚀 Optimizaciones para MySQL/MariaDB

### Índices Recomendados

Las consultas están optimizadas para aprovechar los siguientes índices (ya creados en el modelo Django):

Los índices se crean automáticamente mediante las migraciones de Django. Los índices definidos en `MergedTelemetricOTTDelancer` son:

- `idx_ott_actionid_timestamp`: Para filtros por actionId y timestamp
- `idx_ott_datadate_timedate`: Para análisis por fecha y hora
- `idx_ott_dataname`: Para agrupaciones por canal
- `idx_ott_deviceid_datadate`: Para análisis por dispositivo
- `idx_ott_recordid`: Para búsquedas por recordId

### Índices Adicionales Recomendados para MySQL/MariaDB

```sql
-- Índice compuesto para análisis de usuarios (MySQL 8.0+ / MariaDB 10.2+)
CREATE INDEX idx_ott_subscriber_datadate ON merged_telemetric_ott(subscriberCode, dataDate);

-- Índice para análisis geográfico
CREATE INDEX idx_ott_country_isp ON merged_telemetric_ott(whoisCountry, whoisIsp);

-- Índice para análisis de duración
CREATE INDEX idx_ott_duration_dataname ON merged_telemetric_ott(dataDuration, dataName);
```

**Nota:** MySQL/MariaDB no soportan índices parciales (con WHERE) como PostgreSQL, pero los índices compuestos funcionan bien.

### Ventajas de MySQL 8.0+ / MariaDB 10.2+

1. **Mejor Optimización de Consultas**
   - Optimizador mejorado en versiones recientes
   - Mejor uso de índices múltiples
   - Estadísticas de tablas para optimización

2. **Funciones de Ventana (Window Functions)**
   - `LAG()`, `LEAD()`, `ROW_NUMBER()` disponibles desde MySQL 8.0+ / MariaDB 10.2+
   - Mejor rendimiento en agregaciones complejas
   - Compatible con estándar SQL

3. **CTEs (Common Table Expressions)**
   - Disponibles desde MySQL 8.0+ / MariaDB 10.2+
   - Mejor legibilidad y mantenibilidad
   - Optimización automática por el optimizador

4. **Tipos de Datos**
   - Tipos de fecha/hora precisos
   - JSON nativo (MySQL 5.7+ / MariaDB 10.2+)
   - Mejor manejo de NULLs

5. **Concurrencia**
   - Buen manejo de múltiples usuarios simultáneos
   - Transacciones robustas
   - Locking eficiente

### Mejores Prácticas para MySQL/MariaDB

1. **Usar EXPLAIN**
   ```sql
   EXPLAIN SELECT ...;
   ```
   - Verificar que se usen los índices correctos
   - Identificar cuellos de botella
   - MySQL 8.0+ incluye `EXPLAIN ANALYZE` (similar a PostgreSQL)

2. **ANALYZE TABLE Regular**
   ```sql
   ANALYZE TABLE merged_telemetric_ott;
   ```
   - Mantener estadísticas actualizadas
   - Mejorar rendimiento del optimizador

3. **Particionamiento (Para Tablas Muy Grandes)**
   - Particionar por `dataDate` si la tabla crece mucho
   - Mejora significativa en consultas por rango de fechas
   - Disponible en MySQL 5.7+ / MariaDB 10.0+

4. **Usar Cache para Análisis Frecuentes**
   - El sistema ya implementa cache con Redis
   - Los resultados de análisis se cachean automáticamente
   - Ver `TelemetriaDelancer/mixins.py` para detalles

### Compatibilidad SQLite vs MySQL/MariaDB

| Función | SQLite | MySQL 8.0+ / MariaDB 10.2+ | Nota |
|---------|--------|---------------------------|------|
| Formato fecha | `strftime('%Y-%m', date)` | `DATE_FORMAT(date, '%Y-%m')` o `YEAR(date), MONTH(date)` | MySQL más eficiente |
| Desviación estándar | `STDDEV()` | `STDDEV_SAMP()` o `STDDEV_POP()` | MySQL más preciso |
| Funciones ventana | Limitado | Completo (8.0+) | MySQL 8.0+ mucho mejor |
| CTEs | Básico | Avanzado (8.0+) | MySQL 8.0+ optimiza mejor |
| Índices parciales | No | No | Solo PostgreSQL soporta WHERE en índices |

### Notas de Implementación

Todas las consultas en este documento están optimizadas para MySQL 8.0+ / MariaDB 10.2+. Para versiones anteriores:

- Reemplazar funciones de ventana por subconsultas
- Reemplazar `STDDEV_POP()` por `STDDEV_SAMP()` o cálculos manuales
- Simplificar CTEs si es necesario
- Usar principalmente Django ORM (funciona en todas las versiones)

---

**Documento creado:** 2025-12-31  
**Última actualización:** 2025-12-31  
**Versión:** 1.2 (Optimizado para MySQL 8.0+ / MariaDB 10.2+)

