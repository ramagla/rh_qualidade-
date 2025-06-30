from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now

from Funcionario.forms import ComunicadoForm
from Funcionario.models import Comunicado, Funcionario
from Funcionario.utils.comunicado_utils import (
    obter_tipo_choices_validos,
    aplicar_filtros_comunicado,
    obter_dados_cards_comunicado,
)


@login_required
def lista_comunicados(request):
    """
    Lista os comunicados com filtros por tipo, departamento e datas, e paginação.
    """
    comunicados = Comunicado.objects.all().order_by("-id")
    tipo = request.GET.get("tipo", "")
    departamento = request.GET.get("departamento", "")
    data_inicio = request.GET.get("data_inicio", "")
    data_fim = request.GET.get("data_fim", "")

    comunicados = aplicar_filtros_comunicado(
        comunicados, tipo, departamento, data_inicio, data_fim
    )

    paginator = Paginator(comunicados, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    tipo_choices = obter_tipo_choices_validos()
    departamentos = Comunicado.objects.values_list(
        "departamento_responsavel", flat=True
    ).distinct()
    total_comunicados, comunicados_por_tipo = obter_dados_cards_comunicado(comunicados)

    context = {
        "comunicados": page_obj,
        "page_obj": page_obj,
        "departamentos": departamentos,
        "tipo": tipo,
        "departamento": departamento,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "total_comunicados": total_comunicados,
        "comunicados_por_tipo": comunicados_por_tipo,
        "tipo_choices": tipo_choices,
    }
    return render(request, "comunicados/lista_comunicados.html", context)


@login_required
def imprimir_comunicado(request, id):
    """
    Renderiza o comunicado em formato de impressão.
    """
    comunicado = get_object_or_404(Comunicado, id=id)
    return render(
        request,
        "comunicados/imprimir_comunicado.html",
        {"comunicado": comunicado, "now": now()},
    )


@login_required
def cadastrar_comunicado(request):
    """
    Cadastra um novo comunicado.
    """
    if request.method == "POST":
        form = ComunicadoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Comunicado cadastrado com sucesso!")
            return redirect("lista_comunicados")
    else:
        form = ComunicadoForm()

    context = {
        "form": form,
        "comunicado": None,
        "edicao": False,
        "param_id": None,
        "ultima_atualizacao_concluida": None,
        "ultima_atualizacao": now(),
    }
    return render(request, "comunicados/form_comunicado.html", context)


@login_required
def visualizar_comunicado(request, id):
    """
    Exibe os detalhes do comunicado.
    """
    comunicado = get_object_or_404(Comunicado, id=id)
    return render(
        request,
        "comunicados/visualizar_comunicado.html",
        {"comunicado": comunicado, "now": now()},
    )


@login_required
def editar_comunicado(request, id):
    """
    Edita um comunicado existente.
    """
    comunicado = get_object_or_404(Comunicado, id=id)
    if request.method == "POST":
        form = ComunicadoForm(request.POST, request.FILES, instance=comunicado)
        if form.is_valid():
            form.save()
            return redirect("lista_comunicados")
    else:
        form = ComunicadoForm(instance=comunicado)

    return render(
        request,
        "comunicados/form_comunicado.html",
        {"form": form, "comunicado": comunicado},
    )


@login_required
def excluir_comunicado(request, id):
    """
    Exclui um comunicado existente.
    """
    comunicado = get_object_or_404(Comunicado, id=id)
    if request.method == "POST":
        comunicado.delete()
        messages.success(request, "Comunicado excluído com sucesso!")
    return redirect("lista_comunicados")


@login_required
def imprimir_assinaturas(request, id):
    """
    Gera a página de impressão das assinaturas do comunicado.
    """
    comunicado = get_object_or_404(Comunicado, id=id)
    funcionarios_ativos = Funcionario.objects.filter(status="Ativo").order_by("nome")
    return render(
        request,
        "comunicados/imprimir_assinaturas.html",
        {
            "comunicado": comunicado,
            "funcionarios_ativos": funcionarios_ativos,
            "now": now(),
        },
    )
