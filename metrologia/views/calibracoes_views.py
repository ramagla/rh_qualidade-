from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from metrologia.forms import CalibracaoForm
from metrologia.models.models_calibracao import Calibracao
from metrologia.models.models_tabelatecnica import TabelaTecnica
from django.contrib.auth.decorators import login_required, permission_required

@login_required
@permission_required("metrologia.view_calibracao", raise_exception=True)
def lista_calibracoes(request):
    # Query inicial para pegar os equipamentos com calibração associada
    calibracoes = Calibracao.objects.select_related("codigo").all()

    # Filtros
    filtro_codigo = request.GET.get("codigo")
    filtro_laboratorio = request.GET.get("laboratorio")
    filtro_status = request.GET.get("status")
    filtro_tipo = request.GET.get("tipo")
    filtro_proprietario = request.GET.get("proprietario")
    data_inicial = request.GET.get("data_inicio")
    data_final = request.GET.get("data_fim")

    # Filtrando apenas os equipamentos com calibrações associadas
    calibracoes = calibracoes.filter(
        codigo__in=TabelaTecnica.objects.filter(calibracao__isnull=False)
    )

    # Aplicar filtros de acordo com os valores recebidos
    if filtro_codigo:
        calibracoes = calibracoes.filter(codigo__codigo=filtro_codigo)
    if filtro_laboratorio:
        calibracoes = calibracoes.filter(laboratorio__icontains=filtro_laboratorio)
    if filtro_status:
        calibracoes = calibracoes.filter(status=filtro_status)
    if filtro_tipo:
        calibracoes = calibracoes.filter(codigo__tipo_avaliacao=filtro_tipo)
    if filtro_proprietario:
        calibracoes = calibracoes.filter(codigo__proprietario=filtro_proprietario)
    if data_inicial and data_final:
        calibracoes = calibracoes.filter(
            data_calibracao__range=[data_inicial, data_final]
        )

    # Dados para os filtros
    codigos = (
        TabelaTecnica.objects.filter(calibracao__isnull=False)
        .values_list("codigo", flat=True)
        .distinct()
    )
    proprietarios = TabelaTecnica.objects.values_list(
        "proprietario", flat=True
    ).distinct()
    laboratorios = Calibracao.objects.values_list("laboratorio", flat=True).distinct()
    tipos = TabelaTecnica.objects.values_list("tipo_avaliacao", flat=True).distinct()

    # Paginação
    paginator = Paginator(calibracoes, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Contagem de status
    total_calibracoes = calibracoes.count()
    total_aprovadas = calibracoes.filter(status="Aprovado").count()
    total_reprovadas = calibracoes.filter(status="Reprovado").count()

    return render(
        request,
        "calibracoes/lista_calibracoes.html",
        {
            "page_obj": page_obj,
            "codigos": codigos,
            "proprietarios": proprietarios,
            "laboratorios": laboratorios,
            "tipos": tipos,
            "filtro_proprietario": filtro_proprietario,
            "total_calibracoes": total_calibracoes,
            "total_aprovadas": total_aprovadas,
            "total_reprovadas": total_reprovadas,
        },
    )


def salvar_calibracao(request, pk=None):
    edicao = pk is not None
    calibracao = get_object_or_404(Calibracao, pk=pk) if edicao else None

    if request.method == "POST":
        form = CalibracaoForm(request.POST, request.FILES, instance=calibracao)
        if form.is_valid():
            form.save()
            return redirect("calibracoes_instrumentos")
    else:
        form = CalibracaoForm(instance=calibracao)

    contexto = {
        "form": form,
        "edicao": edicao,
        "param_id": pk,
        "url_voltar": "calibracoes_instrumentos"
    }
    return render(request, "calibracoes/form_calibracao.html", contexto)

@login_required
@permission_required("metrologia.view_calibracao", raise_exception=True)
def metrologia_calibracoes(request):
    calibracoes = Calibracao.objects.all()
    return render(
        request, "calibracoes/lista_calibracoes.html", {"calibracoes": calibracoes}
    )

@login_required
@permission_required("metrologia.add_calibracao", raise_exception=True)
def cadastrar_calibracao(request):
    return salvar_calibracao(request)


@login_required
@permission_required("metrologia.change_calibracao", raise_exception=True)
def editar_calibracao(request, pk):
    return salvar_calibracao(request, pk=pk)

@login_required
@permission_required("metrologia.delete_calibracao", raise_exception=True)
def excluir_calibracao(request, id):
    calibracao = get_object_or_404(Calibracao, id=id)
    if request.method == "POST":
        calibracao.delete()
        return redirect("calibracoes_instrumentos")
    return render(
        request, "calibracoes/excluir_calibracao.html", {"calibracao": calibracao}
    )


def obter_exatidao_requerida(request, equipamento_id):
    try:
        equipamento = TabelaTecnica.objects.get(id=equipamento_id)

        # Garante que faixa e tolerância em percentual nunca sejam None e converte para Decimal
        faixa = equipamento.faixa if equipamento.faixa else Decimal("0")
        tolerancia_em_percentual = (
            equipamento.tolerancia_em_percentual
            if equipamento.tolerancia_em_percentual
            else Decimal("0")
        )

        # Calcula exatidão requerida
        if equipamento.tipo == "sim" and faixa > 0 and tolerancia_em_percentual > 0:
            exatidao_requerida = faixa * (tolerancia_em_percentual / Decimal("100"))
        else:
            exatidao_requerida = equipamento.exatidao_requerida or Decimal("0")

        return JsonResponse(
            {
                "tipo": equipamento.tipo,
                "faixa": float(faixa),
                "tolerancia_em_percentual": float(tolerancia_em_percentual),
                "exatidao_requerida": float(exatidao_requerida),
                "tipo_avaliacao": equipamento.get_tipo_avaliacao_display(),  # Adiciona o tipo de avaliação
            }
        )

    except TabelaTecnica.DoesNotExist:
        return JsonResponse({"error": "Equipamento não encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
