# tecnico/apps.py
from django.apps import AppConfig

class TecnicoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tecnico"

    def ready(self):
        # importa os signals ao iniciar o app
        from . import signals  # noqa: F401
