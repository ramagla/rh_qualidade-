# Standard Libraries
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta, date

# Django
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView

# Local Apps
from Funcionario.models import (
    Funcionario,
    Treinamento,
    AvaliacaoAnual,
    AvaliacaoTreinamento,
    BancoHoras,
    Departamentos,
)
from Funcionario.utils.relatorios_utils import (
    dividir_horas_por_trimestre,
    generate_training_hours_chart_styled,
    generate_avaliacao_anual_chart,
)

from Funcionario.models.indicadores import FechamentoIndicadorTreinamento



from datetime import datetime
from django.views.generic import TemplateView

from Funcionario.models import Funcionario, Treinamento
from Funcionario.models.indicadores import FechamentoIndicadorTreinamento
from Funcionario.utils.relatorios_utils import (
    dividir_horas_por_trimestre,
    generate_training_hours_chart_styled
)


class RelatorioPlanilhaTreinamentosView(TemplateView):
    template_name = "relatorios/indicador.html"

    def get_context_data(self, **kwargs):
        from Funcionario.models.indicadores import FechamentoIndicadorTreinamento

        context = super().get_context_data(**kwargs)
        ano = int(self.request.GET.get("ano", datetime.now().year))
        trimestre_atual = ((datetime.now().month - 1) // 3) + 1

        trimestres = {1: (1, 3), 2: (4, 6), 3: (7, 9), 4: (10, 12)}
        total_horas_por_trimestre = {t: 0.0 for t in trimestres}
        total_horas_treinamento = 0.0

        # Tenta buscar os 4 registros de fechamento individualmente
        fechamentos = {
            t: FechamentoIndicadorTreinamento.objects.filter(ano=ano, trimestre=t).first()
            for t in range(1, 5)
        }

        if all(fechamentos.values()):
            # Todos os trimestres têm fechamento — usa os dados salvos
            media = {
                1: fechamentos[1].valor_t1 or 0,
                2: fechamentos[2].valor_t2 or 0,
                3: fechamentos[3].valor_t3 or 0,
                4: fechamentos[4].valor_t4 or 0,
            }
            media_geral = round(sum(media.values()) / 4, 2)

        else:
            # Recalcula os dados com base nos treinamentos
            for t, (mes_inicio, mes_fim) in trimestres.items():
                treinamentos = Treinamento.objects.filter(
                    data_inicio__year=ano,
                    data_inicio__month__gte=mes_inicio,
                    data_inicio__month__lte=mes_fim,
                    status="concluido"
                )

                for tmt in treinamentos:
                    carga = float(tmt.carga_horaria.replace("h", "").strip() or 0)
                    participantes = Funcionario.objects.filter(
                        treinamentos__nome_curso=tmt.nome_curso,
                        treinamentos__data_inicio=tmt.data_inicio
                    ).distinct().count()

                    total = carga * participantes
                    total_horas_treinamento += total

                    distribuicao = dividir_horas_por_trimestre(tmt.data_inicio, tmt.data_fim, total)
                    for trimestre, horas in distribuicao.items():
                        total_horas_por_trimestre[trimestre] += horas

            total_funcionarios = Funcionario.objects.filter(status="Ativo").count() or 1
            media = {t: round(h / total_funcionarios, 2) for t, h in total_horas_por_trimestre.items()}
            media_geral = round(sum(media.values()) / 4, 2)

            # Salva corretamente 1 registro por trimestre
            for t in range(1, 5):
                FechamentoIndicadorTreinamento.objects.update_or_create(
                    ano=ano,
                    trimestre=t,
                    defaults={
                        f"valor_t{t}": media.get(t),
                        "media": media_geral
                    }
                )

        # Geração do gráfico
        grafico = generate_training_hours_chart_styled(media, ano)
        # Análise de Dados automática com base na meta de 4h por funcionário
        analise_dados = {}
        meta = 4.0

        for t in range(1, 5):
            valor = media.get(t, 0)
            if valor == 0:
                continue  # ignora trimestres sem dados
            elif valor >= meta:
                icone = "✅"
                mensagem = f"{icone} A média de {valor:.2f}h no {t}º trimestre está dentro da meta de {meta}h por funcionário."
            else:
                icone = "⚠️"
                mensagem = f"{icone} A média de {valor:.2f}h no {t}º trimestre está abaixo da meta de {meta}h por funcionário."

            analise_dados[t] = {"mensagem": mensagem}

       
        context.update({
            "ano": ano,
            "valores": media,
            "media": media_geral,
            "grafico_base64": grafico,
            "total_horas_treinamento": total_horas_treinamento,
            "anos_disponiveis": [d.year for d in Treinamento.objects.dates("data_inicio", "year").distinct()],
            "data_atual": datetime.now().strftime("%d/%m/%Y"),
            "trimestre_atual": trimestre_atual,
            "trimestres": {
                1: "1º Trimestre",
                2: "2º Trimestre",
                3: "3º Trimestre",
                4: "4º Trimestre",
            },
            "analise_dados": analise_dados,
        })
        return context




class RelatorioIndicadorAnualView(TemplateView):
    template_name = "relatorios/indicador_anual.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        avaliacoes = AvaliacaoAnual.objects.exclude(funcionario_id__in=[77, 15, 20, 78, 81])
        anos = sorted(set(avaliacoes.values_list("data_avaliacao__year", flat=True)))[-5:]

        dados_por_ano = {}
        avaliados = {}
        notas_total = colaboradores_total = 0

        for ano in anos:
            avs = avaliacoes.filter(data_avaliacao__year=ano)
            soma = sum(a.calcular_classificacao()["percentual"] for a in avs)
            count = avs.count()
            dados_por_ano[ano] = round(soma / count, 2) if count else 0
            avaliados[ano] = count
            notas_total += soma
            colaboradores_total += count

        media_geral = round(notas_total / colaboradores_total, 2) if colaboradores_total else 0
        analise = {
            ano: f"({ano}) - {'Indicador dentro da Meta.' if val >= 70 else 'Indicador fora da Meta.'}"
            for ano, val in dados_por_ano.items()
        }

        context.update({
            "dados_por_ano": dados_por_ano,
            "funcionarios_avaliados": avaliados,
            "media": media_geral,
            "meta": 70,
            "grafico_base64": generate_avaliacao_anual_chart(dados_por_ano),
            "analise_dados": analise,
        })
        return context

@login_required
@permission_required("Funcionario.view_bancohoras", raise_exception=True)
def relatorio_banco_horas(request):
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    funcionario_id = request.GET.get("funcionario")

    data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date() if data_inicio else None
    data_fim = datetime.strptime(data_fim, "%Y-%m-%d").date() if data_fim else None
    registros = BancoHoras.objects.select_related("funcionario").all()

    if data_inicio:
        registros = registros.filter(data__gte=data_inicio)
    if data_fim:
        registros = registros.filter(data__lte=data_fim)
    if funcionario_id:
        registros = registros.filter(funcionario_id=funcionario_id)

    registros = registros.order_by("data")
    registros_por_mes = defaultdict(list)
    saldos_mensais = defaultdict(float)
    total_he_50 = total_he_100 = saldo_total = total_minutos = 0

    for r in registros:
        mes = r.data.strftime("%b/%Y")
        registros_por_mes[mes].append(r)
        horas = r.horas_trabalhadas.total_seconds() / 3600 if r.horas_trabalhadas else 0

        if r.he_50:
            total_he_50 += horas
        elif r.he_100:
            total_he_100 += horas

        saldo_total += horas
        saldos_mensais[mes] += horas
        total_minutos += horas * 60

    registros_gerais = BancoHoras.objects.filter(funcionario_id=funcionario_id) if funcionario_id else BancoHoras.objects.all()
    saldo_total_geral = sum(
        r.horas_trabalhadas.total_seconds() / 3600 for r in registros_gerais if r.horas_trabalhadas
    )

    grafico_tendencia = {
        "labels": [r.data.strftime("%d/%m") for r in registros],
        "values": [round(r.horas_trabalhadas.total_seconds() / 3600, 2) if r.horas_trabalhadas else 0 for r in registros]
    }

    funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")
    funcionario_nome = get_object_or_404(Funcionario, id=funcionario_id).nome if funcionario_id else None
    total_dias = math.floor(abs(total_minutos) / 453)
    total_dias = -total_dias if saldo_total < 0 else total_dias

    context = {
        "registros_por_mes": dict(registros_por_mes),
        "meses": {mes: mes for mes in saldos_mensais.keys()},
        "total_he_50": round(total_he_50, 2),
        "total_he_100": round(total_he_100, 2),
        "saldo_total_horas": round(saldo_total, 2),
        "saldo_total_geral": round(saldo_total_geral, 2),
        "total_dias": total_dias,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "funcionarios": funcionarios,
        "funcionario_selecionado": funcionario_id,
        "funcionario_nome": funcionario_nome,
        "saldos_mensais": mark_safe(json.dumps({"labels": list(saldos_mensais.keys()), "values": [round(v, 2) for v in saldos_mensais.values()]})),
        "grafico_tendencia": mark_safe(json.dumps(grafico_tendencia)),
    }

    return render(request, "relatorios/relatorio_banco_horas.html", context)


@login_required
def relatorio_aniversariantes(request):
    hoje = date.today()
    mes = int(request.GET.get("mes", hoje.month))

    aniversariantes = Funcionario.objects.filter(data_nascimento__month=mes).order_by("data_nascimento")
    meses = [(i, datetime(2000, i, 1).strftime("%B")) for i in range(1, 13)]

    return render(request, "relatorios/aniversariantes_mes.html", {
        "aniversariantes": aniversariantes,
        "meses": meses,
        "mes_selecionado": mes,
    })

@login_required
def cronograma_treinamentos(request):
    ano = int(request.GET.get("ano", datetime.now().year))
    departamento_id = request.GET.get("departamento")

    treinamentos = Treinamento.objects.filter(data_inicio__year=ano)
    if departamento_id and departamento_id.isdigit():
        treinamentos = treinamentos.filter(funcionarios__local_trabalho_id=int(departamento_id))

    context = {
        "treinamentos": treinamentos.distinct(),
        "anos_disponiveis": [d.year for d in Treinamento.objects.dates("data_inicio", "year", order="DESC")],
        "departamentos": Departamentos.objects.filter(ativo=True).order_by("nome"),
        "ano": ano,
        "filtro_departamento": int(departamento_id) if departamento_id and departamento_id.isdigit() else None,
        "data_atual": datetime.now().strftime("%d/%m/%Y"),
        "meses": [datetime(ano, m, 1).strftime("%b/%y").capitalize() for m in range(1, 13)],
    }
    return render(request, "relatorios/cronograma_treinamentos.html", context)


@login_required
def cronograma_avaliacao_eficacia(request):
    ano = int(request.GET.get("ano", datetime.now().year))
    departamento = request.GET.get("departamento")

    avaliacoes = AvaliacaoTreinamento.objects.filter(data_avaliacao__year=ano)
    if departamento:
        avaliacoes = avaliacoes.filter(funcionario__local_trabalho=departamento)

    avaliacoes_processadas = []
    for avaliacao in avaliacoes:
        treinamento = getattr(avaliacao, "treinamento", None)
        if treinamento and treinamento.data_fim:
            data_final = treinamento.data_fim + timedelta(days=60)
            mes_final = data_final.strftime("%b/%y").capitalize()
        else:
            data_final = mes_final = None

        avaliacoes_processadas.append({
            "avaliacao": avaliacao,
            "data_final": data_final,
            "mes_final": mes_final,
            "periodo_avaliacao": avaliacao.periodo_avaliacao,
        })

    context = {
        "avaliacoes": avaliacoes_processadas,
        "anos_disponiveis": [d.year for d in AvaliacaoTreinamento.objects.dates("data_avaliacao", "year", order="DESC")],
        "departamentos": Funcionario.objects.values_list("local_trabalho", flat=True).distinct(),
        "ano": ano,
        "filtro_departamento": departamento,
        "data_atual": datetime.now().strftime("%d/%m/%Y"),
        "meses": [datetime(ano, m, 1).strftime("%b/%y").capitalize() for m in range(1, 13)],
    }
    return render(request, "relatorios/cronograma_avaliacao_eficacia.html", context)