from datetime import datetime
from django.shortcuts import render
from Funcionario.models import Comunicado, AtualizacaoSistema, Settings  # e outros modelos relevantes

def dashboard(request):
    comunicados = Comunicado.objects.order_by('-data')[:5]
    proximas_atualizacoes = AtualizacaoSistema.objects.order_by('previsao')[:5]
    funcionarios_baixa_avaliacao = [
        {'nome': 'João da Silva', 'cargo': 'Operador', 'avaliacao': 'Insatisfatória'},
        {'nome': 'Maria Souza', 'cargo': 'Analista', 'avaliacao': 'Insatisfatória'},
    ]  # Exemplo de dados mockados

    context = {
        'comunicados': comunicados,
        'proximas_atualizacoes': proximas_atualizacoes,
        'funcionarios_baixa_avaliacao': funcionarios_baixa_avaliacao,
    }
    return render(request, 'dashboard.html', context)



