from django.shortcuts import render
from django.http import HttpResponseForbidden
from datetime import datetime
import requests
from django.http import JsonResponse



def acesso_negado(request):
    current_time = datetime.now()
    return render(request, 'acesso_negado.html', {'user': request.user, 'current_time': current_time})


# View para Permissões de Acesso
def permissoes_acesso(request):
    return render(request, 'configuracoes/permissoes_acesso.html')

# View para Logs
def logs(request):
    return render(request, 'configuracoes/logs.html')

# View para Alertas de E-mails
def alertas_emails(request):
    return render(request, 'configuracoes/alertas_emails.html')

# View para Feriados
def feriados(request):
    # Usando a API de Feriados para obter dados
    try:
        response = requests.get("https://brasilapi.com.br/api/feriados/v1/2025")
        feriados = response.json()
    except Exception as e:
        feriados = []
    return render(request, 'configuracoes/feriados.html', {'feriados': feriados})