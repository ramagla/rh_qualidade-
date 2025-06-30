# Django
from django.db.models import Q

# Local
from Funcionario.models import JobRotationEvaluation


def filtrar_avaliacoes(request):
    """Aplica filtros à queryset de avaliações de Job Rotation."""
    evaluations = JobRotationEvaluation.objects.select_related("cargo_atual").all()
    funcionario_id = request.GET.get("funcionario")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    if funcionario_id:
        evaluations = evaluations.filter(funcionario_id=funcionario_id)

    if data_inicio and data_fim:
        evaluations = evaluations.filter(data_inicio__range=[data_inicio, data_fim])

    return evaluations


def obter_totais(evaluations):
    """Retorna contadores agregados para os cards da tela de listagem."""
    return {
        "total_avaliacoes": evaluations.count(),
        "apto": evaluations.filter(avaliacao_rh="Apto").count(),
        "prorrogar": evaluations.filter(avaliacao_rh="Prorrogar TN").count(),
        "inapto": evaluations.filter(avaliacao_rh="Inapto").count(),
    }


def gerar_descricao_cargo(evaluation):
    """Gera a descrição formatada da nova função para impressão."""
    ultima_revisao = (
        evaluation.nova_funcao.revisoes.order_by("-data_revisao").first()
        if evaluation.nova_funcao else None
    )
    if evaluation.nova_funcao and ultima_revisao:
        descricao = (
            f"Conforme: Descrição de cargo N° {evaluation.nova_funcao.numero_dc} - "
            f"Nome: {evaluation.nova_funcao.nome}, "
            f"Última Revisão N° {ultima_revisao.numero_revisao}"
        )
    else:
        descricao = "Descrição de cargo não disponível"
    return descricao, ultima_revisao
