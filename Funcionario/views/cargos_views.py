# Django core
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

# Local apps
from ..forms import CargoForm, RevisaoForm
from ..models import Cargo, Funcionario, Revisao
from ..utils.cargos_utils import (
    agrupar_cargos_por_nivel,
    obter_dados_cards,
    preencher_datas_formulario
)
from Funcionario.models.departamentos import Departamentos


@login_required
def organograma_cargos(request):
    """Exibe o organograma de cargos com funcionário ativo por nível hierárquico."""
    niveis_ordenados = agrupar_cargos_por_nivel()
    return render(request, "cargos/organograma_cargos.html", {"niveis_ordenados": niveis_ordenados})


@login_required
def lista_cargos(request):
    """Lista os cargos com filtros, paginação e dados analíticos."""
    cargos = Cargo.objects.all().order_by("nome")
    departamento = request.GET.get("departamento")
    cargo_nome = request.GET.get("cargo")

    if departamento:
        cargos = cargos.filter(departamento=departamento)
    if cargo_nome:
        cargos = cargos.filter(nome=cargo_nome)

    for cargo in cargos:
        cargo.ultima_revisao = cargo.revisoes.order_by("-data_revisao").first()

    paginator = Paginator(cargos, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "cargos": page_obj,
        "page_obj": page_obj,
        "departamentos": Departamentos.objects.all(),
        "todos_cargos": Cargo.objects.all().distinct("nome").order_by("nome"),
    }
    context.update(obter_dados_cards(cargos))

    return render(request, "cargos/lista_cargos.html", context)


@login_required
def cadastrar_cargo(request):
    """Cadastra um novo cargo com o formulário apropriado."""
    form = CargoForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        cargo = form.save()
        return redirect("lista_cargos")
    return render(request, "cargos/form_cargo.html", {"form": form, "cargo": form.instance})



@login_required
def editar_cargo(request, cargo_id):
    cargo = get_object_or_404(Cargo, pk=cargo_id)
    form = CargoForm(
        request.POST or None,
        request.FILES or None,
        instance=cargo,
        initial=preencher_datas_formulario(cargo)
    )
    if request.method == "POST" and form.is_valid():
        # Remoção solicitada pelo partial (_campo_anexo.html)
        if request.POST.get("remover_descricao_arquivo") == "1" and cargo.descricao_arquivo:
            cargo.descricao_arquivo.delete(save=False)
            cargo.descricao_arquivo = None

        form.save()
        return redirect("lista_cargos")

    return render(request, "cargos/form_cargo.html", {"form": form, "cargo": cargo})


@login_required
def excluir_cargo(request, cargo_id):
    """Exclui um cargo com base no ID."""
    cargo = get_object_or_404(Cargo, id=cargo_id)
    cargo.delete()
    messages.success(request, "Cargo excluído com sucesso!")
    return redirect("lista_cargos")


@login_required
def historico_revisoes(request, cargo_id):
    """Exibe o histórico de revisões de um cargo."""
    cargo = get_object_or_404(Cargo, id=cargo_id)
    revisoes = cargo.revisoes.all()
    return render(request, "cargos/historico_revisoes.html", {"cargo": cargo, "revisoes": revisoes})


@login_required
def adicionar_revisao(request, cargo_id):
    """Adiciona uma nova revisão para um cargo específico."""
    cargo = get_object_or_404(Cargo, id=cargo_id)
    form = RevisaoForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        revisao = form.save(commit=False)
        revisao.cargo = cargo
        revisao.save()
        return redirect("historico_revisoes", cargo_id=cargo_id)

    return render(
        request,
        "cargos/adicionar_revisao.html",
        {
            "form": form,
            "cargo": cargo,
            "titulo_pagina": f"Adicionar Revisão para {cargo.nome}",
            "param_id": cargo.id,
        },
    )


@login_required
def excluir_revisao(request, revisao_id):
    """Exclui uma revisão e redireciona para o histórico do cargo correspondente."""
    revisao = get_object_or_404(Revisao, id=revisao_id)
    cargo_id = revisao.cargo.id
    revisao.delete()
    messages.success(request, "Revisão excluída com sucesso.")
    return redirect("historico_revisoes", cargo_id=cargo_id)


@login_required
def buscar_cargos(request, funcionario_id):
    """Retorna os cargos inicial e atual de um funcionário."""
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    data = {
        "cargo_inicial": funcionario.cargo_inicial.nome,
        "cargo_atual": funcionario.cargo_atual.nome,
    }
    return JsonResponse(data)


def obter_cargos(request, funcionario_id):
    """API para obter dados brutos de cargos de um funcionário por ID."""
    try:
        funcionario = Funcionario.objects.get(pk=funcionario_id)
        cargos = {
            "cargo_inicial": funcionario.cargo_inicial,
            "cargo_atual": funcionario.cargo_atual,
        }
        return JsonResponse(cargos)
    except Funcionario.DoesNotExist:
        return JsonResponse({"error": "Funcionário não encontrado"}, status=404)


@login_required
def imprimir_cargo(request, cargo_id):
    """Renderiza o template de impressão de cargo com revisões."""
    cargo = get_object_or_404(Cargo, pk=cargo_id)
    revisoes = cargo.revisoes.all().order_by("-data_revisao")
    return render(request, "cargos/imprimir_cargo.html", {"cargo": cargo, "revisoes": revisoes})

@login_required
def obter_treinamentos_por_cargo(request, cargo_id):
    """Retorna os treinamentos internos e externos de um cargo."""
    cargo = get_object_or_404(Cargo, id=cargo_id)
    return JsonResponse({
        "treinamento_interno": cargo.treinamento_interno_minimo or "",
        "treinamento_externo": cargo.treinamento_externo or "",
    })
