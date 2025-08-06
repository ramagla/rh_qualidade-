from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from Funcionario.models import AvaliacaoTreinamento, Funcionario, ListaPresenca, Treinamento
from Funcionario.utils.avaliacao_treinamento_utils import (
    get_opcoes_avaliacao,
    processar_formulario_avaliacao
)


@login_required
def lista_avaliacoes(request):
    """
    Lista todas as avaliações de treinamento com filtros por funcionário, treinamento e período.
    """
    avaliacoes = AvaliacaoTreinamento.objects.all().order_by("funcionario__nome")

    treinamento_id = request.GET.get("treinamento")
    if treinamento_id:
        avaliacoes = avaliacoes.filter(treinamento_id=treinamento_id)

    funcionario_id = request.GET.get("funcionario")
    if funcionario_id:
        avaliacoes = avaliacoes.filter(funcionario_id=funcionario_id)

    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    if data_inicio and data_fim:
        avaliacoes = avaliacoes.filter(data_avaliacao__range=[data_inicio, data_fim])

    total = avaliacoes.count()
    muito_eficaz = avaliacoes.filter(avaliacao_geral=5).count()
    eficaz = avaliacoes.filter(avaliacao_geral=2).count()
    pouco_eficaz = avaliacoes.filter(avaliacao_geral=1).count()

    paginator = Paginator(avaliacoes, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    funcionarios = Funcionario.objects.filter(
        id__in=avaliacoes.values_list("funcionario_id", flat=True).distinct(),
        status="Ativo"
    ).order_by("nome")
    treinamentos = Treinamento.objects.filter(id__in=avaliacoes.values_list("treinamento_id", flat=True).distinct())

    return render(
        request,
        "avaliacao_treinamento/lista_avaliacao.html",
        {
            "avaliacoes_treinamento": page_obj,
            "funcionarios_ativos": funcionarios,
            "listas_presenca": treinamentos,
            "total_avaliacoes": total,
            "muito_eficaz": muito_eficaz,
            "eficaz": eficaz,
            "pouco_eficaz": pouco_eficaz,
            "page_obj": page_obj,
        },
    )


@login_required
def cadastrar_avaliacao(request):
    """
    Cadastra uma nova avaliação de treinamento.
    """
    form, funcionarios, listas_presenca, status = processar_formulario_avaliacao(request)
    if status is True:
        messages.success(request, "Avaliação cadastrada com sucesso!")
        return redirect("lista_avaliacoes")
    data_fim = (
        form.instance.treinamento.data_fim.strftime("%Y-%m-%d")
        if form.instance.treinamento and form.instance.treinamento.data_fim
        else ""
    )
    return render(
        request,
        "avaliacao_treinamento/form_avaliacao.html",
        {
            "form": form,
            "funcionarios": funcionarios,
            "listas_presenca": listas_presenca,
                    "data_fim_treinamento": data_fim,

            **get_opcoes_avaliacao(),
        },
    )


@login_required
def editar_avaliacao(request, id):
    """
    Edita uma avaliação existente.
    """
    avaliacao = get_object_or_404(AvaliacaoTreinamento, id=id)
    form, funcionarios, listas_presenca, status = processar_formulario_avaliacao(request, instance=avaliacao)

    if status is True:
        messages.success(request, "Avaliação atualizada com sucesso!")
        return redirect("lista_avaliacoes")

    treinamentos = Treinamento.objects.filter(funcionarios=avaliacao.funcionario)
    data_fim = (
        form.instance.treinamento.data_fim.strftime("%Y-%m-%d")
        if form.instance.treinamento and form.instance.treinamento.data_fim
        else ""
    )

    return render(
        request,
        "avaliacao_treinamento/form_avaliacao.html",
        {
            "form": form,
            "avaliacao": avaliacao,
            "funcionarios": funcionarios,
            "treinamentos": treinamentos,
            "listas_presenca": listas_presenca,
            "data_fim_treinamento": data_fim,
            **get_opcoes_avaliacao(),
        },
    )


@login_required
def visualizar_avaliacao(request, id):
    """
    Visualiza os detalhes de uma avaliação.
    """
    avaliacao = get_object_or_404(AvaliacaoTreinamento, id=id)

    conhecimento = AvaliacaoTreinamento.OPCOES_CONHECIMENTO
    aplicacao = AvaliacaoTreinamento.OPCOES_APLICACAO
    resultados = AvaliacaoTreinamento.OPCOES_RESULTADOS
    geral_map = {1: "Pouco Eficaz", 2: "Eficaz", 5: "Muito Eficaz"}

    return render(
        request,
        "avaliacao_treinamento/visualizar_avaliacao.html",
        {
            "avaliacao": avaliacao,
            "grau_conhecimento": dict(conhecimento).get(avaliacao.pergunta_1, "Não especificado"),
            "aplicacao_conceitos": dict(aplicacao).get(avaliacao.pergunta_2, "Não especificado"),
            "resultados_obtidos": dict(resultados).get(avaliacao.pergunta_3, "Não especificado"),
            "melhorias": avaliacao.descricao_melhorias,
            "avaliacao_geral": geral_map.get(avaliacao.avaliacao_geral, "Indeterminado"),
            "treinamento": avaliacao.treinamento,
            "now": timezone.now(),
        },
    )


def get_treinamentos_por_funcionario(request, funcionario_id):
    """
    Retorna os treinamentos associados a um funcionário para preenchimento dinâmico.
    """
    treinamentos = ListaPresenca.objects.filter(participantes__id=funcionario_id)
    data = [
        {
            "id": t.id,
            "treinamento": t.treinamento,
            "data_realizacao": t.data_realizacao.strftime("%Y-%m-%d"),
            "assunto": t.assunto,
        }
        for t in treinamentos
    ]
    return JsonResponse(data, safe=False)


@login_required
def imprimir_treinamento(request, treinamento_id):
    """
    Gera o template de impressão da avaliação de treinamento.
    """
    avaliacao = get_object_or_404(AvaliacaoTreinamento, id=treinamento_id)
    funcionario = avaliacao.funcionario

    return render(
        request,
        "avaliacao_treinamento/impressao_treinamento.html",
        {
            "avaliacao": avaliacao,
            "opcoes_conhecimento": AvaliacaoTreinamento.OPCOES_CONHECIMENTO,
            "opcoes_aplicacao": AvaliacaoTreinamento.OPCOES_APLICACAO,
            "opcoes_resultados": AvaliacaoTreinamento.OPCOES_RESULTADOS,
            "responsavel_funcionario": funcionario.responsavel if funcionario else "Não definido",
        },
    )


@login_required
def excluir_avaliacao(request, id):
    """
    Exclui uma avaliação de treinamento.
    """
    avaliacao = get_object_or_404(AvaliacaoTreinamento, id=id)
    avaliacao.delete()
    return redirect("lista_avaliacoes")
