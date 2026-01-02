# Tareas Periódicas con Celery

## 📋 Descripción

Este documento explica cómo funciona el sistema de tareas periódicas implementado con Celery y Celery Beat para sincronizar telemetría y hacer merge OTT automáticamente.

## 🎯 Funcionalidad

El sistema ejecuta automáticamente cada **2 minutos** una cadena de tareas:

1. **Sincronización de Telemetría** (`sync_telemetry_task`)
   - Descarga registros nuevos desde PanAccess
   - Guarda los registros en la base de datos
   - Procesa timestamps para extraer fecha y hora

2. **Merge OTT** (`merge_ott_task`)
   - Se ejecuta **después** de que termine la sincronización
   - Fusiona registros OTT (actionId 7 y 8)
   - Guarda los registros fusionados en `MergedTelemetricOTT`

## 🔧 Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

Esto instalará:
- `celery==5.3.4` - Framework de tareas asíncronas
- `redis==5.0.1` - Broker de mensajes (requerido por Celery)

### 2. Instalar y ejecutar Redis

**Windows:**
- Descargar Redis desde: https://github.com/microsoftarchive/redis/releases
- O usar WSL2 con Redis instalado

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis
```

**Iniciar Redis:**
```bash
# Windows (si está instalado)
redis-server

# Linux/Mac
sudo systemctl start redis
# O manualmente:
redis-server
```

### 3. Verificar que Redis está corriendo

```bash
redis-cli ping
# Debe responder: PONG
```

## 🚀 Uso

### Desarrollo

Necesitas ejecutar **3 terminales**:

**Terminal 1: Servidor Django**
```bash
python manage.py runserver
```

**Terminal 2: Celery Worker** (ejecuta las tareas)
```bash
celery -A TelemetriaDelancer worker --loglevel=info
```

**Terminal 3: Celery Beat** (programa las tareas periódicas)
```bash
celery -A TelemetriaDelancer beat --loglevel=info
```

### Producción

Para producción, usa un gestor de procesos como **supervisor** o **systemd**:

**Ejemplo con supervisor (`/etc/supervisor/conf.d/celery.conf`):**
```ini
[program:celery_worker]
command=/ruta/a/env/bin/celery -A TelemetriaDelancer worker --loglevel=info
directory=/ruta/a/proyecto
user=usuario
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/ruta/a/logs/celery_worker.log

[program:celery_beat]
command=/ruta/a/env/bin/celery -A TelemetriaDelancer beat --loglevel=info
directory=/ruta/a/proyecto
user=usuario
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/ruta/a/logs/celery_beat.log
```

## 📊 Monitoreo

### Ver tareas en tiempo real

```bash
# Ver workers activos
celery -A TelemetriaDelancer inspect active

# Ver tareas programadas
celery -A TelemetriaDelancer inspect scheduled

# Ver estadísticas de workers
celery -A TelemetriaDelancer inspect stats
```

### Logs

Los logs de las tareas se guardan en:
- `logs/django.log` - Logs generales
- `logs/panaccess.log` - Logs de PanAccess
- `logs/errors.log` - Errores

Las tareas también loguean con el prefijo `[CELERY]` para fácil identificación.

## ⚙️ Configuración

### Cambiar frecuencia de ejecución

Edita `TelemetriaDelancer/celery.py`:

```python
app.conf.beat_schedule = {
    'sync-and-merge-telemetry': {
        'task': 'TelemetriaDelancer.tasks.sync_and_merge_telemetry_chain',
        'schedule': 120.0,  # Cambiar aquí (en segundos)
        # Ejemplos:
        # 60.0 = cada 1 minuto
        # 300.0 = cada 5 minutos
        # 3600.0 = cada 1 hora
    },
}
```

### Cambiar configuración de Redis

Edita `backend/settings.py`:

```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'  # Cambiar host/puerto si es necesario
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

## 🔍 Estructura de Tareas

### Tarea Principal: `sync_and_merge_telemetry_chain`

Esta es la tarea que se programa cada 2 minutos. Ejecuta una **cadena** (chain) de tareas:

```
sync_telemetry_task → merge_ott_task
```

La segunda tarea recibe el resultado de la primera como argumento, permitiendo usar información como el `highest_id_after` para optimizar el merge.

### Tarea 1: `sync_telemetry_task`

- Descarga registros nuevos desde PanAccess
- Guarda en `TelemetryRecordEntry`
- Retorna estadísticas de la sincronización

### Tarea 2: `merge_ott_task`

- Recibe el resultado de `sync_telemetry_task`
- Fusiona registros OTT usando el `highest_id_after` si está disponible
- Guarda en `MergedTelemetricOTT`
- Retorna estadísticas del merge

## 🛡️ Manejo de Errores

### Reintentos Automáticos

Cada tarea tiene configurado:
- **Máximo de reintentos:** 3
- **Delay entre reintentos:** 60 segundos
- **Si falla después de 3 intentos:** Se registra el error y continúa

### Logs de Errores

Los errores se registran en:
- `logs/errors.log` - Errores críticos
- `logs/django.log` - Logs generales con prefijo `[CELERY]`

## 🧪 Pruebas

### Ejecutar una tarea manualmente

```bash
# Desde el shell de Django
python manage.py shell

>>> from TelemetriaDelancer.tasks import sync_telemetry_task, merge_ott_task
>>> result = sync_telemetry_task.delay()
>>> result.get()  # Esperar resultado
```

### Ejecutar la cadena completa

```bash
python manage.py shell

>>> from TelemetriaDelancer.tasks import sync_and_merge_telemetry_chain
>>> result = sync_and_merge_telemetry_chain.delay()
>>> result.get()
```

## 📝 Notas Importantes

1. **Redis debe estar corriendo** antes de iniciar Celery
2. **Beat y Worker deben estar corriendo** para que las tareas periódicas funcionen
3. **En desarrollo**, usa `--loglevel=info` para ver más detalles
4. **En producción**, considera usar `--loglevel=warning` para reducir logs
5. Las tareas usan **transacciones de base de datos** para garantizar consistencia

## 🔗 Referencias

- [Documentación de Celery](https://docs.celeryproject.org/)
- [Celery Beat - Tareas Periódicas](https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html)
- [Celery Chains](https://docs.celeryproject.org/en/stable/userguide/canvas.html#chains)

---

**Última actualización:** 2025-01-XX  
**Versión:** 1.0

