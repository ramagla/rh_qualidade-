from Funcionario.models import AtualizacaoSistema, Settings
from datetime import datetime
from packaging import version

def core_global_settings(request):
    """
    Context processor que retorna configurações globais do sistema,
    evitando colisão de nomes e minimizando consultas ao banco.
    """
    settings = Settings.objects.first()  # ou use .only(...) conforme acima
    versoes_concluidas = (
        AtualizacaoSistema.objects.filter(status="concluido").only("versao", "data_termino")
    )
    versao = "0.0.0"
    if versoes_concluidas.exists():
        ultima_atualizacao = sorted(
            versoes_concluidas,
            key=lambda x: (x.data_termino, version.parse(x.versao)),
            reverse=True
        )[0]
        versao = ultima_atualizacao.versao

    return {
        "core_settings": settings,
        "core_ano_atual": datetime.now().year,
        "core_versao_sistema": versao,
    }
