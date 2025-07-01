import os
from datetime import date, datetime

from django.conf import settings
from django.shortcuts import get_object_or_404, render

from qualidade_fornecimento.forms.relatorio_avaliacao_form import RelatorioAvaliacaoForm
from qualidade_fornecimento.models.fornecedor import FornecedorQualificado
from qualidade_fornecimento.models.inspecao10 import Inspecao10
from qualidade_fornecimento.models.inspecao_servico_externo import (
    InspecaoServicoExterno,
)
from qualidade_fornecimento.models.materiaPrima import RelacaoMateriaPrima
from qualidade_fornecimento.utils import gerar_grafico_velocimetro


def calcular_intervalo(semestre, ano):
    if semestre == "1":
        inicio = date(ano, 1, 1)
        fim = date(ano, 6, 30)
    else:
        inicio = date(ano, 7, 1)
        fim = date(ano, 12, 31)
    return inicio, fim


def relatorio_avaliacao_view(request):
    ano_atual = datetime.today().year
    semestre_atual = "1" if datetime.today().month <= 6 else "2"

    if request.method == "POST":
        form = RelatorioAvaliacaoForm(request.POST)
        if form.is_valid():
            ano = form.cleaned_data["ano"]
            semestre = form.cleaned_data["semestre"]
            fornecedor = form.cleaned_data["fornecedor"]
            tipo = form.cleaned_data["tipo"]
            inicio, fim = calcular_intervalo(semestre, ano)

            if tipo == "servico":
                dados = InspecaoServicoExterno.objects.filter(
                    servico__fornecedor=fornecedor,
                    servico__data_envio__range=[inicio, fim],
                )
                reprovados = sum(
                    1
                    for d in dados
                    if d.status_geral() in ["Reprovado", "Aprovado Condicionalmente"]
                )
                atrasos = [
                    s.servico.atraso_em_dias
                    for s in dados
                    if hasattr(s.servico, "atraso_em_dias")
                    and s.servico.atraso_em_dias is not None
                ]
            else:
                dados = RelacaoMateriaPrima.objects.filter(
                    fornecedor=fornecedor, data_entrada__range=[inicio, fim]
                )
                reprovados = dados.filter(
                    status__in=["Reprovado", "Aprovado Condicionalmente"]
                ).count()
                atrasos = [
                    d.atraso_em_dias for d in dados if d.atraso_em_dias is not None
                ]

            total = max(1, dados.count())
            iqf = 1 - (reprovados / total)
            ip = 1 - (sum(atrasos) / len(atrasos) / 100) if atrasos else 1
            pontuacao = (fornecedor.score or 0) / 100  # transformar score em fração

            # Ponderações
            iqf_pond = iqf * 0.5
            ip_pond = ip * 0.3
            iqs = pontuacao * 0.2
            iqg = round(iqf_pond + ip_pond + iqs, 4)

            # Classificação
            if iqg >= 0.75:
                classificacao = "A - Qualificado"
                mensagem = "Gostaríamos de parabenizá-los pelo atingimento das metas e enfatizamos a importância de manter o alto nível de desempenho nas próximas avaliações."
            elif iqg <= 0.49:
                classificacao = "C - Não Qualificado"
                mensagem = "O desempenho nesta avaliação não atingiu os critérios mínimos. O fornecedor será submetido à apreciação da Diretoria, e deverá apresentar um plano de ação para continuidade da parceria."
            else:
                classificacao = "B - Qualificado Condicionalmente"
                mensagem = "Identificamos um desempenho próximo ao esperado. Solicitamos a apresentação de um plano de ação visando a correção dos desvios observados."

            # 🔧 Caminho do gráfico
            nome_arquivo = f"iqg_{fornecedor.id}_{ano}_{semestre}.png"
            caminho_absoluto = os.path.join(
                settings.MEDIA_ROOT, "graficos", nome_arquivo
            )
            caminho_relativo = os.path.join(
                settings.MEDIA_URL, "graficos", nome_arquivo
            )

            os.makedirs(os.path.dirname(caminho_absoluto), exist_ok=True)
            imagem_grafico = gerar_grafico_velocimetro(iqg * 100)

            contexto = {
                "titulo": f"DESEMPENHO - {semestre}º SEMESTRE DE {ano}",
                "fornecedor": fornecedor,
                "contato": fornecedor.especialista_nome or "Não informado",
                "iqf": iqf * 100,
                "ip": ip * 100,
                "pontuacao": fornecedor.score or 0,
                "iqf_pond": iqf_pond * 100,
                "ip_pond": ip_pond * 100,
                "iqs": iqs * 100,
                "iqg": iqg * 100,
                "classificacao": classificacao.split(" ")[0],
                "mensagem": mensagem,
                "form": form,
                "exibir": True,
                "grafico_base64": imagem_grafico,
            }
            return render(request, "relatorios/relatorio_avaliacao.html", contexto)

    else:
        form = RelatorioAvaliacaoForm(
            initial={"ano": ano_atual, "semestre": semestre_atual}
        )

    return render(
        request, "relatorios/relatorio_avaliacao.html", {"form": form, "exibir": False}
    )


from datetime import datetime
from collections import OrderedDict
import base64
import io

import matplotlib.pyplot as plt
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from qualidade_fornecimento.models.materiaPrima import RelacaoMateriaPrima
from qualidade_fornecimento.utils import gerar_grafico_velocimetro  # se preferir estilo velocímetro

def relatorio_iqf_view(request):
    ano_atual = datetime.now().year
    ano = int(request.GET.get("ano", ano_atual))

    queryset = RelacaoMateriaPrima.objects.filter(data_entrada__year=ano)

    if not queryset.exists():
        return render(request, "relatorios/relatorio_iqf.html", {
            "grafico_base64": None,
            "media": 0,
            "ano": ano,
            "comentarios": [],
            "dados_iqf": {},
            "meses": ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
        })

    # Prepara DataFrame
    df = pd.DataFrame.from_records(queryset.values("data_entrada", "status", "atraso_em_dias"))
    df["data_entrada"] = pd.to_datetime(df["data_entrada"])
    df["mes"] = df["data_entrada"].dt.month  # Inteiro de 1 a 12

    # Monta dicionário de IQF por mês
    dados_iqf = OrderedDict()
    meses_labels = []

    for i in range(1, 13):
        mes_nome = format_date(pd.to_datetime(f"{ano}-{i}-01"), "MMM", locale="pt_BR").lower()
        meses_labels.append(mes_nome)

        grupo_mes = df[df["mes"] == i]
        if grupo_mes.empty:
            dados_iqf[mes_nome] = 0.00
        else:
            total = len(grupo_mes)
            reprovados = grupo_mes[grupo_mes["status"].isin(["Reprovado", "Aprovado Condicionalmente"])].shape[0]
            atrasos = grupo_mes["atraso_em_dias"].dropna()

            iqf = 1 - (reprovados / total)
            ip = 1 - (atrasos.sum() / len(atrasos) / 100) if len(atrasos) > 0 else 1
            iqs = 0.9  # Valor fixo de pontuação como índice de qualidade do fornecedor

            nota_final = round((iqf * 0.5 + ip * 0.3 + iqs * 0.2) * 100, 2)
            dados_iqf[mes_nome] = nota_final

    # Gráfico IQF por mês
    fig, ax = plt.subplots()
    ax.bar([m.upper() for m in dados_iqf.keys()], list(dados_iqf.values()), color="skyblue")
    ax.axhline(y=90, color='green', linestyle='--', label='Meta (90%)')
    ax.set_title(f"IQF por Mês ({ano})")
    ax.set_ylabel("IQF (%)")
    ax.set_xlabel("Mês")
    ax.legend()
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    plt.close(fig)
    grafico_base64 = base64.b64encode(buffer.getvalue()).decode()

    # Comentários mensais
    comentarios = []
    for mes, valor in dados_iqf.items():
        if valor < 90:
            comentarios.append({
                "data": f"{mes.upper()}/{ano}",
                "texto": f"O IQF foi {valor:.2f}%, abaixo da meta estabelecida."
            })

    if not comentarios:
        comentarios.append({
            "data": "-",
            "texto": "Todos os meses atingiram a meta. Nenhuma ação necessária."
        })

    # Calcula a média apenas dos meses com dados (valor > 0)
    valores_validos = [v for v in dados_iqf.values() if v > 0]
    media = round(sum(valores_validos) / len(valores_validos), 2) if valores_validos else 0.00

    # Renderiza template
    return render(request, "relatorios/relatorio_iqf.html", {
        "grafico_base64": grafico_base64,
        "media": media,
        "ano": ano,
        "comentarios": comentarios,
        "dados_iqf": dados_iqf,
        "meses": list(dados_iqf.keys()),
    })


# qualidade_fornecimento/views/relatorio_inspecao.py
from django.shortcuts import render
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime
from qualidade_fornecimento.models.inspecao10 import Inspecao10

def gerar_grafico_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    imagem_base64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    plt.close(fig)
    return imagem_base64

def relatorio_inspecao_analitico(request):
    queryset = Inspecao10.objects.all()

    df = pd.DataFrame.from_records(
        queryset.values("data", "fornecedor__nome", "quantidade_total", "quantidade_nok", "tempo_gasto")
    )

    if df.empty:
        return render(request, "relatorios/relatorio_inspecao_analitico.html", {
            "grafico_top10": None,
            "grafico_reprovacao": None,
            "grafico_tempo": None,
            "grafico_evolucao": None,
            "comentarios": []
        })

    # Preparar colunas
    df["mes"] = pd.to_datetime(df["data"]).dt.to_period("M").astype(str)
    df["tempo_segundos"] = df["tempo_gasto"].dt.total_seconds()

    # Agrupamento por fornecedor
    df_grouped = df.groupby("fornecedor__nome").agg({
        "quantidade_nok": "sum",
        "quantidade_total": "sum",
        "tempo_segundos": "mean"
    }).reset_index()
    df_grouped["taxa_reprovacao"] = df_grouped["quantidade_nok"] / df_grouped["quantidade_total"] * 100

    # Gráfico 1: Top 10 fornecedores com mais falhas
    top10 = df_grouped.nlargest(10, "quantidade_nok")
    fig1, ax1 = plt.subplots()
    ax1.barh(top10["fornecedor__nome"], top10["quantidade_nok"])
    ax1.set_title("Top 10 Fornecedores com mais falhas")
    ax1.invert_yaxis()
    grafico_top10 = gerar_grafico_base64(fig1)

    # Gráfico 2: Taxa de reprovação por fornecedor
    fig2, ax2 = plt.subplots()
    ax2.bar(df_grouped["fornecedor__nome"], df_grouped["taxa_reprovacao"])
    ax2.set_title("Taxa de Reprovação por Fornecedor (%)")
    ax2.set_xticklabels(df_grouped["fornecedor__nome"], rotation=45, ha="right")
    grafico_reprovacao = gerar_grafico_base64(fig2)

    # Gráfico 3: Tempo médio por inspeção (em minutos)
    tempo_minutos = df_grouped["tempo_segundos"] / 60
    fig3, ax3 = plt.subplots()
    ax3.bar(df_grouped["fornecedor__nome"], tempo_minutos)
    ax3.set_title("Tempo Médio por Inspeção (min)")
    ax3.set_xticklabels(df_grouped["fornecedor__nome"], rotation=45, ha="right")
    grafico_tempo = gerar_grafico_base64(fig3)

    # Gráfico 4: Evolução Temporal (quantidade NOK ao longo do tempo)
    df_evolucao = df.groupby("mes")["quantidade_nok"].sum().reset_index()
    fig4, ax4 = plt.subplots()
    ax4.plot(df_evolucao["mes"], df_evolucao["quantidade_nok"], marker="o")
    ax4.set_title("Evolução de Falhas ao Longo do Tempo")
    ax4.set_xticklabels(df_evolucao["mes"], rotation=45, ha="right")
    grafico_evolucao = gerar_grafico_base64(fig4)

    # Lista de inspeções críticas
    criticos = df[(df["quantidade_total"] > 700) & (df["quantidade_nok"] > 85)]
    comentarios = [
        f"{row.fornecedor__nome}: {row.quantidade_nok} falhas em {row.quantidade_total} peças"
        for _, row in criticos.iterrows()
    ]

    return render(request, "relatorios/relatorio_inspecao_analitico.html", {
        "grafico_top10": grafico_top10,
        "grafico_reprovacao": grafico_reprovacao,
        "grafico_tempo": grafico_tempo,
        "grafico_evolucao": grafico_evolucao,
        "comentarios": comentarios,
    })




from django.shortcuts import render
from qualidade_fornecimento.models.inspecao10 import Inspecao10
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime
from babel.dates import format_date

def relatorio_ppm_view(request):
    ano_atual = datetime.now().year
    ano = request.GET.get("ano", str(ano_atual))

    queryset = Inspecao10.objects.filter(data__year=ano)

    df = pd.DataFrame.from_records(
        queryset.values("data", "quantidade_total", "quantidade_nok")
    )

    if df.empty:
        return render(request, "relatorios/relatorio_ppm.html", {
            "grafico_base64": None,
            "media": 0,
            "dados": {},
            "comentarios": [],
            "ano": ano,
            "dados_nc": {},
            "dados_totais": {},
            "dados_ppm": {},
            "dados_icte": {},
            "meses": ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
        })

    # Agrupar por mês
    df["mes"] = pd.to_datetime(df["data"]).dt.to_period("M").astype(str)
    df_grouped = df.groupby("mes")[["quantidade_total", "quantidade_nok"]].sum()

    # Cálculo ICTE
    df_grouped["quantidade_ok"] = df_grouped["quantidade_total"] - df_grouped["quantidade_nok"]
    df_grouped["icte"] = (
        df_grouped["quantidade_ok"] / df_grouped["quantidade_total"].replace(0, pd.NA)
    ) * 100
    df_grouped = df_grouped.fillna(0)

    # Rótulos dos meses (jan, fev, ...)
    labels = [
        format_date(pd.to_datetime(f"{mes}-01"), format="MMM", locale="pt_BR").capitalize()
        for mes in df_grouped.index
    ]

    # Gráfico
    fig, ax = plt.subplots()
    df_grouped["icte"].plot(kind="bar", ax=ax, color="skyblue")
    ax.set_title(f"ICTE por Mês ({ano})")
    ax.set_ylabel("Conformidade (%)")
    ax.set_xlabel("Mês")
    ax.set_xticklabels(labels, rotation=0)
    ax.axhline(y=97, color='green', linestyle='--', label='Meta (97%)')
    ax.legend()
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    plt.close(fig)
    grafico_base64 = base64.b64encode(buffer.getvalue()).decode()

    # Comentários estruturados
    comentarios = []
    for mes, row in df_grouped.iterrows():
        icte_valor = row["icte"]
        if icte_valor < 97:
            comentarios.append({
                "data": format_date(pd.to_datetime(f"{mes}-01"), format="MM/yyyy", locale="pt_BR"),
                "texto": f"O ICTE foi {icte_valor:.2f}%, abaixo da meta."
            })

    # Força pelo menos 1 comentário se a lista estiver vazia (para testes)
    if not comentarios:
        comentarios.append({
            "data": "-",
            "texto": "Todos os meses ficaram dentro da meta. Nenhum comentário necessário."
        })



    # Dados por mês
    dados_nc, dados_totais, dados_icte = {}, {}, {}
    for mes, row in df_grouped.iterrows():
        nome_mes = format_date(pd.to_datetime(f"{mes}-01"), format="MMM", locale="pt_BR").lower().replace(".", "")
        dados_nc[nome_mes] = int(row["quantidade_nok"])
        dados_totais[nome_mes] = int(row["quantidade_total"])
        dados_icte[nome_mes] = round(row["icte"], 2)

    return render(request, "relatorios/relatorio_ppm.html", {
        "grafico_base64": grafico_base64,
        "media": df_grouped["icte"].mean().round(2),
        "dados": df_grouped["icte"].round(2).to_dict(),
        "comentarios": comentarios,
        "ano": ano,
        "dados_nc": dados_nc,
        "dados_totais": dados_totais,
        "dados_icte": dados_icte,
        "dados_ppm": dados_icte,  # mantém compatibilidade com o nome antigo
        "meses": ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
    })
