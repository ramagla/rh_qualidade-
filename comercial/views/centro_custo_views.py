from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.utils.timezone import now

from comercial.models.centro_custo import CentroDeCusto
from comercial.forms.centro_custo_form import CentroDeCustoForm


@login_required
@permission_required("comercial.view_centrodecusto", raise_exception=True)
def lista_centros_custo(request):
    centros = CentroDeCusto.objects.all()

    # 🔍 Filtros
    nome = request.GET.get("nome")
    if nome:
        centros = centros.filter(nome__icontains=nome)

    # 📊 Indicadores
    total_centros = centros.count()
    vigentes = centros.filter(vigencia__lte=now().date()).count()
    futuros = centros.filter(vigencia__gt=now().date()).count()

    # 📄 Paginação
    paginator = Paginator(centros.order_by("nome"), 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "total_centros": total_centros,
        "vigentes": vigentes,
        "futuros": futuros,
        "mes_ano": now().strftime("%m/%Y"),
    }

    return render(request, "cadastros/lista_centro_de_custos.html", context)


@login_required
@permission_required("comercial.add_centrodecusto", raise_exception=True)
def cadastrar_centro_custo(request):
    if request.method == "POST":
        form = CentroDeCustoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Centro de custo cadastrado com sucesso!")
            return redirect("lista_centros_custo")
    else:
        form = CentroDeCustoForm()
    return render(request, "cadastros/form_centro_custo.html", {"form": form})


@login_required
@permission_required("comercial.change_centrodecusto", raise_exception=True)
def editar_centro_custo(request, pk):
    centro = get_object_or_404(CentroDeCusto, pk=pk)
    if request.method == "POST":
        form = CentroDeCustoForm(request.POST, instance=centro)
        if form.is_valid():
            form.save()
            messages.success(request, "Centro de custo atualizado com sucesso!")
            return redirect("lista_centros_custo")
    else:
        form = CentroDeCustoForm(instance=centro)
    return render(request, "cadastros/form_centro_custo.html", {"form": form, "centro": centro})


@login_required
@permission_required("comercial.view_centrodecusto", raise_exception=True)
def visualizar_centro_custo(request, pk):
    centro = get_object_or_404(CentroDeCusto, pk=pk)
    historico = centro.historico_custos.all()
    return render(request, "centro_custo/visualizar.html", {
        "centro": centro,
        "historico": historico
    })
