# Django - Autenticação e permissões
from django.contrib.auth.decorators import login_required, permission_required

# Django - Mensagens, redirecionamento, renderização, paginação, utilitários
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q

# Utilitários
from datetime import datetime, timedelta
from django.utils.dateparse import parse_duration

# App Interno - Formulários e modelos
from Funcionario.forms.banco_horas_form import BancoHorasForm
from Funcionario.models import Funcionario
from Funcionario.models.banco_horas import BancoHoras
from portaria.models import AtrasoSaida



def parse_horas_trabalhadas(horas_str):
    negativo = horas_str.startswith("-")
    horas_str = horas_str.lstrip("+-")
    partes = horas_str.split(":")
    if len(partes) != 2:
        return None
    try:
        horas = int(partes[0])
        minutos = int(partes[1])
        td = timedelta(hours=horas, minutes=minutos)
        return -td if negativo else td
    except:
        return None

@login_required
@permission_required("Funcionario.view_bancohoras", raise_exception=True)
def listar_banco_horas(request):
    registros = BancoHoras.objects.select_related("funcionario").order_by("-data")

    # Filtros
    funcionario_id = request.GET.get("funcionario")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    if funcionario_id:
        registros = registros.filter(funcionario_id=funcionario_id)

    if data_inicio:
        registros = registros.filter(data__gte=data_inicio)
    if data_fim:
        registros = registros.filter(data__lte=data_fim)

    # Paginação
    paginator = Paginator(registros, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Lista de funcionários ativos (para filtro)
    funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")

    # Formulário para a modal
    form = BancoHorasForm()

    # 🔢 Total de horas trabalhadas visíveis (paginadas)
    total_horas = sum(
        (registro.horas_trabalhadas or timedelta() for registro in page_obj),
        timedelta()
    )


    # 👥 Total de funcionários únicos nos registros filtrados (antes da paginação)
    funcionarios_filtrados = registros.values_list("funcionario", flat=True).distinct()

    context = {
        "page_obj": page_obj,
        "funcionarios": funcionarios,
        "form": form,
        "total_horas": total_horas,
        "funcionarios_unicos_count": funcionarios_filtrados.count(),
    }

    return render(request, "banco_horas/lista_banco_de_horas.html", context)




@login_required
@permission_required("Funcionario.add_bancohoras", raise_exception=True)
def cadastrar_banco_horas(request):
    if request.method == "POST":
        form = BancoHorasForm(request.POST)
        if form.is_valid():
            registro = form.save(commit=False)

            saldo_inicial = request.POST.get("saldo_inicial") == "on"
            horas_str = request.POST.get("horas_trabalhadas")
            he_50 = request.POST.get("he_50") == "on"
            he_100 = request.POST.get("he_100") == "on"
            ocorrencia_id = request.POST.get("ocorrencia_unica")  # nova entrada

            try:
                duracao = parse_horas_trabalhadas(horas_str)
                if duracao is None:
                    messages.error(request, "Formato inválido para Horas Trabalhadas.")
                    return render(request, "banco_horas/form_banco_de_horas.html", {"form": form})

                # Aplica acréscimo de horas extras se necessário
                if he_50:
                    duracao += duracao * 0.5
                elif he_100:
                    duracao += duracao

                registro.horas_trabalhadas = duracao
                registro.saldo_inicial = saldo_inicial
                registro._ocorrencia_vinculada_id = ocorrencia_id

                # ✅ Calcula o saldo de horas com base na entrada e saída, se não vier preenchido
                if not registro.saldo_horas:
                    registro.saldo_horas = 0

                registro.save()



                # Se veio uma ocorrência associada, marque como utilizada
                if ocorrencia_id:
                    try:
                        ocorrencia = AtrasoSaida.objects.get(id=ocorrencia_id)
                        ocorrencia.utilizado_no_banco = True
                        ocorrencia.save()
                    except AtrasoSaida.DoesNotExist:
                        messages.warning(request, "Ocorrência informada não encontrada.")

                messages.success(request, "Registro de banco de horas cadastrado com sucesso.")
                return redirect("listar_banco_horas")
            except Exception:
                messages.error(request, "Erro ao interpretar o campo Horas Trabalhadas.")
        else:
            messages.error(request, "Erro ao cadastrar. Verifique os campos.")
    else:
        form = BancoHorasForm()

    return render(request, "banco_horas/form_banco_de_horas.html", {"form": form})



@login_required
@permission_required("Funcionario.change_bancohoras", raise_exception=True)
def editar_banco_horas(request, pk):
    registro = get_object_or_404(BancoHoras, pk=pk)

    if request.method == "POST":
        form = BancoHorasForm(request.POST, instance=registro)
        if form.is_valid():
            registro = form.save(commit=False)

            saldo_inicial = request.POST.get("saldo_inicial") == "on"
            horas_str = request.POST.get("horas_trabalhadas")
            he_50 = request.POST.get("he_50") == "on"
            he_100 = request.POST.get("he_100") == "on"
            nova_ocorrencia_id = request.POST.get("ocorrencia_unica")

            try:
                duracao = parse_horas_trabalhadas(horas_str)
                if duracao is None:
                    messages.error(request, "Formato inválido para Horas Trabalhadas.")
                    return redirect("editar_banco_horas", pk=pk)

                if he_50:
                    duracao += duracao * 0.5
                elif he_100:
                    duracao += duracao
                ocorrencia_id = request.POST.get("ocorrencia_unica")

                registro.horas_trabalhadas = duracao
                registro.saldo_inicial = saldo_inicial
                registro._ocorrencia_vinculada_id = ocorrencia_id

                # ✅ Calcula saldo se não preenchido manualmente
                if registro.saldo_horas in [None, ""]:
                    saldo = calcular_saldo(registro.hora_entrada, registro.hora_saida)
                    registro.saldo_horas = saldo

                registro.save()



                # (Opcional) Desmarcar ocorrência anterior se estiver trocando
                if "ocorrencia_unica" in request.POST:
                    # ⚠️ Supondo que você tem como saber qual era a ocorrência anterior (ex: campo no modelo)
                    ocorrencia_anterior_id = request.POST.get("ocorrencia_anterior_id")
                    if ocorrencia_anterior_id and ocorrencia_anterior_id != nova_ocorrencia_id:
                        try:
                            ocorrencia_anterior = AtrasoSaida.objects.get(id=ocorrencia_anterior_id)
                            ocorrencia_anterior.utilizado_no_banco = False
                            ocorrencia_anterior.save()
                        except AtrasoSaida.DoesNotExist:
                            pass

                    if nova_ocorrencia_id:
                        try:
                            nova_ocorrencia = AtrasoSaida.objects.get(id=nova_ocorrencia_id)
                            nova_ocorrencia.utilizado_no_banco = True
                            nova_ocorrencia.save()
                        except AtrasoSaida.DoesNotExist:
                            messages.warning(request, "Ocorrência selecionada não encontrada.")

                messages.success(request, "Registro de banco de horas atualizado com sucesso.")
                return redirect("listar_banco_horas")
            except Exception:
                messages.error(request, "Erro ao interpretar o campo Horas Trabalhadas.")
                return redirect("editar_banco_horas", pk=pk)
        else:
            messages.error(request, "Erro ao editar o registro.")
            return render(request, "banco_horas/form_banco_de_horas.html", {"form": form, "registro": registro})

    else:
        form = BancoHorasForm(instance=registro)

    return render(request, "banco_horas/form_banco_de_horas.html", {
        "form": form,
        "registro": registro,
    })






@login_required
@permission_required("Funcionario.delete_bancohoras", raise_exception=True)
def excluir_banco_horas(request, pk):
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
    registro = get_object_or_404(BancoHoras, pk=pk)
    return render(request, "Funcionario/banco_horas/visualizar.html", {"registro": registro})


@login_required
def buscar_ocorrencias_portaria(request, funcionario_id):
    registros = AtrasoSaida.objects.filter(
        funcionario_id=funcionario_id,
        tipo__in=["atraso", "saida"],
        utilizado_no_banco=False
    ).order_by("-data", "-horario")

    print("Registros encontrados:", registros)
    for r in registros:
        print(r.id, r.tipo, r.data, r.horario, r.utilizado_no_banco, r.calcular_duracao())

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

def calcular_saldo(hora_entrada, hora_saida):
    if hora_entrada and hora_saida:
        entrada = datetime.combine(datetime.today(), hora_entrada)
        saida = datetime.combine(datetime.today(), hora_saida)
        duracao = (saida - entrada).total_seconds() / 3600  # em horas
        saldo = duracao - 8  # considera 8h como jornada padrão
        return round(saldo, 2)
    return None