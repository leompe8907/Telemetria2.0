# Análisis de Usuario/Subscriber con Rango de Fechas

## 📅👤 Descripción

Este módulo (`analytics_user_date_range.py`) proporciona un análisis detallado de un usuario/subscriber específico en un rango de fechas definido. A diferencia del análisis general de usuario, este análisis se enfoca en un período específico y permite comparar el comportamiento del usuario con el promedio general, identificar tendencias y detectar anomalías.

**IMPORTANTE:** Los análisis trabajan con datos de la base de datos local (`MergedTelemetricOTTDelancer`), NO consultan directamente a PanAccess. Los datos se obtienen de PanAccess mediante `telemetry_fetcher.py` y se almacenan localmente para análisis.

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

**Caso 1: Usuario con registros en el período**
```python
{
    "subscriber_code": "USER001",
    "period": {
        "start_date": "2025-01-01",  # ISO format (date().isoformat())
        "end_date": "2025-01-31",  # ISO format (date().isoformat())
        "days": 31  # (end_date - start_date).days + 1
    },
    "period_summary": {
        "total_views": 850,  # Count de registros
        "total_hours": 320.5,  # Calculado desde total_seconds / 3600.0, redondeado a 2 decimales
        "unique_channels": 12,  # Count distinct de dataName
        "unique_devices": 2,  # Count distinct de deviceId
        "active_days": 25,  # Count distinct de dataDate
        "avg_duration_seconds": 1356.0  # Avg de dataDuration, redondeado a 2 decimales
    },
    "temporal_evolution": {
        "daily_activity": [
            {
                "date": "2025-01-01",  # str(dataDate), formato YYYY-MM-DD
                "views": 30,  # Count de registros ese día
                "total_hours": 12.5,  # Calculado desde total_seconds / 3600.0, redondeado a 2 decimales
                "unique_channels": 5  # Count distinct de dataName ese día
            },
            {
                "date": "2025-01-02",
                "views": 25,
                "total_hours": 10.2,
                "unique_channels": 4
            },
            ...
        ],
        # Nota: Solo incluye días con actividad (no todos los días del período)
        # Ordenado por fecha ascendente
        "trend": "creciente"  # "creciente", "decreciente", "estable", o "insuficiente_datos"
    },
    "channels_in_period": [
        {
            "channel": "Canal Premium",  # Nombre del canal (dataName)
            "views": 250,  # Count de registros en este canal
            "total_hours": 150.5,  # Calculado desde total_seconds / 3600.0, redondeado a 2 decimales
            "active_days": 18  # Count distinct de dataDate para este canal
        },
        ...
    ],
    # Nota: Ordenado por views descendente
    # Solo incluye canales donde dataName no es None
    # No hay límite en el número de canales retornados
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
        "user_views": 850,  # Visualizaciones del usuario en el período
        "avg_views": 625.5,  # Promedio de visualizaciones de todos los usuarios en el mismo período (redondeado a 2 decimales)
        "user_vs_avg_views": 136.0,  # Porcentaje: (user_views / avg_views) * 100 (redondeado a 2 decimales)
        "user_hours": 320.5,  # Horas del usuario (redondeado a 2 decimales)
        "avg_hours": 250.2,  # Promedio de horas de todos los usuarios en el mismo período (redondeado a 2 decimales)
        "user_vs_avg_hours": 128.1  # Porcentaje: (user_hours / avg_hours) * 100 (redondeado a 2 decimales)
    },
    # Nota: Los promedios se calculan sobre TODOS los usuarios en el mismo período
    # Si avg_views o avg_hours es 0, los porcentajes serán 0
    "anomalies": [
        {
            "date": "2025-01-15",  # Fecha del día anómalo (str, formato YYYY-MM-DD)
            "total_hours": 25.5,  # Horas vistas ese día
            "type": "alto",  # "alto" si hours > avg_daily_hours, "bajo" si hours < avg_daily_hours
            "z_score": 2.5  # Z-score absoluto (redondeado a 2 decimales), > 2 = anómalo
        },
        {
            "date": "2025-01-20",
            "total_hours": 2.1,
            "type": "bajo",
            "z_score": 2.3
        }
    ]
    # Nota: Lista puede estar vacía si no hay anomalías
    # Requiere al menos 1 día de datos para calcular
    # Z-score se calcula como: abs((hours - avg_daily_hours) / std_daily_hours)
    # Se considera anómalo si z_score > 2
}
```

**Caso 2: Error de fechas inválidas**
```python
{
    "error": "start_date debe ser anterior a end_date"
}
```

**Caso 3: Usuario sin registros en el período**
```python
{
    "subscriber_code": "USER001",
    "period": {
        "start_date": "2025-01-01",
        "end_date": "2025-01-31"
    },
    "message": "No se encontraron registros para este usuario en el período seleccionado",
    "total_records": 0
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
Tendencia general del período (calculada comparando primera mitad vs. segunda mitad):
- **`"creciente"`**: El consumo aumentó en la segunda mitad del período (avg_second > avg_first * 1.1)
- **`"decreciente"`**: El consumo disminuyó en la segunda mitad del período (avg_second < avg_first * 0.9)
- **`"estable"`**: El consumo se mantuvo similar (entre 0.9 y 1.1 veces el promedio de la primera mitad)
- **`"insuficiente_datos"`**: No hay suficientes datos para determinar tendencia (menos de 2 días con actividad)

**Notas:**
- Requiere al menos 2 días con actividad
- Compara promedio de horas de la primera mitad vs. segunda mitad del período
- Usa umbrales de 1.1 (creciente) y 0.9 (decreciente) para determinar tendencia

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
- **`user_views`**: Visualizaciones del usuario en el período
- **`avg_views`**: Promedio de visualizaciones de todos los usuarios en el mismo período
  - Calculado como: `Count('id') / Count('subscriberCode', distinct=True)`
  - Redondeado a 2 decimales
- **`user_vs_avg_views`**: Porcentaje del usuario vs. promedio (`(user_views / avg_views) * 100`)
  - 100% = igual al promedio
  - > 100% = por encima del promedio
  - < 100% = por debajo del promedio
  - Si `avg_views` es 0, retorna 0
  - Redondeado a 2 decimales
- **`user_hours`**: Horas del usuario (redondeado a 2 decimales)
- **`avg_hours`**: Promedio de horas de todos los usuarios en el mismo período
  - Calculado como: `Sum('dataDuration') / 3600.0 / Count('subscriberCode', distinct=True)`
  - Redondeado a 2 decimales
- **`user_vs_avg_hours`**: Porcentaje del usuario vs. promedio (`(user_hours / avg_hours) * 100`)
  - Si `avg_hours` es 0, retorna 0
  - Redondeado a 2 decimales

**Notas:**
- Los promedios se calculan sobre TODOS los usuarios en el mismo período (mismo `start_date` y `end_date`)
- Se usa una sola consulta agregada para calcular ambos promedios eficientemente

**Utilidad:** Entender si el usuario está por encima o por debajo del promedio general.

### `anomalies`
Días con consumo anormalmente alto o bajo (usando z-score):
- **`date`**: Fecha del día anómalo (str, formato YYYY-MM-DD)
- **`total_hours`**: Horas vistas ese día
- **`type`**: "alto" o "bajo" según si está por encima o por debajo del promedio diario del usuario
  - "alto": `hours > avg_daily_hours`
  - "bajo": `hours < avg_daily_hours`
- **`z_score`**: Puntuación Z absoluta (redondeada a 2 decimales)
  - Calculado como: `abs((hours - avg_daily_hours) / std_daily_hours)`
  - Se considera anómalo si `z_score > 2` (más de 2 desviaciones estándar)

**Notas:**
- Lista puede estar vacía si no hay anomalías
- Requiere al menos 1 día de datos para calcular
- Si hay más de 1 día, calcula desviación estándar:
  - Con Pandas disponible: usa `np.std()` de NumPy
  - Sin Pandas: calcula manualmente usando varianza
- El promedio diario se calcula sobre los días con actividad del usuario en el período
- Solo se incluyen días donde el z-score absoluto > 2

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

2. **Validación de fechas:** 
   - Si `start_date > end_date`, retorna: `{"error": "start_date debe ser anterior a end_date"}`
   - No se lanza excepción, se retorna un diccionario con error

3. **Usuario sin datos:** Si el usuario no tiene registros en el período, retorna:
   ```python
   {
       "subscriber_code": "USER001",
       "period": {"start_date": "...", "end_date": "..."},
       "message": "No se encontraron registros para este usuario en el período seleccionado",
       "total_records": 0
   }
   ```

4. **Detección de anomalías:** 
   - Requiere al menos 1 día de datos para calcular
   - Si hay más de 1 día, calcula desviación estándar
   - Usa z-score absoluto > 2 para identificar anomalías
   - Con Pandas disponible: usa `np.std()` de NumPy
   - Sin Pandas: calcula manualmente usando varianza

5. **Tendencia:** 
   - Requiere al menos 2 días con actividad para calcular
   - Compara primera mitad vs. segunda mitad del período
   - Usa umbrales de 1.1 (creciente) y 0.9 (decreciente)
   - Si hay menos de 2 días, retorna "insuficiente_datos"

6. **Pandas opcional:** 
   - Si Pandas está disponible, usa NumPy (`np.std()`) para cálculo de desviación estándar
   - Si no, calcula manualmente usando varianza: `sqrt(sum((x - mean)²) / n)`

7. **Comparación con promedio:** 
   - Calcula el promedio de TODOS los usuarios en el mismo período para comparación justa
   - Usa una sola consulta agregada para calcular ambos promedios eficientemente
   - Si `avg_views` o `avg_hours` es 0, los porcentajes serán 0

8. **Base de datos local:** Todos los análisis trabajan con datos de la base de datos local (`MergedTelemetricOTTDelancer`), NO consultan directamente a PanAccess

9. **Conversión de tiempo:** 
   - Todos los tiempos se almacenan en segundos en la BD (`dataDuration`)
   - Se convierten a horas dividiendo por 3600.0
   - Todos los valores de horas se redondean a 2 decimales

10. **Estructura de datos:**
    - `daily_activity`: Solo incluye días con actividad (no todos los días del período)
    - `channels_in_period`: Ordenado por `views` descendente, sin límite
    - `time_slots_in_period`: Todas las franjas siempre están presentes (incluso con valores 0)
    - `anomalies`: Lista puede estar vacía si no hay anomalías

