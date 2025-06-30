import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now

from Funcionario.forms import AvaliacaoAnualForm
from Funcionario.models import AvaliacaoAnual, Funcionario
from Funcionario.models.departamentos import Departamentos
from Funcionario.utils.avaliacao_anual_utils import (
    aplicar_filtros_avaliacoes,
    calcular_classificacoes,
)

logger = logging.getLogger(__name__)


@login_required
def lista_avaliacao_anual(request):
    """Exibe a lista de avaliações anuais com filtros e paginação."""
    avaliacoes = AvaliacaoAnual.objects.all()
    avaliacoes = aplicar_filtros_avaliacoes(request, avaliacoes)
    classificacao_counter = calcular_classificacoes(avaliacoes)

    total_avaliacoes = avaliacoes.count()
    paginator = Paginator(avaliacoes, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    funcionarios = (
        Funcionario.objects.filter(id__in=avaliacoes.values_list("funcionario_id", flat=True))
        .distinct()
        .order_by("nome")
    )
    departamentos = (
        Departamentos.objects.filter(ativo=True)
        .values_list("id", "nome")
        .order_by("nome")
    )



    return render(
        request,
        "avaliacao_desempenho_anual/lista_avaliacao_anual.html",
        {
            "avaliacoes": page_obj,
            "total_avaliacoes": total_avaliacoes,
            "classificacao_ruim": classificacao_counter.get("Ruim", 0),
            "classificacao_regular": classificacao_counter.get("Regular", 0),
            "classificacao_bom": classificacao_counter.get("Bom", 0),
            "classificacao_otimo": classificacao_counter.get("Ótimo", 0),
            "funcionarios": funcionarios,
            "departamentos": departamentos,
            "page_obj": page_obj,
        },
    )


@login_required
def cadastrar_avaliacao_anual(request):
    """Exibe e processa o formulário de cadastro de avaliação anual."""
    if request.method == "POST":
        form = AvaliacaoAnualForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("lista_avaliacao_anual")
    else:
        form = AvaliacaoAnualForm()

    funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")
    campos_avaliados = obter_campos_avaliados()

    return render(
        request,
        "avaliacao_desempenho_anual/form_avaliacao_anual.html",
        {"form": form, "funcionarios": funcionarios, "campos_avaliados": campos_avaliados},
    )


@login_required
def editar_avaliacao_anual(request, id):
    """Exibe e processa o formulário de edição de avaliação anual."""
    avaliacao = get_object_or_404(AvaliacaoAnual, id=id)
    if request.method == "POST":
        form = AvaliacaoAnualForm(request.POST, request.FILES, instance=avaliacao)
        if request.POST.get("remover_anexo") == "1" and avaliacao.anexo:
            avaliacao.anexo.delete(save=False)
            avaliacao.anexo = None
        if form.is_valid():
            form.save()
            messages.success(request, "Avaliação anual atualizada com sucesso!")
            return redirect("lista_avaliacao_anual")
        messages.error(request, "Erro ao atualizar a avaliação. Verifique os campos.")
    else:
        form = AvaliacaoAnualForm(instance=avaliacao)

    campos_avaliados = obter_campos_avaliados()
    funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")

    return render(
        request,
        "avaliacao_desempenho_anual/form_avaliacao_anual.html",
        {
            "form": form,
            "avaliacao": avaliacao,
            "funcionarios": funcionarios,
            "campos_avaliados": campos_avaliados,
        },
    )


@login_required
def excluir_avaliacao_anual(request, id):
    """Exclui uma avaliação anual."""
    avaliacao = get_object_or_404(AvaliacaoAnual, id=id)
    if request.method == "POST":
        avaliacao.delete()
    return redirect("lista_avaliacao_anual")


@login_required
def imprimir_avaliacao(request, avaliacao_id):
    """Renderiza a versão de impressão da avaliação anual."""
    avaliacao = get_object_or_404(AvaliacaoAnual, id=avaliacao_id)
    classificacao = avaliacao.calcular_classificacao()

    campos_notas = [
        {"nome": f.verbose_name, "valor": getattr(avaliacao, f.name)}
        for f in avaliacao._meta.fields
        if f.name not in ["id", "funcionario", "avaliador", "data", "observacoes", "pontos_fortes", "pontos_melhorar"]
    ]

    return render(
        request,
        "avaliacao_desempenho_anual/imprimir_avaliacao_anual.html",
        {
            "avaliacao": avaliacao,
            "percentual": classificacao["percentual"],
            "status": classificacao["status"],
            "campos_notas": campos_notas,
        },
    )


@login_required
def visualizar_avaliacao_anual(request, id):
    """Exibe a avaliação anual de forma detalhada."""
    avaliacao = get_object_or_404(AvaliacaoAnual, id=id)
    campos = obter_campos_avaliados()

    status_campos = {
        campo: AvaliacaoAnual.get_status_text(getattr(avaliacao, campo)) for campo in campos
    }
    classificacao = avaliacao.calcular_classificacao()

    return render(
        request,
        "avaliacao_desempenho_anual/visualizar_avaliacao_anual.html",
        {
            "avaliacao": avaliacao,
            "status_campos": status_campos,
            "classificacao": classificacao["status"],
            "percentual": classificacao["percentual"],
            "now": now(),
        },
    )


@login_required
def imprimir_simplificado(request, avaliacao_id):
    """Renderiza a versão simplificada da avaliação anual."""
    avaliacao = get_object_or_404(AvaliacaoAnual, id=avaliacao_id)
    return render(
        request,
        "avaliacao_desempenho_anual/template_simplificado.html",
        {"avaliacao": avaliacao},
    )


@login_required
def cadastrar_type_avaliacao(request):
    """Exibe e processa o formulário simplificado de avaliação via modal."""
    if request.method == "POST":
        form = AvaliacaoAnualForm(request.POST, request.FILES)
        if form.is_valid():
            avaliacao = form.save()
            return JsonResponse({"avaliacao_id": avaliacao.id})
        logger.error(f"Erros no formulário: {form.errors}")
        return JsonResponse(
            {"error": "Erro ao salvar a avaliação", "details": form.errors}, status=400
        )

    form = AvaliacaoAnualForm()
    funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")
    campos_avaliados = obter_campos_avaliados()

    return render(
        request,
        "avaliacao_desempenho_anual/type_avaliacao.html",
        {
            "form": form,
            "campos_avaliados": campos_avaliados,
            "funcionarios": funcionarios,
        },
    )


def obter_campos_avaliados():
    """Retorna a lista de campos avaliados para uso nos formulários."""
    return [
        "postura_seg_trabalho",
        "qualidade_produtividade",
        "trabalho_em_equipe",
        "comprometimento",
        "disponibilidade_para_mudancas",
        "disciplina",
        "rendimento_sob_pressao",
        "proatividade",
        "comunicacao",
        "assiduidade",
    ]
