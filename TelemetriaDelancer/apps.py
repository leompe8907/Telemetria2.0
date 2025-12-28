from django.apps import AppConfig
import os
import logging

logger = logging.getLogger(__name__)


class TelemetriadelancerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'TelemetriaDelancer'


    def ready(self):
        """
        Se ejecuta cuando Django está completamente cargado.
        Aquí inicializamos el singleton de PanAccess.
        
        Nota: En modo desarrollo (runserver), Django crea dos procesos:
        - Proceso principal (monitor de archivos)
        - Proceso hijo (servidor real)
        
        Solo inicializamos en el proceso hijo para evitar duplicación.
        """
        # En modo desarrollo, solo ejecutar en el proceso hijo (servidor real)
        # Django establece RUN_MAIN solo en el proceso hijo
        if os.environ.get('RUN_MAIN') != 'true':
            # Estamos en el proceso principal (monitor), no inicializar
            return
        
        try:
            from TelemetriaDelancer.server.panaccess_singleton import initialize_panaccess
            logger.info("🚀 Inicializando PanAccess singleton...")
            initialize_panaccess()
        except Exception as e:
            logger.error(f"❌ Error al inicializar PanAccess en ready(): {str(e)}")
            # No lanzamos excepción para que Django pueda arrancar
            logger.warning("⚠️ El sistema intentará autenticarse en el primer request")