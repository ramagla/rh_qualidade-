# Django - Funcionalidades principais
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now

# App Interno - Formulários e modelos
from Funcionario.forms import ComunicadoForm
from Funcionario.models import Comunicado, Funcionario



@login_required
def lista_comunicados(request):
    comunicados = Comunicado.objects.all().order_by("-id")
    departamentos = Comunicado.objects.values_list(
        "departamento_responsavel", flat=True
    ).distinct()

    # Obtenção dos tipos cadastrados no banco
    tipos_cadastrados = Comunicado.objects.values_list("tipo", flat=True).distinct()

    # Filtrar TIPO_CHOICES com base nos tipos cadastrados
    tipo_choices = [
        choice for choice in Comunicado.TIPO_CHOICES if choice[0] in tipos_cadastrados
    ]

    # Obtenção dos filtros
    tipo = request.GET.get("tipo", "")
    departamento = request.GET.get("departamento", "")
    data_inicio = request.GET.get("data_inicio", "")
    data_fim = request.GET.get("data_fim", "")

    # Filtros com condicional
    if tipo:
        comunicados = comunicados.filter(tipo=tipo)
    if departamento:
        comunicados = comunicados.filter(departamento_responsavel=departamento)
    if data_inicio and data_fim:
        comunicados = comunicados.filter(data__range=[data_inicio, data_fim])
    elif data_inicio:
        comunicados = comunicados.filter(data__gte=data_inicio)
    elif data_fim:
        comunicados = comunicados.filter(data__lte=data_fim)

    # Paginação
    paginator = Paginator(comunicados, 10)  # 10 comunicados por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Dados para os cards
    total_comunicados = comunicados.count()
    comunicados_por_tipo = (
        comunicados.values("tipo").annotate(total=Count("tipo")).order_by("tipo")
    )

    # Contexto do template com os filtros aplicados
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
        "tipo_choices": tipo_choices,  # Apenas tipos cadastrados
    }

    return render(request, "comunicados/lista_comunicados.html", context)


@login_required
def imprimir_comunicado(request, id):
    comunicado = get_object_or_404(Comunicado, id=id)
    return render(
        request,
        "comunicados/imprimir_comunicado.html",
        {
            "comunicado": comunicado,
            "now": now(),  # ✅ adiciona o timestamp
        },
    )


@login_required
def cadastrar_comunicado(request):
    if request.method == "POST":
        form = ComunicadoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Comunicado cadastrado com sucesso!")
            return redirect("lista_comunicados")
    else:
        form = ComunicadoForm()

    return render(
        request,
        "comunicados/form_comunicado.html",
        {
            "form": form,
            "comunicado": None,
            "edicao": False,
            "param_id": None,
            "ultima_atualizacao_concluida": None,
            "ultima_atualizacao": now(),  # <- Aqui está o que falta!
        },
    )



@login_required
def visualizar_comunicado(request, id):
    comunicado = get_object_or_404(Comunicado, id=id)
    return render(
        request,
        "comunicados/visualizar_comunicado.html",
        {
            "comunicado": comunicado,
            "now": now(),  # <-- aqui está o ajuste
        }
    )


@login_required
def editar_comunicado(request, id):
    comunicado = get_object_or_404(Comunicado, id=id)

    if request.method == "POST":
        form = ComunicadoForm(
            request.POST, request.FILES, instance=comunicado
        )  # Inclua request.FILES aqui
        if form.is_valid():
            form.save()
            return redirect("lista_comunicados")
    else:
        # Carrega os dados existentes do banco
        form = ComunicadoForm(instance=comunicado)

    return render(
        request,
        "comunicados/form_comunicado.html",
        {"form": form, "comunicado": comunicado},
    )


@login_required
def excluir_comunicado(request, id):
    comunicado = get_object_or_404(Comunicado, id=id)
    if request.method == "POST":
        comunicado.delete()
        messages.success(request, "Comunicado excluído com sucesso!")
    # Redireciona sempre para a lista de comunicados, pois a confirmação já foi feita via modal
    return redirect("lista_comunicados")


@login_required
def imprimir_assinaturas(request, id):
    comunicado = get_object_or_404(Comunicado, id=id)
    funcionarios_ativos = Funcionario.objects.filter(status="Ativo").order_by("nome")
    return render(
        request,
        "comunicados/imprimir_assinaturas.html",
        {
            "comunicado": comunicado,
            "funcionarios_ativos": funcionarios_ativos,
            "now": now(),  # ✅ adiciona o timestamp
        },
    )


