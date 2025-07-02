from django.db.models import Count

from Funcionario.models import Comunicado


def obter_tipo_choices_validos():
    """
    Retorna os tipos de comunicados cadastrados no banco.
    """
    tipos_cadastrados = Comunicado.objects.values_list("tipo", flat=True).distinct()
    return [
        choice for choice in Comunicado.TIPO_CHOICES if choice[0] in tipos_cadastrados
    ]


def aplicar_filtros_comunicado(queryset, tipo, departamento, data_inicio, data_fim):
    """
    Aplica os filtros de tipo, departamento e data na queryset de comunicados.
    """
    if tipo:
        queryset = queryset.filter(tipo=tipo)
    if departamento:
        queryset = queryset.filter(departamento_responsavel=departamento)
    if data_inicio and data_fim:
        queryset = queryset.filter(data__range=[data_inicio, data_fim])
    elif data_inicio:
        queryset = queryset.filter(data__gte=data_inicio)
    elif data_fim:
        queryset = queryset.filter(data__lte=data_fim)
    return queryset


def obter_dados_cards_comunicado(queryset):
    """
    Retorna a contagem total e por tipo dos comunicados para os cards.
    """
    total = queryset.count()
    por_tipo = queryset.values("tipo").annotate(total=Count("tipo")).order_by("tipo")
    return total, por_tipo
