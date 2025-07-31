# tecnico/views/indicadores_views.py
import calendar
import base64
import io
from datetime import datetime
from django.db.models import Q
from django.shortcuts import render
from django.utils.timezone import now
import matplotlib.pyplot as plt

from comercial.models.ordem_desenvolvimento import OrdemDesenvolvimento
from comercial.utils.indicadores import salvar_registro_indicador
from django.contrib.auth.decorators import login_required, permission_required


@login_required
@permission_required("tecnico.view_indicador_tecnico", raise_exception=True)
def indicador_51_prazo_desenvolvimento(request):
    ano = int(request.GET.get("ano", now().year))
    mes_atual = datetime.now().month
    meta = 95
    meses = [calendar.month_abbr[i].capitalize() for i in range(1, 13)]

    dados_por_mes = {m: {"total": 0, "pontual": 0} for m in meses}
    dados_percentuais = {}

    queryset = OrdemDesenvolvimento.objects.filter(created_at__year=ano)

    for od in queryset:
        if not od.created_at or not od.assinatura_tecnica_data:
            continue

        mes_index = od.created_at.month
        nome_mes = meses[mes_index - 1]

        dados_por_mes[nome_mes]["total"] += 1

        prazos = [
            od.prazo_material, od.prazo_rotinas, od.prazo_docs,
            od.prazo_ferramental, od.prazo_dispositivo, od.prazo_amostra,
            od.prazo_tte, od.prazo_tse, od.prazo_resistencia, od.prazo_durabilidade
        ]
        prazos_validos = [p for p in prazos if p]
        data_entrega = od.assinatura_tecnica_data.date()

        if all(data_entrega <= p for p in prazos_validos):
            dados_por_mes[nome_mes]["pontual"] += 1

    for m in meses:
        total = dados_por_mes[m]["total"]
        pontual = dados_por_mes[m]["pontual"]
        dados_percentuais[m] = round((pontual / total * 100), 2) if total else 0

    # Calcula média somente dos meses até o mês atual com valor > 0
    valores_validos = [v for i, v in enumerate(dados_percentuais.values(), start=1) if i <= mes_atual and v > 0]
    media = round(sum(valores_validos) / len(valores_validos), 2) if valores_validos else 0.0

    # Geração do gráfico
    grafico_base64 = None
    try:
        fig, ax = plt.subplots(figsize=(10, 4))
        x = meses[:mes_atual]
        y = [dados_percentuais[m] for m in x]
        ax.bar(x, y, color="#0d6efd")
        ax.axhline(y=meta, color="red", linestyle="--", label=f"Meta ({meta}%)")
        ax.set_ylim(0, 110)
        ax.set_ylabel("Cumprimento (%)")
        ax.set_title("Cumprimento de Prazo de Desenvolvimento por Mês")
        ax.legend()
        for i, val in enumerate(y):
            ax.text(i, val + 2, f"{val:.0f}%", ha="center", fontsize=9)

        buffer = io.BytesIO()
        plt.tight_layout()
        fig.savefig(buffer, format="png", dpi=150)
        grafico_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        buffer.close()
        plt.close(fig)
    except Exception:
        grafico_base64 = None

    # Comentários mensais até o mês atual
    comentarios = []
    for i, m in enumerate(meses[:mes_atual], start=1):
        valor = dados_percentuais[m]
        if valor >= meta:
            texto = f"O indicador está dentro da meta com {valor:.2f}% de cumprimento."
        else:
            texto = f"O indicador está abaixo da meta com {valor:.2f}% de cumprimento."
        comentarios.append({"data": m, "texto": texto})

    # Registro do indicador
    for i, m in enumerate(meses[:mes_atual], start=1):
        salvar_registro_indicador(
            indicador="5.1",
            ano=ano,
            mes=i,
            valor=dados_percentuais[m],
            media=media,
            meta=meta,
            total_realizados=dados_por_mes[m]["total"],
            total_aprovados=dados_por_mes[m]["pontual"],
            comentario=next((c["texto"] for c in comentarios if c["data"] == m), "")
        )

    context = {
        "ano": ano,
        "mes_atual": mes_atual,
        "meses": meses,
        "dados_percentuais": dados_percentuais,
        "dados_totais": {m: dados_por_mes[m]["total"] for m in meses},
        "dados_pontuais": {m: dados_por_mes[m]["pontual"] for m in meses},
        "media": media,
        "meta": meta,
        "grafico_base64": grafico_base64,
        "comentarios": comentarios,
    }

    return render(request, "indicadores/5_1_prazo_desenvolvimento.html", context)
