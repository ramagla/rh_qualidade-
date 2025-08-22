import io
import base64
import calendar
from datetime import datetime, timedelta
from io import BytesIO

import matplotlib
matplotlib.use("Agg")  # se for gerar gráficos no servidor
import matplotlib.pyplot as plt

from babel.dates import format_date
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count, Q, Min
from django.db.models.functions import TruncMonth, ExtractQuarter
from django.shortcuts import render
from django.utils.timezone import now

from comercial.models import PreCalculo, Cotacao
from Funcionario.models.funcionario import Funcionario
from comercial.utils.indicadores import salvar_registro_indicador


@login_required
@permission_required("comercial.view_indicador_prazo_cotacao", raise_exception=True)
def indicador_prazo_cotacao(request):
    ano = int(request.GET.get("ano", now().year))
    mes_atual = datetime.now().month
    meta = 90

    # 🗓️ Siglas dos meses em português
    meses = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

    # 🔁 Deduplicação por cotação + item + roteiro
    precalc_ids_unicos = (
        PreCalculo.objects
        .filter(cotacao__data_abertura__year=ano)
        .values(
            "cotacao_id",
            "analise_comercial_item__item_id",
            "analise_comercial_item__roteiro_selecionado_id"
        )
        .annotate(precalc_id=Min("id"))
        .values_list("precalc_id", flat=True)
    )

    # Inicializa os dicionários com chaves por sigla
    dados_por_mes = {mes: {"total": 0, "no_prazo": 0} for mes in meses}
    dados_totais = {}
    dados_atendidos = {}

    precalculos = (
        PreCalculo.objects
        .filter(id__in=precalc_ids_unicos)
        .select_related("cotacao")
    )

    for p in precalculos:
        if not p.cotacao or not p.cotacao.data_abertura:
            continue

        # Converte a data de abertura em sigla do mês
        nome_mes = format_date(p.cotacao.data_abertura, format="MMM", locale="pt_BR").lower().replace(".", "")
        
        if nome_mes not in dados_por_mes:
            continue  # segurança contra meses inválidos

        dados_por_mes[nome_mes]["total"] += 1

        prazo_limite = p.cotacao.data_abertura + timedelta(days=3)
        if p.criado_em.date() <= prazo_limite.date():
            dados_por_mes[nome_mes]["no_prazo"] += 1

    # Cálculo de percentuais
    dados_percentuais = {}
    for mes in meses:
        total = dados_por_mes[mes]["total"]
        no_prazo = dados_por_mes[mes]["no_prazo"]
        percentual = (no_prazo / total) * 100 if total else 0
        dados_percentuais[mes] = round(percentual, 2)
        dados_totais[mes] = total
        dados_atendidos[mes] = no_prazo

    # Média geral
    valores_validos = [v for v in dados_percentuais.values() if v > 0]
    media = round(sum(valores_validos) / len(valores_validos), 2) if valores_validos else 0

    # 📊 Geração do gráfico
    grafico_base64 = None
    if valores_validos:
        meses_ate_atual = meses[:mes_atual]
        valores_ate_atual = [dados_percentuais.get(m, 0) for m in meses_ate_atual]

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(meses_ate_atual, valores_ate_atual, color='#0d6efd')
        ax.set_ylim(0, 110)
        ax.set_ylabel('% Atendimento')
        ax.set_title('Atendimento ao Prazo de Cotação por Mês')
        ax.axhline(y=90, color='red', linestyle='--', label='Meta (90%)')
        ax.legend()

        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        grafico_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()
        plt.close()

    # Comentários mensais
    # Comentários mensais apenas até o mês atual
    comentarios = []
    mes_atual = datetime.now().month

    for i, mes in enumerate(meses, start=1):
        if i > mes_atual:
            continue  # pula meses futuros

        valor = dados_percentuais.get(mes, 0)

        if valor >= meta:
            texto = f"O índice de atendimento foi {valor:.2f}%, dentro da meta."
        else:
            texto = f"O índice de atendimento foi {valor:.2f}%, abaixo da meta."

        comentarios.append({
            "data": mes.capitalize(),
            "texto": texto
        })

    # Se por algum motivo nenhum mês até o atual tiver dados (extremamente improvável)
    if not comentarios:
        comentarios.append({
            "data": "-",
            "texto": "Não há dados disponíveis até o mês atual."
        })

    for i, mes in enumerate(meses[:mes_atual], start=1):
        salvar_registro_indicador(
            indicador="4.1",
            ano=ano,
            mes=i,
            valor=dados_percentuais[mes],
            media=media,
            meta=meta,
            total_realizados=dados_totais[mes],
            total_aprovados=dados_atendidos[mes],
            comentario=next((c["texto"] for c in comentarios if c["data"].lower() == mes), "")
        )
 
    # Renderiza com o contexto completo
    contexto = {
        "ano": ano,
        "meses": meses,
        "dados_percentuais": dados_percentuais,
        "dados_totais": dados_totais,
        "dados_atendidos": dados_atendidos,
        "media": media,
        "meta": 90,
        "grafico_base64": grafico_base64,
        "comentarios": comentarios,  # Agora sim, inserido corretamente
         "mes_atual": datetime.now().month,
    }

    return render(request, "indicadores/4_1_prazo_cotacao.html", contexto)


@login_required
@permission_required("comercial.view_indicador_itens_novos", raise_exception=True)
def indicador_itens_novos(request):
    ano = int(request.GET.get("ano", now().year))
    meta = 8
    trimestres_labels = ["1º T", "2º T", "3º T", "4º T"]
    trimestre_atual = ((now().month - 1) // 3) + 1

    precalc_qs = (
        PreCalculo.objects
        .filter(
            analise_comercial_item__isnull=False,
            analise_comercial_item__status="aprovado",
            cotacao__isnull=False,
            cotacao__tipo="Novo",
            cotacao__data_abertura__year=ano,
        )
        .values(
            "cotacao_id",
            "analise_comercial_item__item_id",
            "analise_comercial_item__roteiro_selecionado_id"
        )
        .annotate(precalc_id=Min("id"))
    )
    ids_unicos = list(precalc_qs.values_list("precalc_id", flat=True))

    dados_trim = {1: 0, 2: 0, 3: 0, 4: 0}
    codigos_por_trim = {1: [], 2: [], 3: [], 4: []}

    if ids_unicos:
        por_trim = (
            PreCalculo.objects
            .filter(id__in=ids_unicos)
            .annotate(trim=ExtractQuarter("cotacao__data_abertura"))
            .values("trim")
            .annotate(qtd=Count("id"))
        )
        for item in por_trim:
            dados_trim[int(item["trim"])] = item["qtd"]

        precs = (
            PreCalculo.objects
            .filter(id__in=ids_unicos)
            .select_related("cotacao", "analise_comercial_item", "analise_comercial_item__item")
        )
        for p in precs:
            if not p.cotacao or not p.cotacao.data_abertura:
                continue
            trimestre = ((p.cotacao.data_abertura.month - 1) // 3) + 1
            item = getattr(p.analise_comercial_item, "item", None)
            cod = getattr(item, "codigo", None) or str(item.pk if item else "-")
            codigos_por_trim[trimestre].append(cod)

    valores_validos = [v for i, v in dados_trim.items() if i <= trimestre_atual and v > 0]
    media = round(sum(valores_validos) / len(valores_validos), 2) if valores_validos else 0.0

    meses_por_trim = {
        1: "01|02|03",
        2: "04|05|06",
        3: "07|08|09",
        4: "10|11|12",
    }
    comentarios = []
    for t in range(1, 5):
        if t > trimestre_atual:
            continue
        qtd = dados_trim[t]
        if qtd == 0:
            continue
        status = "DENTRO DA META" if qtd >= meta else "FORA DA META"
        codigos = codigos_por_trim[t]
        comentarios.append({
            "data": f"{t}º T ({meses_por_trim[t]})",
            "texto": f"{qtd} itens novos vendidos ({status}). Códigos: {'; '.join(codigos)}"
        })

    grafico_base64 = None
    try:
        fig, ax = plt.subplots(figsize=(8.5, 3.6))
        x = list(range(trimestre_atual))
        y = [dados_trim[i + 1] for i in range(trimestre_atual)]
        ax.bar(x, y)
        ax.plot(x, [meta] * trimestre_atual, linewidth=2, linestyle="--", color="red")
        ax.set_xticks(x)
        ax.set_xticklabels(trimestres_labels[:trimestre_atual])
        ax.set_ylabel("Qtd. de itens")
        ax.set_title("Itens Novos Vendidos por Trimestre")
        ax.set_ylim(0, max(max(y), meta) + 1)
        for i, val in enumerate(y):
            ax.text(i, val + 0.2, str(val), ha="center", fontsize=9)
        buffer = io.BytesIO()
        plt.tight_layout()
        fig.savefig(buffer, format="png", dpi=150)
        plt.close(fig)
        grafico_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception:
        grafico_base64 = None

    dados_trimestre = {
        trimestres_labels[i - 1]: dados_trim[i] for i in range(1, 5)
    }
    total_itens_vendidos = sum(dados_trimestre.values())
    for t in range(1, trimestre_atual + 1):
        salvar_registro_indicador(
            indicador="4.2",
            ano=ano,
            trimestre=t,
            valor=dados_trim[t],
            media=media,
            meta=meta,
            total_realizados=meta,  # opcional
            total_aprovados=dados_trim[t],
            comentario=next((c["texto"] for c in comentarios if c["data"].startswith(f"{t}º T")), "")
        )

    contexto = {
        "ano": ano,
        "trimestres": trimestres_labels,
        "trimestre_atual": trimestre_atual,
        "dados_trimestre": dados_trimestre,
        "media": media,
        "meta": meta,
        "meta_total": meta * trimestre_atual,
        "grafico_base64": grafico_base64,
        "comentarios": comentarios,
        "codigos_por_trim": codigos_por_trim,
        "total_itens_vendidos": total_itens_vendidos,

    }
    return render(request, "indicadores/4_2_itens_novos.html", contexto)




@login_required
@permission_required("comercial.view_indicador_cotacoes_funcionario", raise_exception=True)
def indicador_cotacoes_funcionario(request):
    ano = int(request.GET.get("ano", datetime.now().year))
    mes_atual = datetime.now().month

    # Filtra funcionários ativos (exceto Gerson)
    funcionarios_ativos = Funcionario.objects.filter(
        data_desligamento__isnull=True,
        local_trabalho__nome__icontains="Comercial"
    ).exclude(nome__icontains="Gerson Melo Rodrigues")

    total_funcionarios = funcionarios_ativos.count()

    # Gera lista de meses abreviados até o mês atual
    meses_labels = [
        format_date(datetime(ano, m, 1), format="MMM", locale="pt_BR").capitalize()
        for m in range(1, mes_atual + 1)
    ]

    # Inicializa estrutura de dados
    dados_mensais = {mes: {"cotas": 0, "media": 0.0} for mes in meses_labels}
    valores_cotacoes = []
    valores_medias = []

    # Coleta de dados por mês
    for i, mes_nome in enumerate(meses_labels):
        mes_num = i + 1
        inicio = datetime(ano, mes_num, 1)
        fim = datetime(ano, mes_num, calendar.monthrange(ano, mes_num)[1])

        qtd_cotacoes = Cotacao.objects.filter(created_at__range=(inicio, fim)).count()
        media = round(qtd_cotacoes / total_funcionarios, 2) if total_funcionarios else 0.0

        dados_mensais[mes_nome]["cotas"] = qtd_cotacoes
        dados_mensais[mes_nome]["media"] = media
        valores_cotacoes.append(qtd_cotacoes)
        valores_medias.append(media)

    # Cálculo da média geral (considera apenas meses com média > 0)
    medias_validas = [v for v in valores_medias if v > 0]
    media_geral = round(sum(medias_validas) / len(medias_validas), 2) if medias_validas else 0.0

    # Cálculo da média de Nº de Cotações (considera apenas meses com cotações > 0)
    cotacoes_validas = [v for v in valores_cotacoes if v > 0]
    media_cotacoes_mensal = round(sum(cotacoes_validas) / len(cotacoes_validas), 2) if cotacoes_validas else 0.0

    # Geração do gráfico
    grafico_base64 = None
    meta = 20  # Meta definida

    if valores_medias:
        fig, ax = plt.subplots(figsize=(10, 3.5))
        ax.bar(meses_labels, valores_medias, color="#0d6efd", label="Média por Funcionário")
        ax.axhline(y=meta, color="red", linestyle="--", linewidth=2, label=f"Meta ({meta})")
        ax.set_ylabel("Cotações")
        ax.set_title("Cotações por Funcionário - Média Mensal")
        ax.set_ylim(0, max(max(valores_medias + [meta]) + 1, meta + 5))
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()

        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=150)
        grafico_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        buffer.close()
        plt.close(fig)

    comentarios = []
    for i, mes_nome in enumerate(meses_labels):
        media_mes = dados_mensais[mes_nome]["media"]
        if media_mes >= meta:
            texto = f"O número médio de cotações por funcionário em {mes_nome} foi {media_mes:.2f}, dentro da meta."
        else:
            texto = f"O número médio de cotações por funcionário em {mes_nome} foi {media_mes:.2f}, abaixo da meta."
        comentarios.append({"data": mes_nome, "texto": texto})

    for i, mes in enumerate(meses_labels, start=1):
        salvar_registro_indicador(
            indicador="4.3",
            ano=ano,
            mes=i,
            valor=dados_mensais[mes]["media"],
            media=media_geral,
            meta=20,
            total_realizados=dados_mensais[mes]["cotas"],
            total_aprovados=0,
            comentario=next((c["texto"] for c in comentarios if c["data"] == mes), "")
        )

    # Contexto para o template
    context = {
        "ano": ano,
        "dados_mensais": dados_mensais,
        "media_geral": media_geral,
        "total_funcionarios": total_funcionarios,
        "grafico_base64": grafico_base64,
        "comentarios": [],
        "mes_atual": mes_atual,
        "meses_labels": meses_labels,
        "media_cotacoes_mensal": media_cotacoes_mensal,
        "meta": meta,
        "comentarios": comentarios,

    }

    return render(request, "indicadores/4_3_cotacoes_funcionario.html", context)


@login_required
@permission_required("comercial.view_indicador_taxa_aprovacao", raise_exception=True)
def indicador_taxa_aprovacao(request):
    ano = int(request.GET.get("ano", datetime.now().year))
    mes_atual = datetime.now().month
    meses = [calendar.month_abbr[i].capitalize() for i in range(1, mes_atual + 1)]
    meta = 15

    precalc_qs = (
        PreCalculo.objects
        .filter(cotacao__data_abertura__year=ano)
        .values(
            "cotacao_id",
            "analise_comercial_item__item_id",
            "analise_comercial_item__roteiro_selecionado_id"
        )
        .annotate(precalc_id=Min("id"))
    )
    ids_unicos = list(precalc_qs.values_list("precalc_id", flat=True))

    dados_por_mes = {mes: {"total": 0, "fechados": 0, "percentual": 0.0} for mes in meses}

    precalcs = (
        PreCalculo.objects
        .filter(id__in=ids_unicos)
        .select_related("cotacao", "analise_comercial_item")
    )

    for p in precalcs:
        if not p.cotacao or not p.cotacao.data_abertura:
            continue

        mes = calendar.month_abbr[p.cotacao.data_abertura.month].capitalize()
        dados_por_mes[mes]["total"] += 1

        if getattr(p.analise_comercial_item, "status", "") == "aprovado":
            dados_por_mes[mes]["fechados"] += 1

    valores_percentuais = []
    for mes in meses:
        total = dados_por_mes[mes]["total"]
        aprovados = dados_por_mes[mes]["fechados"]
        percentual = (aprovados / total * 100) if total else 0
        dados_por_mes[mes]["percentual"] = round(percentual, 2)
        if percentual > 0:
            valores_percentuais.append(percentual)

    valores_validos = [p for p in valores_percentuais if p > 0]
    media = round(sum(valores_validos) / len(valores_validos), 2) if valores_validos else 0.0
    total_fechados = sum(d["fechados"] for d in dados_por_mes.values())
    total_realizados = sum(d["total"] for d in dados_por_mes.values())

    # Gráfico
    grafico_base64 = None
    try:
        fig, ax = plt.subplots(figsize=(10, 3.5))
        x = list(dados_por_mes.keys())
        y = [d["percentual"] for d in dados_por_mes.values()]
        ax.bar(x, y, color="#0d6efd")
        ax.axhline(y=meta, color="red", linestyle="--", linewidth=2, label=f"Meta ({meta}%)")
        ax.set_ylim(0, max(y + [meta]) + 10)
        ax.set_ylabel("Taxa de Aprovação (%)")
        ax.set_title("Taxa de Orçamentos Aprovados por Mês")
        ax.legend()
        for i, val in enumerate(y):
            ax.text(i, val + 1, f"{val:.1f}%", ha="center", fontsize=9)

        buffer = io.BytesIO()
        plt.tight_layout()
        fig.savefig(buffer, format="png", dpi=150)
        grafico_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        buffer.close()
        plt.close(fig)
    except Exception:
        grafico_base64 = None

    # 💬 Comentários por mês com base na meta
    comentarios = []
    for mes in meses:
        percentual = dados_por_mes[mes]["percentual"]
        if percentual >= meta:
            texto = f"O mês de {mes} está dentro da meta com {percentual:.1f}% de aprovação."
        else:
            texto = f"O mês de {mes} está abaixo da meta com apenas {percentual:.1f}% de aprovação."
        comentarios.append({"data": mes, "texto": texto})

    for i, mes in enumerate(meses, start=1):
        salvar_registro_indicador(
            indicador="4.4",
            ano=ano,
            mes=i,
            valor=dados_por_mes[mes]["percentual"],
            media=media,
            meta=meta,
            total_realizados=dados_por_mes[mes]["total"],
            total_aprovados=dados_por_mes[mes]["fechados"],
            comentario=next((c["texto"] for c in comentarios if c["data"] == mes), "")
        )

    context = {
        "ano": ano,
        "meta": meta,
        "media": media,
        "dados_por_mes": dados_por_mes,
        "grafico_base64": grafico_base64,
        "total_fechados": total_fechados,
        "total_realizados": total_realizados,
         "comentarios": comentarios,  # 👈 Aqui
        
    }

    return render(request, "indicadores/4_4_taxa_aprovacao.html", context)



from decimal import Decimal
from io import BytesIO
import base64

# helper local para gráfico de barras (mesmo padrão dos outros)
def gerar_grafico_barras(x_labels, y_values, metas_values=None, titulo="Faturamento Líquido Mensal"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # saneamento dos dados
    y = list(map(float, y_values))
    m = list(map(float, metas_values)) if metas_values is not None else None
    if m is not None and len(m) != len(y):
        # iguala o comprimento: preenche com a última meta conhecida ou zero
        last = m[-1] if m else 0.0
        m = (m + [last] * (len(y) - len(m)))[:len(y)]

    fig, ax = plt.subplots(figsize=(10, 3.5))

    # barras do realizado
    ax.bar(x_labels, y, label="Realizado", zorder=2)

    # linha da meta acima das barras
    if m is not None:
        ax.plot(x_labels, m, linestyle="--", linewidth=1.8, marker="o",
                label="Meta", color="red", zorder=3)

    ax.set_title(titulo)
    ax.set_ylabel("R$")

    # define limites com folga de 10% considerando realizado e meta
    ymax = max(y + (m if m is not None else [0.0])) if y else 0.0
    ax.set_ylim(0, ymax * 1.10 if ymax > 0 else 1)

    # rótulos nas barras
    for i, v in enumerate(y):
        if v > 0:
            ax.text(i, v, f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    ha="center", va="bottom", fontsize=8)

    # rótulos na meta
    if m is not None:
        for i, mv in enumerate(m):
            if mv > 0:
                ax.text(i, mv, f"{mv:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                        ha="center", va="bottom", fontsize=8, color="red")

    # grade leve para leitura
    ax.grid(axis="y", alpha=0.2, zorder=1)

    # legenda sempre visível
    ax.legend(loc="upper left")

    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")




@login_required
@permission_required("comercial.view_indicador_faturamento", raise_exception=True)
def indicador_faturamento(request):

    from django.utils.timezone import now
    from comercial.models.faturamento import FaturamentoRegistro
    from comercial.models.indicadores import MetaFaturamento
    from comercial.utils.indicadores import salvar_registro_indicador

    ano = int(request.GET.get("ano", now().year))
    mes_atual = now().month
    meses_labels = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

    # base do ano
    qs = (FaturamentoRegistro.objects
          .filter(ocorrencia__year=ano)
          .only("ocorrencia","tipo","nfe","valor_total","valor_total_com_ipi"))

    nf_validas = [Decimal("0.00")] * 12
    vales = [Decimal("0.00")] * 12
    devolucoes = [Decimal("0.00")] * 12

    for r in qs:
        m = r.ocorrencia.month - 1
        valor = r.valor_total_com_ipi or r.valor_total or Decimal("0.00")
        tipo = (r.tipo or "Venda")
        nfe = (r.nfe or "").strip().lower()

        if tipo == "Venda" and nfe not in ("", "vale"):
            nf_validas[m] += valor
        elif tipo == "Venda":
            vales[m] += valor
        elif tipo == "Devolução":
            devolucoes[m] += valor

    liquido = [(nf_validas[i] + vales[i] - devolucoes[i]).quantize(Decimal("0.01")) for i in range(12)]

    # metas por mês vindas do banco (até o mês atual)
    metas_mes = []
    for i in range(1, mes_atual + 1):
        meta_obj = MetaFaturamento.objects.filter(ano=ano, mes=i).first()
        metas_mes.append(meta_obj.valor if meta_obj else Decimal("0.00"))

    # médias e totais (até mês atual)
    realizado_visivel = liquido[:mes_atual]
    media = (sum(realizado_visivel) / (mes_atual or 1)).quantize(Decimal("0.01"))
    media_meta = (sum(metas_mes) / (mes_atual or 1)).quantize(Decimal("0.01"))
    meta_total = sum(metas_mes).quantize(Decimal("0.01"))

    # comentários + persistência no registro de indicadores
    comentarios = []
    for i in range(mes_atual):
        val = realizado_visivel[i]
        meta_val = metas_mes[i]
        status = "dentro da meta" if val >= meta_val else "abaixo da meta"
        texto = (
            "Faturamento de R$ "
            + f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            + " (meta: R$ "
            + f"{meta_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            + f") — {status}."
        )
        comentarios.append({"data": f"{meses_labels[i]}/{ano}", "texto": texto})

        # segue a MESMA assinatura usada nos indicadores 4.x
        salvar_registro_indicador(
            indicador="1.1",
            ano=ano,
            mes=i+1,
            valor=float(val),
            media=float(media),
            meta=float(meta_val),
            total_realizados=float(val),
            total_aprovados=0,
            comentario=texto
        )

    grafico_base64 = gerar_grafico_barras(
    meses_labels[:mes_atual],
    [float(v) for v in realizado_visivel],
    [float(m) for m in metas_mes]
)


    context = {
        "ano": ano,
        "mes_atual": mes_atual,
        "meses": meses_labels,
        "dados_faturamento": dict(zip(meses_labels, liquido)),
        "total_ano": sum(realizado_visivel),
        "media": media,
        "media_meta": media_meta,
        "metas_mes": dict(zip(meses_labels[:mes_atual], metas_mes)),
        "grafico_base64": grafico_base64,
        "comentarios": comentarios,
        "meta_total": meta_total,
    }
    return render(request, "indicadores/1_1_faturamento.html", context)
