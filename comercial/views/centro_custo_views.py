from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from ..models.centro_custo import CentroDeCusto, HistoricoCustoCentroDeCusto
from ..forms.centro_custo_form import CentroDeCustoForm

@login_required
@permission_required("Funcionario.view_centrodecusto", raise_exception=True)
def lista_centros_custo(request):
    centros = CentroDeCusto.objects.select_related("departamento").all()
    return render(request, "centro_custo/lista.html", {"centros": centros})

@login_required
@permission_required("Funcionario.add_centrodecusto", raise_exception=True)
def cadastrar_centro_custo(request):
    if request.method == "POST":
        form = CentroDeCustoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Centro de custo cadastrado com sucesso!")
            return redirect("lista_centros_custo")
    else:
        form = CentroDeCustoForm()
    return render(request, "centro_custo/form.html", {"form": form})

@login_required
@permission_required("Funcionario.change_centrodecusto", raise_exception=True)
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
    return render(request, "centro_custo/form.html", {"form": form, "centro": centro})

@login_required
@permission_required("Funcionario.view_centrodecusto", raise_exception=True)
def visualizar_centro_custo(request, pk):
    centro = get_object_or_404(CentroDeCusto, pk=pk)
    historico = centro.historico_custos.all()
    return render(request, "centro_custo/visualizar.html", {
        "centro": centro,
        "historico": historico
    })
