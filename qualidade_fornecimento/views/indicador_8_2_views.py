# qualidade_fornecimento/views/indicador_8_2.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import base64
from io import BytesIO

from comercial.models.faturamento import FaturamentoRegistro

@login_required
@permission_required("qualidade_fornecimento.view_relatorioiqf", raise_exception=True)
def indicador_8_2_view(request):
    ano_atual = datetime.now().year
    ano = int(request.GET.get("ano", ano_atual))

    # 🔹 Busca registros de faturamento do ano selecionado
    queryset = FaturamentoRegistro.objects.filter(ocorrencia__year=ano)

    if not queryset.exists():
        return render(request, "relatorios/indicador_8_2.html", {
            "grafico_base64": None,
            "media": 0,
            "dados": {},
            "comentarios": [],
            "ano": ano,
            "trimestres": ["1ºT", "2ºT", "3ºT", "4ºT"],
        })

    # 🔹 Converte para DataFrame
    df = pd.DataFrame.from_records(
        queryset.values("ocorrencia", "valor_total", "tipo")
    )
    df["ocorrencia"] = pd.to_datetime(df["ocorrencia"])
    df["trimestre"] = df["ocorrencia"].dt.to_period("Q")

    # 🔹 Compras = tipo == "Devolução" ou "Compra"
    df["compras"] = df.apply(lambda x: x["valor_total"] if x["tipo"] == "Devolução" else 0, axis=1)
    df["faturamento"] = df.apply(lambda x: x["valor_total"] if x["tipo"] == "Venda" else 0, axis=1)

    agrupado = df.groupby("trimestre")[["compras", "faturamento"]].sum()

    # 🔹 Cálculo do índice (Compras/Faturamento × 100)
    agrupado["indice"] = (agrupado["compras"] / agrupado["faturamento"]) * 100

    # 🔹 Gráfico
    fig, ax = plt.subplots()
    ax.plot(agrupado.index.astype(str), agrupado["indice"], marker="o", label="Índice (%)")
    ax.axhline(y=30, color="red", linestyle="--", label="Meta ≤ 30%")
    ax.set_title(f"8.2 - Compras x Faturamento ({ano})")
    ax.set_ylabel("Índice (%)")
    ax.legend()
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    plt.close(fig)
    grafico_base64 = base64.b64encode(buffer.getvalue()).decode()

    # 🔹 Média do ano
    media = round(agrupado["indice"].mean(), 2)

    # 🔹 Comentários automáticos
    comentarios = []
    for trimestre, linha in agrupado.iterrows():
        if linha["indice"] <= 30:
            comentarios.append({"data": str(trimestre), "texto": f"{linha['indice']:.2f}% - Dentro da meta"})
        else:
            comentarios.append({"data": str(trimestre), "texto": f"{linha['indice']:.2f}% - Acima da meta"})

    return render(request, "relatorios/indicador_8_2.html", {
        "grafico_base64": grafico_base64,
        "media": media,
        "ano": ano,
        "comentarios": comentarios,
        "dados": agrupado.to_dict("index"),
        "trimestres": [str(t) for t in agrupado.index],
    })
