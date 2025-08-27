from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from alerts import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from comercial.models.faturamento import FaturamentoRegistro, FaturamentoDuplicata
from comercial.forms.faturamento_forms import FaturamentoRegistroForm


from django.core.paginator import Paginator
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import datetime

from datetime import datetime
from decimal import Decimal
from django.db.models import F, Sum, Q
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from comercial.models.faturamento import FaturamentoRegistro
from datetime import datetime
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from comercial.models.faturamento import FaturamentoRegistro
from django.db.models import F, Sum, Value

from django.urls import reverse
from comercial.services.faturamento_sync import (
    sincronizar_faturamento,           # VENDAS
    sincronizar_faturamento_notas,     # NOTAS  ✅
)

# + imports para agregações
from decimal import Decimal
from django.db.models import Sum, Max, Value, DecimalField
from django.db.models.functions import Coalesce




def _parse_iso_date_or_none(s: str):
    if not s:
        return None
    try:
        # input type="date" envia YYYY-MM-DD
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None

@login_required
@permission_required("comercial.view_faturamentoregistro", raise_exception=True)
def lista_faturamento(request):
    # -------- Filtros (GET) --------
    de  = request.GET.get("de") or ""
    ate = request.GET.get("ate") or ""
    cliente = request.GET.get("cliente") or ""   # Cliente (texto)
    tipo = request.GET.get("tipo") or ""         # Novo: Tipo (Venda ou Devolução)
    nfe = request.GET.get("nfe") or ""
    item = request.GET.get("item") or ""
    apenas_congelados = request.GET.get("apenas_congelados") == "1"

    dt_de  = _parse_iso_date_or_none(de)
    dt_ate = _parse_iso_date_or_none(ate)

    qs_base = FaturamentoRegistro.objects.select_related("cliente_vinculado").all()
    qs = qs_base


    # Cliente (texto), NF-e, Cód. Item, Congelado
    if cliente:
        qs = qs.filter(cliente__icontains=cliente)
    if nfe:
        qs = qs.filter(nfe__icontains=nfe)
    if item:
        qs = qs.filter(item_codigo__icontains=item)
    if apenas_congelados:
        qs = qs.filter(congelado=True)

    if tipo:
        qs = qs.filter(tipo=tipo)

    # -------- Filtro por OCORRÊNCIA (DateField) --------
    if dt_de:
        qs = qs.filter(ocorrencia__gte=dt_de)
    if dt_ate:
        qs = qs.filter(ocorrencia__lte=dt_ate)


    qs = qs.order_by("-id")

    # -------- Indicadores (RESPEITANDO TODOS OS FILTROS APLICADOS EM qs) --------
    qs_indicadores = (
        qs
        .exclude(valor_total__isnull=True)
        .exclude(valor_total_com_ipi__isnull=True)
        .select_related("cliente_vinculado")
    )

    total_sem_ipi = Decimal("0.00")
    total_ipi = Decimal("0.00")
    total_icms = Decimal("0.00")

    for r in qs_indicadores.only(
        "valor_total",
        "valor_total_com_ipi",
        "perc_icms",
        "cliente_vinculado__icms"
    ):
        base = r.valor_total or Decimal("0.00")
        com_ipi = r.valor_total_com_ipi or base
        ipi = (com_ipi - base).quantize(Decimal("0.01"))

        # ICMS: prioridade do registro; senão, do cliente; fallback 0
        try:
            if r.perc_icms is not None:
                perc_icms = Decimal(str(r.perc_icms))
            elif r.cliente_vinculado and r.cliente_vinculado.icms is not None:
                perc_icms = Decimal(str(r.cliente_vinculado.icms))
            else:
                perc_icms = Decimal("0.00")
        except Exception:
            perc_icms = Decimal("0.00")

        icms = (base * perc_icms / Decimal("100")).quantize(Decimal("0.01"))

        total_sem_ipi += base
        total_ipi += ipi
        total_icms += icms

    indicadores = {
        "total_sem_ipi": total_sem_ipi,
        "total_ipi": total_ipi,
        "total_icms": total_icms,
        # agora contam conforme os MESMOS filtros da tabela
        "total_registros": qs.count(),
        "total_clientes": qs.values("cliente").distinct().count(),
    }


    # -------- Paginação --------
    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

   # -------- Clientes do select (sem filtro por congelado) --------
    clientes_texto_options = (
        qs_base.exclude(cliente__isnull=True)
            .exclude(cliente__exact="")
            .values_list("cliente", flat=True)
            .distinct()
            .order_by("cliente")
    )


    context = {
        "registros": page_obj,
        "page_obj": page_obj,
        "paginator": paginator,
        "indicadores": indicadores,
        "filtros": {
            "de": de,
            "ate": ate,
            "cliente": cliente,
            "tipo": tipo,
            "nfe": nfe,
            "item": item,
            "apenas_congelados": "1" if apenas_congelados else "0",
        },

        "clientes_texto_options": clientes_texto_options,
        "tipo_choices": FaturamentoRegistro.TIPO_CHOICES,
    }
    return render(request, "faturamento/lista.html", context)



@login_required
@permission_required("comercial.view_faturamentoregistro", raise_exception=True)
def sync_faturamento(request):
    if request.method != "POST":
        messages.error(request, "Método inválido.")
        return redirect("lista_faturamento")

    data_inicio = request.POST.get("data_inicio")
    data_fim = request.POST.get("data_fim")
    sobrescrever = request.POST.get("sobrescrever") == "1"

    if not data_inicio or not data_fim:
        messages.error(request, "Informe o período (Data Início e Data Fim).")
        return redirect("lista_faturamento")

    try:
        ins, upd, skip = sincronizar_faturamento(data_inicio, data_fim, sobrescrever=sobrescrever)
        if sobrescrever:
            messages.success(request, f"Vendas sincronizadas. Inseridos: {ins} | Atualizados: {upd} | Pulados: {skip}.")
        else:
            messages.success(request, f"Vendas sincronizadas (somente inserir). Inseridos: {ins} | Já existentes (pulados): {skip}.")
    except Exception as e:
        messages.error(request, f"Falha na sincronização de vendas: {e}")

    return redirect("lista_faturamento")

from django.urls import reverse
from comercial.services.faturamento_sync import (
    sincronizar_faturamento,
    sincronizar_faturamento_notas,  # ✅ importar a função de notas
)


@login_required
@permission_required("comercial.view_faturamentoregistro", raise_exception=True)
def sync_faturamento_notas(request):
    if request.method != "POST":
        messages.error(request, "Método inválido.")
        return redirect("relatorio_duplicatas")

    # DEBUG: payload recebido
    print("[SYNC-NOTAS:VIEW] POST recebido =", request.POST.dict())

    data_inicio = (request.POST.get("data_inicio") or "").strip()
    data_fim    = (request.POST.get("data_fim") or "").strip()

    if not data_inicio or not data_fim:
        print("[SYNC-NOTAS:VIEW] período ausente -> bloqueando")  # DEBUG
        messages.error(request, "Informe o período (Data Início e Data Fim).")
        return redirect("relatorio_duplicatas")

    try:
        print(f"[SYNC-NOTAS:VIEW] executando wrapper período {data_inicio}..{data_fim}")  # DEBUG
        dup_ins, icms_upd, dup_skip = sincronizar_faturamento_notas(
            data_inicio, data_fim, registros="500"
        )
        messages.success(
            request,
            f"Notas sincronizadas. Duplicatas inseridas: {dup_ins} | ICMS atualizados: {icms_upd} | Duplicatas puladas: {dup_skip}."
        )
    except Exception as e:
        print("[SYNC-NOTAS:VIEW] EXCEPTION:", repr(e))  # DEBUG
        messages.error(request, f"Falha na sincronização de notas: {e}")

    url = reverse("relatorio_duplicatas")
    return redirect(f"{url}?data_inicio={data_inicio}&data_fim={data_fim}")


@login_required
@permission_required("comercial.add_faturamentoregistro", raise_exception=True)
def criar_faturamento(request):
    if request.method == "POST":
        form = FaturamentoRegistroForm(request.POST)
        if form.is_valid():
            obj = form.save()  # chave_unica é recalculada no model.save()
            messages.success(request, "Registro criado com sucesso.")
            return redirect("lista_faturamento")
    else:
        form = FaturamentoRegistroForm()
    return render(request, "faturamento/form.html", {"form": form, "modo": "criar"})

@login_required
@permission_required("comercial.change_faturamentoregistro", raise_exception=True)
def editar_faturamento(request, pk: int):
    obj = get_object_or_404(FaturamentoRegistro, pk=pk)
    if request.method == "POST":
        form = FaturamentoRegistroForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()  # recalcula chave_unica automaticamente
            messages.success(request, "Registro atualizado com sucesso.")
            return redirect("lista_faturamento")
    else:
        form = FaturamentoRegistroForm(instance=obj)
    if form.errors:
        messages.error(request, "Erros encontrados. Verifique os campos destacados.")
    return render(request, "faturamento/form.html", {"form": form, "modo": "editar", "obj": obj})




from django.views.decorators.http import require_POST
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required

@login_required
@permission_required("comercial.delete_faturamentoregistro", raise_exception=True)
@require_POST
def excluir_faturamento(request, pk: int):
    obj = get_object_or_404(FaturamentoRegistro, pk=pk)

    # respeita proteção opcional (congelado)
    if getattr(obj, "congelado", False):
        messages.warning(request, "Registro congelado: exclusão bloqueada.")
        return redirect(request.POST.get("next") or "lista_faturamento")

    try:
        with transaction.atomic():
            obj.delete()
        messages.success(request, "Registro excluído com sucesso.")
    except IntegrityError as e:
        messages.error(request, f"Não foi possível excluir este registro: {e}")

    # volta para a lista preservando filtros/paginação, se enviados
    return redirect(request.POST.get("next") or "lista_faturamento")


import csv
from django.http import HttpResponse

# comercial/views/faturamento_views.py

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from django.db.models import F, Value
from django.db.models.functions import Coalesce
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from comercial.models.faturamento import FaturamentoRegistro

# comercial/views/faturamento_views.py

from datetime import datetime
from decimal import Decimal
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from comercial.models.faturamento import FaturamentoRegistro

def _parse_any_date(s: str):
    """
    Aceita 'yyyy-mm-dd' (input type=date) e 'dd/mm/yyyy' (dados da ocorrência).
    """
    s = (s or "").strip()
    if not s:
        raise ValueError("empty")
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"invalid date: {s}")

from decimal import Decimal
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required

# Se o _parse_any_date já existir em outro módulo seu, remova este import e use o existente.
# A view abaixo assume que _parse_any_date(data_str) aceita "dd/mm/yyyy" e "yyyy-mm-dd" e retorna date.


@login_required
@permission_required("comercial.view_faturamentoregistro", raise_exception=True)
def relatorio_faturamento(request):
    data_inicio = (request.GET.get("data_inicio") or "").strip()
    data_fim    = (request.GET.get("data_fim") or "").strip()

    # --- Defaults seguros (evitam UnboundLocalError quando não há período) ---
    tabela_vendas_por_dia = []
    totais_vendas = {
        "valor_c_ipi": Decimal("0.00"),
        "valor_icms":  Decimal("0.00"),
        "valor_ipi":   Decimal("0.00"),
    }
    tabela_vales      = []
    total_vales       = Decimal("0.00")
    tabela_devolucoes = []
    total_devolucoes  = Decimal("0.00")

    # Sem período: renderiza com mensagem e totalizador 0.00
    if not data_inicio or not data_fim:
        messages.info(request, "Selecione Data Início e Data Fim para visualizar.")
        return render(request, "faturamento/relatorio.html", {
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "tabela_vendas_por_dia": tabela_vendas_por_dia,
            "totais_vendas": totais_vendas,
            "tabela_vales": tabela_vales,
            "total_vales": total_vales,
            "tabela_devolucoes": tabela_devolucoes,
            "total_devolucoes": total_devolucoes,
            "totalizador": Decimal("0.00"),
        })

    # --- Validação/parse de datas do filtro ---
    try:
        dt_ini = _parse_any_date(data_inicio)  # yyyy-mm-dd ou dd/mm/yyyy
        dt_fim = _parse_any_date(data_fim)
    except Exception:
        messages.error(request, "Datas inválidas. Use o seletor de data.")
        return redirect(request.path)

    # --- Base: filtra registros com ocorrência preenchida no período ---
    qs = (FaturamentoRegistro.objects
      .select_related("cliente_vinculado")
      .filter(ocorrencia__isnull=False)
      .filter(ocorrencia__gte=dt_ini, ocorrencia__lte=dt_fim)
      .only("ocorrencia", "nfe", "tipo", "valor_total", "valor_total_com_ipi",
            "item_ipi", "cliente", "cliente_vinculado_id", "perc_icms")
      .order_by("ocorrencia", "id"))

    registros_periodo = []
    for r in qs:
        r._data_obj = r.ocorrencia  # já é date
        registros_periodo.append(r)


    # -----------------------------------------------------------
    # TABELA 1: Vendas com NF-e válida (≠ 'Vale' e não vazia)
    # -----------------------------------------------------------
    vendas_validas = [
        r for r in registros_periodo
        if (r.tipo or "Venda") == "Venda" and (r.nfe or "").strip().lower() not in ("", "vale")
    ]

    agrupado = defaultdict(lambda: {
        "valor_c_ipi": Decimal("0.00"),
        "valor_icms":  Decimal("0.00"),
        "valor_ipi":   Decimal("0.00"),
    })

    total_c_ipi = Decimal("0.00")
    total_icms  = Decimal("0.00")
    total_ipi   = Decimal("0.00")

    for r in vendas_validas:
        base_sem_ipi = (r.valor_total or Decimal("0.00"))
        valor_c_ipi  = (r.valor_total_com_ipi or base_sem_ipi)
        valor_ipi    = (valor_c_ipi - base_sem_ipi).quantize(Decimal("0.01"))

        # ICMS: prioriza perc_icms do registro; senão, ICMS do cliente; fallback 0
        try:
            if getattr(r, "perc_icms", None) is not None:
                perc_icms = Decimal(str(r.perc_icms))
            elif getattr(r, "cliente_vinculado", None) and getattr(r.cliente_vinculado, "icms", None) is not None:
                perc_icms = Decimal(str(r.cliente_vinculado.icms or 0))
            else:
                perc_icms = Decimal("0.00")
        except Exception:
            perc_icms = Decimal("0.00")

        valor_icms = (base_sem_ipi * (perc_icms / Decimal("100"))).quantize(Decimal("0.01"))

        dia = r._data_obj.strftime("%d/%m/%Y")
        agrupado[dia]["valor_c_ipi"] += valor_c_ipi
        agrupado[dia]["valor_icms"]  += valor_icms
        agrupado[dia]["valor_ipi"]   += valor_ipi

        total_c_ipi += valor_c_ipi
        total_icms  += valor_icms
        total_ipi   += valor_ipi

    tabela_vendas_por_dia = [
        {"dia": dia, **valores}
        for dia, valores in sorted(agrupado.items(), key=lambda x: _parse_any_date(x[0]))
    ]
    totais_vendas = {
        "valor_c_ipi": total_c_ipi,
        "valor_icms":  total_icms,
        "valor_ipi":   total_ipi,
    }

    # -----------------------------------------------------------
    # TABELA 2: Vendas – NF-e “Vale/Null”
    # (nfe vazio ou "vale", mantendo tipo "Venda")
    # -----------------------------------------------------------
    vendas_vale = [
        r for r in registros_periodo
        if (r.tipo or "Venda") == "Venda" and (r.nfe is None or (r.nfe or "").strip().lower() in ("", "vale"))
    ]

    tabela_vales = []
    for r in vendas_vale:
        cliente_nome = getattr(r.cliente_vinculado, "razao_social", None) or (r.cliente or "—")
        valor = (r.valor_total_com_ipi or r.valor_total or Decimal("0.00")).quantize(Decimal("0.01"))
        data = r.ocorrencia.strftime("%d/%m/%Y") if r.ocorrencia else "—"
        tabela_vales.append({
            "cliente": cliente_nome,
            "data": data,
            "valor": valor,
        })

    total_vales = sum(r["valor"] for r in tabela_vales)


    # -----------------------------------------------------------
    # TABELA 3: Devoluções
    # -----------------------------------------------------------
    devolucoes = [r for r in registros_periodo if (r.tipo or "") == "Devolução"]

    tabela_devolucoes = []
    total_devolucoes = Decimal("0.00")
    for r in devolucoes:
        valor = (r.valor_total_com_ipi or r.valor_total or Decimal("0.00")).quantize(Decimal("0.01"))
        tabela_devolucoes.append({
            "cliente": getattr(r.cliente_vinculado, "razao_social", None) or (r.cliente or "—"),
            "nfe": (r.nfe or "—"),
            "valor": valor,
        })
        total_devolucoes += valor

    # -----------------------------------------------------------
    # TOTALIZADOR FINAL (Vendas NF + Vales − Devoluções)
    # -----------------------------------------------------------
    totalizador = (totais_vendas["valor_c_ipi"] or Decimal("0.00")) \
                  + (total_vales or Decimal("0.00")) \
                  - (total_devolucoes or Decimal("0.00"))

    # Render
    return render(request, "faturamento/relatorio.html", {
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "tabela_vendas_por_dia": tabela_vendas_por_dia,
        "totais_vendas": totais_vendas,
        "tabela_vales": tabela_vales,
        "total_vales": total_vales,
        "tabela_devolucoes": tabela_devolucoes,
        "total_devolucoes": total_devolucoes,
        "totalizador": totalizador,
    })




CFOPS_TOTALIZADORES = {"5101", "6101", "5124", "6124","5125","6109"}


@login_required
@permission_required("comercial.view_faturamentoregistro", raise_exception=True)
def relatorio_duplicatas(request):
    """
    ...
    - Todos os cards de “Totalizadores do Período” (Quantidade, Total no Período, Total ICMS, Total IPI, Total Geral)
      passam a considerar somente NFs com CFOP em CFOPS_TOTALIZADORES.
    - A listagem continua exibindo todas as NFs.
    - O gráfico Top 10 continua filtrado pelos CFOPs permitidos.
    """
    from decimal import Decimal
    from collections import defaultdict
    from datetime import timedelta
    from django.db.models import Q, Max

    data_inicio = (request.GET.get("data_inicio") or "").strip()
    data_fim    = (request.GET.get("data_fim") or "").strip()

    if not data_inicio or not data_fim:
        messages.info(request, "Selecione Data Início e Data Fim para visualizar.")
        return render(request, "faturamento/relatorio_duplicatas.html", {
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "linhas": [],
            "total_periodo": Decimal("0.00"),
            "total_mes": Decimal("0.00"),
            "total_avista": Decimal("0.00"),
            "total_tributos": Decimal("0.00"),
            "qtde_duplicatas": 0,
            "chart_data": [],
            "total_valor": Decimal("0.00"),
            "total_icms": Decimal("0.00"),
            "total_ipi": Decimal("0.00"),
            "total_geral": Decimal("0.00"),
            "cfops_totalizadores": ", ".join(sorted(CFOPS_TOTALIZADORES)),
        })

    try:
        dt_ini = _parse_any_date(data_inicio)
        dt_fim = _parse_any_date(data_fim)
    except Exception:
        messages.error(request, "Datas inválidas. Use o seletor de data.")
        return redirect(request.path)

    nfs_por_emissao = list(
        FaturamentoRegistro.objects
        .filter(ocorrencia__isnull=False, ocorrencia__gte=dt_ini, ocorrencia__lte=dt_fim)
        .values_list("nfe", flat=True)
        .distinct()
    )

    qs = (
        FaturamentoDuplicata.objects
        .select_related("cliente_vinculado")
        .filter(
            Q(nfe__in=nfs_por_emissao) |
            Q(ocorrencia__isnull=False, ocorrencia__gte=dt_ini, ocorrencia__lte=dt_fim)
        )
        .filter(data_vencimento__isnull=False)
        .only("nfe","numero_parcela","data_vencimento","valor_duplicata",
              "cliente","cliente_codigo","cliente_vinculado_id","ocorrencia",
              "natureza","cfop","valor_pis","valor_cofins","valor_ipi")
        .order_by("ocorrencia","nfe","id")
    )

    nfs = list(qs.values_list("nfe", flat=True).distinct())
    icms_por_nf = defaultdict(lambda: Decimal("0.00"))
    ipi_por_nf  = defaultdict(lambda: Decimal("0.00"))
    data_por_nf = {}

    if nfs:
        regs = (
            FaturamentoRegistro.objects
            .filter(nfe__in=nfs)
            .only("nfe","ocorrencia","item_quantidade","item_valor_unitario","perc_icms")
        )
        for r in regs:
            qtd   = r.item_quantidade or 0
            vunit = Decimal(str(r.item_valor_unitario or "0"))
            base  = (vunit * Decimal(qtd)) if (qtd and vunit is not None) else Decimal("0.00")
            if r.perc_icms is not None:
                icms_por_nf[r.nfe] += (base * (Decimal(str(r.perc_icms)) / Decimal("100")))
            if r.ocorrencia and (r.nfe not in data_por_nf or r.ocorrencia < data_por_nf[r.nfe]):
                data_por_nf[r.nfe] = r.ocorrencia

        ipi_rows = (
            FaturamentoDuplicata.objects
            .filter(nfe__in=nfs)
            .values("nfe")
            .annotate(v_ipi=Max("valor_ipi"))
        )
        for row in ipi_rows:
            ipi_por_nf[row["nfe"]] = (row["v_ipi"] or Decimal("0.00")).quantize(Decimal("0.01"))

    linhas = []
    nfs_cfop_permitido = set()

    for d in qs:
        nfe = d.nfe or ""
        emissao = d.ocorrencia or data_por_nf.get(nfe)
        cliente_nome = getattr(d.cliente_vinculado, "razao_social", None) or (d.cliente or "—")

        valor_dup  = Decimal(str(d.valor_duplicata or "0")).quantize(Decimal("0.01"))
        valor_icms = icms_por_nf[nfe].quantize(Decimal("0.01"))
        valor_ipi  = ipi_por_nf[nfe].quantize(Decimal("0.01"))

        cfop_str = str(getattr(d, "cfop", "") or "").strip()
        if cfop_str in CFOPS_TOTALIZADORES and nfe:
            nfs_cfop_permitido.add(nfe)



        # Dicionário para abreviar os nomes longos
        NATUREZA_MAP = {
            "VENDA DE PRODUCAO DO ESTABELECIMENTO": "Venda",
            "REMESSA P/INDUSTRIALIZACAO POR ENCOMENDA": "Beneficiamento",
            "INDUSTRIALIZ. EFETUADA P/OUTRA EMPRESA": "Remessa Industrialização",
            "DEVOLUCAO DE COMPRA PARA INDUSTRIALIZACAO": "Devolução Ind.",
            "COMPRA PARA INDUSTRIALIZACAO": "Compra Ind.",
            "TRANSFERENCIA DE PRODUCAO": "Transferência",
            "BONIFICACAO": "Bonificação",
            "EXPORTACAO DE PRODUCAO": "Exportação",
            "IMPORTACAO DE MERCADORIAS": "Importação",
            "OUTRAS SAIDAS": "Outras Saídas",
            "OUTRAS ENTRADAS": "Outras Entradas",
            "REMESSA DE AMOSTRA GRATIS": "Amostra Grátis",
            "REMESSA DE VASILHAME OU SACARIA": "Vasilhame/Sacaria",
            "DEVOLUCAO DE VASILHAME OU SACARIA": "Dev. Vasilhame/Sacaria",
            "REMESSA P/ CONSERTO": "Remessa p/ Conserto",
            "VENDA PROD.ESTAB. P/ ZONA FRANCA MANAUS": "Venda p/ ZFM",
        }
        natureza_original = getattr(d, "natureza", None)
        natureza_formatada = NATUREZA_MAP.get(
            str(natureza_original).strip().upper(),
            natureza_original or ""
        )

        linhas.append({
            "nfe": nfe,
            "data": emissao,
            "cliente": cliente_nome,
            "vencimento": d.data_vencimento,
            "valor": valor_dup,
            "valor_icms": valor_icms,
            "valor_ipi": valor_ipi,
            "natureza": natureza_formatada,  # <- já formatada!
            "cfop": getattr(d, "cfop", None),
            "valor_pis": Decimal(str(getattr(d, "valor_pis", "0") or "0")).quantize(Decimal("0.01")),
            "valor_cofins": Decimal(str(getattr(d, "valor_cofins", "0") or "0")).quantize(Decimal("0.01")),
            "valor_total": valor_dup,
            "emissao": emissao,
        })
    # === GRÁFICO (FILTRADO) ===
    from collections import defaultdict as _dd
    agg_por_cliente_cfop = _dd(lambda: Decimal("0.00"))
    for l in linhas:
        if l["nfe"] in nfs_cfop_permitido:
            agg_por_cliente_cfop[l["cliente"]] += l["valor"]
    top10 = sorted(agg_por_cliente_cfop.items(), key=lambda kv: kv[1], reverse=True)[:10]
    chart_data = [{"cliente": k, "valor": v} for k, v in top10]

    # === CARDS filtrados por CFOP ===
    linhas_filtradas = [l for l in linhas if l["nfe"] in nfs_cfop_permitido]
    total_periodo = sum(l["valor"] for l in linhas_filtradas)
    total_icms    = sum(icms_por_nf.get(nf, Decimal("0.00")) for nf in nfs_cfop_permitido)
    total_ipi     = sum(ipi_por_nf.get(nf, Decimal("0.00")) for nf in nfs_cfop_permitido)
    total_geral   = total_periodo                       # duplicata já inclui IPI
    qtde_dups     = len(linhas_filtradas)

    # === Auxiliares não filtrados (mantidos) ===
    total_mes = sum(
        l["valor"] for l in linhas
        if l["vencimento"] and l["vencimento"].year == dt_ini.year and l["vencimento"].month == dt_ini.month
    )
    total_avista = sum(
        l["valor"] for l in linhas
        if l.get("emissao") and (l["vencimento"] == l["emissao"] or l["vencimento"] == l["emissao"] + timedelta(days=1))
    )
    nfs_distintas = {l["nfe"] for l in linhas if l["nfe"]}
    total_tributos = sum(
        (icms_por_nf.get(nf, Decimal("0")) + ipi_por_nf.get(nf, Decimal("0")))
        for nf in nfs_distintas
    )
    total_valor = sum(l["valor"] for l in linhas)

    q2 = lambda x: Decimal(x).quantize(Decimal("0.01"))
    context = {
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "linhas": linhas,

        # KPIs do topo (somente 'total_periodo' filtrado por CFOP)
        "total_periodo": q2(total_periodo),
        "total_mes": q2(total_mes),
        "total_avista": q2(total_avista),
        "total_tributos": q2(total_tributos),

        # CARDS “Totalizadores do Período” (todos filtrados)
        "qtde_duplicatas": qtde_dups,
        "total_icms": q2(total_icms),
        "total_ipi": q2(total_ipi),
        "total_geral": q2(total_geral),

        # Gráfico
        "chart_data": chart_data,

        # Não filtrados, caso use em outro lugar:
        "total_valor": q2(total_valor),

        "cfops_totalizadores": ", ".join(sorted(CFOPS_TOTALIZADORES)),
    }
    return render(request, "faturamento/relatorio_duplicatas.html", context)


