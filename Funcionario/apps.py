from django.apps import AppConfig

class FuncionarioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Funcionario"

    def ready(self):
        import Funcionario.signals
