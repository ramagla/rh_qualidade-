from django.apps import AppConfig

class ComercialConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'comercial'

    def ready(self):
        import comercial.signals  # Ativa os signals ao carregar a app
