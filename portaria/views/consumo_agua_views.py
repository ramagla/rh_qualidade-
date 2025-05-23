from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404, redirect
from portaria.forms.registro_agua_form import RegistroConsumoAguaForm
from portaria.models.consumo_agua import RegistroConsumoAgua
from django.contrib import messages

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from portaria.models.consumo_agua import RegistroConsumoAgua
from django.db.models import F, ExpressionWrapper, DecimalField
from django.utils.timezone import now

@login_required
@permission_required("portaria.view_registroconsumoagua", raise_exception=True)
def listar_consumo_agua(request):
    registros = RegistroConsumoAgua.objects.annotate(
        consumo=ExpressionWrapper(
            F("leitura_final") - F("leitura_inicial"),
            output_field=DecimalField(max_digits=6, decimal_places=2)
        )
    ).order_by("-data")

    # Filtros
    data = request.GET.get("data")
    consumo_minimo = request.GET.get("consumo_minimo")
    consumo_maximo = request.GET.get("consumo_maximo")

    if data:
        registros = registros.filter(data=data)
    if consumo_minimo:
        registros = registros.filter(consumo__gte=consumo_minimo)
    if consumo_maximo:
        registros = registros.filter(consumo__lte=consumo_maximo)

    # Indicadores
    total_acima = registros.filter(consumo__gt=5).count()
    total_dentro = registros.filter(consumo__lte=5).count()

    context = {
        "registros": registros,
        "total_acima": total_acima,
        "total_dentro": total_dentro,
    }

    return render(request, "agua/consumo_agua_lista.html", context)

@login_required
@permission_required("portaria.add_registroconsumoagua", raise_exception=True)
def cadastrar_consumo_agua(request):
    if request.method == "POST":
        form = RegistroConsumoAguaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registro salvo com sucesso.")
            return redirect("listar_consumo_agua")
    else:
        form = RegistroConsumoAguaForm()
    return render(request, "agua/form_consumo_agua.html", {"form": form, "registro": None})

@login_required
@permission_required("portaria.change_registroconsumoagua", raise_exception=True)
def editar_consumo_agua(request, pk):
    registro = get_object_or_404(RegistroConsumoAgua, pk=pk)
    if request.method == "POST":
        form = RegistroConsumoAguaForm(request.POST, instance=registro)
        if form.is_valid():
            form.save()
            messages.success(request, "Registro atualizado com sucesso.")
            return redirect("listar_consumo_agua")
    else:
        form = RegistroConsumoAguaForm(instance=registro)
    return render(request, "agua/form_consumo_agua.html", {"form": form, "registro": registro})


@login_required
@permission_required("portaria.delete_registroconsumoagua", raise_exception=True)
def excluir_consumo_agua(request, pk):
    registro = get_object_or_404(RegistroConsumoAgua, pk=pk)
    registro.delete()
    messages.success(request, "Registro excluído com sucesso.")
    return redirect("listar_consumo_agua")