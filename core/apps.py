from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        # Importa sinais relacionados à criação de permissões customizadas
        import core.signals.permissoes_signals
