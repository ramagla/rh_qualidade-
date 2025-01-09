from django.apps import AppConfig


class MetrologiaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "metrologia"

    def ready(self):
        import metrologia.signals
