from datetime import datetime
from Funcionario.models import AtualizacaoSistema
from alerts.models import AlertaUsuario

from contexto_menu.metrologia import menu_metrologia
from contexto_menu.rh import menu_rh
from contexto_menu.qualidade import menu_qualidade
from contexto_menu.portaria import menu_portaria
from contexto_menu.home import menu_home
from contexto_menu.modulos_disponiveis import listar_modulos
from contexto_menu.comercial import menu_comercial



def global_menu(request):
    user = request.user
    path_parts = request.path.split("/")
    active_module = path_parts[1] if len(path_parts) > 1 else ""

    # Escolhe qual menu carregar com base no módulo ativo
    if active_module == "metrologia":
        menu = menu_metrologia(user)
    elif active_module == "qualidade":
        menu = menu_qualidade(user)
    elif active_module == "portaria":
        menu = menu_portaria(user)
    elif active_module == "rh":
        menu = menu_rh(user)
    elif active_module == "comercial":
        menu = menu_comercial(user)

    else:
        # Módulo principal (home)
        menu = menu_home(user)

    # Módulos disponíveis
    modulos_disponiveis = listar_modulos(user)

    # Detecta módulo ativo (usando a URL base como identificador)
    modulo_ativo = next((m for m in modulos_disponiveis if active_module in m["url"]), None)

    # Alertas (in-app)
    alertas_nao_lidos = 0
    ultimos_alertas = []
    if user.is_authenticated:
        alertas_nao_lidos = AlertaUsuario.objects.filter(usuario=user, lido=False).count()
        ultimos_alertas = AlertaUsuario.objects.filter(usuario=user).order_by("-criado_em")[:5]

    # Atualizações do sistema
    ultima = AtualizacaoSistema.objects.filter(status="concluido").order_by("-data_termino").first()
    historico = AtualizacaoSistema.objects.filter(
        status="concluido"
    ).exclude(
        id=ultima.id if ultima else None
    ).order_by("-data_termino")

    # Retorno do contexto global
    return {
        "menu": menu,
        "modulo_ativo": modulo_ativo,
        "modulos_disponiveis": modulos_disponiveis,
        "ano_atual": datetime.now().year,
        "alertas_nao_lidos": alertas_nao_lidos,
        "ultimos_alertas": ultimos_alertas,
        "ultima_atualizacao_concluida": ultima,
        "historico_versoes": historico,
    }
