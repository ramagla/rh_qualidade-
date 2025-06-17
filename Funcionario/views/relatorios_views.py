import base64
import io
import os
from datetime import date, datetime, timedelta

import matplotlib.pyplot as plt
from django.contrib.auth.decorators import login_required
from django.db import models
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.views.generic import TemplateView
from django_ckeditor_5.fields import CKEditor5Field

from Funcionario.models import (
    AvaliacaoAnual,
    AvaliacaoTreinamento,
    Funcionario,
    Treinamento,
)


def generate_training_hours_chart_styled(total_horas_por_trimestre, ano):
    # Conteúdo da função para gerar o gráfico
    plt.figure(figsize=(8, 4))
    trimestres = ["1º T", "2º T", "3º T", "4º T"]
    valores = [total_horas_por_trimestre.get(t, 0) for t in range(1, 5)]
    meta = [4] * 4

    plt.bar(
        trimestres, valores, color="lightblue", edgecolor="green", label="Índice Mensal"
    )
    plt.plot(trimestres, meta, color="green", marker="o", label="Meta", linewidth=2)

    plt.ylabel("Horas", fontsize=12, color="green")
    plt.ylim(0, 11)
    plt.xticks(fontsize=10, color="green")
    plt.yticks(fontsize=10, color="green")
    plt.title(
        f"Horas de Treinamento - {ano}", fontsize=14, color="green", weight="bold"
    )
    plt.legend(loc="lower center", bbox_to_anchor=(0.5, -0.2), ncol=2, frameon=False)

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    graphic = base64.b64encode(image_png).decode("utf-8")
    plt.close()
    return graphic

def dividir_horas_por_trimestre(data_inicio, data_fim, carga_horaria_total):
    dias_total = (data_fim - data_inicio).days + 1
    if dias_total <= 0 or carga_horaria_total <= 0:
        return {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}

    horas_por_trimestre = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
    dias_por_trimestre = {1: 0, 2: 0, 3: 0, 4: 0}

    current = data_inicio
    while current <= data_fim:
        mes = current.month
        if mes in [1, 2, 3]:
            dias_por_trimestre[1] += 1
        elif mes in [4, 5, 6]:
            dias_por_trimestre[2] += 1
        elif mes in [7, 8, 9]:
            dias_por_trimestre[3] += 1
        elif mes in [10, 11, 12]:
            dias_por_trimestre[4] += 1
        current += timedelta(days=1)

    for trimestre in horas_por_trimestre:
        horas_por_trimestre[trimestre] = round(
            (dias_por_trimestre[trimestre] / dias_total) * carga_horaria_total, 2
        )

    return horas_por_trimestre


@method_decorator(login_required, name="dispatch")
class RelatorioPlanilhaTreinamentosView(TemplateView):
    template_name = "relatorios/relatorio_planilha_treinamentos.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["data_atual"] = datetime.now().strftime("%d/%m/%Y")

        # Obtendo anos disponíveis para o filtro
        anos_disponiveis = Treinamento.objects.dates("data_inicio", "year").distinct()
        context["anos_disponiveis"] = [ano.year for ano in anos_disponiveis]

        # Pega o ano selecionado ou o ano atual
        ano = int(self.request.GET.get("ano", datetime.now().year))

        # Configuração dos trimestres
        trimestres = {1: (1, 3), 2: (4, 6), 3: (7, 9), 4: (10, 12)}

        # Inicializar dados
        total_horas_por_mes = {mes: 0.0 for mes in range(1, 13)}
        total_horas_por_trimestre = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
        total_horas_treinamento = 0.0

        # Processar treinamentos por mês e trimestre
        for trimestre, (mes_inicio, mes_fim) in trimestres.items():
            treinamentos = Treinamento.objects.filter(
                data_inicio__year=ano,
                data_inicio__month__gte=mes_inicio,
                data_inicio__month__lte=mes_fim,
                status="concluido", 
            ).order_by("data_inicio")

            for treinamento in treinamentos:
                carga_horaria = (
                    float(treinamento.carga_horaria.replace("h", "").strip())
                    if treinamento.carga_horaria
                    else 0
                )
                participantes_count = (
                    Funcionario.objects.filter(
                        treinamentos__nome_curso=treinamento.nome_curso,
                        treinamentos__data_inicio=treinamento.data_inicio,
                        treinamentos__data_fim=treinamento.data_fim,
                    )
                    .distinct()
                    .count()
                )

                total_horas = carga_horaria * participantes_count
                total_horas_treinamento += total_horas

                # ✅ Dividir corretamente por trimestre
                horas_trimestre = dividir_horas_por_trimestre(
                    treinamento.data_inicio, 
                    treinamento.data_fim, 
                    total_horas
                )

                for t, horas in horas_trimestre.items():
                    total_horas_por_trimestre[t] += horas

                # ✅ Distribuir por mês apenas como total bruto (não precisa mais aqui)
                for mes in range(mes_inicio, mes_fim + 1):
                    total_horas_por_mes[mes] += total_horas

        # Calcular média de horas por trimestre (dividindo pelo total de funcionários ativos)
        total_funcionarios = Funcionario.objects.filter(status="Ativo").count() or 1
        media_por_funcionario = {
            trimestre: round(total / total_funcionarios, 2)
            for trimestre, total in total_horas_por_trimestre.items()
        }

        # Média anual
        media_anual = sum(media_por_funcionario.values()) / len(media_por_funcionario)

        # Gráfico
        grafico_base64 = generate_training_hours_chart_styled(
            media_por_funcionario, ano
        )

        # Total de horas trabalhadas na empresa
        total_horas_trabalhadas_empresa = total_funcionarios * 176 * 12

        # Análise
        analise_dados = {}
        for trimestre, media in media_por_funcionario.items():
            analise_dados[trimestre] = {
                "status": "Ok" if media >= 4 else "Nok",
                "mensagem": "Indicador dentro da meta estabelecida" if media >= 4 else "Indicador fora da meta estabelecida",
            }

        # Contexto
        context.update({
            "ano": ano,
            "trimestres": trimestres,
            "valores": media_por_funcionario,
            "media": round(media_anual, 2),
            "total_horas_por_trimestre": total_horas_por_trimestre,
            "total_horas_treinamento": total_horas_treinamento,
            "total_horas_trabalhadas_empresa": total_horas_trabalhadas_empresa,
            "grafico_base64": grafico_base64,
            "anos_disponiveis": context["anos_disponiveis"],
            "analise_dados": analise_dados,
        })

        return context



class RelatorioIndicadorAnualView(TemplateView):
    template_name = "relatorios/indicador_anual.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Buscar todas as avaliações anuais
        avaliacoes = AvaliacaoAnual.objects.all()

        # Obter anos distintos
        anos = sorted(set(avaliacoes.values_list("data_avaliacao__year", flat=True)))

        # Filtrar para mostrar apenas os últimos 5 anos
        anos = anos[-5:] if len(anos) > 5 else anos

        # Calcular o índice anual por ano
        dados_por_ano = {}
        funcionarios_avaliados = {}
        total_notas = 0
        total_colaboradores = 0

        for ano in anos:
            avaliacoes_ano = avaliacoes.filter(
                data_avaliacao__year=ano
            ).exclude(funcionario_id__in=[77, 15, 20, 78, 81])
            somatoria_notas = sum(
                a.calcular_classificacao()["percentual"] for a in avaliacoes_ano
            )
            total_colaboradores_ano = avaliacoes_ano.count()

            if total_colaboradores_ano > 0:
                indice = somatoria_notas / total_colaboradores_ano
                # Arredondar para 2 casas decimais
                dados_por_ano[ano] = round(indice, 2)
                funcionarios_avaliados[ano] = total_colaboradores_ano

                # Acumular dados para cálculo da média geral
                total_notas += somatoria_notas
                total_colaboradores += total_colaboradores_ano
            else:
                dados_por_ano[ano] = 0  # Evitar divisão por zero
                funcionarios_avaliados[ano] = 0

        # Calcular média geral
        media = (total_notas / total_colaboradores) if total_colaboradores > 0 else 0

        # Construir análise de dados por ano
        analise_dados = {
            ano: f"({ano}) - {'Indicador dentro da Meta. Vamos manter a meta e continuar o acompanhamento.' if dados_por_ano[ano] >= 70 else 'Indicador fora da Meta. Revisar as ações corretivas.'}"
            for ano in anos
        }

        # Adicionar informações ao contexto
        context["grafico_base64"] = self.gerar_grafico(dados_por_ano)
        context["dados_por_ano"] = dados_por_ano
        # Adicionar números de funcionários avaliados
        context["funcionarios_avaliados"] = funcionarios_avaliados
        context["meta"] = 70  # Meta fixa de 70%
        context["media"] = round(media, 2)  # Média geral arredondada
        context["analise_dados"] = analise_dados  # Mensagens de análise por ano

        return context

    def gerar_grafico(self, dados_por_ano):
        # Obter anos e índices
        anos = sorted(dados_por_ano.keys())
        indices = [dados_por_ano[ano] for ano in anos]
        meta = [70] * len(anos)  # Meta fixa de 70%

        # Configurar o gráfico
        plt.figure(figsize=(8, 4))
        x_pos = range(len(anos))  # Posicionamento categórico para cada ano
        plt.bar(
            x_pos,
            indices,
            color="lightblue",
            edgecolor="green",
            label="Índice Anual",
            width=0.6,
        )
        plt.plot(
            x_pos,
            meta,
            color="green",
            marker="o",
            linestyle="--",
            linewidth=2,
            label="Meta",
        )  # Linha da meta

        # Configurar o eixo X para valores categóricos (anos)
        plt.xticks(ticks=x_pos, labels=anos, fontsize=10, color="black")
        plt.yticks(range(0, 101, 10), fontsize=10, color="black")  # Escala de 0 a 100%
        plt.gca().set_facecolor("#B5E61D")  # Fundo verde

        # Configurações de título e legendas
        plt.xlabel("Ano", fontsize=12, color="green")
        plt.ylabel("Porcentagem", fontsize=12, color="black", weight="bold")
        plt.title(
            "Índice de Avaliação Anual de Desempenho",
            fontsize=14,
            color="black",
            weight="bold",
        )
        plt.ylim(0, 100)
        plt.legend(
            loc="lower center", bbox_to_anchor=(0.5, -0.3), ncol=2, frameon=False
        )

        # Geração do gráfico em base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight")
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()

        return base64.b64encode(image_png).decode("utf-8")

from Funcionario.models.departamentos import Departamentos  # Import necessário


@login_required
def cronograma_treinamentos(request):
    # Obtém os filtros
    ano = request.GET.get("ano", None)
    departamento = request.GET.get("departamento", None)

    # Define o ano padrão como o ano atual, se necessário
    ano = int(ano) if ano else datetime.now().year

    # Filtra os treinamentos
    treinamentos = Treinamento.objects.filter(data_inicio__year=ano)
    if departamento:
        treinamentos = treinamentos.filter(funcionarios__local_trabalho=departamento)

    # Obter anos disponíveis para o filtro
    anos_disponiveis = Treinamento.objects.dates("data_inicio", "year", order="DESC")
    anos_disponiveis = [data.year for data in anos_disponiveis]

    # Buscar departamentos ativos ordenados por nome
    departamentos = Departamentos.objects.filter(ativo=True).order_by("nome")

    # Gerar os meses dinamicamente com base no ano filtrado
    meses = [datetime(ano, mes, 1).strftime("%b/%y").capitalize() for mes in range(1, 13)]

    # Monta o contexto para o template
    context = {
        "treinamentos": treinamentos,
        "anos_disponiveis": anos_disponiveis,
        "departamentos": departamentos,
        "ano": ano,
        "filtro_departamento": departamento,
        "data_atual": datetime.now().strftime("%d/%m/%Y"),
        "meses": meses,
    }

    return render(request, "relatorios/cronograma_treinamentos.html", context)


@login_required
def cronograma_avaliacao_eficacia(request):
    # Obtém os filtros da URL
    ano = request.GET.get("ano", None)
    departamento = request.GET.get("departamento", None)

    # Define o ano padrão como o ano atual, se necessário
    ano = int(ano) if ano else datetime.now().year

    # Filtra as avaliações
    avaliacoes = AvaliacaoTreinamento.objects.filter(data_avaliacao__year=ano)
    if departamento:
        avaliacoes = avaliacoes.filter(funcionario__local_trabalho=departamento)

    # Obter anos disponíveis para o filtro
    anos_disponiveis = AvaliacaoTreinamento.objects.dates(
        "data_avaliacao", "year", order="DESC"
    )
    anos_disponiveis = [data.year for data in anos_disponiveis]

    # Obter departamentos únicos
    departamentos = Funcionario.objects.values_list(
        "local_trabalho", flat=True
    ).distinct()

    # Gerar os meses dinamicamente com base no ano filtrado
    meses = [
        datetime(ano, mes, 1).strftime("%b/%y").capitalize() for mes in range(1, 13)
    ]

    # Processar avaliações para definir o mês correto no cronograma
    avaliacoes_processadas = []
    for avaliacao in avaliacoes:
        treinamento = getattr(avaliacao, "treinamento", None)
        if treinamento and treinamento.data_fim:
            data_final = treinamento.data_fim + timedelta(days=60)
            mes_final = data_final.strftime("%b/%y").capitalize()
        else:
            data_final = None
            mes_final = None

        # Adiciona a propriedade mes_final para cada avaliação
        avaliacoes_processadas.append(
            {
                "avaliacao": avaliacao,
                "data_final": data_final,  # Adiciona para uso direto no template
                "mes_final": mes_final,
                "periodo_avaliacao": avaliacao.periodo_avaliacao,  # Inclui para evitar erro
            }
        )

    # Monta o contexto para o template
    context = {
        "avaliacoes": avaliacoes_processadas,
        "anos_disponiveis": anos_disponiveis,
        "departamentos": departamentos,
        "ano": ano,
        "filtro_departamento": departamento,
        "data_atual": datetime.now().strftime("%d/%m/%Y"),
        "meses": meses,
    }

    return render(request, "relatorios/cronograma_avaliacao_eficacia.html", context)


def relatorio_aniversariantes(request):
    hoje = date.today()
    mes = int(request.GET.get('mes', hoje.month))

    aniversariantes = Funcionario.objects.filter(
        data_nascimento__month=mes
    ).order_by('data_nascimento')

    meses = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro'),
    ]

    return render(request, 'relatorios/aniversariantes_mes.html', {
        'aniversariantes': aniversariantes,
        'meses': meses,
        'mes_selecionado': mes,
    })

from datetime import datetime
from collections import defaultdict
import json

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.utils.safestring import mark_safe

from datetime import date
from collections import defaultdict
import json

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.utils.safestring import mark_safe

from Funcionario.models.banco_horas import BancoHoras
from Funcionario.models import Funcionario


from collections import defaultdict
import json
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.utils.safestring import mark_safe
from Funcionario.models.banco_horas import BancoHoras
from Funcionario.models import Funcionario


from collections import defaultdict
from datetime import timedelta
import json

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.utils.safestring import mark_safe

from Funcionario.models.banco_horas import BancoHoras
from Funcionario.models import Funcionario
import math


@login_required
@permission_required("Funcionario.view_bancohoras", raise_exception=True)
def relatorio_banco_horas(request):
    # Corrigir datas como objetos
    data_inicio_raw = request.GET.get("data_inicio")
    data_fim_raw = request.GET.get("data_fim")

    data_inicio = datetime.strptime(data_inicio_raw, "%Y-%m-%d").date() if data_inicio_raw else None
    data_fim = datetime.strptime(data_fim_raw, "%Y-%m-%d").date() if data_fim_raw else None
    funcionario_id = request.GET.get("funcionario")

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
    total_he_50 = 0
    total_he_100 = 0
    saldo_total = 0
    total_minutos = 0

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

    # Saldo geral (não filtrado)
    registros_gerais = BancoHoras.objects.filter(funcionario_id=funcionario_id) if funcionario_id else BancoHoras.objects.all()
    saldo_total_geral = sum(
        r.horas_trabalhadas.total_seconds() / 3600 for r in registros_gerais if r.horas_trabalhadas
    )

    # Gráfico de tendência por dia
    registros_filtrados = registros.order_by("data")
    grafico_tendencia = {
        "labels": [r.data.strftime("%d/%m") for r in registros_filtrados],
        "values": [round(r.horas_trabalhadas.total_seconds() / 3600, 2) if r.horas_trabalhadas else 0 for r in registros_filtrados]
    }

    funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")

    funcionario_nome = None
    if funcionario_id:
        try:
            funcionario_nome = Funcionario.objects.get(id=funcionario_id).nome
        except Funcionario.DoesNotExist:
            funcionario_nome = "Funcionário não encontrado"

    total_dias = math.floor(abs(total_minutos) / 453)
    if saldo_total < 0:
        total_dias = -total_dias

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
        "saldos_mensais": mark_safe(json.dumps({
            "labels": list(saldos_mensais.keys()),
            "values": [round(v, 2) for v in saldos_mensais.values()],
        })),
        "grafico_tendencia": mark_safe(json.dumps(grafico_tendencia)),
    }

    return render(request, "relatorios/relatorio_banco_horas.html", context)


