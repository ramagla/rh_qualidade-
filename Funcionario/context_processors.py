# Funcionario/context_processors.py
from datetime import datetime

from Funcionario.models import AtualizacaoSistema, Settings


def global_settings(request):
    settings = Settings.objects.first()
    ultima_atualizacao = AtualizacaoSistema.objects.order_by("-previsao").first()
    versao = ultima_atualizacao.versao if ultima_atualizacao else "1.0.0"

    return {
        "settings": settings,
        "ano_atual": datetime.now().year,
        "versao": versao,
    }
