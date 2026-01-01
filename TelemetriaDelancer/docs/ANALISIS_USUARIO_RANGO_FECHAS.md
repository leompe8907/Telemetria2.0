# Análisis de Usuario/Subscriber con Rango de Fechas

## 📅👤 Descripción

Este módulo (`analytics_user_date_range.py`) proporciona un análisis detallado de un usuario/subscriber específico en un rango de fechas definido. A diferencia del análisis general de usuario, este análisis se enfoca en un período específico y permite comparar el comportamiento del usuario con el promedio general, identificar tendencias y detectar anomalías.

**Ideal para:**
- Análisis de comportamiento en períodos específicos
- Comparación de usuario vs. promedio general
- Detección de anomalías y eventos inusuales
- Análisis de tendencias temporales
- Evaluación de impacto de campañas o eventos

---

## 🎯 Función Disponible

### **`get_user_date_range_analysis(subscriber_code, start_date, end_date)`**

Análisis detallado de un usuario en un rango de fechas específico.

**Parámetros:**
- `subscriber_code` (str, obligatorio): Código del subscriber a analizar
- `start_date` (datetime, obligatorio): Fecha de inicio del período
- `end_date` (datetime, obligatorio): Fecha de fin del período

**Retorna:**
```python
{
    "subscriber_code": "USER001",
    "period": {
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "days": 31
    },
    "period_summary": {
        "total_views": 850,
        "total_hours": 320.5,
        "unique_channels": 12,
        "unique_devices": 2,
        "active_days": 25,
        "avg_duration_seconds": 1356.0
    },
    "temporal_evolution": {
        "daily_activity": [
            {
                "date": "2025-01-01",
                "views": 30,
                "total_hours": 12.5,
                "unique_channels": 5
            },
            {
                "date": "2025-01-02",
                "views": 25,
                "total_hours": 10.2,
                "unique_channels": 4
            },
            ...
        ],
        "trend": "creciente"
    },
    "channels_in_period": [
        {
            "channel": "Canal Premium",
            "views": 250,
            "total_hours": 150.5,
            "active_days": 18
        },
        ...
    ],
    "time_slots_in_period": {
        "madrugada": {
            "total_hours": 40.2,
            "total_views": 100
        },
        "mañana": {
            "total_hours": 60.5,
            "total_views": 150
        },
        "tarde": {
            "total_hours": 100.3,
            "total_views": 300
        },
        "noche": {
            "total_hours": 119.5,
            "total_views": 300
        }
    },
    "comparison_with_average": {
        "user_views": 850,
        "avg_views": 625.5,
        "user_vs_avg_views": 136.0,
        "user_hours": 320.5,
        "avg_hours": 250.2,
        "user_vs_avg_hours": 128.1
    },
    "anomalies": [
        {
            "date": "2025-01-15",
            "total_hours": 25.5,
            "type": "alto",
            "z_score": 2.5
        },
        {
            "date": "2025-01-20",
            "total_hours": 2.1,
            "type": "bajo",
            "z_score": 2.3
        }
    ]
}
```

**Ejemplo de uso:**
```python
from datetime import datetime
from TelemetriaDelancer.panaccess.analytics_user_date_range import get_user_date_range_analysis

start = datetime(2025, 1, 1)
end = datetime(2025, 1, 31)
analysis = get_user_date_range_analysis(
    subscriber_code="USER001",
    start_date=start,
    end_date=end
)
```

---

## 📊 Estructura de la Respuesta

### `subscriber_code`
- **Tipo:** str
- **Descripción:** Código del subscriber analizado
- **Utilidad:** Identificación del usuario

### `period`
Información del período analizado:
- **`start_date`**: Fecha de inicio del período
- **`end_date`**: Fecha de fin del período
- **`days`**: Número de días en el período

**Utilidad:** Contexto del período de análisis.

### `period_summary`
Resumen de métricas del usuario en el período:
- **`total_views`**: Total de visualizaciones en el período
- **`total_hours`**: Total de horas vistas en el período
- **`unique_channels`**: Canales únicos consumidos en el período
- **`unique_devices`**: Dispositivos únicos utilizados en el período
- **`active_days`**: Días activos del usuario en el período
- **`avg_duration_seconds`**: Duración promedio de sesión en segundos

**Utilidad:** Vista general del comportamiento del usuario en el período específico.

### `temporal_evolution`
Evolución temporal del usuario:

#### `daily_activity`
Actividad día por día en el período:
- **`date`**: Fecha del día
- **`views`**: Visualizaciones ese día
- **`total_hours`**: Horas vistas ese día
- **`unique_channels`**: Canales únicos consumidos ese día

**Utilidad:** Visualizar tendencias diarias y patrones de consumo.

#### `trend`
Tendencia general del período:
- **`"creciente"`**: El consumo aumentó en la segunda mitad del período
- **`"decreciente"`**: El consumo disminuyó en la segunda mitad del período
- **`"estable"`**: El consumo se mantuvo similar
- **`"insuficiente_datos"`**: No hay suficientes datos para determinar tendencia

**Utilidad:** Identificar si el usuario está aumentando o disminuyendo su consumo.

### `channels_in_period`
Canales consumidos durante el período:
- **`channel`**: Nombre del canal
- **`views`**: Visualizaciones en ese canal durante el período
- **`total_hours`**: Horas vistas en ese canal durante el período
- **`active_days`**: Días en los que consumió ese canal

**Utilidad:** Entender preferencias de contenido del usuario en el período específico.

### `time_slots_in_period`
Distribución de consumo por franjas horarias en el período:
- **`madrugada`** (00:00 - 05:59)
- **`mañana`** (06:00 - 11:59)
- **`tarde`** (12:00 - 17:59)
- **`noche`** (18:00 - 23:59)

Cada franja incluye:
- **`total_hours`**: Horas vistas en esa franja
- **`total_views`**: Visualizaciones en esa franja

**Utilidad:** Entender patrones horarios del usuario en el período específico.

### `comparison_with_average`
Comparación del usuario con el promedio general (en el mismo período):
- **`user_views`**: Visualizaciones del usuario
- **`avg_views`**: Promedio de visualizaciones de todos los usuarios
- **`user_vs_avg_views`**: Porcentaje del usuario vs. promedio (100% = igual al promedio)
- **`user_hours`**: Horas del usuario
- **`avg_hours`**: Promedio de horas de todos los usuarios
- **`user_vs_avg_hours`**: Porcentaje del usuario vs. promedio

**Utilidad:** Entender si el usuario está por encima o por debajo del promedio general.

### `anomalies`
Días con consumo anormalmente alto o bajo:
- **`date`**: Fecha del día anómalo
- **`total_hours`**: Horas vistas ese día
- **`type`**: "alto" o "bajo" según si está por encima o por debajo del promedio
- **`z_score`**: Puntuación Z (más de 2 desviaciones estándar = anómalo)

**Utilidad:** Identificar días inusuales que pueden requerir investigación (eventos especiales, problemas técnicos, etc.).

---

## 🎨 Casos de Uso

### 1. Análisis de Período Específico
- Analizar comportamiento del usuario durante una campaña
- Evaluar impacto de eventos o promociones
- Comparar períodos diferentes del mismo usuario

### 2. Comparación con Promedio
- Identificar usuarios por encima/debajo del promedio
- Entender posición relativa del usuario
- Detectar usuarios VIP o en riesgo

### 3. Detección de Anomalías
- Identificar días con consumo inusual
- Investigar causas de picos o caídas
- Detectar problemas técnicos o de servicio

### 4. Análisis de Tendencias
- Identificar si el usuario está aumentando o disminuyendo consumo
- Evaluar efectividad de estrategias de retención
- Predecir comportamiento futuro

### 5. Personalización Temporal
- Adaptar ofertas según tendencias del período
- Enviar notificaciones en momentos óptimos según el período
- Personalizar contenido según canales consumidos en el período

---

## 🔧 Endpoint API

**Ruta:** `POST /delancer/telemetry/users/analysis/date-range/`

**Parámetros requeridos:**
```json
{
    "subscriber_code": "USER001",
    "start_date": "2025-01-01",
    "end_date": "2025-01-31"
}
```

**Ejemplo de respuesta:**
```json
{
    "subscriber_code": "USER001",
    "period": {...},
    "period_summary": {...},
    "temporal_evolution": {...},
    "channels_in_period": [...],
    "time_slots_in_period": {...},
    "comparison_with_average": {...},
    "anomalies": [...]
}
```

---

## 📈 Optimizaciones

- **Django ORM optimizado:** Usa agregaciones eficientes con índices de base de datos
- **Cálculo de tendencia:** Compara primera y segunda mitad del período para determinar tendencia
- **Detección de anomalías:** Usa desviación estándar (con Pandas si está disponible, o cálculo manual)
- **Comparación eficiente:** Calcula promedios generales en una sola consulta

---

## ⚠️ Notas Importantes

1. **Fechas obligatorias:** A diferencia del análisis general de usuario, este análisis requiere `start_date` y `end_date` obligatorios.

2. **Validación de fechas:** Si `start_date > end_date`, retorna un error.

3. **Usuario sin datos:** Si el usuario no tiene registros en el período, retorna un mensaje indicando que no se encontraron datos.

4. **Detección de anomalías:** Requiere al menos 2 días de datos. Usa z-score > 2 para identificar anomalías.

5. **Tendencia:** Requiere al menos 2 días de datos. Compara primera mitad vs. segunda mitad del período.

6. **Pandas opcional:** Si Pandas está disponible, usa NumPy para cálculo de desviación estándar. Si no, calcula manualmente.

7. **Comparación con promedio:** Calcula el promedio de TODOS los usuarios en el mismo período para comparación justa.

