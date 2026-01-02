"""
Configuración de Celery para tareas periódicas.

Este módulo configura Celery para ejecutar tareas en background,
específicamente para sincronización de telemetría y merge OTT.
"""
import os
from celery import Celery

# Establecer el módulo de configuración de Django por defecto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Crear instancia de Celery
app = Celery('TelemetriaDelancer')

# Configurar Celery usando configuración de Django
# El namespace 'CELERY' significa que todas las configuraciones de Celery
# deben tener el prefijo 'CELERY_' en settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descubrir tareas en todas las apps instaladas
# Buscará archivos tasks.py en cada app
app.autodiscover_tasks()

# Configurar tareas periódicas (Beat Schedule)
from celery.schedules import crontab

app.conf.beat_schedule = {
    'sync-and-merge-telemetry': {
        'task': 'TelemetriaDelancer.tasks.sync_and_merge_telemetry_chain',
        'schedule': 120.0,  # Cada 2 minutos (120 segundos)
        # Sin expires - las tareas no expiran, se ejecutan cuando sea necesario
    },
}

# Configuración adicional de Celery
app.conf.update(
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Resultado de tareas (opcional, para monitoreo)
    result_backend='redis://localhost:6379/0',
    
    # Broker (Redis)
    broker_url='redis://localhost:6379/0',
    
    # Configuración de tareas
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Configuración de workers
    # None = sin límite de prefetch, los workers tomarán tareas según su capacidad
    worker_prefetch_multiplier=None,
    task_acks_late=True,  # Confirmar tarea solo después de completarse
    
    # Configuración de reintentos
    task_default_retry_delay=60,  # Reintentar después de 60 segundos
    task_max_retries=3,  # Máximo 3 reintentos
    
    # Sin límites de tiempo - las tareas duran lo que necesiten
    # No establecer task_time_limit ni task_soft_time_limit
    # task_time_limit=None,  # Sin límite de tiempo
    # task_soft_time_limit=None,  # Sin límite soft
)

