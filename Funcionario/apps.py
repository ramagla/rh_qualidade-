from django.apps import AppConfig

class FuncionarioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Funcionario"

    def ready(self):
        try:
            import Funcionario.signals
        except ImportError:
            pass 
