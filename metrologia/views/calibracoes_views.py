from django.shortcuts import render, get_object_or_404, redirect
from metrologia.models.models_calibracao import Calibracao
from metrologia.forms import CalibracaoForm
from metrologia.models.models_tabelatecnica import TabelaTecnica
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator


def lista_calibracoes(request):
    # Query inicial para pegar os equipamentos com calibração associada
    calibracoes = Calibracao.objects.select_related('codigo').all()

    # Filtros
    filtro_codigo = request.GET.get('codigo')
    filtro_laboratorio = request.GET.get('laboratorio')
    filtro_status = request.GET.get('status')
    filtro_tipo = request.GET.get('tipo')
    filtro_proprietario = request.GET.get('proprietario')
    data_inicial = request.GET.get('data_inicio')
    data_final = request.GET.get('data_fim')

    # Filtrando apenas os equipamentos com calibrações associadas
    calibracoes = calibracoes.filter(codigo__in=TabelaTecnica.objects.filter(calibracao__isnull=False))

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
        calibracoes = calibracoes.filter(data_calibracao__range=[data_inicial, data_final])

    # Dados para os filtros
    codigos = TabelaTecnica.objects.filter(calibracao__isnull=False).values_list('codigo', flat=True).distinct()
    proprietarios = TabelaTecnica.objects.values_list('proprietario', flat=True).distinct()
    laboratorios = Calibracao.objects.values_list('laboratorio', flat=True).distinct()
    tipos = TabelaTecnica.objects.values_list('tipo_avaliacao', flat=True).distinct()

    # Paginação
    paginator = Paginator(calibracoes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Contagem de status
    total_calibracoes = calibracoes.count()
    total_aprovadas = calibracoes.filter(status="Aprovado").count()
    total_reprovadas = calibracoes.filter(status="Reprovado").count()

    return render(request, 'calibracoes/lista_calibracoes.html', {
        'page_obj': page_obj,
        'codigos': codigos,
        'proprietarios': proprietarios,
        'laboratorios': laboratorios,
        'tipos': tipos,
        'filtro_proprietario': filtro_proprietario,
        'total_calibracoes': total_calibracoes,
        'total_aprovadas': total_aprovadas,
        'total_reprovadas': total_reprovadas,
    })


def metrologia_calibracoes(request):
    calibracoes = Calibracao.objects.all()
    return render(request, 'calibracoes/lista_calibracoes.html', {'calibracoes': calibracoes})



def cadastrar_calibracao(request):
    if request.method == "POST":
        form = CalibracaoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('calibracoes_instrumentos')
    else:
        # Inicializa o formulário e passa os dados necessários
        form = CalibracaoForm()
    
    return render(request, 'calibracoes/cadastrar_calibracao.html', {'form': form})


def editar_calibracao(request, pk):
    # Obtenha a instância da Calibração
    calibracao = get_object_or_404(Calibracao, pk=pk)

    if request.method == 'POST':
        form = CalibracaoForm(request.POST, request.FILES, instance=calibracao)
        if form.is_valid():
            form.save()
            return redirect('calibracoes_instrumentos')  # Redireciona para a lista
    else:
        form = CalibracaoForm(instance=calibracao)  # Carrega a instância no formulário

    # Renderiza o template com o formulário preenchido
    return render(request, 'calibracoes/editar_calibracao.html', {'form': form})


def excluir_calibracao(request, id):
    calibracao = get_object_or_404(Calibracao, id=id)
    if request.method == "POST":
        calibracao.delete()
        return redirect('calibracoes_instrumentos')
    return render(request, 'calibracoes/excluir_calibracao.html', {'calibracao': calibracao})

from django.core.exceptions import ObjectDoesNotExist
from decimal import Decimal



def obter_exatidao_requerida(request, equipamento_id):
    try:
        equipamento = TabelaTecnica.objects.get(id=equipamento_id)

        # Garante que faixa e tolerância em percentual nunca sejam None e converte para Decimal
        faixa = equipamento.faixa if equipamento.faixa else Decimal('0')
        tolerancia_em_percentual = equipamento.tolerancia_em_percentual if equipamento.tolerancia_em_percentual else Decimal('0')

        # Calcula exatidão requerida
        if equipamento.tipo == 'sim' and faixa > 0 and tolerancia_em_percentual > 0:
            exatidao_requerida = faixa * (tolerancia_em_percentual / Decimal('100'))
        else:
            exatidao_requerida = equipamento.exatidao_requerida or Decimal('0')

        return JsonResponse({
            "tipo": equipamento.tipo,
            "faixa": float(faixa),
            "tolerancia_em_percentual": float(tolerancia_em_percentual),
            "exatidao_requerida": float(exatidao_requerida),
            "tipo_avaliacao": equipamento.get_tipo_avaliacao_display(),  # Adiciona o tipo de avaliação
        })

    except TabelaTecnica.DoesNotExist:
        return JsonResponse({"error": "Equipamento não encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)