import locale
from datetime import date

from django.utils.timezone import now

from Funcionario.models import Funcionario


def obter_valores_mes_ano(request):
    """Retorna mês e ano válidos a partir da requisição."""
    try:
        mes = int(request.GET.get("mes") or now().month)
        ano = int(request.GET.get("ano") or now().year)
    except ValueError:
        mes = now().month
        ano = now().year
    return mes, ano


def obter_nome_mes(mes, ano):
    """Retorna o nome do mês por extenso em português."""
    try:
        locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
    except locale.Error:
        locale.setlocale(locale.LC_TIME, "Portuguese_Brazil.1252")

    data_base = date(ano, mes, 1)
    return data_base.strftime("%B").capitalize()


def obter_funcionarios_ativos_ordenados():
    """Retorna todos os funcionários ativos ordenados por nome."""
    return Funcionario.objects.filter(status="Ativo").order_by("nome")
