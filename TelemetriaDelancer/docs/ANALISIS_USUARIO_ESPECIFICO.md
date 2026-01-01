# Análisis de Usuario/Subscriber Específico

## 👤 Descripción

Este módulo (`analytics_user_specific.py`) proporciona un análisis detallado e individual de un usuario/subscriber específico. Permite obtener un perfil completo del usuario, su comportamiento de consumo, patrones temporales y estadísticas individuales.

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
```python
{
    "subscriber_code": "USER001",
    "profile": {
        "total_views": 1250,
        "total_hours": 450.5,
        "unique_channels": 15,
        "unique_devices": 2,
        "active_days": 45,
        "first_activity": "2024-12-01T10:30:00",
        "last_activity": "2025-01-15T22:45:00"
    },
    "consumption_behavior": {
        "top_channels": [
            {
                "channel": "Canal Premium",
                "views": 350,
                "total_hours": 180.5,
                "active_days": 25
            },
            ...
        ],
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
                "device_id": 12345,
                "views": 800,
                "total_hours": 300.2
            },
            {
                "device_id": 67890,
                "views": 450,
                "total_hours": 150.3
            }
        ]
    },
    "temporal_patterns": {
        "hourly_activity": [
            {
                "hour": 0,
                "views": 10,
                "total_hours": 3.5
            },
            {
                "hour": 1,
                "views": 5,
                "total_hours": 1.2
            },
            ...
        ]
    },
    "user_statistics": {
        "avg_hours_per_active_day": 10.0,
        "avg_views_per_active_day": 27.8,
        "avg_session_duration_seconds": 1296.0,
        "frequency_percentage": 75.0,
        "days_in_period": 60
    }
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
- **`total_views`**: Total de visualizaciones del usuario
- **`total_hours`**: Total de horas vistas por el usuario
- **`unique_channels`**: Número de canales únicos consumidos
- **`unique_devices`**: Número de dispositivos únicos utilizados
- **`active_days`**: Días en los que el usuario ha estado activo
- **`first_activity`**: Fecha y hora de la primera actividad registrada
- **`last_activity`**: Fecha y hora de la última actividad registrada

**Utilidad:** Vista general del usuario para entender su nivel de engagement y antigüedad.

### `consumption_behavior`
Comportamiento de consumo del usuario:

#### `top_channels`
Lista de los 10 canales más consumidos por el usuario:
- **`channel`**: Nombre del canal
- **`views`**: Número de visualizaciones en ese canal
- **`total_hours`**: Horas totales vistas en ese canal
- **`active_days`**: Días en los que consumió ese canal

**Utilidad:** Identificar preferencias de contenido del usuario para recomendaciones.

#### `preferred_time_slots`
Distribución de consumo por franjas horarias:
- **`madrugada`** (00:00 - 05:59): Horas y visualizaciones en esta franja
- **`mañana`** (06:00 - 11:59): Horas y visualizaciones en esta franja
- **`tarde`** (12:00 - 17:59): Horas y visualizaciones en esta franja
- **`noche`** (18:00 - 23:59): Horas y visualizaciones en esta franja

**Utilidad:** Entender patrones de consumo horarios para optimizar ofertas y notificaciones.

#### `devices_used`
Lista de dispositivos utilizados por el usuario:
- **`device_id`**: ID del dispositivo
- **`views`**: Visualizaciones desde ese dispositivo
- **`total_hours`**: Horas vistas desde ese dispositivo

**Utilidad:** Entender preferencias de dispositivo y multi-dispositivo del usuario.

### `temporal_patterns`
Patrones temporales detallados:

#### `hourly_activity`
Actividad por hora del día (0-23):
- **`hour`**: Hora del día (0-23)
- **`views`**: Visualizaciones en esa hora
- **`total_hours`**: Horas vistas en esa hora

**Utilidad:** Identificar horas pico de consumo del usuario para personalización.

### `user_statistics`
Estadísticas calculadas del usuario:
- **`avg_hours_per_active_day`**: Promedio de horas vistas por día activo
- **`avg_views_per_active_day`**: Promedio de visualizaciones por día activo
- **`avg_session_duration_seconds`**: Duración promedio de sesión en segundos
- **`frequency_percentage`**: Porcentaje de días activos sobre el total del período
- **`days_in_period`**: Días totales del período analizado

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

1. **Usuario no encontrado:** Si el usuario no tiene registros, retorna un mensaje indicando que no se encontraron datos.

2. **Filtros de fecha:** Si no se proporcionan fechas, analiza todo el historial disponible del usuario.

3. **Top Channels:** Siempre retorna máximo 10 canales para mantener el rendimiento.

4. **Franjas horarias:** Las franjas horarias se calculan usando el campo `timeDate` (0-23) directamente.

5. **Días en período:** Si no se proporcionan fechas, calcula el período desde la primera hasta la última actividad del usuario.

