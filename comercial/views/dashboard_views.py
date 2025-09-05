from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import (
    Count, Min, Sum, F, Case, When, DecimalField, ExpressionWrapper, Q
)
from django.db.models.functions import Coalesce, TruncMonth
from django.shortcuts import render
from django.utils.timezone import now

from comercial.models import Cliente, Cotacao, OrdemDesenvolvimento
from comercial.models.precalculo import PreCalculo, AnaliseComercial
from comercial.models.viabilidade import ViabilidadeAnaliseRisco
from comercial.models import Item


@login_required
def dashboard_comercial(request):
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    filtro_data = {}
    if data_inicio and data_fim:
        data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
        data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d")
        filtro_data = {"criado_em__range": (data_inicio_dt, data_fim_dt)}


    # Contagem de clientes e ordens
    clientes_ativos = Cliente.objects.filter(status="Ativo").count()
    clientes_reativados = Cliente.objects.filter(status="Reativado").count()

    # IDs únicos de pré-cálculos (1 por item + roteiro por cotação)
    precalc_ids_unicos = (
        PreCalculo.objects
        .filter(**filtro_data)
        .values(
            "cotacao_id",
            "analise_comercial_item__item_id",
            "analise_comercial_item__roteiro_selecionado_id"
        )
        .annotate(precalc_id=Min("id"))
        .values_list("precalc_id", flat=True)
    )


    total_clientes = clientes_ativos + clientes_reativados
    total_ordens = OrdemDesenvolvimento.objects.filter(created_at__range=filtro_data["criado_em__range"]).count() if filtro_data else OrdemDesenvolvimento.objects.count()

    hoje = now().date()

    ods_qs = OrdemDesenvolvimento.objects.all()
    if filtro_data:
        ods_qs = ods_qs.filter(created_at__range=filtro_data["criado_em__range"])

    ods_dentro_prazo = ods_qs.filter(
        prazo_amostra__isnull=False,
        prazo_amostra__gte=hoje
    ).count()

    ods_fora_prazo = ods_qs.filter(
        prazo_amostra__isnull=False,
        prazo_amostra__lt=hoje
    ).count()

    ods_amostras = ods_qs.filter(amostra="sim").count()
    ods_novos_itens = ods_qs.filter(razao="novo").count()




    # Últimas cotações abertas
    ultimas_cotacoes = Cotacao.objects.filter(data_abertura__range=filtro_data["criado_em__range"]) if filtro_data else Cotacao.objects.all().order_by("-data_abertura")[:5]

    # Total de cotações registradas
    total_cotacoes = Cotacao.objects.filter(data_abertura__range=filtro_data["criado_em__range"]).count() if filtro_data else Cotacao.objects.count()

    # Contagem de análises comerciais por status
    analises = AnaliseComercial.objects.select_related("precalculo")
    if filtro_data:
        analises = analises.filter(precalculo__criado_em__range=filtro_data["criado_em__range"])
    perdidas = analises.filter(status="reprovado").count()
    aprovadas = analises.filter(status="aprovado").count()
    em_analise = analises.filter(status="andamento").count()

    precos = PreCalculo.objects.filter(id__in=precalc_ids_unicos).annotate(
        preco_final=Case(
            When(preco_manual__gt=0, then=F("preco_manual")),
            default=F("preco_selecionado"),
            output_field=DecimalField()
        ),
        valor_total=F("analise_comercial_item__qtde_estimada") * Case(
            When(preco_manual__gt=0, then=F("preco_manual")),
            default=F("preco_selecionado"),
            output_field=DecimalField()
        )
    )

    valor_aprovadas = precos.filter(analise_comercial_item__status="aprovado").aggregate(total=Sum("valor_total"))["total"] or 0
    valor_reprovadas = precos.filter(analise_comercial_item__status="reprovado").aggregate(total=Sum("valor_total"))["total"] or 0
    valor_andamento = precos.filter(analise_comercial_item__status="andamento").aggregate(total=Sum("valor_total"))["total"] or 0
    total_cotacoes_com_analise = PreCalculo.objects.filter(id__in=precalc_ids_unicos, analise_comercial_item__isnull=False).count()

    # Total de cotações aprovadas
    total_aprovadas = PreCalculo.objects.filter(id__in=precalc_ids_unicos, analise_comercial_item__status="aprovado").count()
    valor_total = valor_aprovadas + valor_reprovadas + valor_andamento
    taxa_conversao = round((total_aprovadas / total_cotacoes_com_analise * 100), 1) if total_cotacoes_com_analise else 0
    
    # 1. Pré-cálculos por mês
    # 1. Pré-cálculos por mês
    precalculos_por_mes = (
        PreCalculo.objects.filter(criado_em__range=filtro_data["criado_em__range"]).annotate(mes=TruncMonth("criado_em"))
        if filtro_data
        else PreCalculo.objects.annotate(mes=TruncMonth("criado_em"))
    ).values("mes").annotate(total=Count("id")).order_by("mes")


    # 2. Itens por tipo por mês
    itens_por_tipo = (
        Item.objects.filter(criado_em__range=filtro_data["criado_em__range"]).annotate(mes=TruncMonth("criado_em"))
        if filtro_data
        else Item.objects.annotate(mes=TruncMonth("criado_em"))
    ).values("mes", "tipo_item").annotate(total=Count("id")).order_by("mes")

    # Organiza itens por mês/tipo (Cotacao/Corrente)
    dados_tipo_mes = {}
    for r in itens_por_tipo:
        mes_str = r["mes"].strftime("%b/%y")
        if mes_str not in dados_tipo_mes:
            dados_tipo_mes[mes_str] = {"Cotacao": 0, "Corrente": 0}
        dados_tipo_mes[mes_str][r["tipo_item"]] = r["total"]


    # 3. Top 5 clientes com maior valor total em cotações
    top_clientes_base = (
    PreCalculo.objects.filter(id__in=precalc_ids_unicos).annotate(
        valor_total=F("analise_comercial_item__qtde_estimada") * Case(
            When(preco_manual__gt=0, then=F("preco_manual")),
            default=F("preco_selecionado"),
            output_field=DecimalField()
        )
    )
    )
    top_clientes = (
        top_clientes_base.values("cotacao__cliente__razao_social")
        .annotate(total=Sum("valor_total"))
        .filter(total__gt=0)
        .order_by("-total")[:5]
    )


    top_itens = (
        top_clientes_base.values("analise_comercial_item__item__codigo", "analise_comercial_item__item__descricao")
        .annotate(total=Sum("valor_total"))
        .filter(total__gt=0)
        .order_by("-total")[:5]
    )


    total_viabilidades = (
        ViabilidadeAnaliseRisco.objects.filter(criado_em__range=filtro_data["criado_em__range"]).count()
        if filtro_data else
        ViabilidadeAnaliseRisco.objects.count()
    )


    # 1. Carrega viabilidades
    viabilidades = ViabilidadeAnaliseRisco.objects.all()
    if filtro_data:
        viabilidades = viabilidades.filter(criado_em__range=filtro_data["criado_em__range"])

    # 2. Conta conclusões por área
    def contar_conclusao(queryset, campo):
        return {
            "viavel": queryset.filter(**{campo: "viavel"}).count(),
            "alteracoes": queryset.filter(**{campo: "alteracoes"}).count(),
            "inviavel": queryset.filter(**{campo: "inviavel"}).count(),
        }

    comercial = contar_conclusao(viabilidades, "conclusao_comercial")
    viab_custos = contar_conclusao(viabilidades, "conclusao_custos")
    tecnica = contar_conclusao(viabilidades, "conclusao_tecnica")



    # 4. Faturamento por setor (setor da 1ª etapa)
    from tecnico.models import RoteiroProducao
    prec_base = PreCalculo.objects.filter(id__in=precalc_ids_unicos).annotate(
        preco_unitario=Coalesce(
            Case(
                When(preco_manual__gt=0, then=F("preco_manual")),
                default=F("preco_selecionado"),
                output_field=DecimalField()
            ),
            0,
            output_field=DecimalField()
        ),
        qtde=Coalesce(F("analise_comercial_item__qtde_estimada"), 0),
        valor_total=ExpressionWrapper(F("qtde") * F("preco_unitario"), output_field=DecimalField()),
    ).values("id", "valor_total", "roteiro_item__setor__nome")

    # Passo 2: somar os valores por setor, ignorando repetições de mesmo PreCalculo
    valores_por_setor = defaultdict(lambda: {"total": Decimal("0.00"), "qtd": 0})
    vistos = set()

    for row in prec_base:
        pid = row["id"]
        setor = row["roteiro_item__setor__nome"] or "SEM SETOR"
        if pid not in vistos:
            valores_por_setor[setor]["total"] += row["valor_total"]
            valores_por_setor[setor]["qtd"] += 1
            vistos.add(pid)

    faturamento_setores = sorted(
        [
            {"setor": setor, "total": dados["total"], "qtd": dados["qtd"]}
            for setor, dados in valores_por_setor.items()
            if dados["total"] > 0
        ],
        key=lambda x: x["total"],
        reverse=True
    )


    faturamento_setores_total = sum(x["total"] for x in faturamento_setores)
    faturamento_setores_qtd_total = sum(x["qtd"] for x in faturamento_setores)


    # 5. Cotações por segmento de cliente
    if filtro_data:
        segmentos = Cotacao.objects.filter(data_abertura__range=filtro_data["criado_em__range"]) \
            .values("cliente__tipo_cliente") \
            .annotate(total=Count("id")) \
            .order_by("cliente__tipo_cliente")
    else:
        segmentos = Cotacao.objects.values("cliente__tipo_cliente") \
            .annotate(total=Count("id")) \
            .order_by("cliente__tipo_cliente")


    precalculos_margem = PreCalculo.objects.filter(id__in=precalc_ids_unicos).exclude(preco_manual=0, preco_selecionado=None)

    margens = []
    for p in precalculos_margem:
        try:
            preco_final = (
                p.preco_manual if p.preco_manual and p.preco_manual > Decimal("0.00")
                else p.preco_selecionado
            )

            if preco_final is None:
                continue  # pula se não tem preço final

            precos_calculados = p.calcular_precos_com_impostos()
            if precos_calculados:
                custo_unitario = precos_calculados[0].get("unitario")
                if custo_unitario and custo_unitario > 0:
                    margem = ((preco_final - custo_unitario) / custo_unitario) * 100
                    margens.append(margem)
        except Exception as e:
            print(f"⚠️ Erro ao calcular margem para PreCalculo {p.id}: {e}")


    margem_media = round(sum(margens) / len(margens), 2) if margens else 0

    ultimos_precalculos = (
        PreCalculo.objects
        .filter(id__in=precalc_ids_unicos)
        .select_related(
            "cotacao", 
            "cotacao__cliente", 
            "analise_comercial_item", 
            "analise_comercial_item__item"
        )
        .order_by("-criado_em")[:5]
        .annotate(
            preco_final=Case(
                When(preco_manual__gt=0, then=F("preco_manual")),
                default=F("preco_selecionado"),
                output_field=DecimalField()
            ),
            valor_total=ExpressionWrapper(
                F("analise_comercial_item__qtde_estimada") *
                Case(
                    When(preco_manual__gt=0, then=F("preco_manual")),
                    default=F("preco_selecionado"),
                    output_field=DecimalField()
                ),
                output_field=DecimalField()
            )
        )
    )



    # Contexto do template
    context = {
        "total_clientes": total_clientes,
        "total_ordens": total_ordens,
        "ultimas_cotacoes": ultimas_cotacoes,
        "total_cotacoes": total_cotacoes,
        "perdidas": perdidas,
        "aprovadas": aprovadas,
        "em_analise": em_analise,
        "valor_aprovadas": valor_aprovadas,
        "valor_reprovadas": valor_reprovadas,
        "valor_andamento": valor_andamento,
        "valor_total": valor_total,
        "taxa_conversao": taxa_conversao,
        "dados_prec_mes": {
            r["mes"].strftime("%b/%y"): r["total"] for r in precalculos_por_mes
        },
        "dados_tipo_mes": dados_tipo_mes,
        "top_clientes": list(top_clientes),
        "faturamento_setores": faturamento_setores,
        "faturamento_setores_total": faturamento_setores_total,
        "faturamento_setores_qtd_total": faturamento_setores_qtd_total,
        "cotacoes_por_segmento": list(segmentos),
        "clientes_ativos": clientes_ativos,
        "clientes_reativados": clientes_reativados,
        "total_clientes": total_clientes,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "margem_media": margem_media,
        "top_itens": list(top_itens),
        "total_viabilidades": total_viabilidades,
        "ods_dentro_prazo": ods_dentro_prazo,
        "ods_fora_prazo": ods_fora_prazo,
        "ods_amostras": ods_amostras,
        "ods_novos_itens": ods_novos_itens,

       "viab_com_viavel": comercial["viavel"],
        "viab_com_alt": comercial["alteracoes"],
        "viab_com_inv": comercial["inviavel"],

       "viab_cus_viavel": viab_custos["viavel"],
        "viab_cus_alt": viab_custos["alteracoes"],
        "viab_cus_inv": viab_custos["inviavel"],


        "viab_tec_viavel": tecnica["viavel"],
        "viab_tec_alt": tecnica["alteracoes"],
        "viab_tec_inv": tecnica["inviavel"],
        "ultimos_precalculos": ultimos_precalculos,


    }

    return render(request, "comercial/dashboard_comercial.html", context)



# dashboard_views.py
from django.db.models import Count
from django.shortcuts import render
from comercial.models import Cliente

from collections import defaultdict
from django.db.models import Count
from django.shortcuts import render
from comercial.models import Cliente

@login_required
def mapa_clientes_por_regiao(request):
    # 1) Agrupa clientes por cidade/UF, coletando a razão social de cada um
    clientes = Cliente.objects.filter(status__in=["Ativo", "Reativado"], tipo_cadastro="Cliente") \
        .values("cidade", "uf", "razao_social")

    agrupado = defaultdict(list)
    for c in clientes:
        chave = (c["cidade"], c["uf"])
        agrupado[chave].append(c["razao_social"])

    dados_mapa = []
    for (cidade, uf), nomes in agrupado.items():
        dados_mapa.append({
            "cidade": cidade.title() if cidade else "",
            "uf": uf.upper() if uf else "",
            "total": len(nomes),
            "clientes": nomes
        })

    # 2) Calcula total geral de clientes (para %)
    total_geral = sum(item["total"] for item in dados_mapa)

    # 3) Agrupa por estado (UF), calculando total e % de representatividade
    estados_raw = Cliente.objects.filter(status__in=["Ativo", "Reativado"], tipo_cadastro="Cliente") \
        .values("uf") \
        .annotate(total=Count("id")) \
        .order_by("-total")

    dados_estados = []
    for e in estados_raw:
        percent = round(e["total"] / total_geral * 100, 1) if total_geral else 0
        dados_estados.append({
            "uf": e["uf"],
            "total": e["total"],
            "percent": percent
        })

    # 4) Renderiza a página, passando mapa e tabela de estados
    return render(request, "comercial/mapa_clientes.html", {
        "dados_mapa": dados_mapa,
        "total_geral": total_geral,
        "dados_estados": dados_estados
    })


from django.http import JsonResponse
from comercial.models import Cliente

from django.db.models import Count
from django.http import JsonResponse
from comercial.models import Cliente

@login_required
def listar_cidades_clientes(request):
    cidades_raw = (
        Cliente.objects
        .filter(status__in=["Ativo", "Reativado"], tipo_cadastro="Cliente")
        .values("cidade", "uf")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    cidades_dict = {
        f"{c['cidade'].upper()}-{c['uf']}": {
            "cidade": c["cidade"],
            "uf": c["uf"],
            "total": c["total"],
            "clientes": []
        }
        for c in cidades_raw
    }

    # corrige aqui também:
    for cli in Cliente.objects.filter(status__in=["Ativo", "Reativado"], tipo_cadastro="Cliente"):
        chave = f"{cli.cidade.upper()}-{cli.uf}"
        if chave in cidades_dict:
            cidades_dict[chave]["clientes"].append(cli.razao_social)

    return JsonResponse(list(cidades_dict.values()), safe=False)


@login_required
def listar_cidades_nomes(request):
    cidades_raw = (
        Cliente.objects
        .filter(status__in=["Ativo", "Reativado"], tipo_cadastro="Cliente")
        .values("cidade", "uf")
        .distinct()
    )

    cidades_lista = [
        f"{c['cidade'].upper()}-{c['uf'].upper()}"
        for c in cidades_raw
        if c["cidade"] and c["uf"]
    ]

    return JsonResponse(cidades_lista, safe=False)


# dashboard_views.py (substitua a view de faturamento por esta versão)
from datetime import date, datetime
from calendar import month_abbr
from decimal import Decimal
from django.conf import settings
from django.db.models import Sum, Count, Max, Q
from django.db.models.functions import TruncMonth
from comercial.models.faturamento import FaturamentoRegistro
from comercial.models import Item  # usado para tentar resolver setor primário
from comercial.models.indicadores import MetaFaturamento  # <- usar a tabela de metas
from decimal import Decimal, ROUND_HALF_UP
from tecnico.models import RoteiroProducao
from django.db.models import OuterRef, Subquery, CharField, Value
from django.db.models.functions import Coalesce
from tecnico.models.roteiro import EtapaRoteiro  # campo correto está aqui
from comercial.models import Cliente
import json


def _range_datas(request):
    """Resolve o intervalo [data_inicio, data_fim]. Default: ano corrente."""
    hj = date.today()
    di = request.GET.get("data_inicio")
    df = request.GET.get("data_fim")
    if di and df:
        di = datetime.strptime(di, "%Y-%m-%d").date()
        df = datetime.strptime(df, "%Y-%m-%d").date()
    else:
        di = date(hj.year, 1, 1)
        df = date(hj.year, 12, 31)
    return di, df

def _meses_label(di, df):
    """Retorna lista de (ano, mes) dentro do intervalo e labels 'jan', 'fev', ..."""
    meses = []
    cur = date(di.year, di.month, 1)
    while cur <= df:
        meses.append((cur.year, cur.month, month_abbr[cur.month].lower()))
        # próximo mês
        if cur.month == 12:
            cur = date(cur.year+1, 1, 1)
        else:
            cur = date(cur.year, cur.month+1, 1)
    return meses

# dashboard_views.py (funções auxiliares – agora lê do banco e só cai no settings se faltar)
def _meta_anual(ano: int) -> Decimal:
    mapa = getattr(settings, "META_FATURAMENTO_ANUAL", {})
    val = mapa.get(ano, Decimal("0"))
    return Decimal(str(val))

def _meta_mensal_fallback(ano: int, mes: int) -> Decimal:
    meta_ano = _meta_anual(ano)
    if meta_ano > 0:
        return (meta_ano / Decimal("12")).quantize(Decimal("0.01"))
    return Decimal("0.00")

def _metas_mensais_por_periodo(di, df):
    """
    Retorna (metas_mes_chart:list[float], meta_acumulada:Decimal) para o range.
    Prioriza registros de MetaFaturamento; se faltar mês, usa fallback do settings.
    """
    meses = _meses_label(di, df)  # [(ano, mes, 'jan'), ...]
    # carrega todos os registros do(s) ano(s) do range
    metas_qs = MetaFaturamento.objects.filter(ano__gte=di.year, ano__lte=df.year)
    metas_map = {(m.ano, m.mes): m.valor for m in metas_qs}

    metas_mes_dec = []
    for y, m, _ in meses:
        val = metas_map.get((y, m))
        if val is None:
            val = _meta_mensal_fallback(y, m)
        metas_mes_dec.append(Decimal(val))

    meta_acumulada = sum(metas_mes_dec) if metas_mes_dec else Decimal("0.00")
    # Para os gráficos (Chart.js), entregamos floats serializáveis
    metas_mes_chart = [float(v) for v in metas_mes_dec]
    return metas_mes_chart, meta_acumulada


def _resolver_setor_primario_por_item_codigo(item_codigo: str) -> str:
    """
    Resolve o setor 'primário' do item via modelo Item/roteiro.
    Fallback para 'SEM SETOR' quando não for possível resolver.
    """
    try:
        it = Item.objects.filter(codigo__iexact=item_codigo).first()
        if not it:
            return "SEM SETOR"
        # Tente acessar alguma relação de roteiro/etapas -> setor
        # Ajuste estes acessos conforme seus modelos do app técnico.
        # Preferimos o primeiro setor do roteiro principal.
        if hasattr(it, "roteiro_item") and getattr(it.roteiro_item, "setor", None):
            return it.roteiro_item.setor.nome or "SEM SETOR"
        if hasattr(it, "roteiroproducao_set"):
            r0 = it.roteiroproducao_set.order_by("ordem").first()
            if r0 and getattr(r0, "setor", None):
                return r0.setor.nome or "SEM SETOR"
    except Exception:
        pass
    return "SEM SETOR"

@login_required
@permission_required("comercial.view_dashboard_faturamento", raise_exception=True)
def dashboard_faturamento(request):
    di, df = _range_datas(request)
    tab_ativa = (request.GET.get("tab") or "").strip()
    ano_ref = df.year  # usamos o ano do fim do filtro como referência

    # Base do período
    base = FaturamentoRegistro.objects.filter(ocorrencia__gte=di, ocorrencia__lte=df)
    vendas = base.filter(tipo="Venda")
    devolucoes = base.filter(tipo="Devolução")

    # === CARDS (aba Metas) ===
    fat_acumulado = vendas.aggregate(s=Sum("valor_total_com_ipi"))["s"] or Decimal("0")
    meta_ano = _meta_anual(ano_ref)

    # dashboard_views.py (dentro da dashboard_faturamento – novo cálculo de metas)
    meses = _meses_label(di, df)

    # vendas por mês (em float para Chart.js)
    valores_mes_dec = []
    for y, m, _ in meses:
        v_mes = vendas.filter(ocorrencia__year=y, ocorrencia__month=m)\
                    .aggregate(s=Sum("valor_total_com_ipi"))["s"] or Decimal("0")
        valores_mes_dec.append(Decimal(v_mes))

    valores_mes = [float(v) for v in valores_mes_dec]  # série para o gráfico

    # metas do período (DB + fallback) e meta acumulada
    metas_mes, meta_acumulada = _metas_mensais_por_periodo(di, df)

    dif_valor = (fat_acumulado - meta_acumulada)

    # % somente se houver meta > 0
    dif_percent = (dif_valor / meta_acumulada * 100) if meta_acumulada else Decimal("0")
    dif_percent = dif_percent.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # >>> GARANTE valores para o card
    dif_negativo = dif_valor < 0
    dif_valor_abs = abs(dif_valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Séries acumuladas (linhas)
    metas_mes_dec = [Decimal(str(v)) for v in metas_mes]

    # Acumulados (usando Decimal internamente)
    acum_fat_dec = []
    acum_meta_dec = []
    running_fat = Decimal("0")
    running_meta = Decimal("0")
    for i in range(len(meses)):
        running_fat += valores_mes_dec[i]     # usa Decimal
        running_meta += metas_mes_dec[i]      # usa Decimal
        acum_fat_dec.append(running_fat)
        acum_meta_dec.append(running_meta)

    # Séries finais para Chart.js (float)
    acum_fat  = [float(v) for v in acum_fat_dec]
    acum_meta = [float(v) for v in acum_meta_dec]

    # Desvio por mês (float, para o gráfico)
    desvios_percent = []
    for i in range(len(meses)):
        mm = float(metas_mes_dec[i])
        vm = float(valores_mes_dec[i])
        desvios_percent.append(((vm - mm) / mm * 100) if mm else 0.0)

    # === Tabela: Faturamento por Setor Primário ===
    # somamos por item e mapeamos para setor primário
    # 1) Apura faturamento por item no período
    agg_por_item = (
        vendas.exclude(item_codigo__isnull=True).exclude(item_codigo__exact="")
            .values("item_codigo")
            .annotate(total=Sum("valor_total_com_ipi"))
    )

    # 2) Normaliza códigos e prepara lista única para buscar o setor no Item.roteiro_item.setor
    codigos_norm = { (r["item_codigo"] or "").strip().upper() for r in agg_por_item }
    primeira_etapa_setor = (
        EtapaRoteiro.objects
        .filter(roteiro__item=OuterRef("pk"))        # FK: EtapaRoteiro -> RoteiroProducao -> Item
        .order_by("etapa", "pk")                     # campo correto é 'etapa'
        .values("setor__nome")[:1]                   # pega o nome do setor da 1ª etapa
    )

    itens = (
        Item.objects
            .filter(codigo__in=codigos_norm)
            .annotate(
                setor_primario=Coalesce(
                    Subquery(primeira_etapa_setor, output_field=CharField()),
                    Value("SEM SETOR")
                )
            )
            .values("codigo", "setor_primario")
    )

    item_setor_map = {
        (row["codigo"] or "").strip().upper(): (row["setor_primario"] or "SEM SETOR")
        for row in itens
    }

    # 4) Agrega por setor primário
    por_setor = {}
    for r in agg_por_item:
        cod = (r["item_codigo"] or "").strip().upper()
        setor = item_setor_map.get(cod, "SEM SETOR")
        por_setor[setor] = por_setor.get(setor, Decimal("0.00")) + (r["total"] or Decimal("0.00"))

    # 5) Monta tabela ordenada e totais
    tabela_setores = [
        {"setor": s, "total": v} for s, v in sorted(por_setor.items(), key=lambda x: x[1], reverse=True)
    ]
    total_setores = sum((x["total"] for x in tabela_setores), Decimal("0.00"))

    # === Aba Vendas ===
    total_vendas_periodo = fat_acumulado or Decimal("0")
    top_itens_raw = list(agg_por_item.order_by("-total")[:10])
    top_itens = []
    for r in top_itens_raw:
        tot = r["total"] or Decimal("0")
        perc = (tot / total_vendas_periodo * 100) if total_vendas_periodo else Decimal("0")
        top_itens.append({
            "item_codigo": r["item_codigo"] or "—",
            "total": float(tot),
            "percent": float(perc.quantize(Decimal("0.01")))
        })

    # ===== Curva ABC por CLIENTE =====
    abc_cli_qs = (
        vendas
        .annotate(
            cliente_label=Case(
                When(cliente_vinculado__isnull=False, then=F("cliente_vinculado__razao_social")),
                default=F("cliente"),
                output_field=CharField(),
            )
        )
        .values("cliente_label")
        .annotate(total=Sum("valor_total_com_ipi"))
        .order_by("-total")
    )
    abc_cli = list(abc_cli_qs)

    total_geral_abc = sum((r["total"] or Decimal("0")) for r in abc_cli) or Decimal("0")
    limite_clientes = 30
    if len(abc_cli) > limite_clientes:
        top = abc_cli[:limite_clientes]
        soma_top = sum((r["total"] or Decimal("0")) for r in top)
        resto = total_geral_abc - soma_top
        if resto > 0:
            top.append({"cliente__razao_social": "OUTROS", "total": resto})
        abc_cli = top

    acum = Decimal("0")
    abc_labels = []
    abc_values = []
    abc_cumperc = []
    for r in abc_cli:
        v = r["total"] or Decimal("0")
        acum += v
        abc_labels.append(r.get("cliente_label") or "—")
        abc_values.append(float(v))
        abc_cumperc.append(float((acum / total_geral_abc) * Decimal("100")) if total_geral_abc else 0.0)


    # Comparativo YOY (ano_ref vs ano_ref-1), meses 1..12
    def _serie_ano(ano):
        qs = FaturamentoRegistro.objects.filter(ocorrencia__year=ano, tipo="Venda")
        by_mes = dict(qs.annotate(m=TruncMonth("ocorrencia"))
                        .values("m").annotate(s=Sum("valor_total_com_ipi"))
                        .values_list("m", "s"))
        out = []
        for m in range(1, 12+1):
            key = date(ano, m, 1)
            val = by_mes.get(key, Decimal("0"))
            out.append(float(val or 0))
        return out

    serie_atual = _serie_ano(ano_ref)        # retorna Decimals
    serie_ant   = _serie_ano(ano_ref - 1)    # retorna Decimals
    labels_yoy  = ["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"]

    # === Aba Devoluções ===
    valor_devolucoes = devolucoes.aggregate(s=Sum("valor_total_com_ipi"))["s"] or Decimal("0")
    qtde_devolucoes  = devolucoes.count()

    # Se o campo 'cliente' do FaturamentoRegistro for FK e você quiser o nome,
    # troque "cliente" por "cliente__razao_social" abaixo.
    dev_por_cliente = list(
        devolucoes.values("cliente").annotate(total=Sum("valor_total_com_ipi")).order_by("-total")
    )
    dev_por_item = list(
        devolucoes.values("item_codigo").annotate(total=Sum("valor_total_com_ipi")).order_by("-total")
    )

    # Serializa para JSON seguro (labels e valores já prontos)
    dev_cliente_json = json.dumps(
        [{"label": (r.get("cliente") or "—"), "total": float(r.get("total") or 0)} for r in dev_por_cliente],
        ensure_ascii=False
    )
    dev_item_json = json.dumps(
        [{"label": (r.get("item_codigo") or "—"), "total": float(r.get("total") or 0)} for r in dev_por_item],
        ensure_ascii=False
    )

    # === Aba FICHA (filtro local por cliente) ===
    # O select trabalha com o NOME do cliente que vem do próprio FaturamentoRegistro (campo de texto "cliente")
    cliente_nome_sel = (request.GET.get("cliente") or "").strip()

    # Opções do select: nomes distintos de clientes presentes no período filtrado
    clientes_opcoes = list(
        base.exclude(cliente__isnull=True)
            .exclude(cliente__exact="")
            .values_list("cliente", flat=True)
            .distinct()
            .order_by("cliente")
    )

    # Tentativa de mapear o nome a um Cliente cadastrado (apenas para exibir status etc.)
    cliente_sel = Cliente.objects.filter(razao_social__iexact=cliente_nome_sel).first() if cliente_nome_sel else None

    # Monta o filtro preferindo o nome; amplia com FK/código quando existir correspondência
    q_cli = Q()
    if cliente_nome_sel:
        q_cli |= Q(cliente__iexact=cliente_nome_sel)
    if cliente_sel:
        q_cli |= Q(cliente_vinculado_id=cliente_sel.id)
        cod_bm = (getattr(cliente_sel, "cod_bm", "") or "").strip()
        if cod_bm:
            q_cli |= Q(cliente_codigo__iexact=cod_bm)

    # Querysets da ficha
    vendas_cli = vendas.filter(q_cli) if q_cli else vendas.none()
    devol_cli  = devolucoes.filter(q_cli) if q_cli else devolucoes.none()

    # Acumulados / métricas
    ficha_total = vendas_cli.aggregate(s=Sum("valor_total_com_ipi"))["s"] or Decimal("0")
    ficha_qtde_devolucoes = devol_cli.count()
    ficha_ultima_compra = vendas_cli.aggregate(m=Max("ocorrencia"))["m"]

    ficha_pedidos = (
        vendas_cli.exclude(nfe__isnull=True).exclude(nfe__exact="")
                .values("nfe").distinct().count()
    )
    ficha_valor_medio = (ficha_total / ficha_pedidos) if ficha_pedidos else Decimal("0")

    # Ranking por participação no faturamento do período
    perc = (ficha_total / fat_acumulado * 100) if fat_acumulado else Decimal("0")
    ficha_ranking = "A" if perc > 7 else ("B" if perc >= 2 else "C")

    # Tabela de itens
    itens_cli = (
        vendas_cli.exclude(item_codigo__isnull=True).exclude(item_codigo__exact="")
                .values("item_codigo")
                .annotate(
                    qtde=Sum("item_quantidade"),
                    total=Sum("valor_total_com_ipi"),
                    ultima=Max("ocorrencia"),
                )
                .order_by("-total")
    )
    ficha_produtos = [
        {
            "item_codigo": r["item_codigo"],
            "qtde": r["qtde"] or 0,
            "total": r["total"] or Decimal("0"),
            "ultima": r["ultima"],
        }
        for r in itens_cli
    ]
    ficha_totais = {
        "qtde": sum((r["qtde"] or 0) for r in ficha_produtos),
        "total": sum((r["total"] or Decimal("0")) for r in ficha_produtos),
    }


    context = {
        # filtro
        "data_inicio": di.strftime("%Y-%m-%d"),
        "data_fim": df.strftime("%Y-%m-%d"),

        # === Metas ===
        "fat_acumulado": fat_acumulado,
        "meta_acumulada": meta_acumulada,
        "valores_mes": valores_mes,    
        "metas_mes": metas_mes,  
        "dif_valor": dif_valor,
        "dif_percent": dif_percent,     # já vem com 2 casas
        "dif_negativo": dif_negativo,
        "dif_valor_abs": dif_valor_abs, # Decimal pronto para o filtro formatar_reais
        "labels_meses": [lbl for (_, _, lbl) in meses],
        "valores_mes": valores_mes,
        "metas_mes": metas_mes,
        "acum_fat": acum_fat,
        "acum_meta": acum_meta,
        "desvios_percent": [round(x, 2) for x in desvios_percent],
        "tabela_setores": tabela_setores,
        "total_setores": total_setores,

        # === Vendas ===
        "top_itens_json":   json.dumps(top_itens, ensure_ascii=False),
        "labels_yoy_json":  json.dumps(labels_yoy, ensure_ascii=False),
        "serie_atual_json": json.dumps([float(v or 0) for v in serie_atual]),
        "serie_ant_json":   json.dumps([float(v or 0) for v in serie_ant]),
        "ano_ref": ano_ref,
        "ano_ant": ano_ref - 1,

        # >>> Curva ABC (por CLIENTE) em JSON <<<
        "abc_labels_json":  json.dumps(abc_labels, ensure_ascii=False),
        "abc_values_json":  json.dumps(abc_values),
        "abc_cumperc_json": json.dumps(abc_cumperc),

        # === Devoluções ===
         "valor_devolucoes": valor_devolucoes,
        "qtde_devolucoes": qtde_devolucoes,
        "dev_cliente_json": dev_cliente_json,
        "dev_item_json": dev_item_json,

        # === Ficha ===
        "clientes_opcoes": clientes_opcoes,  
        "cliente_nome_sel": cliente_nome_sel,
        "cliente_sel": cliente_sel,
        "ficha_total": ficha_total,
        "ficha_qtde_devolucoes": ficha_qtde_devolucoes,
        "ficha_pedidos": ficha_pedidos,
        "ficha_valor_medio": ficha_valor_medio,
        "ficha_ultima_compra": ficha_ultima_compra,
        "ficha_ranking": ficha_ranking,
        "ficha_produtos": ficha_produtos,
        "ficha_totais": ficha_totais,
        "tab_ativa": tab_ativa,  
    }
    return render(request, "comercial/dashboard_faturamento.html", context)


# comercial/views/dashboard_views.py
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.db.models import Q

from comercial.models.cotacao import Cotacao
from comercial.models.precalculo import PreCalculo, PreCalculoMaterial, PreCalculoServicoExterno

# ----------------------------
# Página
# ----------------------------
@login_required
@permission_required("comercial.view_precalculo", raise_exception=True)
def acompanhamento_precalculo(request):
    """
    Página do acompanhamento do Pré-Cálculo (por Cotação/Pré-Cálculo).
    O fluxo é atualizado via AJAX.
    """
    # Carrega algumas cotações para o select (opcionalmente filtra por período GET)
    qs_cot = Cotacao.objects.order_by("-id")[:50]
    contexto = {
        "cotacoes": qs_cot,
        "titulo": "Acompanhamento do Pré-Cálculo (tempo real)",
        "descricao": "Selecione a Cotação e o Pré-Cálculo para visualizar o fluxo por etapas.",
    }
    return render(request, "comercial/acompanhamento_live.html", contexto)


# ----------------------------
# AJAX helpers
# ----------------------------
@login_required
@permission_required("comercial.view_precalculo", raise_exception=True)
def ajax_precalculos_por_cotacao(request, cotacao_id: int):
    """
    Retorna a lista de pré-cálculos de uma cotação para preencher o segundo select.
    """
    cot = get_object_or_404(Cotacao, pk=cotacao_id)
    precs = (
        PreCalculo.objects
        .filter(cotacao=cot)
        .order_by("-id")
        .values("id", "numero")
    )
    data = [{"id": p["id"], "label": f'{p["numero"]}'} for p in precs]
    return JsonResponse({"ok": True, "precalculos": data})


from django.utils import timezone

@login_required
@permission_required("comercial.view_precalculo", raise_exception=True)
def ajax_status_precalculo(request, pk: int):
    """
    Calcula o status de cada etapa do fluxo e retorna em JSON,
    incluindo 'meta' (responsável e data) para exibição à direita do card.
    """
    prec = get_object_or_404(PreCalculo, pk=pk)

    def _fmt_date(dt):
        """Aceita date/datetime; não quebra com datetime naive."""
        if not dt:
            return ""
        try:
            if isinstance(dt, datetime):
                # só converte para o fuso local se for AWARE
                if timezone.is_aware(dt):
                    dt = timezone.localtime(dt)
                # quando for datetime, muitas vezes você quer hora também
                return dt.strftime("%d/%m/%Y %H:%M")
            # objetos date (ou qualquer um com strftime)
            return dt.strftime("%d/%m/%Y")
        except Exception:
            return ""

    def _first_attr(obj, *names):
        """retorna o primeiro atributo existente e não vazio"""
        for n in names:
            if obj and hasattr(obj, n):
                val = getattr(obj, n)
                if callable(val):
                    try:
                        val = val()
                    except Exception:
                        val = None
                if val not in (None, "", 0):
                    return val
        return None

    def _nome(obj):
        # tenta achar nome amigável de usuário/funcionário
        v = _first_attr(obj,
            "nome", "get_full_name", "full_name", "nome_completo",
            "first_name", "username", "responsavel_nome")
        return str(v) if v else ""

    # ---------- Nó: Cotação ----------
    cot = getattr(prec, "cotacao", None)
    cot_resp = _first_attr(cot, "responsavel", "usuario_responsavel", "criado_por", "usuario")
    cot_dt   = _first_attr(cot, "data_abertura", "criado_em", "atualizado_em")
    no_cotacao = {
        "titulo": "Cotação",
        "icone": "bi-clipboard-data",
        "status": "ok" if cot else "pendente",
        "detalhe": f"#{getattr(cot, 'numero', '')}" if cot else "Sem cotação vinculada",
        "meta": {
            "resp": f"Resp.: {_nome(cot_resp)}" if cot_resp else "",
            "data": _fmt_date(cot_dt)
        }
    }

    # --- Nó: Análise Comercial (conclusão pela "Conclusão da Análise Crítica")
    ac = getattr(prec, "analise_comercial_item", None)

    # tenta localizar o campo "Conclusão da Análise Crítica" em possíveis nomes
    ac_conc = _first_attr(
        ac,
        "conclusao_analise_critica", "conclusao_da_analise_critica",
        "conclusao_critica", "analise_critica_conclusao", "conclusao"
    )

    # regra: OK somente se o campo estiver preenchido (não vazio/None)
    if ac_conc not in (None, "", 0, False):
        ac_status = "ok"
        ac_detalhe = str(ac_conc)
    else:
        # se quiser manter informação auxiliar do status anterior, pode sinalizar "Pendente"
        ac_status = "pendente"
        ac_detalhe = "Pendente"

    ac_resp = _first_attr(ac, "responsavel", "usuario", "atualizado_por", "criado_por")
    ac_dt   = _first_attr(ac, "atualizado_em", "modificado_em", "criado_em", "data")

    no_analise = {
        "titulo": "Análise Comercial",
        "icone": "bi-clipboard-check",
        "status": ac_status,
        "detalhe": ac_detalhe,
        "meta": { "resp": f"Resp.: {_nome(ac_resp)}" if ac_resp else "", "data": _fmt_date(ac_dt) }
    }
    # ---------- Nó: Materiais (apenas selecionado em cartões laterais) ----------
    qs_mat = PreCalculoMaterial.objects.filter(precalculo=prec)
    tem_preco_mat = qs_mat.filter(preco_kg__isnull=False).exists()
    compras_atraso_mat = getattr(prec, "compras_em_atraso", False)
    status_materiais = "ok" if tem_preco_mat else "pendente"
    if compras_atraso_mat:
        status_materiais = "atraso"

    def _fmt_brl(v):
        from decimal import Decimal
        try:
            q = Decimal(str(v or 0))
        except Exception:
            return ""
        s = f"{q:,.4f}"
        return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")

    # só os selecionados
    mat_sel = qs_mat.filter(selecionado=True)

    cards_lado_mat = []
    for m in mat_sel:   # sem select_related para não dar FieldError
        codigo = getattr(m, "codigo", "") or getattr(m, "nome_materia_prima", "") or "-"
        descricao = (getattr(m, "descricao", "") or "").strip()

        preco = getattr(m, "preco_kg", None)
        # tentativas de “peso total”
        peso_total = (
            getattr(m, "peso_liquido_total", None)
            or getattr(m, "peso_bruto_total", None)
            or getattr(m, "peso_liquido", None)
            or getattr(m, "desenvolvido_mm", None)
            or 0
        )
        valor_total = (preco or 0) * (peso_total or 0)

        cards_lado_mat.append({
            "titulo": str(codigo),
            "sub": descricao,
            "badge": "Material",
            "info1": f"Preço: {_fmt_brl(preco)}" if preco else "Preço: —",
            "info2": f"Peso: {peso_total}",
            "info3": f"Total: {_fmt_brl(valor_total)}",
        })

    mat_last = qs_mat.order_by("-id").first()
    mat_resp = _first_attr(mat_last, "responsavel", "usuario", "comprador", "atualizado_por", "criado_por")
    mat_dt   = _first_attr(mat_last, "atualizado_em", "modificado_em", "criado_em", "data")

    no_materiais = {
        "titulo": "Materiais",
        "icone": "bi-box",
        "status": status_materiais,
        "detalhe": "Com preço" if tem_preco_mat else "Sem preço",
        "meta": { "resp": f"Resp.: {_nome(mat_resp)}" if mat_resp else "", "data": _fmt_date(mat_dt) },
        # >>> cartões laterais
        "cards_lado": cards_lado_mat
    }

    # ---------- Nó: Serviços Externos (apenas selecionado em cartões laterais) ----------
    qs_serv = PreCalculoServicoExterno.objects.filter(precalculo=prec)
    total_serv = qs_serv.count()
    com_preco_serv = qs_serv.filter(preco_kg__gt=0).count()
    compras_atraso_serv = getattr(prec, "compras_em_atraso", False)
    status_servicos = "ok" if (total_serv == 0 or com_preco_serv == total_serv) else "andamento"
    if total_serv and com_preco_serv == 0:
        status_servicos = "pendente"
    if compras_atraso_serv:
        status_servicos = "atraso"

    serv_sel = qs_serv.filter(selecionado=True)

    cards_lado_serv = []
    for s in serv_sel: 
        # tenta código/desc do insumo ou da matéria-prima vinculada no insumo
        alvo = getattr(s, "insumo", None)
        codigo = (
            getattr(s, "codigo_materia_prima", "")
            or (getattr(alvo, "materia_prima", None) and getattr(alvo.materia_prima, "codigo", "")) or "-"
        )
        descricao = (
            getattr(s, "descricao_materia_prima", "")
            or (getattr(alvo, "materia_prima", None) and getattr(alvo.materia_prima, "descricao", "")) or ""
        )

        preco = getattr(s, "preco_kg", None)
        peso_total = (
            getattr(s, "peso_liquido_total", None)
            or getattr(s, "peso_bruto_total", None)
            or getattr(s, "peso_liquido", None)
            or getattr(s, "desenvolvido_mm", None)
            or 0
        )
        valor_total = (preco or 0) * (peso_total or 0)

        cards_lado_serv.append({
            "titulo": str(codigo),
            "sub": (descricao or "").strip(),
            "badge": "Serviço",
            "info1": f"Preço: {_fmt_brl(preco)}" if preco else "Preço: —",
            "info2": f"Peso: {peso_total}",
            "info3": f"Total: {_fmt_brl(valor_total)}",
        })

    serv_last = qs_serv.order_by("-id").first()
    serv_resp = _first_attr(serv_last, "responsavel", "usuario", "comprador", "atualizado_por", "criado_por")
    serv_dt   = _first_attr(serv_last, "atualizado_em", "modificado_em", "criado_em", "data")

    no_servicos = {
        "titulo": "Serviços Externos",
        "icone": "bi-tools",
        "status": status_servicos,
        "detalhe": f"{com_preco_serv}/{total_serv} com preço" if total_serv else "Sem serviços",
        "meta": { "resp": f"Resp.: {_nome(serv_resp)}" if serv_resp else "", "data": _fmt_date(serv_dt) },
        # >>> cartões laterais
        "cards_lado": cards_lado_serv
    }



    # ---------- Nó: Roteiro (OK se houver Observações do Roteiro no PreCalculo) ----------
    import re

    # CKEditor fica em PreCalculo.observacoes_roteiro
    obs_html = getattr(prec, "observacoes_roteiro", "") or ""
    obs_txt  = re.sub(r"<[^>]+>", "", str(obs_html)).strip()  # remove tags e espaços

    if obs_txt:
        rot_status  = "ok"
        rot_detalhe = obs_txt[:80]  # mostra um resumo
    else:
        rot_status  = "pendente"
        rot_detalhe = "Não definido"

    # meta: como as observações pertencem ao PreCalculo, usamos o próprio registro
    rot_resp = _first_attr(prec, "updated_by", "criado_por", "created_by", "usuario")
    rot_dt   = _first_attr(prec, "updated_at", "criado_em", "created_at")

    no_roteiro = {
        "titulo": "Roteiro",
        "icone": "bi-diagram-3",
        "status": rot_status,
        "detalhe": rot_detalhe,
        "meta": {
            "resp": f"Resp.: {_nome(rot_resp)}" if rot_resp else "",
            "data": _fmt_date(rot_dt),
        },
    }

    # --- Nó: Avaliação Técnica (usa conclusao_tec preenchido) ---
    aval = getattr(prec, "avaliacao_tecnica_item", None)  # OneToOne no PreCalculo

    # concluído se houver qualquer valor nas choices
    if aval and getattr(aval, "conclusao_tec", None):
        aval_status  = "ok"
        # mostra o rótulo amigável da choice
        aval_detalhe = getattr(aval, "get_conclusao_tec_display", lambda: str(aval.conclusao_tec))()
    else:
        aval_status  = "pendente"
        aval_detalhe = "Pendente"

    # meta: quem e quando (prioriza assinatura)
    aval_resp = _first_attr(aval, "usuario", "responsavel", "atualizado_por", "criado_por")
    aval_dt   = _first_attr(aval, "data_assinatura", "assinado_em", "atualizado_em", "criado_em")

    no_avaliacao = {
        "titulo": "Avaliação Técnica",
        "icone": "bi-gear",
        "status": aval_status,
        "detalhe": aval_detalhe,
        "meta": {
            "resp": f"Resp.: {_nome(aval_resp)}" if aval_resp else "",
            "data": _fmt_date(aval_dt),
        },
    }


  # ---------- Nó: Desenvolvimento (Pré-Cálculo) ----------
    # pega o objeto correto: PreCalculo → desenvolvimento_item
    dev_obj = getattr(prec, "desenvolvimento_item", None)  # OneToOne do pré-cálculo

    # lê a flag booleana do próprio Desenvolvimento
    dev_val = None
    if dev_obj is not None:
        if hasattr(dev_obj, "completo"):
            dev_val = getattr(dev_obj, "completo")
        elif hasattr(dev_obj, "todas_informacoes_preenchidas"):
            # fallback se o nome for diferente no seu banco
            dev_val = getattr(dev_obj, "todas_informacoes_preenchidas")

    # define status e detalhe
    if dev_val is True:
        dev_status  = "ok"
        dev_detalhe = "✔️ Sim"
    elif dev_val is False:
        dev_status  = "pendente"
        dev_detalhe = "❌ Não"
    else:
        dev_status  = "pendente"
        dev_detalhe = "—"

    # meta (quem e quando) – o seu modelo usa campos padrão de auditoria
    dev_resp = _first_attr(dev_obj, "usuario", "responsavel", "responsavel_tecnico", "criado_por")
    dev_dt   = _first_attr(dev_obj, "data_assinatura", "atualizado_em", "criado_em", "data_abertura")

    no_desenvolvimento = {
        "titulo": "Desenvolvimento",
        "icone": "bi-rocket-takeoff",
        "status": dev_status,
        "detalhe": dev_detalhe,
        "meta": {
            "resp": f"Resp.: {_nome(dev_resp)}" if dev_resp else "",
            "data": _fmt_date(dev_dt),
        },
    }




    # ---------- Nó: Preço Final ----------
    from decimal import Decimal

    from decimal import Decimal

    def _fmt_brl(v):
        try:
            q = Decimal(str(v or 0))
        except Exception:
            return ""
        s = f"{q:,.4f}"
        return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")

    preco_manual      = getattr(prec, "preco_manual", None)
    preco_selecionado = getattr(prec, "preco_selecionado", None)

    preco_ok  = ((preco_manual or 0) > 0) or bool(preco_selecionado)
    origem    = "manual" if (preco_manual or 0) > 0 else ("selecionado" if preco_selecionado else None)

    valor_escolhido_str = ""

    if origem == "manual":
        valor_escolhido_str = _fmt_brl(preco_manual)

    elif origem == "selecionado":
        alvo = preco_selecionado
        # 1) tenta atributos/métodos comuns
        candidatos = [
            "preco_final", "valor_final", "preco", "valor",
            "preco_unitario", "valor_unitario", "unitario",
            "get_preco_final_display", "get_valor_display"
        ]
        valor_num = None
        for nome in candidatos:
            if hasattr(alvo, nome):
                val = getattr(alvo, nome)
                if callable(val):
                    try:
                        val = val()
                    except Exception:
                        val = None
                # guarda se for numérico
                if isinstance(val, (int, float, Decimal)):
                    valor_num = val
                    break
                # pode ser string já formatada -> usar direto
                if isinstance(val, str) and val.strip():
                    valor_escolhido_str = val.strip()
                    break

        # 2) se achou número, formata BRL
        if not valor_escolhido_str and valor_num is not None:
            valor_escolhido_str = _fmt_brl(valor_num)

        # 3) fallback final: usa representação textual do objeto
        if not valor_escolhido_str:
            try:
                valor_escolhido_str = str(alvo).strip()
            except Exception:
                valor_escolhido_str = ""

    # Detalhe
    if preco_ok:
        sufixo = f" — {valor_escolhido_str}" if valor_escolhido_str else ""
        preco_detalhe = f"Definido ({origem}){sufixo}"
    else:
        preco_detalhe = "Indefinido"

    # Meta: apenas quando houver preço
    meta_resp = meta_data = ""
    if preco_ok:
        resp_obj = _first_attr(prec, "usuario_preco", "responsavel_preco", "atualizado_por")
        dt_val   = _first_attr(prec, "data_preco", "data_definicao_preco", "atualizado_em")
        if resp_obj: meta_resp = f"Resp.: {_nome(resp_obj)}"
        if dt_val:   meta_data = _fmt_date(dt_val)

    no_preco = {
        "titulo": "Preço Final",
        "icone": "bi-currency-dollar",
        "status": "ok" if preco_ok else "pendente",
        "detalhe": preco_detalhe,  # ex.: "Definido (selecionado) — 0.40 (25%) 🧮"  ou  "Definido (manual) — R$ 12.345,6789"
        "meta": {"resp": meta_resp, "data": meta_data}
    }




    # ---------- Nó: Proposta (data + hora) ----------
    data_envio = getattr(cot, "data_envio_proposta", None) if cot else None
    prop_resp  = _first_attr(cot, "responsavel_envio", "responsavel", "usuario_responsavel")

    # formata dd/mm/aaaa HH:MM (com timezone local quando houver)
    data_hora_envio = ""
    if data_envio:
        try:
            from django.utils import timezone
            dt_show = timezone.localtime(data_envio) if getattr(data_envio, "tzinfo", None) else data_envio
        except Exception:
            dt_show = data_envio
        data_hora_envio = dt_show.strftime("%d/%m/%Y %H:%M")

    no_proposta = {
        "titulo": "Proposta",
        "icone": "bi-envelope-paper",
        "status": "ok" if data_envio else "pendente",
        "detalhe": (data_hora_envio if data_envio else "Sem envio"),
        "meta": {
            "resp": f"Resp.: {_nome(prop_resp)}" if prop_resp else "",
            "data": data_hora_envio
        }
    }

    fluxo = [
        no_cotacao,
        no_analise,
        no_avaliacao,
        no_materiais,
        no_servicos,
        no_roteiro,
        no_desenvolvimento,
        no_preco,
        no_proposta,
    ]

    return JsonResponse({"ok": True, "fluxo": fluxo})

