from django.shortcuts import render
from Funcionario.models import Comunicado, AtualizacaoSistema, Settings
from django.contrib.auth.decorators import login_required
import requests
from datetime import datetime


# Página inicial com a listagem de feriados, comunicados e atualizações do sistema
@login_required
def home(request):
    # Obter feriados da API
    url = 'https://brasilapi.com.br/api/feriados/v1/2025'
    feriados = []
    try:
        response = requests.get(url)
        if response.status_code == 200:
            feriados = response.json()
    except Exception as e:
        print("Exceção ao chamar a API:", e)
    
    # Consulta aos últimos comunicados
    comunicados = Comunicado.objects.order_by('-data')[:4]
    
    # Dados fictícios para funcionários com avaliação baixa
    funcionarios_avaliacao_baixa = [
        {"nome": "Funcionário 1", "avaliacao": "Baixa"},
        {"nome": "Funcionário 2", "avaliacao": "Baixa"},
        {"nome": "Funcionário 3", "avaliacao": "Baixa"},
    ]
    
    # Consulta às próximas atualizações do sistema
    proximas_atualizacoes = AtualizacaoSistema.objects.order_by('-previsao')[:5]
    
    # Consulta às configurações da empresa, incluindo logos
    settings = Settings.objects.first()  # Obtém a primeira instância de Settings, caso haja mais de uma

    # Contexto para o template
    context = {
        'feriados': feriados,
        'comunicados': comunicados,
        'funcionarios_avaliacao_baixa': funcionarios_avaliacao_baixa,
        'proximas_atualizacoes': proximas_atualizacoes,
        'settings': settings,  # Inclui settings para acesso aos logos
    }
    
    return render(request, 'home.html', context)

def sucesso_view(request):
    return render(request, 'sucesso.html')


def login_view(request):
    # Obtém o logo e outras configurações
    settings = Settings.objects.first()
    
    # Obtém a última versão registrada
    ultima_atualizacao = AtualizacaoSistema.objects.order_by('-previsao').first()
    
    # Contexto para o template de login
    context = {
        'settings': settings,
        'ano_atual': datetime.now().year,
        'versao': ultima_atualizacao.versao if ultima_atualizacao else '1.0.0'  # Usa a última versão ou um valor padrão
    }
    
    return render(request, 'login.html', context)

