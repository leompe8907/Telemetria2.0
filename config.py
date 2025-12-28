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
