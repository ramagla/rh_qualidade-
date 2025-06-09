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


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from datetime import datetime
import requests

from Funcionario.models import (
    AtualizacaoSistema,
    AvaliacaoAnual,
    Comunicado,
    Settings,
)

from django.utils.timezone import now
from Funcionario.models import Funcionario, AvaliacaoAnual, Treinamento
from django.db.models.functions import ExtractYear

from collections import Counter
from datetime import datetime

import requests
from django.contrib.auth.decorators import login_required
from django.db.models.functions import ExtractYear
from django.shortcuts import render
from django.utils.timezone import now

from Funcionario.models import Funcionario, AvaliacaoAnual


from collections import Counter
from datetime import datetime
import requests

from django.contrib.auth.decorators import login_required
from django.db.models.functions import ExtractYear
from django.shortcuts import render
from django.utils.timezone import now

from alerts.models import AlertaConfigurado




from packaging import version  # IMPORTANTE - adicione no topo

@login_required
def home(request):
    # 🔗 Feriados via API
    feriados = []
    try:
        response = requests.get("https://brasilapi.com.br/api/feriados/v1/2025")
        if response.status_code == 200:
            feriados = response.json()
    except Exception as e:
        print("Erro ao buscar feriados:", e)

    # 📣 Comunicados recentes
    comunicados = Comunicado.objects.order_by("-data")[:4]

    # 📊 Classificações de avaliações
    avaliacoes = AvaliacaoAnual.objects.all()
    classificacao_counter = Counter()
    funcionarios_avaliacao_baixa = []

    for avaliacao in avaliacoes:
        funcionario = avaliacao.funcionario
        if funcionario.status != "Ativo":
            continue
        classificacao = avaliacao.calcular_classificacao()
        status = classificacao["status"]
        percentual = classificacao["percentual"]

        classificacao_counter[status] += 1

        if percentual < 66:
            funcionarios_avaliacao_baixa.append({
                "id": avaliacao.id,
                "funcionario_id": avaliacao.funcionario.id,
                "nome": avaliacao.funcionario.nome,
                "foto": avaliacao.funcionario.foto.url if avaliacao.funcionario.foto else None,
                "classificacao": percentual,
                "status": status,
            })

    # 🔧 Atualizações
    proximas_atualizacoes = AtualizacaoSistema.objects.filter(
        status="em_andamento"
    ).order_by("previsao")

    # Agora com version.parse para garantir versão correta
    versoes_concluidas = AtualizacaoSistema.objects.filter(
        status="concluido"
    )

    ultima_atualizacao_concluida = sorted(
        versoes_concluidas,
        key=lambda x: (x.data_termino, version.parse(x.versao)),
        reverse=True
    )[0] if versoes_concluidas else None

    historico_versoes = versoes_concluidas.exclude(
        id=ultima_atualizacao_concluida.id if ultima_atualizacao_concluida else None
    ).order_by("-data_termino")

    # 📌 Indicadores gerais
    ano_atual = now().year
    total_colaboradores = Funcionario.objects.filter(status="Ativo").count()

    ids_funcionarios_avaliados = AvaliacaoAnual.objects.annotate(
        ano=ExtractYear("data_avaliacao")
    ).filter(ano=ano_atual).values_list("funcionario_id", flat=True)

    funcionarios_pendentes = Funcionario.objects.filter(
        status="Ativo"
    ).exclude(id__in=ids_funcionarios_avaliados)

    avaliacoes_pendentes = funcionarios_pendentes.count()

    treinamentos = Treinamento.objects.filter(data_inicio__gte=now()).prefetch_related("funcionarios")
    treinamentos_agendados = treinamentos.count()

    aniversariantes = Funcionario.objects.filter(
        status="Ativo",
        data_nascimento__month=now().month
    )

    settings = Settings.objects.first()
    # Faixas etárias
    faixas_idade_labels = ['<= 20', '21-30', '31-40', '41-50', '51-60', '61-70', '> 70']
    faixas_idade_counts = [0] * len(faixas_idade_labels)

    # Ano de contratação
    anos_contratacao_dict = {}

    # Escolaridade
    escolaridade_dict = {}

    # Processamento
    for f in Funcionario.objects.filter(status='Ativo'):
        print(f"Funcionario: {f.nome} - Nascimento: {f.data_nascimento} - Admissao: {f.data_admissao} - Escolaridade: {f.escolaridade}")

        # Idade
        idade = (now().date() - f.data_nascimento).days // 365 if f.data_nascimento else 0
        if idade <= 20:
            faixas_idade_counts[0] += 1
        elif 21 <= idade <= 30:
            faixas_idade_counts[1] += 1
        elif 31 <= idade <= 40:
            faixas_idade_counts[2] += 1
        elif 41 <= idade <= 50:
            faixas_idade_counts[3] += 1
        elif 51 <= idade <= 60:
            faixas_idade_counts[4] += 1
        elif 61 <= idade <= 70:
            faixas_idade_counts[5] += 1
        else:
            faixas_idade_counts[6] += 1

        # Ano de contratação (protegido)
        if f.data_admissao:
            ano_contratacao = f.data_admissao.year
            anos_contratacao_dict[ano_contratacao] = anos_contratacao_dict.get(ano_contratacao, 0) + 1

        # Escolaridade
        esc = f.escolaridade.strip() if f.escolaridade else "Não Informado"
        escolaridade_dict[esc] = escolaridade_dict.get(esc, 0) + 1

    # Ordena ano de contratação
    anos_contratacao_labels = list(sorted(anos_contratacao_dict.keys()))
    anos_contratacao_counts = [anos_contratacao_dict[ano] for ano in anos_contratacao_labels]

    # Ordena escolaridade alfabeticamente
    escolaridade_labels = list(sorted(escolaridade_dict.keys()))
    escolaridade_counts = [escolaridade_dict[label] for label in escolaridade_labels]

    # >>> GÊNERO
    genero_labels = []
    genero_counts = []

    for g in Funcionario.objects.values_list('genero', flat=True):
        if g not in genero_labels:
            genero_labels.append(g)
            genero_counts.append(1)
        else:
            index = genero_labels.index(g)
            genero_counts[index] += 1

    # >>> TURNOVER (Exemplo simples: quantidade de desligados por mês)
    from django.db.models.functions import TruncMonth
    from django.db.models import Count

    turnover_qs = Funcionario.objects.filter(data_desligamento__isnull=False).annotate(
        mes=TruncMonth('data_desligamento')
    ).values('mes').annotate(qtd=Count('id')).order_by('mes')

    turnover_labels = [item['mes'].strftime("%m/%Y") for item in turnover_qs]
    turnover_counts = [item['qtd'] for item in turnover_qs]

    context = {
        "nome_modulo": "Recursos Humanos",
        "icone_modulo": "bi-people",
        "feriados": feriados,
        "comunicados": comunicados,
        "funcionarios_avaliacao_baixa": funcionarios_avaliacao_baixa,
        "proximas_atualizacoes": proximas_atualizacoes,
        "ultima_atualizacao_concluida": ultima_atualizacao_concluida,
        "historico_versoes": historico_versoes,
        "settings": settings,
        "ano_atual": ano_atual,
        "total_colaboradores": total_colaboradores,
        "avaliacoes_pendentes": avaliacoes_pendentes,
        "treinamentos_agendados": treinamentos_agendados,
        "treinamentos": treinamentos,  # usado no modal de detalhes
        "aniversariantes": aniversariantes,
        # Classificações
        "classificacao_ruim": classificacao_counter.get("Ruim", 0),
        "classificacao_regular": classificacao_counter.get("Regular", 0),
        "classificacao_bom": classificacao_counter.get("Bom", 0),
        "classificacao_otimo": classificacao_counter.get("Ótimo", 0),
        "avaliacoes_pendentes": avaliacoes_pendentes,
        "funcionarios_pendentes": funcionarios_pendentes,
        "faixas_idade_labels": json.dumps(faixas_idade_labels),
        "faixas_idade_counts": json.dumps(faixas_idade_counts),
        "anos_contratacao_labels": json.dumps(list(anos_contratacao_labels)),
        "anos_contratacao_counts": json.dumps(list(anos_contratacao_counts)),
        "escolaridade_labels": json.dumps(escolaridade_labels),
        "escolaridade_counts": json.dumps(escolaridade_counts),
        "genero_labels": json.dumps(genero_labels),
        "genero_counts": json.dumps(genero_counts),
        "turnover_labels": json.dumps(turnover_labels),
        "turnover_counts": json.dumps(turnover_counts),
    }

    form = EventoForm()
    context["form"] = form

    return render(request, "dashboard/home.html", context)






@login_required
def sucesso_view(request):
    return render(request, "sucesso.html")

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from datetime import datetime
from Funcionario.models import Settings, AtualizacaoSistema

from packaging import version  # Adicione no topo

def login_view(request):
    settings = Settings.objects.first()

    # 🔧 Correção: pegar a maior versão corretamente
    versoes_concluidas = AtualizacaoSistema.objects.filter(
        status="concluido"
    )

    ultima_atualizacao = sorted(
        versoes_concluidas,
        key=lambda x: (x.data_termino, version.parse(x.versao)),
        reverse=True
    )[0] if versoes_concluidas else None

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        print(f"Tentando autenticar: {username}")  # Debug

        user = authenticate(request, username=username, password=password)

        if user is not None:
            print(f"Usuário autenticado: {user.username}")  # Debug
            login(request, user)
            return redirect("home_geral")  # ✅ Novo redirecionamento correto
        else:
            print("❌ Falha na autenticação!")  # Debug
            context = {
                "settings": settings,
                "ano_atual": datetime.now().year,
                "versao": ultima_atualizacao.versao if ultima_atualizacao else "0.0.0",
                "erro": "Usuário ou senha inválidos.",
            }
            return render(request, "login.html", context)

    context = {
        "settings": settings,
        "ano_atual": datetime.now().year,
        "versao": ultima_atualizacao.versao if ultima_atualizacao else "0.0.0",
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

@login_required
def marcar_alertas_como_lidos(request):
    alertas = request.user.alertas.filter(lido=False)
    alertas.update(lido=True)
    return JsonResponse({"status": "ok"})

