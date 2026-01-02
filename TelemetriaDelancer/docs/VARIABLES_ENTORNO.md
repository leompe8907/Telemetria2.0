# Variables de Entorno - Configuración

## 📋 Archivo .env

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

## 🔧 Variables Requeridas

### Django
```env
SECRET_KEY=tu-secret-key-aqui
ALLOWED_HOSTS=localhost,127.0.0.1
salt=tu-salt-aqui
```

### PanAccess
```env
drmDelancer=https://tu-servidor-panaccess.com
usernameDelancer=tu-usuario
passwordDelancer=tu-contraseña
api_tokenDelancer=tu-api-token
```

### Celery/Redis
```env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## ⚙️ Variables Opcionales (con valores por defecto)

### Celery - Configuración Avanzada

```env
# Serialización (default: json)
CELERY_TASK_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_RESULT_SERIALIZER=json

# Timezone (default: UTC)
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=True

# Workers (default: None = sin límite)
CELERY_WORKER_PREFETCH_MULTIPLIER=None

# Confirmación de tareas (default: True)
CELERY_TASK_ACKS_LATE=True

# Reintentos (default: 60 segundos, 3 intentos)
CELERY_TASK_DEFAULT_RETRY_DELAY=60
CELERY_TASK_MAX_RETRIES=3

# Rastreo de tareas (default: True)
CELERY_TASK_TRACK_STARTED=True
```

## 📝 Ejemplo Completo de .env

```env
# ============================================================================
# CONFIGURACIÓN DE DJANGO
# ============================================================================

SECRET_KEY=django-insecure-tu-secret-key-aqui-cambiar-en-produccion
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
salt=tu-salt-secreto-aqui

# ============================================================================
# CONFIGURACIÓN DE PANACCESS
# ============================================================================

drmDelancer=https://tu-servidor-panaccess.com
usernameDelancer=tu-usuario
passwordDelancer=tu-contraseña
api_tokenDelancer=tu-api-token

# ============================================================================
# CONFIGURACIÓN DE CELERY/REDIS
# ============================================================================

# Redis local (default)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Redis remoto (ejemplo)
# CELERY_BROKER_URL=redis://usuario:password@redis.example.com:6379/0
# CELERY_RESULT_BACKEND=redis://usuario:password@redis.example.com:6379/0

# Configuración opcional (puedes omitir estas líneas, usarán valores por defecto)
CELERY_TASK_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_RESULT_SERIALIZER=json
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=True
CELERY_WORKER_PREFETCH_MULTIPLIER=None
CELERY_TASK_ACKS_LATE=True
CELERY_TASK_DEFAULT_RETRY_DELAY=60
CELERY_TASK_MAX_RETRIES=3
CELERY_TASK_TRACK_STARTED=True
```

## 🔐 Generar SECRET_KEY

Para generar un SECRET_KEY seguro:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 📍 Ubicación del Archivo

El archivo `.env` debe estar en la raíz del proyecto, al mismo nivel que `manage.py`:

```
Telemetria/
├── .env              ← Aquí
├── manage.py
├── config.py
├── backend/
└── TelemetriaDelancer/
```

## ⚠️ Importante

1. **NUNCA** subas el archivo `.env` al repositorio
2. Asegúrate de que `.env` esté en `.gitignore`
3. En producción, usa valores seguros
4. No uses `DEBUG=True` en producción
5. Cambia todos los valores por defecto en producción

## 🔍 Verificar Configuración

Para verificar que todas las variables están configuradas correctamente:

```bash
python manage.py check
```

O desde Python:

```python
from config import DjangoConfig, CeleryConfig, PanaccessConfigDelancer

# Esto lanzará una excepción si faltan variables requeridas
DjangoConfig.validate()
CeleryConfig.validate()
PanaccessConfigDelancer.validate()
```

---

**Última actualización:** 2025-01-XX  
**Versión:** 1.0

