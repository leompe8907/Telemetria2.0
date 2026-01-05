import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Cargar variables desde el archivo .env
load_dotenv()

def _csv(name):
    raw = os.getenv(name, "")
    return [x.strip() for x in raw.split(",") if x.strip()]

class PanaccessConfigDelancer:
    drmDelancer = os.getenv("drmDelancer")
    usernameDelancer = os.getenv("usernameDelancer")
    passwordDelancer = os.getenv("passwordDelancer")
    api_tokenDelancer = os.getenv("api_tokenDelancer")

    @classmethod
    def validate(cls):
        missing = []
        if not cls.drmDelancer:
            missing.append("drmDelancer")
        if not cls.usernameDelancer:
            missing.append("usernameDelancer")
        if not cls.passwordDelancer:
            missing.append("password")
        if not cls.api_tokenDelancer:
            missing.append("api_tokenDelancer")

        if missing:
            raise EnvironmentError(f"❌ Faltan variables de entorno: {', '.join(missing)}")

class DjangoConfig:
    SECRET_KEY = os.getenv("SECRET_KEY")
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    ALLOWED_HOSTS = _csv("ALLOWED_HOSTS") # usar ALLOWED_HOSTS (plural) y filtrar vacíos
    SALT = os.getenv("salt")

    @classmethod
    def validate(cls):
        missing = []
        if not cls.SECRET_KEY:
            missing.append("SECRET_KEY")
        if not cls.ALLOWED_HOSTS:
            missing.append("ALLOWED_HOSTS")
        if not cls.SALT:
            missing.append("SALT")
        if missing:
            raise EnvironmentError(f"❌ Faltan variables de entorno: {', '.join(missing)}")

class CeleryConfig:
    """
    Configuración de Celery para tareas periódicas.
    
    Variables requeridas:
    - CELERY_BROKER_URL: URL del broker Redis (requerido)
    - CELERY_RESULT_BACKEND: URL del backend de resultados Redis (requerido)
    
    Variables opcionales (tienen valores por defecto):
    - CELERY_TASK_SERIALIZER: Serializador de tareas (default: 'json')
    - CELERY_ACCEPT_CONTENT: Contenido aceptado (default: ['json'])
    - CELERY_RESULT_SERIALIZER: Serializador de resultados (default: 'json')
    - CELERY_TIMEZONE: Zona horaria (default: 'UTC')
    - CELERY_ENABLE_UTC: Habilitar UTC (default: True)
    - CELERY_WORKER_PREFETCH_MULTIPLIER: Multiplicador de prefetch (default: None)
    - CELERY_TASK_ACKS_LATE: Confirmar tarea después de completarse (default: True)
    - CELERY_TASK_DEFAULT_RETRY_DELAY: Delay entre reintentos en segundos (default: 60)
    - CELERY_TASK_MAX_RETRIES: Máximo de reintentos (default: 3)
    - CELERY_TASK_TRACK_STARTED: Rastrear inicio de tareas (default: True)
    """
    # Variables requeridas
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    # Serialización (valores por defecto)
    CELERY_TASK_SERIALIZER = os.getenv("CELERY_TASK_SERIALIZER", "json")
    CELERY_ACCEPT_CONTENT = _csv("CELERY_ACCEPT_CONTENT") or ["json"]
    CELERY_RESULT_SERIALIZER = os.getenv("CELERY_RESULT_SERIALIZER", "json")
    
    # Timezone (valores por defecto)
    CELERY_TIMEZONE = os.getenv("CELERY_TIMEZONE", "UTC")
    CELERY_ENABLE_UTC = os.getenv("CELERY_ENABLE_UTC", "True").lower() in ("true", "1", "yes")
    
    # Configuración de workers (valores por defecto)
    # Prefetch multiplier: None = sin límite, los workers toman tareas según necesidad
    prefetch_multiplier = os.getenv("CELERY_WORKER_PREFETCH_MULTIPLIER", "None")
    if prefetch_multiplier.lower() == "none" or prefetch_multiplier == "":
        CELERY_WORKER_PREFETCH_MULTIPLIER = None
    else:
        try:
            CELERY_WORKER_PREFETCH_MULTIPLIER = int(prefetch_multiplier)
        except ValueError:
            CELERY_WORKER_PREFETCH_MULTIPLIER = None
    
    CELERY_TASK_ACKS_LATE = os.getenv("CELERY_TASK_ACKS_LATE", "True").lower() in ("true", "1", "yes")
    
    # Configuración de reintentos (valores por defecto)
    CELERY_TASK_DEFAULT_RETRY_DELAY = int(os.getenv("CELERY_TASK_DEFAULT_RETRY_DELAY", "60"))
    CELERY_TASK_MAX_RETRIES = int(os.getenv("CELERY_TASK_MAX_RETRIES", "3"))
    
    # Configuración de tareas (valores por defecto)
    CELERY_TASK_TRACK_STARTED = os.getenv("CELERY_TASK_TRACK_STARTED", "True").lower() in ("true", "1", "yes")
    
    # Sin límites de tiempo por defecto (las tareas duran lo que necesiten)
    # Estas variables no se usan, pero se pueden configurar si se necesita
    # CELERY_TASK_TIME_LIMIT = os.getenv("CELERY_TASK_TIME_LIMIT")
    # CELERY_TASK_SOFT_TIME_LIMIT = os.getenv("CELERY_TASK_SOFT_TIME_LIMIT")

    @classmethod
    def validate(cls):
        """
        Valida que las variables requeridas estén configuradas.
        Las variables opcionales tienen valores por defecto, así que no se validan.
        """
        missing = []
        if not cls.CELERY_BROKER_URL:
            missing.append("CELERY_BROKER_URL")
        if not cls.CELERY_RESULT_BACKEND:
            missing.append("CELERY_RESULT_BACKEND")
        
        if missing:
            raise EnvironmentError(f"❌ Faltan variables de entorno requeridas: {', '.join(missing)}")

class MariaConfig:
    """
    Configuración de base de datos MariaDB/MySQL.
    
    Variables requeridas:
    - Maria_HOST: Host de la base de datos
    - Maria_PORT: Puerto de la base de datos
    - Maria_USER: Usuario de la base de datos
    - Maria_NAME: Nombre de la base de datos
    
    Variables opcionales:
    - Maria_PASSWORD: Contraseña de la base de datos (default: '')
    """
    Maria_HOST = os.getenv("Maria_HOST", "127.0.0.1")
    Maria_PORT = os.getenv("Maria_PORT", "3307")
    Maria_USER = os.getenv("Maria_USER", "root")
    Maria_NAME = os.getenv("Maria_NAME") or os.getenv("Maria_DB")  # Soporta ambos nombres
    Maria_PASSWORD = os.getenv("Maria_PASSWORD", "")

    @classmethod
    def validate(cls):
        missing = []
        if not cls.Maria_HOST:
            missing.append("Maria_HOST")
        if not cls.Maria_PORT:
            missing.append("Maria_PORT")
        if not cls.Maria_USER:
            missing.append("Maria_USER")
        if not cls.Maria_NAME:
            missing.append("Maria_NAME o Maria_DB")
        # Maria_PASSWORD es opcional, no se valida
        
        if missing:
            raise EnvironmentError(f"❌ Faltan variables de entorno requeridas: {', '.join(missing)}")
            