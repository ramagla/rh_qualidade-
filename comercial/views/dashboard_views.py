from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Case, When
from django.db.models.functions import Coalesce
from django.db.models import FloatField, ExpressionWrapper

from comercial.models import Cliente, Cotacao, OrdemDesenvolvimento
from comercial.models.precalculo import PreCalculo, AnaliseComercial
from decimal import Decimal
from comercial.models.viabilidade import ViabilidadeAnaliseRisco

from django.db.models import F, Case, When, DecimalField, Sum, Min
from django.db.models.functions import TruncMonth
from django.db.models import Count
from django.db.models import F, Case, When, DecimalField, ExpressionWrapper
from collections import defaultdict
from django.db.models import Q
from datetime import datetime
from django.utils.timezone import now
from comercial.models.ordem_desenvolvimento import OrdemDesenvolvimento

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
    from comercial.models import Item
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