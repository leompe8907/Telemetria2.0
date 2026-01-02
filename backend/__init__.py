"""
Este archivo asegura que la app de Celery se cargue cuando Django arranque.
"""
from TelemetriaDelancer.celery import app as celery_app

__all__ = ('celery_app',)

