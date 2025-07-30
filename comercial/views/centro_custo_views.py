from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.utils.timezone import now

from comercial.models.centro_custo import CentroDeCusto
from comercial.forms.centro_custo_form import CentroDeCustoForm
from functools import wraps
from django.core.exceptions import PermissionDenied

def requer_acesso_comercial(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.has_perm("comercial.acesso_comercial"):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped

@login_required
@requer_acesso_comercial
@permission_required("comercial.view_centrodecusto", raise_exception=True)
def lista_centros_custo(request):
    centros = CentroDeCusto.objects.all()

    # 🔍 Filtros
    nome = request.GET.get("departamento")  # O campo do filtro se chama "departamento"
    if nome:
        centros = centros.filter(nome=nome)

    # 📊 Indicadores
    total_centros = centros.count()
    vigentes = centros.filter(vigencia__lte=now().date()).count()
    futuros = centros.filter(vigencia__gt=now().date()).count()

    # 📄 Paginação
    paginator = Paginator(centros.order_by("nome"), 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Lista de departamentos únicos
    nomes_departamentos = CentroDeCusto.objects.values_list("nome", flat=True).distinct()

    context = {
        "page_obj": page_obj,
        "total_centros": total_centros,
        "vigentes": vigentes,
        "futuros": futuros,
        "mes_ano": now().strftime("%m/%Y"),
        "nomes_departamentos": nomes_departamentos,  # para o filtro
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
    historico = centro.historico_custos.all().order_by("-alterado_em")

    context = {
        "centro": centro,
        "historico": historico,
    }
    return render(request, "cadastros/visualizar_centro_de_custos.html", context)
