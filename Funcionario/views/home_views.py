from django.shortcuts import render
from Funcionario.models import Comunicado, AtualizacaoSistema, Settings,Evento
from django.contrib.auth.decorators import login_required
import requests
from datetime import datetime

from django.shortcuts import render, get_object_or_404, redirect
from Funcionario.forms import EventoForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt



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
    
    # Consulta às atualizações do sistema com status "concluído"
    proximas_atualizacoes = AtualizacaoSistema.objects.all().order_by('-previsao')[:4]
    
    # Consulta a última atualização para o modal de informações de versão
    ultima_atualizacao_concluida = AtualizacaoSistema.objects.filter(status='concluido').order_by('-previsao').first()

    # Consulta às configurações da empresa, incluindo logos
    settings = Settings.objects.first()  # Obtém a primeira instância de Settings, caso haja mais de uma

    # Contexto para o template
    context = {
        'feriados': feriados,
        'comunicados': comunicados,
        'funcionarios_avaliacao_baixa': funcionarios_avaliacao_baixa,
        'proximas_atualizacoes': proximas_atualizacoes,
        'ultima_atualizacao_concluida': ultima_atualizacao_concluida,
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

from django.core import serializers


def calendario_view(request):
    # Captura o ano da query string ou usa o ano atual como padrão
    ano = str(request.GET.get('ano', datetime.now().year))

    # Obtenha todos os eventos do banco de dados
    eventos = Evento.objects.all()
    eventos_json = serializers.serialize('json', eventos)

    # Lista de anos para o filtro no template
    lista_anos = [str(y) for y in range(2020, 2031)]

    # Requisição de feriados nacionais para o ano selecionado
    url = f'https://brasilapi.com.br/api/feriados/v1/{ano}'
    feriados = []
    try:
        response = requests.get(url)
        if response.status_code == 200:
            feriados = response.json()
            # Formate os feriados para o formato JSON necessário
            feriados = [
                {
                    "name": feriado["name"],
                    "date": feriado["date"]
                }
                for feriado in feriados
            ]
    except Exception as e:
        print("Erro ao carregar feriados: ", e)

    return render(request, 'calendario/calendario.html', {
        'eventos': eventos_json,
        'feriados': feriados,  # Passa os feriados para o template
        'ano': ano,  # Passa o ano selecionado para o template
        'lista_anos': lista_anos,  # Passa a lista de anos para o template
    })


from django.utils import timezone
from datetime import datetime



@csrf_exempt
def adicionar_evento(request):
    if request.method == 'POST':
        print("Recebendo requisição POST para adicionar evento")
        print("Dados recebidos:", request.POST)
        
        # Recebe os dados do formulário
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        cor = request.POST.get('cor')
        tipo = request.POST.get('tipo')

        # Recebe e converte as datas de início e fim
        data_inicio_str = request.POST.get('data_inicio')
        data_fim_str = request.POST.get('data_fim')

        if not data_inicio_str or not data_fim_str:
            return JsonResponse({"error": "Data de início ou fim não foi fornecida"}, status=400)

        try:
            # Converte strings para date (sem horário)
            data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").date()
            data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").date()

            # Cria o evento sem horário
            evento = Evento(
                titulo=titulo,
                descricao=descricao,
                cor=cor,
                tipo=tipo,
                data_inicio=data_inicio,
                data_fim=data_fim
            )
            evento.save()

            print("Evento criado com sucesso:", evento)
            return JsonResponse({"status": "Evento criado com sucesso!"}, status=201)

        except ValueError as e:
            print("Erro ao processar as datas:", e)
            return JsonResponse({"error": "Erro ao processar as datas"}, status=400)

    return JsonResponse({"error": "Erro ao criar o evento"}, status=400)

def excluir_evento(request, evento_id):
    if request.method == 'DELETE':
        evento = get_object_or_404(Evento, id=evento_id)
        evento.delete()
        return JsonResponse({"status": "Evento excluído com sucesso!"}, status=200)
    else:
        return JsonResponse({"error": "Método não permitido"}, status=405)

@csrf_exempt
def editar_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    if request.method == 'POST':
        form = EventoForm(request.POST, instance=evento)
        if form.is_valid():
            form.save()
            return JsonResponse({"status": "Evento atualizado com sucesso!"})
        else:
            print("Erros do formulário de edição:", form.errors)  # Log de erros de validação no editar_evento
    return JsonResponse({"error": "Erro ao atualizar o evento"}, status=400)

# views.py
from django.http import HttpResponse
from icalendar import Calendar, Event
import pytz

def exportar_calendario(request):
    cal = Calendar()
    cal.add('prodid', '-//Your Calendar//')
    cal.add('version', '2.0')

    eventos = Evento.objects.all()
    timezone = pytz.timezone("America/Sao_Paulo")  # Ajuste para o seu fuso horário

    for evento in eventos:
        event = Event()
        event.add('summary', evento.titulo)
        event.add('description', evento.descricao)
        event.add('dtstart', timezone.localize(evento.data_inicio))
        event.add('dtend', timezone.localize(evento.data_fim))
        event.add('location', 'Local do Evento')  # Se houver um campo de localização
        cal.add_component(event)

    response = HttpResponse(cal.to_ical(), content_type='text/calendar')
    response['Content-Disposition'] = 'attachment; filename="calendario.ics"'
    return response

import requests
from django.shortcuts import render
from django.utils.dateparse import parse_date


def imprimir_calendario(request):
    # Lista de anos para o filtro
    anos_disponiveis = [2023, 2024, 2025, 2026]
    
    # Obtém o ano a partir dos parâmetros da URL (padrão: ano atual)
    ano = request.GET.get('ano', '2024')  # Define 2024 como padrão

    # Obter eventos do banco de dados para o ano selecionado
    eventos_banco = Evento.objects.filter(data_inicio__year=ano)

    # Obter feriados da API para o ano selecionado
    url = f'https://brasilapi.com.br/api/feriados/v1/{ano}'
    eventos_api = []
    try:
        response = requests.get(url)
        if response.status_code == 200:
            for feriado in response.json():
                eventos_api.append({
                    'titulo': feriado['name'],
                    'data_inicio': parse_date(feriado['date']),
                    'data_fim': parse_date(feriado['date']),
                    'tipo': 'feriado',
                    'cor': '#CC99FF'  # Cor padrão para feriados
                })
    except Exception as e:
        print("Erro ao carregar feriados da API:", e)

    # Combine e ordene os eventos por data de início
    eventos_combinados = sorted(
        list(eventos_banco) + eventos_api,
        key=lambda evento: evento.data_inicio if isinstance(evento, Evento) else evento['data_inicio']
    )

    return render(request, 'calendario/imprimir_calendario.html', {
        'eventos': eventos_combinados,
        'ano': ano,
        'anos_disponiveis': anos_disponiveis
    })