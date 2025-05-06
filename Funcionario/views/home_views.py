import json
from datetime import datetime

import pytz
import requests
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.core.serializers import serialize
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt
from icalendar import Calendar, Event

from Funcionario.forms import EventoForm
from Funcionario.models import (
    AtualizacaoSistema,
    AvaliacaoAnual,
    Comunicado,
    Evento,
    Funcionario,
    Settings,
)


@login_required
def home(request):
    # Obter feriados da API

    url = "https://brasilapi.com.br/api/feriados/v1/2025"
    feriados = []
    try:
        response = requests.get(url)
        if response.status_code == 200:
            feriados = response.json()
    except Exception as e:
        print("Exceção ao chamar a API:", e)

    # Consulta aos últimos comunicados
    comunicados = Comunicado.objects.order_by("-data")[:4]

    # Consulta ao banco de dados para funcionários com avaliação baixa
    funcionarios_avaliacao_baixa = [
        {
            "id": avaliacao.id,
            "funcionario_id": avaliacao.funcionario.id,  # Ainda pode ser útil para exibição
            "nome": avaliacao.funcionario.nome,
            "foto": (
                avaliacao.funcionario.foto.url if avaliacao.funcionario.foto else None
            ),
            "classificacao": classificacao["percentual"],
            "status": classificacao["status"],
        }
        for avaliacao in AvaliacaoAnual.objects.all()
        if (classificacao := avaliacao.calcular_classificacao())["percentual"] < 66
    ]

    # Consulta às atualizações do sistema com status "concluído"
    proximas_atualizacoes = AtualizacaoSistema.objects.all().order_by("-previsao")[:4]

    # Consulta a última atualização para o modal de informações de versão
    ultima_atualizacao_concluida = (
        AtualizacaoSistema.objects.filter(status="concluido")
        .order_by("-previsao")
        .first()
    )

    # Consulta às configurações da empresa, incluindo logos
    # Obtém a primeira instância de Settings, caso haja mais de uma
    settings = Settings.objects.first()

    # Contexto para o template
    context = {
        "nome_modulo": "Recursos Humanos",
        "icone_modulo": "bi-people",
        "feriados": feriados,
        "comunicados": comunicados,
        "funcionarios_avaliacao_baixa": funcionarios_avaliacao_baixa,
        "proximas_atualizacoes": proximas_atualizacoes,
        "ultima_atualizacao_concluida": ultima_atualizacao_concluida,
        "settings": settings,  # Inclui settings para acesso aos logos
    }

    return render(request, "dashboard/home.html", context)


@login_required
def sucesso_view(request):
    return render(request, "sucesso.html")

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from datetime import datetime
from Funcionario.models import Settings, AtualizacaoSistema

def login_view(request):
    settings = Settings.objects.first()
    ultima_atualizacao = AtualizacaoSistema.objects.order_by("-previsao").first()

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        print(f"Tentando autenticar: {username}")  # Debug

        user = authenticate(request, username=username, password=password)

        if user is not None:
            print(f"Usuário autenticado: {user.username}")  # Debug
            login(request, user)
            return redirect("home")  # Ou outro nome, ex: "funcionarios_home"
        else:
            print("❌ Falha na autenticação!")  # Debug
            context = {
                "settings": settings,
                "ano_atual": datetime.now().year,
                "versao": ultima_atualizacao.versao if ultima_atualizacao else "1.0.0",
                "erro": "Usuário ou senha inválidos.",
            }
            return render(request, "login.html", context)

    context = {
        "settings": settings,
        "ano_atual": datetime.now().year,
        "versao": ultima_atualizacao.versao if ultima_atualizacao else "1.0.0",
    }
    return render(request, "login.html", context)


def calendario_view(request):
    ano = str(request.GET.get("ano", datetime.now().year))

    # Buscar eventos do banco de dados
    eventos = Evento.objects.all().values(
        "id", "titulo", "descricao", "data_inicio", "data_fim", "cor", "tipo"
    )

    # 🔥 ✅ Convertendo os objetos de data para string antes da serialização JSON
    eventos_list = [
        {
            "id": evento["id"],
            "titulo": evento["titulo"],
            "descricao": evento["descricao"],
            "data_inicio": (
                evento["data_inicio"].strftime("%Y-%m-%d")
                if evento["data_inicio"]
                else None
            ),
            "data_fim": (
                evento["data_fim"].strftime("%Y-%m-%d") if evento["data_fim"] else None
            ),
            "cor": evento["cor"],
            "tipo": evento["tipo"],
        }
        for evento in eventos
    ]

    # Buscar feriados da API externa
    url = f"https://brasilapi.com.br/api/feriados/v1/{ano}"
    feriados = []
    try:
        response = requests.get(url)
        if response.status_code == 200:
            feriados = response.json()
    except Exception as e:
        print("Erro ao carregar feriados:", e)

    # Se for uma requisição AJAX, retorna JSON, senão renderiza o template
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"eventos": eventos_list, "feriados": feriados}, safe=False)

    return render(
        request,
        "calendario/calendario.html",
        {
            "eventos_json": json.dumps(eventos_list),
            "feriados_json": json.dumps(feriados),
            "ano": ano,
        },
    )


@csrf_exempt
@login_required
def adicionar_evento(request):
    if request.method == "POST":
        titulo = request.POST.get("titulo")
        data_inicio = request.POST.get("data_inicio")
        data_fim = request.POST.get("data_fim")
        cor = request.POST.get("cor")

        try:
            evento = Evento.objects.create(
                titulo=titulo,
                data_inicio=datetime.strptime(data_inicio, "%Y-%m-%dT%H:%M"),
                data_fim=datetime.strptime(data_fim, "%Y-%m-%dT%H:%M"),
                cor=cor,
            )
            return JsonResponse({"status": "Evento criado com sucesso!"}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@login_required
def excluir_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    evento.delete()
    return JsonResponse({"status": "Evento excluído com sucesso!"}, status=200)


@csrf_exempt
@login_required
def editar_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    if request.method == "POST":
        evento.titulo = request.POST.get("titulo")
        evento.data_inicio = datetime.strptime(
            request.POST.get("data_inicio"), "%Y-%m-%dT%H:%M"
        )
        evento.data_fim = datetime.strptime(
            request.POST.get("data_fim"), "%Y-%m-%dT%H:%M"
        )
        evento.cor = request.POST.get("cor")
        evento.save()
        return JsonResponse({"status": "Evento atualizado com sucesso!"})
    return JsonResponse({"error": "Erro ao atualizar o evento"}, status=400)


@login_required
def imprimir_calendario(request):
    # Lista de anos para o filtro
    anos_disponiveis = [2023, 2024, 2025, 2026]

    # Obtém o ano a partir dos parâmetros da URL (padrão: ano atual)
    ano = request.GET.get("ano", "2024")  # Define 2024 como padrão

    # Obter eventos do banco de dados para o ano selecionado
    eventos_banco = Evento.objects.filter(data_inicio__year=ano)

    # Obter feriados da API para o ano selecionado
    url = f"https://brasilapi.com.br/api/feriados/v1/{ano}"
    eventos_api = []
    try:
        response = requests.get(url)
        if response.status_code == 200:
            for feriado in response.json():
                eventos_api.append(
                    {
                        "titulo": feriado["name"],
                        "data_inicio": parse_date(feriado["date"]),
                        "data_fim": parse_date(feriado["date"]),
                        "tipo": "feriado",
                        "cor": "#CC99FF",  # Cor padrão para feriados
                    }
                )
    except Exception as e:
        print("Erro ao carregar feriados da API:", e)

    # Combine e ordene os eventos por data de início
    eventos_combinados = sorted(
        list(eventos_banco) + eventos_api,
        key=lambda evento: (
            evento.data_inicio if isinstance(evento, Evento) else evento["data_inicio"]
        ),
    )

    return render(
        request,
        "calendario/imprimir_calendario.html",
        {
            "eventos": eventos_combinados,
            "ano": ano,
            "anos_disponiveis": anos_disponiveis,
        },
    )


@login_required
def exportar_calendario(request):
    cal = Calendar()
    cal.add("prodid", "-//Your Calendar//")
    cal.add("version", "2.0")

    eventos = Evento.objects.all()
    timezone = pytz.timezone("America/Sao_Paulo")  # Ajuste para o seu fuso horário

    for evento in eventos:
        event = Event()
        event.add("summary", evento.titulo)
        event.add("description", evento.descricao)
        event.add("dtstart", timezone.localize(evento.data_inicio))
        event.add("dtend", timezone.localize(evento.data_fim))
        event.add("location", "Local do Evento")  # Se houver um campo de localização
        cal.add_component(event)

    response = HttpResponse(cal.to_ical(), content_type="text/calendar")
    response["Content-Disposition"] = 'attachment; filename="calendario.ics"'
    return response


@login_required
def eventos_json(request):
    ano = str(request.GET.get("ano", datetime.now().year))
    eventos = Evento.objects.all().values(
        "id", "titulo", "descricao", "data_inicio", "data_fim", "cor", "tipo"
    )

    eventos_list = [
        {
            "id": evento["id"],
            "titulo": evento["titulo"],
            "descricao": evento["descricao"],
            "data_inicio": (
                evento["data_inicio"].strftime("%Y-%m-%d")
                if evento["data_inicio"]
                else None
            ),
            "data_fim": (
                evento["data_fim"].strftime("%Y-%m-%d") if evento["data_fim"] else None
            ),
            "cor": evento["cor"],
            "tipo": evento["tipo"],
        }
        for evento in eventos
    ]

    # Buscar feriados da API externa
    url = f"https://brasilapi.com.br/api/feriados/v1/{ano}"
    feriados = []
    try:
        response = requests.get(url)
        if response.status_code == 200:
            feriados = response.json()
    except Exception as e:
        print("Erro ao carregar feriados:", e)

    return JsonResponse({"eventos": eventos_list, "feriados": feriados}, safe=False)
