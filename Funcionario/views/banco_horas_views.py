from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from Funcionario.forms.banco_horas_form import BancoHorasForm
from Funcionario.models import Funcionario
from Funcionario.models.banco_horas import BancoHoras
from portaria.models import AtrasoSaida
from Funcionario.utils.banco_horas_utils import parse_horas_trabalhadas, calcular_saldo


@login_required
@permission_required("Funcionario.view_bancohoras", raise_exception=True)
def listar_banco_horas(request):
    """Exibe a lista de registros de banco de horas com filtros e paginação."""
    registros = BancoHoras.objects.select_related("funcionario").order_by("-data")

    funcionario_id = request.GET.get("funcionario")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    if funcionario_id:
        registros = registros.filter(funcionario_id=funcionario_id)
    if data_inicio:
        registros = registros.filter(data__gte=data_inicio)
    if data_fim:
        registros = registros.filter(data__lte=data_fim)

    paginator = Paginator(registros, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")

    total_horas = sum(
        (registro.horas_trabalhadas or timedelta() for registro in page_obj),
        timedelta()
    )
    funcionarios_filtrados = registros.values_list("funcionario", flat=True).distinct()

    context = {
        "page_obj": page_obj,
        "funcionarios": funcionarios,
        "form": BancoHorasForm(),
        "total_horas": total_horas,
        "funcionarios_unicos_count": funcionarios_filtrados.count(),
    }

    return render(request, "banco_horas/lista_banco_de_horas.html", context)


@login_required
@permission_required("Funcionario.add_bancohoras", raise_exception=True)
def cadastrar_banco_horas(request):
    """Realiza o cadastro de novo registro no banco de horas."""
    if request.method == "POST":
        form = BancoHorasForm(request.POST)
        if form.is_valid():
            registro = form.save(commit=False)
            horas_str = request.POST.get("horas_trabalhadas")
            duracao = parse_horas_trabalhadas(horas_str)

            if duracao is None:
                messages.error(request, "Formato inválido para Horas Trabalhadas.")
                return render(request, "banco_horas/form_banco_de_horas.html", {"form": form})

            if request.POST.get("he_50") == "on":
                duracao += duracao * 0.5
            elif request.POST.get("he_100") == "on":
                duracao += duracao

            registro.horas_trabalhadas = duracao
            registro.saldo_inicial = request.POST.get("saldo_inicial") == "on"
            registro._ocorrencia_vinculada_id = request.POST.get("ocorrencia_unica")
            if not registro.saldo_horas:
                registro.saldo_horas = 0
            registro.save()

            ocorrencia_id = request.POST.get("ocorrencia_unica")
            if ocorrencia_id:
                try:
                    ocorrencia = AtrasoSaida.objects.get(id=ocorrencia_id)
                    ocorrencia.utilizado_no_banco = True
                    ocorrencia.save()
                except AtrasoSaida.DoesNotExist:
                    messages.warning(request, "Ocorrência informada não encontrada.")

            messages.success(request, "Registro de banco de horas cadastrado com sucesso.")
            return redirect("listar_banco_horas")
        messages.error(request, "Erro ao cadastrar. Verifique os campos.")
    else:
        form = BancoHorasForm()

    return render(request, "banco_horas/form_banco_de_horas.html", {"form": form})


@login_required
@permission_required("Funcionario.change_bancohoras", raise_exception=True)
def editar_banco_horas(request, pk):
    """Edita um registro existente de banco de horas."""
    registro = get_object_or_404(BancoHoras, pk=pk)

    if request.method == "POST":
        form = BancoHorasForm(request.POST, instance=registro)
        if form.is_valid():
            registro = form.save(commit=False)
            horas_str = request.POST.get("horas_trabalhadas")
            duracao = parse_horas_trabalhadas(horas_str)

            if duracao is None:
                messages.error(request, "Formato inválido para Horas Trabalhadas.")
                return redirect("editar_banco_horas", pk=pk)

            if request.POST.get("he_50") == "on":
                duracao += duracao * 0.5
            elif request.POST.get("he_100") == "on":
                duracao += duracao

            registro.horas_trabalhadas = duracao
            registro.saldo_inicial = request.POST.get("saldo_inicial") == "on"
            registro._ocorrencia_vinculada_id = request.POST.get("ocorrencia_unica")

            if registro.saldo_horas in [None, ""]:
                registro.saldo_horas = calcular_saldo(registro.hora_entrada, registro.hora_saida)

            registro.save()

            nova_id = request.POST.get("ocorrencia_unica")
            anterior_id = request.POST.get("ocorrencia_anterior_id")
            if anterior_id and anterior_id != nova_id:
                try:
                    AtrasoSaida.objects.filter(id=anterior_id).update(utilizado_no_banco=False)
                except AtrasoSaida.DoesNotExist:
                    pass

            if nova_id:
                try:
                    AtrasoSaida.objects.filter(id=nova_id).update(utilizado_no_banco=True)
                except AtrasoSaida.DoesNotExist:
                    messages.warning(request, "Ocorrência selecionada não encontrada.")

            messages.success(request, "Registro de banco de horas atualizado com sucesso.")
            return redirect("listar_banco_horas")

        messages.error(request, "Erro ao editar o registro.")

    return render(request, "banco_horas/form_banco_de_horas.html", {
        "form": BancoHorasForm(instance=registro),
        "registro": registro,
    })


@login_required
@permission_required("Funcionario.delete_bancohoras", raise_exception=True)
def excluir_banco_horas(request, pk):
    """Exclui um registro de banco de horas após confirmação."""
    registro = get_object_or_404(BancoHoras, pk=pk)
    if request.method == "POST":
        registro.delete()
        messages.success(request, "Registro excluído com sucesso.")
        return redirect("listar_banco_horas")

    return render(request, "partials/_modal_exclusao.html", {
        "objeto": registro,
        "url_excluir": "excluir_banco_horas",
    })


@login_required
@permission_required("Funcionario.view_bancohoras", raise_exception=True)
def visualizar_banco_horas(request, pk):
    """Exibe detalhes de um registro de banco de horas."""
    registro = get_object_or_404(BancoHoras, pk=pk)
    return render(request, "Funcionario/banco_horas/visualizar.html", {"registro": registro})


@login_required
def buscar_ocorrencias_portaria(request, funcionario_id):
    """Retorna as ocorrências de atraso e saída não utilizadas no banco de horas."""
    registros = AtrasoSaida.objects.filter(
        funcionario_id=funcionario_id,
        tipo__in=["atraso", "saida"],
        utilizado_no_banco=False
    ).order_by("-data", "-horario")

    dados = []
    for r in registros:
        duracao = r.calcular_duracao()
        if not duracao or duracao.total_seconds() <= 0:
            continue
        dados.append({
            "id": r.id,
            "data": r.data.strftime("%d/%m/%Y"),
            "horario": r.horario.strftime("%H:%M") if r.horario else "",
            "tipo": r.get_tipo_display(),
            "observacao": r.observacao or "",
            "duracao": r.calcular_duracao_formatada()
        })

    return JsonResponse({"registros": dados})
