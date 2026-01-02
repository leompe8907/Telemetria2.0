# Implementación de Tareas Asíncronas con Redis y Celery

## 🎯 Objetivo

Implementar un sistema de tareas asíncronas para operaciones que requieren mucho tiempo o recursos, mejorando la experiencia del usuario y la escalabilidad del sistema.

---

## 📋 Tipos de Tareas Identificadas

### 1. **Tareas de Sincronización de Datos** 🔄
**Prioridad: ALTA**

#### 1.1. Sincronización Completa de Telemetría
- **Operación actual:** `TelemetrySyncView.post()` - Descarga y guarda 400,000+ registros
- **Problema:** Bloquea el request HTTP durante minutos/horas
- **Solución:** Ejecutar en background con progreso

**Características:**
- ⏱️ **Duración:** 10-60 minutos (depende de cantidad de registros)
- 💾 **Memoria:** Media (procesa en lotes)
- 🔄 **Reintentos:** Sí (si falla un lote, continuar con el siguiente)
- 📊 **Progreso:** Trackeable (registros procesados, porcentaje)

#### 1.2. Merge de Datos OTT
- **Operación actual:** `MergeOTTView.post()` - Fusiona actionId 7 y 8
- **Problema:** Puede tardar varios minutos con muchos registros
- **Solución:** Ejecutar en background

**Características:**
- ⏱️ **Duración:** 2-10 minutos
- 💾 **Memoria:** Media
- 🔄 **Reintentos:** Sí
- 📊 **Progreso:** Trackeable (registros procesados, merged, saved)

---

### 2. **Tareas de Análisis Pesados** 📊
**Prioridad: MEDIA-ALTA**

#### 2.1. Análisis Completo General
- **Operación actual:** `AnalyticsView.post()` - Ejecuta todos los análisis
- **Problema:** Con Pandas puede tardar 30-60 segundos
- **Solución:** Ejecutar en background y cachear resultados

**Características:**
- ⏱️ **Duración:** 10-60 segundos
- 💾 **Memoria:** Alta (Pandas carga datos en RAM)
- 🔄 **Reintentos:** Opcional
- 📊 **Progreso:** Parcial (por análisis completado)
- 💾 **Cache:** Sí (mismos parámetros = mismo resultado)

#### 2.2. Análisis por Período Completo
- **Operación actual:** `PeriodAnalysisView.post()` - Análisis del período
- **Problema:** Similar al anterior
- **Solución:** Ejecutar en background y cachear

**Características:**
- ⏱️ **Duración:** 10-60 segundos
- 💾 **Memoria:** Alta
- 🔄 **Reintentos:** Opcional
- 📊 **Progreso:** Parcial
- 💾 **Cache:** Sí

#### 2.3. Análisis de Usuarios General
- **Operación actual:** `GeneralUsersAnalysisView.post()` - Análisis de todos los usuarios
- **Problema:** Con muchos usuarios puede tardar
- **Solución:** Ejecutar en background

**Características:**
- ⏱️ **Duración:** 5-30 segundos
- 💾 **Memoria:** Media-Alta
- 🔄 **Reintentos:** Opcional
- 📊 **Progreso:** No necesario (rápido)
- 💾 **Cache:** Sí

---

### 3. **Tareas de Generación de Reportes** 📄
**Prioridad: MEDIA**

#### 3.1. Generación de Reportes PDF/Excel
- **Operación:** Exportar análisis a PDF o Excel
- **Problema:** Generar archivos grandes puede tardar
- **Solución:** Generar en background y notificar cuando esté listo

**Características:**
- ⏱️ **Duración:** 5-30 segundos
- 💾 **Memoria:** Media
- 🔄 **Reintentos:** Sí
- 📊 **Progreso:** No necesario
- 📁 **Almacenamiento:** Archivo temporal o S3

---

### 4. **Tareas Programadas (Cron)** ⏰
**Prioridad: MEDIA**

#### 4.1. Sincronización Automática Diaria
- **Operación:** Sincronizar nuevos registros automáticamente
- **Frecuencia:** Diaria (ej: 2:00 AM)
- **Solución:** Tarea programada con Celery Beat

#### 4.2. Merge Automático OTT
- **Operación:** Merge automático de nuevos registros OTT
- **Frecuencia:** Cada 6 horas
- **Solución:** Tarea programada con Celery Beat

#### 4.3. Limpieza de Cache
- **Operación:** Limpiar cache de análisis antiguos
- **Frecuencia:** Diaria
- **Solución:** Tarea programada

---

## 🏗️ Arquitectura Propuesta

```
┌─────────────┐
│   Django    │
│   Backend   │
└──────┬──────┘
       │
       │ 1. Encola tarea
       ▼
┌─────────────┐
│    Redis    │
│   (Broker)  │
└──────┬──────┘
       │
       │ 2. Distribuye tarea
       ▼
┌─────────────┐
│   Celery    │
│   Workers   │
└──────┬──────┘
       │
       │ 3. Ejecuta tarea
       ▼
┌─────────────┐
│  PostgreSQL │
│   / SQLite  │
└─────────────┘
```

---

## 🔄 Flujo Completo de una Tarea

### Ejemplo: Sincronización de Telemetría

```
1. CLIENTE (Frontend)
   POST /telemetry/sync/
   ↓
2. DJANGO VIEW
   - Valida parámetros
   - Encola tarea en Redis
   - Retorna: { "task_id": "abc123", "status": "PENDING" }
   ↓
3. REDIS (Broker)
   - Almacena tarea en cola
   - Notifica a Celery Worker disponible
   ↓
4. CELERY WORKER
   - Recibe tarea
   - Ejecuta: sync_telemetry_task.delay(...)
   - Actualiza progreso en Redis
   ↓
5. EJECUCIÓN
   - Descarga registros en lotes
   - Guarda en BD
   - Actualiza progreso cada lote
   ↓
6. REDIS (Result Backend)
   - Almacena resultado final
   - Almacena progreso intermedio
   ↓
7. CLIENTE (Frontend)
   GET /telemetry/sync/status/{task_id}/
   - Obtiene progreso en tiempo real
   - Muestra: "Procesando... 45% (180,000/400,000 registros)"
   ↓
8. CLIENTE (Frontend)
   GET /telemetry/sync/result/{task_id}/
   - Obtiene resultado final cuando status = "SUCCESS"
```

---

## 📦 Instalación y Configuración

### 1. Instalar Dependencias

```bash
pip install celery redis
```

Agregar a `requirements.txt`:
```
celery>=5.3.0
redis>=5.0.0
```

### 2. Configurar Redis

**Docker (Recomendado):**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**O instalar Redis localmente:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis
```

### 3. Configurar Celery en Django

**Crear archivo:** `TelemetriaDelancer/celery.py`

```python
import os
from celery import Celery

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TelemetriaDelancer.settings')

app = Celery('TelemetriaDelancer')

# Configuración desde Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descubrir tareas en apps
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

**Modificar:** `TelemetriaDelancer/__init__.py`

```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

**Agregar a:** `settings.py`

```python
# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Mexico_City'

# Configuración de tareas
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutos máximo
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutos soft limit

# Retry configuration
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# Result expiration
CELERY_RESULT_EXPIRES = 3600  # 1 hora
```

---

## 🔧 Implementación de Tareas

### 1. Tarea de Sincronización de Telemetría

**Crear archivo:** `TelemetriaDelancer/tasks/telemetry_tasks.py`

```python
from celery import shared_task
from celery import current_task
from django.core.cache import cache
import logging

from TelemetriaDelancer.panaccess.telemetry_fetcher import (
    get_telemetry_records,
    save_telemetry_records,
    extract_timestamp_details,
    is_database_empty,
    get_highest_record_id
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='telemetry.sync_all')
def sync_telemetry_task(self, limit=100, process_timestamps=True, batch_size=100):
    """
    Tarea asíncrona para sincronizar todos los registros de telemetría.
    
    Args:
        limit: Registros por página
        process_timestamps: Si procesar timestamps
        batch_size: Tamaño del lote para guardar
    
    Returns:
        Dict con resultados de la sincronización
    """
    task_id = self.request.id
    logger.info(f"Iniciando sincronización de telemetría - Task ID: {task_id}")
    
    try:
        # Estado inicial
        was_empty_before = is_database_empty()
        highest_id_before = get_highest_record_id()
        
        total_downloaded = 0
        total_saved = 0
        total_skipped = 0
        total_errors = 0
        
        # Actualizar progreso inicial
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 0,
                'total': 100,
                'status': 'Iniciando descarga...',
                'downloaded': 0,
                'saved': 0
            }
        )
        
        if is_database_empty():
            # Descargar todos los registros
            offset = 0
            page_count = 0
            estimated_total = 400000  # Estimación inicial
            
            while True:
                try:
                    page_count += 1
                    
                    # Descargar lote
                    response = get_telemetry_records(
                        offset=offset,
                        limit=limit,
                        order_by="recordId",
                        order_dir="DESC"
                    )
                    
                    answer = response.get("answer", {})
                    records = answer.get("telemetryRecordEntries", [])
                    
                    if not records:
                        break
                    
                    # Procesar timestamps
                    if process_timestamps:
                        records = extract_timestamp_details(records)
                    
                    total_downloaded += len(records)
                    
                    # Guardar lote
                    save_result = save_telemetry_records(records, batch_size=batch_size)
                    total_saved += save_result['saved_records']
                    total_skipped += save_result['skipped_records']
                    total_errors += save_result['errors']
                    
                    # Actualizar progreso
                    progress = min(int((total_downloaded / estimated_total) * 100), 99)
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'current': progress,
                            'total': 100,
                            'status': f'Procesando lote {page_count}...',
                            'downloaded': total_downloaded,
                            'saved': total_saved,
                            'skipped': total_skipped,
                            'errors': total_errors
                        }
                    )
                    
                    # Cachear progreso para consulta externa
                    cache.set(
                        f'telemetry_sync_progress_{task_id}',
                        {
                            'progress': progress,
                            'downloaded': total_downloaded,
                            'saved': total_saved,
                            'status': 'PROGRESS'
                        },
                        timeout=3600
                    )
                    
                    if len(records) < limit:
                        break
                    
                    offset += limit
                    
                except Exception as e:
                    logger.error(f"Error en lote {page_count}: {str(e)}", exc_info=True)
                    offset += limit
                    continue
        else:
            # Descargar solo nuevos
            from TelemetriaDelancer.panaccess.telemetry_fetcher import fetch_telemetry_records_smart
            
            records = fetch_telemetry_records_smart(
                limit=limit,
                process_timestamps=process_timestamps
            )
            
            total_downloaded = len(records)
            
            if records:
                save_result = save_telemetry_records(records, batch_size=batch_size)
                total_saved = save_result['saved_records']
                total_skipped = save_result['skipped_records']
                total_errors = save_result['errors']
        
        # Estado final
        is_empty_after = is_database_empty()
        highest_id_after = get_highest_record_id()
        
        result = {
            "success": True,
            "message": "Sincronización completada exitosamente",
            "download": {
                "total_records_downloaded": total_downloaded
            },
            "save": {
                "total_records": total_downloaded,
                "saved_records": total_saved,
                "skipped_records": total_skipped,
                "errors": total_errors
            },
            "database_status": {
                "was_empty_before": was_empty_before,
                "highest_record_id_before": highest_id_before,
                "is_empty_after": is_empty_after,
                "highest_record_id_after": highest_id_after
            }
        }
        
        # Cachear resultado final
        cache.set(f'telemetry_sync_result_{task_id}', result, timeout=3600)
        
        logger.info(f"Sincronización completada - Task ID: {task_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error en sincronización - Task ID: {task_id}: {str(e)}", exc_info=True)
        raise
```

### 2. Tarea de Merge OTT

**Agregar a:** `TelemetriaDelancer/tasks/telemetry_tasks.py`

```python
@shared_task(bind=True, name='telemetry.merge_ott')
def merge_ott_task(self, max_record_id=None, batch_size=500):
    """
    Tarea asíncrona para merge de registros OTT.
    """
    task_id = self.request.id
    logger.info(f"Iniciando merge OTT - Task ID: {task_id}")
    
    try:
        from TelemetriaDelancer.panaccess.ott_merger import merge_ott_records
        
        # Ejecutar merge
        result = merge_ott_records(
            max_record_id=max_record_id,
            batch_size=batch_size
        )
        
        # Cachear resultado
        cache.set(f'merge_ott_result_{task_id}', result, timeout=3600)
        
        logger.info(f"Merge OTT completado - Task ID: {task_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error en merge OTT - Task ID: {task_id}: {str(e)}", exc_info=True)
        raise
```

### 3. Tarea de Análisis Completo

**Crear archivo:** `TelemetriaDelancer/tasks/analytics_tasks.py`

```python
from celery import shared_task
from django.core.cache import cache
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='analytics.full_analysis')
def full_analysis_task(self, start_date=None, end_date=None, limit=20, period='daily', 
                      forecast_days=7, n_segments=4, include_pandas=True):
    """
    Tarea asíncrona para análisis completo general.
    """
    task_id = self.request.id
    logger.info(f"Iniciando análisis completo - Task ID: {task_id}")
    
    try:
        # Verificar cache primero
        cache_key = f'analytics_full_{start_date}_{end_date}_{limit}_{period}'
        cached_result = cache.get(cache_key)
        
        if cached_result:
            logger.info(f"Resultado encontrado en cache - Task ID: {task_id}")
            return cached_result
        
        # Importar funciones de análisis
        from TelemetriaDelancer.panaccess.analytics import (
            get_top_channels, get_channel_audience, get_peak_hours_by_channel,
            get_average_duration_by_channel, get_temporal_analysis,
            get_geographic_analysis, get_correlation_analysis,
            get_time_series_analysis, get_user_segmentation_analysis,
            get_channel_performance_matrix, get_general_summary,
            get_time_slot_analysis
        )
        
        # Parsear fechas
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        results = {
            "success": True,
            "generated_at": datetime.now().isoformat(),
            "filters": {
                "start_date": start.date().isoformat() if start else None,
                "end_date": end.date().isoformat() if end else None
            },
            "analyses": {}
        }
        
        # Ejecutar análisis (similar a AnalyticsView)
        # ... (código de análisis)
        
        # Cachear resultado (1 hora)
        cache.set(cache_key, results, timeout=3600)
        
        logger.info(f"Análisis completo finalizado - Task ID: {task_id}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error en análisis completo - Task ID: {task_id}: {str(e)}", exc_info=True)
        raise
```

---

## 🌐 Endpoints para Gestionar Tareas

### 1. Endpoint para Encolar Sincronización

**Modificar:** `TelemetriaDelancer/views.py`

```python
from celery.result import AsyncResult
from django.core.cache import cache

class TelemetrySyncView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        POST: Encola tarea de sincronización.
        """
        try:
            limit = int(request.data.get('limit', 100))
            process_timestamps = request.data.get('process_timestamps', True)
            batch_size = int(request.data.get('batch_size', 100))
            
            # Encolar tarea
            from TelemetriaDelancer.tasks.telemetry_tasks import sync_telemetry_task
            
            task = sync_telemetry_task.delay(
                limit=limit,
                process_timestamps=process_timestamps,
                batch_size=batch_size
            )
            
            return Response({
                "success": True,
                "message": "Tarea de sincronización encolada",
                "task_id": task.id,
                "status": "PENDING"
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            logger.error(f"Error al encolar tarea: {str(e)}", exc_info=True)
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request, task_id=None):
        """
        GET: Obtiene estado y resultado de una tarea.
        """
        if not task_id:
            return Response(
                {"error": "task_id es requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            task_result = AsyncResult(task_id)
            
            if task_result.state == 'PENDING':
                response = {
                    "task_id": task_id,
                    "status": "PENDING",
                    "message": "Tarea en cola, esperando ejecución"
                }
            elif task_result.state == 'PROGRESS':
                response = {
                    "task_id": task_id,
                    "status": "PROGRESS",
                    "progress": task_result.info.get('current', 0),
                    "total": task_result.info.get('total', 100),
                    "message": task_result.info.get('status', 'Procesando...'),
                    "downloaded": task_result.info.get('downloaded', 0),
                    "saved": task_result.info.get('saved', 0)
                }
            elif task_result.state == 'SUCCESS':
                response = {
                    "task_id": task_id,
                    "status": "SUCCESS",
                    "result": task_result.result
                }
            else:  # FAILURE
                response = {
                    "task_id": task_id,
                    "status": "FAILURE",
                    "error": str(task_result.info)
                }
            
            return Response(response, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error al obtener estado de tarea: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

### 2. Actualizar URLs

**Modificar:** `TelemetriaDelancer/urls.py`

```python
urlpatterns = [
    # ... rutas existentes
    path('telemetry/sync/', TelemetrySyncView.as_view(), name='telemetry-sync'),
    path('telemetry/sync/<str:task_id>/', TelemetrySyncView.as_view(), name='telemetry-sync-status'),
]
```

---

## 🚀 Ejecutar Celery Worker

### Desarrollo

```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery Worker
celery -A TelemetriaDelancer worker --loglevel=info

# Terminal 3: Celery Beat (para tareas programadas)
celery -A TelemetriaDelancer beat --loglevel=info
```

### Producción (con Supervisor)

**Crear:** `/etc/supervisor/conf.d/celery.conf`

```ini
[program:celery]
command=/path/to/venv/bin/celery -A TelemetriaDelancer worker --loglevel=info
directory=/path/to/project
user=www-data
numprocs=1
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
```

---

## 📊 Monitoreo de Tareas

### Flower (Recomendado)

```bash
pip install flower
celery -A TelemetriaDelancer flower
```

Acceder a: `http://localhost:5555`

### Django Admin (Básico)

```python
# settings.py
CELERY_RESULT_BACKEND = 'django-db'  # Requiere django-celery-results
```

---

## 🔄 Flujo de Usuario Final

### Frontend (Ejemplo con JavaScript)

```javascript
// 1. Iniciar sincronización
const response = await fetch('/delancer/telemetry/sync/', {
  method: 'POST',
  body: JSON.stringify({ limit: 100, batch_size: 100 })
});
const { task_id } = await response.json();

// 2. Polling para obtener progreso
const pollStatus = async () => {
  const statusResponse = await fetch(`/delancer/telemetry/sync/${task_id}/`);
  const status = await statusResponse.json();
  
  if (status.status === 'PROGRESS') {
    // Actualizar UI con progreso
    updateProgressBar(status.progress);
    updateStatus(status.message);
    updateCounts(status.downloaded, status.saved);
    
    // Continuar polling
    setTimeout(pollStatus, 2000); // Cada 2 segundos
  } else if (status.status === 'SUCCESS') {
    // Mostrar resultado final
    showSuccess(status.result);
  } else if (status.status === 'FAILURE') {
    // Mostrar error
    showError(status.error);
  }
};

pollStatus();
```

---

## 📝 Resumen de Beneficios

✅ **Mejor UX:** Respuesta inmediata, progreso en tiempo real
✅ **Escalabilidad:** Múltiples workers procesando tareas en paralelo
✅ **Confiabilidad:** Reintentos automáticos, manejo de errores
✅ **Monitoreo:** Estado de tareas, logs, métricas
✅ **Cache:** Resultados cacheados para análisis repetidos
✅ **Programación:** Tareas automáticas con Celery Beat

---

## ⚠️ Consideraciones Importantes

1. **Redis debe estar disponible** antes de iniciar workers
2. **Configurar límites de tiempo** para evitar tareas infinitas
3. **Manejar errores** adecuadamente con reintentos
4. **Limpiar resultados** antiguos para no llenar Redis
5. **Monitorear memoria** de workers con tareas pesadas (Pandas)

