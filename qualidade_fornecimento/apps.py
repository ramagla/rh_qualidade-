from django.apps import AppConfig


class QualidadeFornecimentoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "qualidade_fornecimento"

    def ready(self):
        import qualidade_fornecimento.signals
