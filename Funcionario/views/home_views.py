from django.shortcuts import render
from Funcionario.models import Comunicado, AtualizacaoSistema
import requests

# Página inicial com a listagem de feriados, comunicados e atualizações do sistema
def home(request):
    # URL para API de feriados
    url = 'https://brasilapi.com.br/api/feriados/v1/2025'
    feriados = []
    try:
        response = requests.get(url)
        if response.status_code == 200:
            feriados = response.json()
    except Exception as e:
        print("Exceção ao chamar a API:", e)
    
    # Consulta aos últimos comunicados
    comunicados = Comunicado.objects.order_by('-data')[:5]
    
    # Dados fictícios para funcionários com avaliação baixa
    funcionarios_avaliacao_baixa = [
        {"nome": "Funcionário 1", "avaliacao": "Baixa"},
        {"nome": "Funcionário 2", "avaliacao": "Baixa"},
        {"nome": "Funcionário 3", "avaliacao": "Baixa"},
    ]
    
    # Consulta às próximas atualizações do sistema
    proximas_atualizacoes = AtualizacaoSistema.objects.order_by('-previsao')[:5]

    # Contexto para o template
    context = {
        'feriados': feriados,
        'comunicados': comunicados,
        'funcionarios_avaliacao_baixa': funcionarios_avaliacao_baixa,
        'proximas_atualizacoes': proximas_atualizacoes,
    }
    
    return render(request, 'home.html', context)

def sucesso_view(request):
    return render(request, 'sucesso.html') 
