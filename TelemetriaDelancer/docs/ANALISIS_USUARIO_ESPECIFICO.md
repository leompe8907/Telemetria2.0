# Análisis de Usuario/Subscriber Específico

## 👤 Descripción

Este módulo (`analytics_user_specific.py`) proporciona un análisis detallado e individual de un usuario/subscriber específico. Permite obtener un perfil completo del usuario, su comportamiento de consumo, patrones temporales y estadísticas individuales.

**IMPORTANTE:** Los análisis trabajan con datos de la base de datos local (`MergedTelemetricOTTDelancer`), NO consultan directamente a PanAccess. Los datos se obtienen de PanAccess mediante `telemetry_fetcher.py` y se almacenan localmente para análisis.

**Ideal para:**
- Perfiles de usuario detallados
- Análisis de comportamiento individual
- Soporte al cliente (entender historial de usuario)
- Personalización de contenido basada en preferencias
- Análisis de casos de uso específicos

---

## 🎯 Función Disponible

### **`get_user_analysis(subscriber_code, start_date=None, end_date=None)`**

Análisis detallado de un usuario/subscriber específico.

**Parámetros:**
- `subscriber_code` (str, obligatorio): Código del subscriber a analizar
- `start_date` (datetime, opcional): Fecha de inicio para filtrar (si no se proporciona, analiza todo el historial)
- `end_date` (datetime, opcional): Fecha de fin para filtrar (si no se proporciona, analiza todo el historial)

**Retorna:**

**Caso 1: Usuario con registros**
```python
{
    "subscriber_code": "USER001",
    "profile": {
        "total_views": 1250,
        "total_hours": 450.5,  # Calculado desde total_seconds / 3600.0
        "unique_channels": 15,
        "unique_devices": 2,
        "active_days": 45,  # Días únicos con actividad
        "first_activity": "2024-12-01T10:30:00",  # ISO format, puede ser None
        "last_activity": "2025-01-15T22:45:00"  # ISO format, puede ser None
    },
    "consumption_behavior": {
        "top_channels": [
            {
                "channel": "Canal Premium",  # Nombre del canal (dataName)
                "views": 350,  # Total de visualizaciones en este canal
                "total_hours": 180.5,  # Horas totales vistas (calculado desde segundos)
                "active_days": 25  # Días únicos en que consumió este canal
            },
            ...
        ],
        # Nota: Máximo 10 canales (top 10), puede tener menos si el usuario no ha visto tantos
        "preferred_time_slots": {
            "madrugada": {
                "total_hours": 50.2,
                "total_views": 120
            },
            "mañana": {
                "total_hours": 80.5,
                "total_views": 200
            },
            "tarde": {
                "total_hours": 150.3,
                "total_views": 400
            },
            "noche": {
                "total_hours": 169.5,
                "total_views": 530
            }
        },
        "devices_used": [
            {
                "device_id": 12345,  # ID del dispositivo (deviceId)
                "views": 800,  # Visualizaciones desde este dispositivo
                "total_hours": 300.2  # Horas vistas desde este dispositivo (calculado desde segundos)
            },
            {
                "device_id": 67890,
                "views": 450,
                "total_hours": 150.3
            }
        ]
        # Nota: Lista puede estar vacía si no hay dispositivos registrados
    },
    "temporal_patterns": {
        "hourly_activity": [
            {
                "hour": 0,  # Hora del día (0-23, desde timeDate)
                "views": 10,  # Visualizaciones en esta hora
                "total_hours": 3.5  # Horas vistas en esta hora (calculado desde segundos)
            },
            {
                "hour": 1,
                "views": 5,
                "total_hours": 1.2
            },
            ...
        ]
        # Nota: Solo incluye horas con actividad (no todas las 24 horas)
        # Ordenado por hora (0-23)
    },
    "user_statistics": {
        "avg_hours_per_active_day": 10.0,  # total_hours / active_days
        "avg_views_per_active_day": 27.8,  # total_views / active_days
        "avg_session_duration_seconds": 1296.0,  # Promedio de dataDuration en segundos
        "frequency_percentage": 75.0,  # (active_days / days_in_period) * 100
        "days_in_period": 60  # Días totales del período (calculado según filtros)
    }
}
```

**Caso 2: Usuario sin registros**
```python
{
    "subscriber_code": "USER001",
    "message": "No se encontraron registros para este usuario",
    "total_records": 0
}
```

**Ejemplo de uso:**
```python
from datetime import datetime
from TelemetriaDelancer.panaccess.analytics_user_specific import get_user_analysis

# Análisis completo del historial del usuario
analysis = get_user_analysis(subscriber_code="USER001")

# Análisis filtrado por fecha
start = datetime(2025, 1, 1)
end = datetime(2025, 1, 31)
analysis = get_user_analysis(
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

### `profile`
Perfil general del usuario:
- **`total_views`**: Total de visualizaciones del usuario (Count de registros)
- **`total_hours`**: Total de horas vistas por el usuario (calculado desde `total_seconds / 3600.0`, redondeado a 2 decimales)
- **`unique_channels`**: Número de canales únicos consumidos (Count distinct de `dataName`)
- **`unique_devices`**: Número de dispositivos únicos utilizados (Count distinct de `deviceId`)
- **`active_days`**: Días únicos en los que el usuario ha estado activo (Count distinct de `dataDate`)
- **`first_activity`**: Fecha y hora de la primera actividad registrada (Min de `timestamp`, formato ISO, puede ser `None`)
- **`last_activity`**: Fecha y hora de la última actividad registrada (Max de `timestamp`, formato ISO, puede ser `None`)

**Utilidad:** Vista general del usuario para entender su nivel de engagement y antigüedad.

### `consumption_behavior`
Comportamiento de consumo del usuario:

#### `top_channels`
Lista de los 10 canales más consumidos por el usuario (ordenados por `views` descendente):
- **`channel`**: Nombre del canal (`dataName`)
- **`views`**: Número de visualizaciones en ese canal (Count de registros)
- **`total_hours`**: Horas totales vistas en ese canal (calculado desde `total_seconds / 3600.0`, redondeado a 2 decimales)
- **`active_days`**: Días únicos en los que consumió ese canal (Count distinct de `dataDate`)

**Notas:**
- Máximo 10 canales (limitado con `[:10]`)
- Puede tener menos de 10 si el usuario no ha visto tantos canales
- Solo incluye canales donde `dataName` no es `None`

**Utilidad:** Identificar preferencias de contenido del usuario para recomendaciones.

#### `preferred_time_slots`
Distribución de consumo por franjas horarias (calculado desde `timeDate`):
- **`madrugada`** (00:00 - 05:59): `{"total_hours": float, "total_views": int}` - Horas y visualizaciones en esta franja
- **`mañana`** (06:00 - 11:59): `{"total_hours": float, "total_views": int}` - Horas y visualizaciones en esta franja
- **`tarde`** (12:00 - 17:59): `{"total_hours": float, "total_views": int}` - Horas y visualizaciones en esta franja
- **`noche`** (18:00 - 23:59): `{"total_hours": float, "total_views": int}` - Horas y visualizaciones en esta franja

**Notas:**
- `total_hours` se calcula desde `total_seconds / 3600.0` y se redondea a 2 decimales
- Todas las franjas siempre están presentes en el diccionario (incluso si tienen 0)
- Solo incluye registros donde `timeDate` no es `None`
- Las franjas se calculan usando `Case/When` de Django ORM

**Utilidad:** Entender patrones de consumo horarios para optimizar ofertas y notificaciones.

#### `devices_used`
Lista de dispositivos utilizados por el usuario (ordenados por `views` descendente):
- **`device_id`**: ID del dispositivo (`deviceId`)
- **`views`**: Visualizaciones desde ese dispositivo (Count de registros)
- **`total_hours`**: Horas vistas desde ese dispositivo (calculado desde `total_seconds / 3600.0`, redondeado a 2 decimales)

**Notas:**
- Lista puede estar vacía si no hay dispositivos registrados
- Solo incluye dispositivos donde `deviceId` no es `None`
- No hay límite en el número de dispositivos retornados

**Utilidad:** Entender preferencias de dispositivo y multi-dispositivo del usuario.

### `temporal_patterns`
Patrones temporales detallados:

#### `hourly_activity`
Actividad por hora del día (0-23):
- **`hour`**: Hora del día (0-23, desde `timeDate`)
- **`views`**: Visualizaciones en esa hora (Count de registros)
- **`total_hours`**: Horas vistas en esa hora (calculado desde `total_seconds / 3600.0`, redondeado a 2 decimales)

**Notas:**
- Solo incluye horas con actividad (no todas las 24 horas)
- Ordenado por hora ascendente (0-23)
- Solo incluye registros donde `timeDate` no es `None`

**Utilidad:** Identificar horas pico de consumo del usuario para personalización.

### `user_statistics`
Estadísticas calculadas del usuario:
- **`avg_hours_per_active_day`**: Promedio de horas vistas por día activo (`total_hours / active_days`, redondeado a 2 decimales)
- **`avg_views_per_active_day`**: Promedio de visualizaciones por día activo (`total_views / active_days`, redondeado a 2 decimales)
- **`avg_session_duration_seconds`**: Duración promedio de sesión en segundos (Avg de `dataDuration`, redondeado a 2 decimales)
- **`frequency_percentage`**: Porcentaje de días activos sobre el total del período (`(active_days / days_in_period) * 100`, redondeado a 2 decimales)
- **`days_in_period`**: Días totales del período analizado
  - Si se proporcionan `start_date` y `end_date`: `(end_date - start_date).days + 1`
  - Si no se proporcionan fechas: `(max_date - min_date).days + 1` (desde los datos del usuario)
  - Mínimo: 1 día

**Utilidad:** Métricas de engagement individual para comparar con promedios generales.

---

## 🎨 Casos de Uso

### 1. Perfil de Usuario
Mostrar información completa del usuario en su perfil:
- Resumen de actividad
- Canales favoritos
- Dispositivos utilizados
- Patrones de consumo

### 2. Recomendaciones Personalizadas
- Usar `top_channels` para recomendar contenido similar
- Usar `preferred_time_slots` para enviar notificaciones en momentos óptimos
- Usar `hourly_activity` para optimizar ofertas

### 3. Soporte al Cliente
- Ver historial completo del usuario
- Identificar problemas de consumo
- Entender preferencias para resolver consultas

### 4. Análisis de Comportamiento
- Estudiar patrones de usuarios específicos
- Comparar comportamiento individual vs. promedio
- Identificar casos de uso extremos

### 5. Personalización de Contenido
- Mostrar canales favoritos destacados
- Adaptar interfaz según dispositivos utilizados
- Optimizar experiencia según horarios de consumo

---

## 🔧 Endpoint API

**Ruta:** `POST /delancer/telemetry/users/analysis/`

**Parámetros requeridos:**
```json
{
    "subscriber_code": "USER001"
}
```

**Parámetros opcionales:**
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
    "profile": {...},
    "consumption_behavior": {...},
    "temporal_patterns": {...},
    "user_statistics": {...}
}
```

---

## 📈 Optimizaciones

- **Django ORM optimizado:** Usa agregaciones eficientes con índices de base de datos
- **Top 10 limitado:** Limita canales a top 10 para mejor rendimiento
- **Filtros opcionales:** Permite análisis completo o filtrado por fecha
- **Cálculos eficientes:** Usa agregaciones de Django para evitar procesamiento en memoria

---

## ⚠️ Notas Importantes

1. **Usuario no encontrado:** Si el usuario no tiene registros, retorna:
   ```python
   {
       "subscriber_code": "USER001",
       "message": "No se encontraron registros para este usuario",
       "total_records": 0
   }
   ```

2. **Filtros de fecha:** 
   - Si no se proporcionan fechas, analiza todo el historial disponible del usuario
   - Si se proporcionan, filtra por `dataDate >= start_date.date()` y `dataDate <= end_date.date()`
   - Los filtros son opcionales pero recomendados para mejorar rendimiento

3. **Top Channels:** 
   - Siempre retorna máximo 10 canales (limitado con `[:10]`)
   - Puede tener menos de 10 si el usuario no ha visto tantos canales
   - Ordenado por número de visualizaciones descendente

4. **Franjas horarias:** 
   - Las franjas horarias se calculan usando el campo `timeDate` (0-23) directamente
   - Usa `Case/When` de Django ORM para categorizar
   - Todas las franjas siempre están presentes (incluso con valores 0)
   - Solo incluye registros donde `timeDate` no es `None`

5. **Días en período:** 
   - Si se proporcionan `start_date` y `end_date`: `(end_date - start_date).days + 1`
   - Si no se proporcionan fechas: `(max_date - min_date).days + 1` (desde los datos del usuario)
   - Mínimo: 1 día

6. **Actividad por hora:** 
   - Solo incluye horas con actividad (no todas las 24 horas)
   - Ordenado por hora ascendente (0-23)
   - Solo incluye registros donde `timeDate` no es `None`

7. **Dispositivos:** 
   - Lista puede estar vacía si no hay dispositivos registrados
   - Ordenado por número de visualizaciones descendente
   - No hay límite en el número de dispositivos retornados

8. **Base de datos local:** Todos los análisis trabajan con datos de la base de datos local (`MergedTelemetricOTTDelancer`), NO consultan directamente a PanAccess

9. **Conversión de tiempo:** 
   - Todos los tiempos se almacenan en segundos en la BD (`dataDuration`)
   - Se convierten a horas dividiendo por 3600.0
   - Todos los valores de horas se redondean a 2 decimales

10. **Valores None:** 
    - `first_activity` y `last_activity` pueden ser `None` si no hay datos de timestamp
    - Se manejan con `.isoformat()` si existen, o `None` si no

