# Estrategia de Análisis - Telemetría OTT

## 📊 Enfoque Híbrido Recomendado

Este documento explica la estrategia de análisis implementada para el sistema de telemetría OTT.

---

## 🎯 Decisión: ¿Librerías o Solo Funciones?

**Respuesta: Enfoque Híbrido Inteligente**

No usamos una sola librería para todo. En su lugar, elegimos la mejor herramienta para cada tipo de análisis:

### 1. **Django ORM + Funciones Python** (80% de los casos)
- ✅ **Para:** Análisis simples y medianos
- ✅ **Ventajas:**
  - Aprovecha índices de base de datos automáticamente
  - Muy eficiente en memoria (no carga todo en RAM)
  - Integrado con Django (sin dependencias extra)
   - Funciona perfectamente con MySQL/MariaDB
  - Fácil de mantener y depurar

- 📋 **Ejemplos de uso:**
  - Top canales más vistos
  - Análisis por fecha (diario, semanal, mensual)
  - Estadísticas básicas (promedios, sumas, conteos)
  - Análisis geográfico
  - Agrupaciones simples

### 2. **Raw SQL Optimizado** (15% de los casos)
- ✅ **Para:** Análisis complejos que requieren funciones avanzadas
- ✅ **Ventajas:**
  - Funciones de ventana (LAG, LEAD, ROW_NUMBER) - MySQL 8.0+/MariaDB 10.2+
  - CTEs (Common Table Expressions) complejas - MySQL 8.0+/MariaDB 10.2+
  - Optimización manual para MySQL/MariaDB
  - Máximo rendimiento en consultas complejas

- 📋 **Ejemplos de uso:**
  - Comparación día a día (day-over-day)
  - Detección de anomalías con desviación estándar
  - Análisis de tendencias con funciones de ventana
  - Consultas con múltiples niveles de agregación

### 3. **Pandas (Opcional)** (5% de los casos)
- ✅ **Para:** Análisis estadísticos muy avanzados
- ⚠️ **Consideración:** Solo cuando realmente sea necesario
- ✅ **Ventajas:**
  - Análisis estadísticos complejos
  - Transformaciones de datos avanzadas
  - Exportación fácil a Excel/CSV
  - Visualizaciones (con matplotlib/plotly)

- 📋 **Ejemplos de uso:**
  - Análisis de cohortes complejos
  - Correlaciones entre múltiples variables
  - Series temporales con forecasting
  - Análisis de regresión

---

## 📦 Dependencias

### Requeridas (Ya instaladas)
- Django ORM (incluido en Django)
- MySQL/MariaDB driver (mysqlclient - ya instalado)

### Opcionales (Solo si necesitas análisis avanzados)
```bash
pip install pandas  # Para análisis estadísticos avanzados
pip install numpy   # Dependencia de pandas
```

---

## 🏗️ Arquitectura del Módulo de Análisis

```
TelemetriaDelancer/panaccess/analytics.py
├── Análisis Simples (Django ORM)
│   ├── get_top_channels()
│   ├── get_channel_audience()
│   ├── get_peak_hours_by_channel()
│   ├── get_average_duration_by_channel()
│   └── get_temporal_analysis()
│
├── Análisis Complejos (Raw SQL)
│   ├── get_day_over_day_comparison()
│   └── get_anomaly_detection()
│
└── Análisis Avanzados (Pandas - Opcional)
    └── get_cohort_analysis_pandas()
```

---

## 💡 ¿Por Qué Este Enfoque?

### Ventajas del Enfoque Híbrido

1. **Rendimiento Óptimo**
   - Django ORM usa índices automáticamente
   - Raw SQL permite optimización manual
   - Pandas solo cuando es absolutamente necesario

2. **Escalabilidad**
   - No carga toda la tabla en memoria (Django ORM)
   - MySQL/MariaDB hace el trabajo pesado
   - Pandas solo para análisis puntuales

3. **Mantenibilidad**
   - Código claro y fácil de entender
   - Separación de responsabilidades
   - Fácil de testear

4. **Flexibilidad**
   - Puedes agregar pandas después si lo necesitas
   - No estás atado a una sola librería
   - Compatible con MySQL/MariaDB (producción) y SQLite (desarrollo)

---

## 🚀 Ejemplos de Uso

### Ejemplo 1: Análisis Simple (Django ORM)
```python
from TelemetriaDelancer.panaccess.analytics import get_top_channels

# Top 10 canales más vistos
top_channels = get_top_channels(limit=10)
# Resultado: Lista de dicts con channel, total_views, percentage
```

### Ejemplo 2: Análisis Complejo (Raw SQL)
```python
from TelemetriaDelancer.panaccess.analytics import get_day_over_day_comparison
from datetime import datetime, timedelta

# Comparación día a día de los últimos 30 días
end_date = datetime.now()
start_date = end_date - timedelta(days=30)
comparison = get_day_over_day_comparison(start_date, end_date)
# Resultado: Lista con daily_views, previous_day_views, day_over_day_change
```

### Ejemplo 3: Análisis Avanzado (Pandas - Opcional)
```python
from TelemetriaDelancer.panaccess.analytics import get_cohort_analysis_pandas

# Análisis de cohortes (requiere pandas)
try:
    cohort_data = get_cohort_analysis_pandas()
except ImportError:
    print("Pandas no está instalado. Instala con: pip install pandas")
```

---

## 📈 Rendimiento Esperado

### Con Django ORM (Análisis Simples)
- **Tiempo:** < 1 segundo para 223K registros
- **Memoria:** Mínima (solo resultados agregados)
- **Índices:** Aprovechados automáticamente

### Con Raw SQL (Análisis Complejos)
- **Tiempo:** 1-5 segundos para 223K registros
- **Memoria:** Mínima (MySQL/MariaDB hace el trabajo)
- **Optimización:** Manual pero muy eficiente (requiere MySQL 8.0+ o MariaDB 10.2+ para funciones de ventana)

### Con Pandas (Análisis Avanzados)
- **Tiempo:** 5-30 segundos (depende de la complejidad)
- **Memoria:** Media-Alta (carga datos en RAM)
- **Uso:** Solo cuando es absolutamente necesario

---

## 🔄 Requisitos de Base de Datos

### Versiones Recomendadas

**MySQL 8.0+ o MariaDB 10.2+** (Recomendado para producción)

1. **Funciones Avanzadas Disponibles**
   - CTEs (Common Table Expressions) - MySQL 8.0+ / MariaDB 10.2+
   - Funciones de ventana (LAG, LEAD, ROW_NUMBER) - MySQL 8.0+ / MariaDB 10.2+
   - Mejor optimización de consultas complejas

2. **Rendimiento**
   - Mejor uso de índices múltiples
   - Optimización automática de CTEs
   - Mejor manejo de grandes volúmenes

3. **Escalabilidad**
   - Mejor concurrencia
   - Replicación y sharding disponibles

### Versiones Anteriores

Si usas MySQL 5.7 o MariaDB 10.1 o anteriores:
- Las funciones de ventana (LAG, LEAD) NO estarán disponibles
- Algunas consultas avanzadas pueden fallar
- Se recomienda usar principalmente Django ORM

### Cambios Necesarios

Las consultas están optimizadas para MySQL 8.0+ / MariaDB 10.2+. Para versiones anteriores:

1. **Usar principalmente Django ORM** (funciona en todas las versiones)
2. **Evitar consultas con funciones de ventana** si la versión no las soporta
3. **El driver mysqlclient ya está instalado** (ver requirements.txt)

   La configuración ya está lista en `settings.py` usando `MariaConfig`.

---

## 📝 Recomendaciones

### ✅ Hacer
- Usar Django ORM para análisis simples
- Usar Raw SQL para análisis complejos
- Instalar pandas solo si realmente lo necesitas
- Aprovechar índices de base de datos
- Aprovechar índices compuestos en MySQL/MariaDB para análisis frecuentes

### ❌ Evitar
- Cargar toda la tabla en memoria innecesariamente
- Usar pandas para análisis que se pueden hacer con SQL
- Hacer análisis complejos en Python cuando SQL es más eficiente
- Olvidar usar índices en consultas frecuentes

---

## 🎓 Conclusión

**Estrategia Final:**
- **80% Django ORM** → Rápido, eficiente, integrado
- **15% Raw SQL** → Para análisis complejos optimizados
- **5% Pandas** → Solo cuando sea absolutamente necesario

Esta estrategia te da:
- ✅ Máximo rendimiento
- ✅ Mínima complejidad
- ✅ Fácil mantenimiento
- ✅ Escalabilidad
- ✅ Optimizado para MySQL 8.0+ / MariaDB 10.2+

---

**Documento creado:** 2025-12-31  
**Última actualización:** 2025-12-31  
**Versión:** 1.0

