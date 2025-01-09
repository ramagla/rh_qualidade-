from django.db.models import F, Value, ExpressionWrapper, DateField, DurationField
from django.db.models.functions import Coalesce
from django.utils.timezone import now
from metrologia.models.models_tabelatecnica import TabelaTecnica
from datetime import timedelta
from django.shortcuts import render
from Funcionario.models import Funcionario
from django.shortcuts import render, get_object_or_404

from django.http import JsonResponse



def lista_equipamentos_a_calibrar(request):
    today = now().date()
    range_end = today + timedelta(days=30)

    # Adiciona a anotação para calcular 'proxima_calibracao'
    tabelas = TabelaTecnica.objects.annotate(
        proxima_calibracao=ExpressionWrapper(
            Coalesce(F('data_ultima_calibracao'), Value(today)) +
            ExpressionWrapper(
                Coalesce(F('frequencia_calibracao'), Value(1)) * Value(30),
                output_field=DurationField()
            ),
            output_field=DateField()
        )
    )

    # Equipamentos com calibração vencida
    equipamentos_vencidos = tabelas.filter(proxima_calibracao__lt=today).order_by('proxima_calibracao')

    # Equipamentos próximos do vencimento
    equipamentos_proximos = tabelas.filter(
        proxima_calibracao__gte=today,
        proxima_calibracao__lte=range_end
    ).order_by('proxima_calibracao')

    context = {
        'equipamentos_vencidos': equipamentos_vencidos,
        'equipamentos_proximos': equipamentos_proximos,
    }
    return render(request, 'relatorios/equipamentos_a_calibrar.html', context)

def listar_equipamentos_funcionario(request, funcionario_id):
    # Obtém o funcionário pelo ID
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)

    # Filtra os equipamentos associados ao funcionário
    equipamentos = TabelaTecnica.objects.filter(responsavel=funcionario)

    context = {
        'funcionario': funcionario,
        'equipamentos': equipamentos,
        'data_atual': now().date(),  # Adiciona a data atual

    }
    return render(request, 'relatorios/listar_equipamentos_funcionario.html', context)

def listar_funcionarios_ativos(request):
    funcionarios = Funcionario.objects.filter(status='Ativo').values('id', 'nome')
    return JsonResponse(list(funcionarios), safe=False)

def equipamentos_por_funcionario(request):
    return render(request, 'relatorios/selecionar_funcionario.html')