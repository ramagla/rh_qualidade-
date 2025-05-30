from packaging import version
from Funcionario.models import AtualizacaoSistema, Settings
from datetime import datetime

def global_settings(request):
    settings = Settings.objects.first()

    versoes_concluidas = AtualizacaoSistema.objects.filter(
        status="concluido"
    )

    ultima_atualizacao = sorted(
        versoes_concluidas,
        key=lambda x: (x.data_termino, version.parse(x.versao)),
        reverse=True
    )[0] if versoes_concluidas else None

    versao = ultima_atualizacao.versao if ultima_atualizacao else "0.0.0"

    return {
        "settings": settings,
        "ano_atual": datetime.now().year,
        "versao": versao,
    }
