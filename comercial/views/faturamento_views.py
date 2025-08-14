from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from alerts import models
from comercial.models.faturamento import FaturamentoRegistro
from comercial.services.faturamento_sync import sincronizar_faturamento
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from comercial.models.faturamento import FaturamentoRegistro
from comercial.services.faturamento_sync import sincronizar_faturamento
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
from django.db.models import F, Sum, Value, DateField, Func, Case, When
from django.db.models.functions import Trim, Substr  
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from comercial.models.faturamento import FaturamentoRegistro
from django.db.models import F, Sum, Value, DateField, Func, Case, When

class ToDate(Func):
    function = "to_date"
    arity = 2
    output_field = DateField()


def _parse_iso_date_or_none(s: str):
    if not s:
        return None
    try:
        # input type="date" envia YYYY-MM-DD
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None

@login_required
@permission_required("comercial.view_faturamento", raise_exception=True)
def lista_faturamento(request):
    # -------- Filtros (GET) --------
    de  = request.GET.get("de") or ""
    ate = request.GET.get("ate") or ""
    cliente = request.GET.get("cliente") or ""   # Cliente (texto)
    nfe = request.GET.get("nfe") or ""
    item = request.GET.get("item") or ""
    apenas_congelados = request.GET.get("apenas_congelados") == "1"

    dt_de  = _parse_iso_date_or_none(de)
    dt_ate = _parse_iso_date_or_none(ate)

    qs = (FaturamentoRegistro.objects
          .select_related("cliente_vinculado")
          .all())

    # Cliente (texto), NF-e, Cód. Item, Congelado
    if cliente:
        qs = qs.filter(cliente__icontains=cliente)
    if nfe:
        qs = qs.filter(nfe__icontains=nfe)
    if item:
        qs = qs.filter(item_codigo__icontains=item)
    if apenas_congelados:
        qs = qs.filter(congelado=True)

    # -------- Filtro por OCORRÊNCIA (string dd/mm/yyyy) no banco --------
    # Converte 'ocorrencia' (texto) em date usando PostgreSQL to_date('DD/MM/YYYY')
    if dt_de or dt_ate:
        PADRAO_BR = Value("DD/MM/YYYY")
        PADRAO_ISO = Value("YYYY-MM-DD")

        # Normaliza a string (trim) e limita a 10 chars antes do to_date,
        # aceitando 'YYYY-MM-DD' e 'DD/MM/YYYY' mesmo que venha com hora.
        qs = qs.annotate(
            oc_txt=Trim(F("ocorrencia")),
        ).annotate(
            oc_dt=Case(
                # BR: 01/07/2025... ou "01/07/2025 00:00:00"
                When(
                    oc_txt__regex=r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/\d{4}",
                    then=ToDate(Substr(F("oc_txt"), 1, 10), PADRAO_BR),
                ),
                # ISO: 2025-07-01... ou "2025-07-01 00:00:00"
                When(
                    oc_txt__regex=r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])",
                    then=ToDate(Substr(F("oc_txt"), 1, 10), PADRAO_ISO),
                ),
                default=None,
                output_field=DateField(),
            )
        ).filter(oc_dt__isnull=False)

        if dt_de:
            qs = qs.filter(oc_dt__gte=dt_de)
        if dt_ate:
            qs = qs.filter(oc_dt__lte=dt_ate)

    qs = qs.order_by("-id")

    # -------- Indicadores (sobre o conjunto filtrado) --------
    total_registros = qs.count()
    total_valor = qs.aggregate(total=Sum(F("item_quantidade") * F("item_valor_unitario")))["total"] or 0
    total_frete = qs.aggregate(total=Sum("valor_frete"))["total"] or 0
    total_clientes = qs.values("cliente").distinct().count()  # por nome textual

    indicadores = {
        "total_registros": total_registros,
        "total_valor": total_valor,
        "total_frete": total_frete,
        "total_clientes": total_clientes,
    }

    # -------- Paginação --------
    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # -------- Opções para Select2 (Cliente texto) --------
    clientes_texto_options = (
        qs.exclude(cliente__isnull=True)
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
            "nfe": nfe,
            "item": item,
            "apenas_congelados": "1" if apenas_congelados else "0",
        },
        "clientes_texto_options": clientes_texto_options,
    }
    return render(request, "faturamento/lista.html", context)

@login_required
@permission_required("comercial.view_faturamento", raise_exception=True)
def sync_faturamento(request):
    if request.method != "POST":
        messages.error(request, "Método inválido.")
        return redirect("lista_faturamento")

    data_inicio = request.POST.get("data_inicio")
    data_fim = request.POST.get("data_fim")
    sobrescrever = request.POST.get("sobrescrever") == "1"  # checkbox

    if not data_inicio or not data_fim:
        messages.error(request, "Informe o período (Data Início e Data Fim).")
        return redirect("lista_faturamento")

    try:
        ins, upd, skip = sincronizar_faturamento(data_inicio, data_fim, sobrescrever=sobrescrever)
        if sobrescrever:
            messages.success(request, f"Sincronização concluída. Inseridos: {ins} | Atualizados: {upd} | Pulados: {skip}.")
        else:
            messages.success(request, f"Sincronização (somente inserir) concluída. Inseridos: {ins} | Já existentes (pulados): {skip}.")
    except Exception as e:
        messages.error(request, f"Falha na sincronização: {e}")

    return redirect("lista_faturamento")


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

@login_required
@permission_required("comercial.view_faturamentoregistro", raise_exception=True)
def relatorio_faturamento(request):
    data_inicio = (request.GET.get("data_inicio") or "").strip()
    data_fim    = (request.GET.get("data_fim") or "").strip()

    if not data_inicio or not data_fim:
        messages.info(request, "Selecione Data Início e Data Fim para visualizar.")
        return render(request, "faturamento/relatorio.html", {
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "tabela_vendas_por_dia": [],
            "totais_vendas": {"valor_c_ipi": Decimal("0.00"), "valor_icms": Decimal("0.00"), "valor_ipi": Decimal("0.00")},
            "tabela_vales": [],
            "total_vales": Decimal("0.00"),
            "tabela_devolucoes": [],
            "total_devolucoes": Decimal("0.00"),
        })

    try:
        dt_ini = _parse_any_date(data_inicio)  # yyyy-mm-dd
        dt_fim = _parse_any_date(data_fim)     # yyyy-mm-dd
    except ValueError:
        messages.error(request, "Datas inválidas. Use o seletor de data.")
        return redirect(request.path)

    qs = (FaturamentoRegistro.objects
          .select_related("cliente_vinculado")
          .exclude(ocorrencia__isnull=True)
          .exclude(ocorrencia__exact="")
          .order_by("ocorrencia", "id"))

    registros_periodo = []
    for r in qs.only("ocorrencia", "nfe", "tipo", "valor_total", "valor_total_com_ipi",
                     "item_ipi", "cliente", "cliente_vinculado_id", "perc_icms"):

        try:
            d = _parse_any_date(r.ocorrencia)  # aceita dd/mm/yyyy (origem) e yyyy-mm-dd (se mudar no futuro)
        except Exception:
            continue
        if dt_ini <= d <= dt_fim:
            r._data_obj = d
            registros_periodo.append(r)

    # --- TABELA 1: vendas com NF-e válida (≠ 'Vale' e não vazia) ---
    vendas_validas = [r for r in registros_periodo
                      if (r.tipo or "Venda") == "Venda" and (r.nfe or "").strip().lower() not in ("", "vale")]

    from collections import defaultdict
    agrupado = defaultdict(lambda: {"valor_c_ipi": Decimal("0.00"),
                                    "valor_icms": Decimal("0.00"),
                                    "valor_ipi": Decimal("0.00")})

    total_c_ipi = Decimal("0.00")
    total_icms = Decimal("0.00")
    total_ipi = Decimal("0.00")

    for r in vendas_validas:
        base_sem_ipi = (r.valor_total or Decimal("0.00"))
        valor_c_ipi = (r.valor_total_com_ipi or base_sem_ipi)
        valor_ipi = (valor_c_ipi - base_sem_ipi).quantize(Decimal("0.01"))
        # Prioriza ICMS da NF (perc_icms); fallback para ICMS do cliente
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
        agrupado[dia]["valor_icms"] += valor_icms
        agrupado[dia]["valor_ipi"] += valor_ipi

        total_c_ipi += valor_c_ipi
        total_icms += valor_icms
        total_ipi += valor_ipi

    tabela_vendas_por_dia = [
        {"dia": dia, **valores}
        for dia, valores in sorted(agrupado.items(), key=lambda x: _parse_any_date(x[0]))
    ]
    totais_vendas = {"valor_c_ipi": total_c_ipi, "valor_icms": total_icms, "valor_ipi": total_ipi}

    # --- TABELA 2: vendas Vale/Null ---
    vendas_vale = [r for r in registros_periodo
                   if (r.tipo or "Venda") == "Venda" and (r.nfe is None or (r.nfe or "").strip().lower() in ("", "vale"))]

    tabela_vales = []
    total_vales = Decimal("0.00")
    for r in vendas_vale:
        valor = (r.valor_total_com_ipi or r.valor_total or Decimal("0.00")).quantize(Decimal("0.01"))
        tabela_vales.append({
            "cliente": getattr(r.cliente_vinculado, "razao_social", None) or (r.cliente or "—"),
            "data": r._data_obj.strftime("%d/%m/%Y"),
            "valor": valor,
        })
        total_vales += valor

    # --- TABELA 3: devoluções ---
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

    return render(request, "faturamento/relatorio.html", {
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "tabela_vendas_por_dia": tabela_vendas_por_dia,
        "totais_vendas": totais_vendas,
        "tabela_vales": tabela_vales,
        "total_vales": total_vales,
        "tabela_devolucoes": tabela_devolucoes,
        "total_devolucoes": total_devolucoes,
    })
