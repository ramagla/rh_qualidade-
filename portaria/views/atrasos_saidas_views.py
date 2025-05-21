from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.utils.timezone import now
from datetime import date
from ..models import AtrasoSaida  # modelo que representa os eventos
from Funcionario.models import Funcionario
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from portaria.forms.AtrasoSaidaForm import AtrasoSaidaForm
from django.db.models import Q



@login_required
@permission_required("portaria.view_funcionario", raise_exception=True)
def lista_atrasos_saidas(request):
    eventos = AtrasoSaida.objects.select_related("funcionario").order_by("-data", "-horario")

    # Filtros
    nome = request.GET.get("nome")
    data_filtro = request.GET.get("data")
    tipo = request.GET.get("tipo")

    if nome:
        eventos = eventos.filter(funcionario__nome=nome)
    if data_filtro:
        eventos = eventos.filter(data=data_filtro)
    if tipo in ["atraso", "saida", "hora_extra"]:
        eventos = eventos.filter(tipo=tipo)

    # Indicadores
    total_registros = eventos.count()
    total_hoje = eventos.filter(data=date.today()).count()

    # Contar registros sem justificativa (exceto hora extra)
    total_sem_justificativa = eventos.exclude(tipo="hora_extra").filter(
        Q(observacao__isnull=True) | Q(observacao__exact="")
    ).count()

    # Contar registros do tipo hora extra
    total_hora_extra = eventos.filter(tipo="hora_extra").count()

    nomes_disponiveis = Funcionario.objects.filter(status="Ativo").values_list("nome", flat=True).distinct()

    context = {
        "eventos": eventos,
        "nomes_disponiveis": nomes_disponiveis,
        "total_registros": total_registros,
        "total_hoje": total_hoje,
        "total_sem_justificativa": total_sem_justificativa,
        "total_hora_extra": total_hora_extra,
    }

    return render(request, "atrasosSaidas/atrasos_saidas_lista.html", context)

@login_required
@permission_required("portaria.add_atrasosaida", raise_exception=True)
def cadastrar_atraso_saida(request):
    if request.method == "POST":
        form = AtrasoSaidaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Ocorrência registrada com sucesso!")
            return redirect("lista_atrasos_saidas")
    else:
        form = AtrasoSaidaForm()

    return render(request, "atrasosSaidas/form_atrasos_saidas.html", {"form": form})

@login_required
@permission_required("portaria.change_atrasosaida", raise_exception=True)
def editar_atraso_saida(request, pk):
    ocorrencia = get_object_or_404(AtrasoSaida, pk=pk)

    if request.method == "POST":
        form = AtrasoSaidaForm(request.POST, instance=ocorrencia)
        if form.is_valid():
            form.save()
            messages.success(request, "Ocorrência atualizada com sucesso!")
            return redirect("lista_atrasos_saidas")
    else:
        form = AtrasoSaidaForm(instance=ocorrencia)

    return render(request, "atrasosSaidas/form_atrasos_saidas.html", {"form": form})

@login_required
@permission_required("portaria.delete_atrasosaida", raise_exception=True)
def excluir_atraso_saida(request, pk):
    atraso_saida = get_object_or_404(AtrasoSaida, pk=pk)
    atraso_saida.delete()
    messages.success(request, "Ocorrência excluída com sucesso.")
    return redirect("lista_atrasos_saidas")

@login_required
@permission_required("portaria.view_atrasosaida", raise_exception=True)
def visualizar_atraso_saida(request, pk):
    ocorrencia = get_object_or_404(AtrasoSaida, pk=pk)
    return render(request, "portaria/atrasos_saidas/visualizar.html", {
        "ocorrencia": ocorrencia,
        "now": now()
    })