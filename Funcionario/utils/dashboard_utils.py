# Bibliotecas padrão
import json
from datetime import datetime
from collections import Counter, defaultdict

# Terceiros
import pytz
import requests
from icalendar import Calendar, Event
from packaging import version

# Django
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from django.utils.timezone import now

# App Interno
from Funcionario.models import (
    AtualizacaoSistema,
    AvaliacaoAnual,
    Comunicado,
    Evento,
    Funcionario,
    Settings,
    Treinamento
)


def obter_contexto_home():
    """Retorna o contexto completo para a página home com indicadores."""
    # Feriados
    feriados = []
    try:
        response = requests.get("https://brasilapi.com.br/api/feriados/v1/2025")
        if response.status_code == 200:
            feriados = response.json()
    except Exception:
        pass

    # Comunicados
    comunicados = Comunicado.objects.order_by("-data")[:4]

    # Avaliações
    avaliacoes = AvaliacaoAnual.objects.all()
    classificacao_counter = Counter()
    funcionarios_baixo = []

    for av in avaliacoes:
        if av.funcionario.status != "Ativo":
            continue
        cls = av.calcular_classificacao()
        if cls["percentual"] < 66:
            funcionarios_baixo.append({
                "id": av.id,
                "funcionario_id": av.funcionario.id,
                "nome": av.funcionario.nome,
                "foto": av.funcionario.foto.url if av.funcionario.foto else None,
                "classificacao": cls["percentual"],
                "status": cls["status"]
            })
        classificacao_counter[cls["status"]] += 1

    # Atualizações
    prox_atualizacoes = AtualizacaoSistema.objects.filter(status="em_andamento").order_by("previsao")
    versoes = AtualizacaoSistema.objects.filter(status="concluido")
    ultima_versao = sorted(versoes, key=lambda x: (x.data_termino, version.parse(x.versao)), reverse=True)[0] if versoes else None
    historico = versoes.exclude(id=ultima_versao.id) if ultima_versao else []

    # Indicadores
    ano = now().year
    ativos = Funcionario.objects.filter(status="Ativo")
    total_colab = ativos.count()

    ids_avaliados = AvaliacaoAnual.objects.filter(data_avaliacao__year=ano).values_list("funcionario_id", flat=True)
    pendentes = ativos.exclude(id__in=ids_avaliados)
    avaliacoes_pendentes = pendentes.count()

    treinamentos = Treinamento.objects.filter(data_inicio__gte=now()).prefetch_related("funcionarios")

    # Aniversariantes
    aniversariantes = ativos.filter(data_nascimento__month=now().month)

    # Faixas etárias
    faixa_labels = ["< 20", "20-29", "30-39", "40-49", "50+"]
    faixa_counts = [0] * 5
    faixa_tooltips = defaultdict(list)

    anos_contratacao = {}
    escolaridade = {}
    genero = {}
    tipo_dict = {}

    for f in ativos:
        idade = (now().date() - f.data_nascimento).days // 365 if f.data_nascimento else 0
        nome = f.nome

        idx = 0 if idade < 20 else 1 if idade < 30 else 2 if idade < 40 else 3 if idade < 50 else 4
        faixa_counts[idx] += 1
        faixa_tooltips[idx].append(f"{nome} ({idade} anos)")

        if f.data_admissao:
            anos_contratacao[f.data_admissao.year] = anos_contratacao.get(f.data_admissao.year, 0) + 1

        esc = f.escolaridade.strip() if f.escolaridade else "Não Informado"
        escolaridade[esc] = escolaridade.get(esc, 0) + 1

        gen = f.genero.strip() if f.genero else "Não Informado"
        genero[gen] = genero.get(gen, 0) + 1

        tipo = f.tipo if f.tipo else "Não Informado"
        tipo_dict[tipo] = tipo_dict.get(tipo, 0) + 1

    # Turnover
    from django.db.models.functions import TruncMonth
    from django.db.models import Count

    turnover = Funcionario.objects.filter(data_desligamento__isnull=False).annotate(
        mes=TruncMonth('data_desligamento')
    ).values('mes').annotate(qtd=Count('id')).order_by('mes')

    turnover_labels = [item["mes"].strftime("%m/%Y") for item in turnover]
    turnover_counts = [item["qtd"] for item in turnover]

    # Gráfico de comparação
    total_func = sum(tipo_dict.values())
    admin = tipo_dict.get("administrativo", 0)
    operac = tipo_dict.get("operacional", 0)
    porcent_admin = round(100 * admin / total_func, 1) if total_func else 0
    porcent_operac = round(100 * operac / total_func, 1) if total_func else 0

    # CIPA
    cipa_ativos = ativos.filter(representante_cipa=True)
    cipa_empregados = []
    cipa_empregador = []

    for f in cipa_ativos:
        membro = {
            "nome": f.nome,
            "setor": f.local_trabalho.nome if f.local_trabalho else "N/D",
            "cargo": f.cargo_atual.nome if f.cargo_atual else "N/D",
            "tipo": f.tipo_cipa,
            "ordem": f"{f.ordem_cipa}º" if f.ordem_cipa else None,
            "foto": f.foto.url if f.foto else None
        }
        if f.tipo_representacao_cipa == "Empregados":
            cipa_empregados.append(membro)
        elif f.tipo_representacao_cipa == "Empregador":
            cipa_empregador.append(membro)

    ordenar_membros(cipa_empregados)
    ordenar_membros(cipa_empregador)

    # Brigada
    brigadistas = []
    for f in ativos.filter(representante_brigada=True):
        brigadistas.append({
            "nome": f.nome,
            "setor": f.local_trabalho.nome if f.local_trabalho else "N/D",
            "cargo": f.cargo_atual.nome if f.cargo_atual else "N/D",
            "ordem": f"{f.ordem_cipa}º" if f.ordem_cipa else None,
            "foto": f.foto.url if f.foto else None
        })

    brigadistas.sort(key=lambda x: int(x["ordem"].replace("º", "")) if x["ordem"] else 99)

    return {
        "nome_modulo": "Recursos Humanos",
        "icone_modulo": "bi-people",
        "feriados": feriados,
        "comunicados": comunicados,
        "funcionarios_avaliacao_baixa": funcionarios_baixo,
        "proximas_atualizacoes": prox_atualizacoes,
        "ultima_atualizacao_concluida": ultima_versao,
        "historico_versoes": historico,
        "settings": Settings.objects.first(),
        "ano_atual": ano,
        "total_colaboradores": total_colab,
        "avaliacoes_pendentes": avaliacoes_pendentes,
        "treinamentos_agendados": treinamentos.count(),
        "treinamentos": treinamentos,
        "aniversariantes": aniversariantes,
        "classificacao_ruim": classificacao_counter.get("Ruim", 0),
        "classificacao_regular": classificacao_counter.get("Regular", 0),
        "classificacao_bom": classificacao_counter.get("Bom", 0),
        "classificacao_otimo": classificacao_counter.get("Ótimo", 0),
        "funcionarios_pendentes": pendentes,
        "faixas_idade_labels": json.dumps(faixa_labels),
        "faixas_idade_counts": json.dumps(faixa_counts),
        "faixas_idade_tooltips": [", ".join(faixa_tooltips[i]) for i in range(5)],
        "anos_contratacao_labels": json.dumps(sorted(anos_contratacao)),
        "anos_contratacao_counts": json.dumps([anos_contratacao[ano] for ano in sorted(anos_contratacao)]),
        "escolaridade_labels": json.dumps(sorted(escolaridade)),
        "escolaridade_counts": json.dumps([escolaridade[esc] for esc in sorted(escolaridade)]),
        "genero_labels": json.dumps(sorted(genero)),
        "genero_counts": json.dumps([genero[g] for g in sorted(genero)]),
        "turnover_labels": json.dumps(turnover_labels),
        "turnover_counts": json.dumps(turnover_counts),
        "tipo_labels": json.dumps(sorted(tipo_dict)),
        "tipo_counts": json.dumps([tipo_dict[t] for t in sorted(tipo_dict)]),
        "grafico_comparativo_labels": json.dumps(["Administrativo", "Operacional"]),
        "grafico_comparativo_dados_atual": json.dumps([porcent_admin, porcent_operac]),
        "grafico_comparativo_dados_ref_min": json.dumps([10, 80]),
        "grafico_comparativo_dados_ref_max": json.dumps([20, 90]),
        "grafico_comparativo_quantidades": json.dumps({
            "Atual": [admin, operac],
            "Total": total_func
        }),
        "cipa_empregados": cipa_empregados,
        "cipa_empregador": cipa_empregador,
        "brigadistas": brigadistas
    }


def ordenar_membros(lista):
    """Ordena membros da CIPA por tipo e ordem."""
    ordem_tipo = {"Titular": 1, "Suplente": 2}
    lista.sort(key=lambda x: (
        ordem_tipo.get(x["tipo"], 99),
        int(x["ordem"].replace("º", "")) if x["ordem"] else 99
    ))


def obter_eventos_json(ano):
    """Retorna eventos e feriados de um determinado ano."""
    eventos = Evento.objects.all().values("id", "titulo", "descricao", "data_inicio", "data_fim", "cor", "tipo")
    eventos_list = [
        {
            "id": e["id"],
            "titulo": e["titulo"],
            "descricao": e["descricao"],
            "data_inicio": e["data_inicio"].strftime("%Y-%m-%d") if e["data_inicio"] else None,
            "data_fim": e["data_fim"].strftime("%Y-%m-%d") if e["data_fim"] else None,
            "cor": e["cor"],
            "tipo": e["tipo"],
        } for e in eventos
    ]

    url = f"https://brasilapi.com.br/api/feriados/v1/{ano}"
    feriados = []
    try:
        response = requests.get(url)
        if response.status_code == 200:
            feriados = response.json()
    except Exception:
        pass

    return eventos_list, feriados


def obter_calendario_feriados(ano):
    """Combina eventos do banco e feriados da API."""
    eventos_db = list(Evento.objects.filter(data_inicio__year=ano))
    eventos_api = []
    try:
        response = requests.get(f"https://brasilapi.com.br/api/feriados/v1/{ano}")
        if response.status_code == 200:
            for f in response.json():
                eventos_api.append({
                    "titulo": f["name"],
                    "data_inicio": parse_date(f["date"]),
                    "data_fim": parse_date(f["date"]),
                    "tipo": "feriado",
                    "cor": "#CC99FF"
                })
    except Exception:
        pass

    return sorted(eventos_db + eventos_api, key=lambda e: e.data_inicio if isinstance(e, Evento) else e["data_inicio"])


def gerar_arquivo_ics():
    """Gera o calendário no formato ICS para exportação."""
    cal = Calendar()
    cal.add("prodid", "-//Your Calendar//")
    cal.add("version", "2.0")

    tz = pytz.timezone("America/Sao_Paulo")
    for evento in Evento.objects.all():
        e = Event()
        e.add("summary", evento.titulo)
        e.add("description", evento.descricao)
        e.add("dtstart", tz.localize(evento.data_inicio))
        e.add("dtend", tz.localize(evento.data_fim))
        cal.add_component(e)

    response = HttpResponse(cal.to_ical(), content_type="text/calendar")
    response["Content-Disposition"] = 'attachment; filename="calendario.ics"'
    return response


def obter_contexto_impressao_cipa():
    """Retorna contexto com membros da CIPA para impressão."""
    ativos = Funcionario.objects.filter(representante_cipa=True, status="Ativo")
    cipa_empregados, cipa_empregador = [], []

    for f in ativos:
        membro = {
            "nome": f.nome,
            "setor": f.local_trabalho.nome if f.local_trabalho else "N/D",
            "cargo": f.cargo_atual.nome if f.cargo_atual else "N/D",
            "tipo": f.tipo_cipa,
            "ordem": f"{f.ordem_cipa}º" if f.ordem_cipa else None,
            "foto": f.foto.url if f.foto else None
        }
        (cipa_empregados if f.tipo_representacao_cipa == "Empregados" else cipa_empregador).append(membro)

    ordenar_membros(cipa_empregados)
    ordenar_membros(cipa_empregador)

    return {
        "cipa_empregados": cipa_empregados,
        "cipa_empregador": cipa_empregador,
        "ano": datetime.now().year
    }


def obter_contexto_impressao_brigada():
    """Retorna contexto com membros da brigada para impressão."""
    brigadistas = []
    for f in Funcionario.objects.filter(representante_brigada=True, status="Ativo"):
        brigadistas.append({
            "nome": f.nome,
            "setor": f.local_trabalho.nome if f.local_trabalho else "N/D",
            "cargo": f.cargo_atual.nome if f.cargo_atual else "N/D",
            "ordem": f"{f.ordem_cipa}º" if f.ordem_cipa else None,
            "foto": f.foto.url if f.foto else None
        })

    brigadistas.sort(key=lambda x: int(x["ordem"].replace("º", "")) if x["ordem"] else 99)

    return {
        "brigadistas": brigadistas,
        "ano": datetime.now().year
    }
