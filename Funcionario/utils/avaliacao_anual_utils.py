from collections import Counter
from datetime import datetime

from django.contrib import messages


def aplicar_filtros_avaliacoes(request, avaliacoes_queryset):
    """Aplica filtros de funcionário, departamento e datas em um queryset de avaliações."""
    funcionario_id = request.GET.get("funcionario")
    departamento = request.GET.get("departamento")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    if funcionario_id:
        avaliacoes_queryset = avaliacoes_queryset.filter(funcionario_id=funcionario_id)

    if departamento and departamento != "None":
        avaliacoes_queryset = avaliacoes_queryset.filter(
            funcionario__local_trabalho_id=departamento
        )



    if data_inicio and data_fim:
        try:
            data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            data_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
            avaliacoes_queryset = avaliacoes_queryset.filter(
                data_avaliacao__range=[data_inicio, data_fim]
            )
        except ValueError:
            messages.error(
                request, "Formato de data inválido. Use o formato AAAA-MM-DD."
            )

    return avaliacoes_queryset


def calcular_classificacoes(avaliacoes):
    """Calcula as classificações e percentuais de um queryset de avaliações."""
    classificacao_counter = Counter()

    for avaliacao in avaliacoes:
        classificacao = avaliacao.calcular_classificacao()
        classificacao_status = classificacao["status"]
        classificacao_percentual = classificacao["percentual"]

        classificacao_counter[classificacao_status] += 1
        avaliacao.classificacao = classificacao_status
        avaliacao.percentual = classificacao_percentual

    return classificacao_counter
