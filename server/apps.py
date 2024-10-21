# apps.py
from django.apps import AppConfig

class MainAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'loocal'

    def ready(self):
        # Importa y registra tu receptor de señal aquí
        from . import signals
