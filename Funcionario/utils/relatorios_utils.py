# Standard Libraries
import base64
import io
from datetime import timedelta

# Terceiros
import matplotlib
matplotlib.use("Agg")  # ✅ Use backend que não exige interface gráfica
import matplotlib.pyplot as plt


def dividir_horas_por_trimestre(data_inicio, data_fim, carga_horaria_total):
    dias_total = (data_fim - data_inicio).days + 1
    if dias_total <= 0 or carga_horaria_total <= 0:
        return {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}

    horas_por_trimestre = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
    dias_por_trimestre = {1: 0, 2: 0, 3: 0, 4: 0}
    current = data_inicio

    while current <= data_fim:
        trimestre = (current.month - 1) // 3 + 1
        dias_por_trimestre[trimestre] += 1
        current += timedelta(days=1)

    for trimestre in horas_por_trimestre:
        horas_por_trimestre[trimestre] = round(
            (dias_por_trimestre[trimestre] / dias_total) * carga_horaria_total, 2
        )

    return horas_por_trimestre


def generate_training_hours_chart_styled(valores, ano):
    plt.figure(figsize=(8, 4))
    trimestres = ["1º T", "2º T", "3º T", "4º T"]
    meta = [4] * 4

    plt.bar(trimestres, list(valores.values()), color="lightblue", edgecolor="green")
    plt.plot(trimestres, meta, color="green", marker="o", linewidth=2)

    plt.ylabel("Horas", fontsize=12, color="green")
    plt.ylim(0, 11)
    plt.title(f"Horas de Treinamento - {ano}", fontsize=14, color="green", weight="bold")
    plt.legend(["Meta", "Índice"], loc="lower center", bbox_to_anchor=(0.5, -0.2), ncol=2)

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)
    graphic = base64.b64encode(buffer.getvalue()).decode("utf-8")
    buffer.close()
    plt.close()
    return graphic


def generate_avaliacao_anual_chart(dados_por_ano):
    anos = sorted(dados_por_ano.keys())
    indices = [dados_por_ano[ano] for ano in anos]
    meta = [70] * len(anos)

    plt.figure(figsize=(8, 4))
    x_pos = range(len(anos))
    plt.bar(x_pos, indices, color="lightblue", edgecolor="green", width=0.6)
    plt.plot(x_pos, meta, color="green", linestyle="--", marker="o", linewidth=2)

    plt.xticks(x_pos, anos, fontsize=10)
    plt.yticks(range(0, 101, 10), fontsize=10)
    plt.title("Índice de Avaliação Anual", fontsize=14, weight="bold")
    plt.xlabel("Ano")
    plt.ylabel("Porcentagem")
    plt.ylim(0, 100)

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)
    graphic = base64.b64encode(buffer.getvalue()).decode("utf-8")
    buffer.close()
    plt.close()
    return graphic
