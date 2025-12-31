# Análisis de Telemetría OTT - MergedTelemetricOTT

> **Nota de Compatibilidad:** Las consultas SQL en este documento están optimizadas para **PostgreSQL** (migración futura). Son compatibles con SQLite para desarrollo, pero funcionarán mejor en PostgreSQL gracias a:
> - Mejor optimización de índices
> - Funciones de ventana (window functions) más eficientes
> - Mejor manejo de agregaciones complejas
> - Soporte nativo para tipos de datos avanzados

## 📋 Índice

1. [Análisis de Consumo por Canal](#análisis-de-consumo-por-canal)
2. [Análisis Temporal](#análisis-temporal)
3. [Análisis por Dispositivo](#análisis-por-dispositivo)
4. [Análisis Geográfico](#análisis-geográfico)
5. [Análisis de Comportamiento](#análisis-de-comportamiento)
6. [Análisis Comparativos](#análisis-comparativos)
7. [Análisis Avanzados](#análisis-avanzados)
8. [Análisis de Negocio](#análisis-de-negocio)

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

**¿En qué consiste?**
- Número de dispositivos únicos que consumen cada canal
- Número de usuarios únicos (subscriberCode/smartcardId) por canal
- Tasa de penetración de cada canal en la base de usuarios

**¿Cómo se calcula?**
```sql
SELECT dataName,
       COUNT(DISTINCT deviceId) as unique_devices,
       COUNT(DISTINCT subscriberCode) as unique_users,
       COUNT(*) as total_views
FROM merged_telemetric_ott
WHERE dataName IS NOT NULL
GROUP BY dataName
```

**Impacto:**
- **Diversificación**: Identificar si un canal tiene muchos views pero pocos usuarios (dependencia)
- **Crecimiento**: Canales con alto potencial de crecimiento de audiencia
- **Retención**: Canales que atraen nuevos usuarios vs. canales que retienen existentes
- **Segmentación**: Entender qué canales atraen a qué tipo de usuarios

---

### 3. Horarios Pico por Canal

**¿En qué consiste?**
- Identificar las franjas horarias (timeDate) con mayor consumo para cada canal
- Patrones diarios de visualización por canal
- Comparación de horarios pico entre diferentes canales

**¿Cómo se calcula?**
```sql
SELECT dataName, timeDate, COUNT(*) as views
FROM merged_telemetric_ott
WHERE dataName IS NOT NULL AND timeDate IS NOT NULL
GROUP BY dataName, timeDate
ORDER BY dataName, views DESC
```

**Impacto:**
- **Programación**: Optimizar horarios de programación especial
- **Publicidad**: Maximizar impacto publicitario en horarios pico
- **Recursos**: Asignar recursos de servidor/CDN según demanda horaria
- **Contenido**: Programar estrenos y contenido premium en horarios de mayor audiencia

---

### 4. Duración Promedio por Canal

**¿En qué consiste?**
- Tiempo promedio de visualización (dataDuration) por canal
- Comparación de duración entre diferentes canales
- Identificación de canales con mayor retención de audiencia

**¿Cómo se calcula?**
```sql
SELECT dataName,
       AVG(dataDuration) as avg_duration_seconds,
       AVG(dataDuration) / 60.0 as avg_duration_minutes,
       COUNT(*) as total_sessions
FROM merged_telemetric_ott
WHERE dataName IS NOT NULL AND dataDuration IS NOT NULL
GROUP BY dataName
ORDER BY avg_duration_seconds DESC
```

**Impacto:**
- **Calidad de contenido**: Canales con mayor duración indican mejor contenido
- **Satisfacción**: Duración como indicador de satisfacción del usuario
- **Monetización**: Canales con mayor duración = más oportunidades publicitarias
- **Renovación de contenido**: Identificar canales que necesitan mejor contenido

---

## ⏰ Análisis Temporal

### 5. Análisis por Fecha (dataDate)

**¿En qué consiste?**
- Consumo diario, semanal y mensual de contenido OTT
- Identificación de tendencias temporales
- Comparación de consumo entre diferentes períodos (días, semanas, meses)

**¿Cómo se calcula?**
```sql
-- Diario
SELECT dataDate, COUNT(*) as daily_views
FROM merged_telemetric_ott
GROUP BY dataDate
ORDER BY dataDate DESC

-- Semanal (PostgreSQL optimizado)
SELECT DATE_TRUNC('week', dataDate) as week, COUNT(*) as weekly_views
FROM merged_telemetric_ott
WHERE dataDate IS NOT NULL
GROUP BY DATE_TRUNC('week', dataDate)
ORDER BY week DESC

-- Mensual (PostgreSQL optimizado)
SELECT DATE_TRUNC('month', dataDate) as month, COUNT(*) as monthly_views
FROM merged_telemetric_ott
WHERE dataDate IS NOT NULL
GROUP BY DATE_TRUNC('month', dataDate)
ORDER BY month DESC

-- Alternativa SQLite (para desarrollo)
-- SELECT strftime('%Y-W%W', dataDate) as week, COUNT(*) as weekly_views
-- SELECT strftime('%Y-%m', dataDate) as month, COUNT(*) as monthly_views
```

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

**¿En qué consiste?**
- Distribución de consumo de contenido por país
- Canales más populares por región geográfica
- Patrones de consumo regionales

**¿Cómo se calcula?**
```sql
SELECT whoisCountry,
       COUNT(*) as total_views,
       COUNT(DISTINCT dataName) as unique_channels,
       COUNT(DISTINCT deviceId) as unique_devices
FROM merged_telemetric_ott
WHERE whoisCountry IS NOT NULL
GROUP BY whoisCountry
ORDER BY total_views DESC
```

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

**¿En qué consiste?**
- Comparación de consumo día a día, semana a semana, mes a mes
- Identificación de tendencias y patrones temporales
- Análisis de crecimiento o declive

**¿Cómo se calcula?**
```sql
-- Comparación día a día (PostgreSQL optimizado con CTE)
WITH daily_stats AS (
    SELECT dataDate, COUNT(*) as daily_views
    FROM merged_telemetric_ott
    WHERE dataDate IS NOT NULL
    GROUP BY dataDate
)
SELECT dataDate,
       daily_views,
       LAG(daily_views) OVER (ORDER BY dataDate) as previous_day_views,
       daily_views - LAG(daily_views) OVER (ORDER BY dataDate) as day_over_day_change,
       ROUND(
           ((daily_views - LAG(daily_views) OVER (ORDER BY dataDate))::numeric / 
            NULLIF(LAG(daily_views) OVER (ORDER BY dataDate), 0)) * 100, 
           2
       ) as day_over_day_percentage
FROM daily_stats
ORDER BY dataDate DESC
```

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

### 20. Análisis Predictivo

**¿En qué consiste?**
- Predicción de consumo futuro basado en patrones históricos
- Predicción de canales que serán populares
- Predicción de horarios pico futuros

**¿Cómo se calcula?**
- Requiere modelos de machine learning o análisis estadístico avanzado
- Basado en tendencias temporales, estacionalidad, y patrones históricos

**Impacto:**
- **Planificación**: Anticipar demanda futura
- **Inversión**: Decidir inversiones en contenido basado en predicciones
- **Recursos**: Dimensionar infraestructura según predicciones
- **Ventaja competitiva**: Anticipar tendencias del mercado

---

### 21. Análisis de Anomalías

**¿En qué consiste?**
- Detección de patrones inusuales o anómalos en el consumo
- Identificación de picos anómalos de consumo
- Detección de posibles problemas técnicos o fraude

**¿Cómo se calcula?**
```sql
-- Detectar picos anómalos (consumo > 3 desviaciones estándar) - PostgreSQL optimizado
WITH daily_counts AS (
    SELECT dataDate, COUNT(*) as daily_views
    FROM merged_telemetric_ott
    WHERE dataDate IS NOT NULL
    GROUP BY dataDate
),
stats AS (
    SELECT 
        AVG(daily_views) as avg_views,
        STDDEV_POP(daily_views) as stddev_views
    FROM daily_counts
)
SELECT dc.dataDate, dc.daily_views,
       s.avg_views as average_views,
       s.stddev_views as standard_deviation,
       ROUND((dc.daily_views - s.avg_views) / NULLIF(s.stddev_views, 0), 2) as z_score
FROM daily_counts dc
CROSS JOIN stats s
WHERE dc.daily_views > (s.avg_views + 3 * s.stddev_views)
ORDER BY dc.daily_views DESC
```

**Impacto:**
- **Seguridad**: Detectar uso fraudulento o abusivo
- **Calidad**: Identificar problemas técnicos rápidamente
- **Optimización**: Corregir problemas antes de que afecten a más usuarios
- **Costos**: Prevenir costos innecesarios por anomalías

---

### 22. Análisis de Cohortes

**¿En qué consiste?**
- Análisis de comportamiento de grupos de usuarios por fecha de inicio
- Evolución del comportamiento de consumo por cohorte
- Comparación de retención entre diferentes cohortes

**¿Cómo se calcula?**
```sql
-- Cohortes por mes de primer uso (PostgreSQL optimizado)
WITH user_first_view AS (
    SELECT 
        subscriberCode,
        DATE_TRUNC('month', MIN(timestamp)) as cohort_month,
        COUNT(*) as total_views,
        COUNT(DISTINCT dataName) as unique_channels,
        SUM(dataDuration) as total_watch_time
    FROM merged_telemetric_ott
    WHERE subscriberCode IS NOT NULL AND timestamp IS NOT NULL
    GROUP BY subscriberCode
)
SELECT 
    TO_CHAR(cohort_month, 'YYYY-MM') as cohort_month,
    COUNT(DISTINCT subscriberCode) as cohort_size,
    AVG(total_views) as avg_views_per_user,
    AVG(unique_channels) as avg_channels_per_user,
    AVG(total_watch_time) as avg_watch_time_per_user
FROM user_first_view
GROUP BY cohort_month
ORDER BY cohort_month DESC
```

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

## 🚀 Optimizaciones para PostgreSQL

### Índices Recomendados

Las consultas están optimizadas para aprovechar los siguientes índices (ya creados en el modelo):

```sql
-- Índices existentes en MergedTelemetricOTT
CREATE INDEX idx_ott_actionid_timestamp ON merged_telemetric_ott(actionId, timestamp);
CREATE INDEX idx_ott_datadate_timedate ON merged_telemetric_ott(dataDate, timeDate);
CREATE INDEX idx_ott_dataname ON merged_telemetric_ott(dataName);
CREATE INDEX idx_ott_deviceid_datadate ON merged_telemetric_ott(deviceId, dataDate);
CREATE INDEX idx_ott_recordid ON merged_telemetric_ott(recordId);
```

### Índices Adicionales Recomendados para PostgreSQL

```sql
-- Índice compuesto para análisis de usuarios
CREATE INDEX idx_ott_subscriber_datadate ON merged_telemetric_ott(subscriberCode, dataDate) 
WHERE subscriberCode IS NOT NULL;

-- Índice para análisis geográfico
CREATE INDEX idx_ott_country_isp ON merged_telemetric_ott(whoisCountry, whoisIsp) 
WHERE whoisCountry IS NOT NULL;

-- Índice para análisis de duración
CREATE INDEX idx_ott_duration_dataname ON merged_telemetric_ott(dataDuration, dataName) 
WHERE dataDuration IS NOT NULL AND dataName IS NOT NULL;

-- Índice parcial para actionId=8 (mayoría de registros)
CREATE INDEX idx_ott_action8_datadate ON merged_telemetric_ott(dataDate, dataName) 
WHERE actionId = 8;
```

### Ventajas de PostgreSQL sobre SQLite

1. **Mejor Optimización de Consultas**
   - Planner más avanzado que optimiza automáticamente
   - Mejor uso de índices múltiples
   - Estadísticas más precisas para optimización

2. **Funciones de Ventana (Window Functions)**
   - `LAG()`, `LEAD()`, `ROW_NUMBER()` más eficientes
   - Particionamiento avanzado
   - Mejor rendimiento en agregaciones complejas

3. **CTEs (Common Table Expressions)**
   - Materialización automática cuando es beneficioso
   - Mejor legibilidad y mantenibilidad
   - Optimización automática por el planner

4. **Tipos de Datos Avanzados**
   - Tipos de fecha/hora más precisos
   - Arrays y JSON nativos
   - Mejor manejo de NULLs

5. **Concurrencia**
   - Mejor manejo de múltiples usuarios simultáneos
   - Transacciones más robustas
   - Locking más eficiente

### Mejores Prácticas para PostgreSQL

1. **Usar EXPLAIN ANALYZE**
   ```sql
   EXPLAIN ANALYZE SELECT ...;
   ```
   - Verificar que se usen los índices correctos
   - Identificar cuellos de botella

2. **VACUUM y ANALYZE Regular**
   ```sql
   VACUUM ANALYZE merged_telemetric_ott;
   ```
   - Mantener estadísticas actualizadas
   - Mejorar rendimiento del planner

3. **Particionamiento (Para Tablas Muy Grandes)**
   - Particionar por `dataDate` si la tabla crece mucho
   - Mejora significativa en consultas por rango de fechas

4. **Materialized Views (Para Análisis Frecuentes)**
   ```sql
   CREATE MATERIALIZED VIEW mv_top_channels AS
   SELECT dataName, COUNT(*) as total_views
   FROM merged_telemetric_ott
   GROUP BY dataName;
   
   CREATE UNIQUE INDEX ON mv_top_channels(dataName);
   REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_channels;
   ```

### Compatibilidad SQLite vs PostgreSQL

| Función | SQLite | PostgreSQL | Nota |
|---------|--------|------------|------|
| Formato fecha | `strftime('%Y-%m', date)` | `TO_CHAR(date, 'YYYY-MM')` o `DATE_TRUNC('month', date)` | PostgreSQL más eficiente |
| Desviación estándar | `STDDEV()` | `STDDEV_POP()` o `STDDEV_SAMP()` | PostgreSQL más preciso |
| Funciones ventana | Limitado | Completo | PostgreSQL mucho mejor |
| CTEs | Básico | Avanzado | PostgreSQL optimiza mejor |
| Índices parciales | No | Sí | PostgreSQL permite `WHERE` en índices |

### Migración de Consultas

Todas las consultas en este documento están escritas para PostgreSQL. Para usar en SQLite durante desarrollo:

- Reemplazar `DATE_TRUNC()` por `strftime()`
- Reemplazar `STDDEV_POP()` por `STDDEV()`
- Simplificar CTEs complejas si es necesario
- Las funciones de ventana básicas funcionan en ambos

---

**Documento creado:** 2025-12-31  
**Última actualización:** 2025-12-31  
**Versión:** 1.1 (Optimizado para PostgreSQL)

