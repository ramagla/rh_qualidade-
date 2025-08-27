# comercial/views/metas_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django import forms

from comercial.forms.indicadores import MetaFaturamentoForm
from comercial.models.indicadores import MetaFaturamento  # modelo já existente
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Sum, Avg, Count, DecimalField
from django.db.models.functions import Coalesce
from django.shortcuts import render, redirect, get_object_or_404

from decimal import Decimal
from datetime import date


# --------- Helpers ----------
def _meses_choices():
    # Tenta extrair choices do campo 'mes' do modelo. Se não houver, gera 1..12.
    try:
        field = MetaFaturamento._meta.get_field("mes")
        if getattr(field, "choices", None):
            return list(field.choices)
    except Exception:
        pass
    meses = [
        (1, "Janeiro"), (2, "Fevereiro"), (3, "Março"), (4, "Abril"),
        (5, "Maio"), (6, "Junho"), (7, "Julho"), (8, "Agosto"),
        (9, "Setembro"), (10, "Outubro"), (11, "Novembro"), (12, "Dezembro"),
    ]
    return meses


# ========================= LISTA (com filtros/cards/paginação) =========================
@login_required
@permission_required("comercial.view_metafaturamento", raise_exception=True)
def lista_metas(request):
    # ---- filtros GET ----
    ano_de   = (request.GET.get("ano_de") or "").strip()
    ano_ate  = (request.GET.get("ano_ate") or "").strip()
    mes      = (request.GET.get("mes") or "").strip()
    vmin_str = (request.GET.get("valor_min") or "").replace(".", "").replace(",", ".").strip()
    vmax_str = (request.GET.get("valor_max") or "").replace(".", "").replace(",", ".").strip()

    qs = MetaFaturamento.objects.all()

    if ano_de.isdigit():
        qs = qs.filter(ano__gte=int(ano_de))
    if ano_ate.isdigit():
        qs = qs.filter(ano__lte=int(ano_ate))
    if mes.isdigit():
        qs = qs.filter(mes=int(mes))

    # Valores (Decimal) seguros
    def _to_dec(s):
        try:
            return Decimal(s)
        except Exception:
            return None

    vmin = _to_dec(vmin_str)
    vmax = _to_dec(vmax_str)
    if vmin is not None:
        qs = qs.filter(valor__gte=vmin)
    if vmax is not None:
        qs = qs.filter(valor__lte=vmax)

    qs = qs.order_by("-ano", "mes")

    # ---- Indicadores (sobre o queryset filtrado) ----
    agg = qs.aggregate(
        total_metas=Count("id"),
        soma_metas=Coalesce(Sum("valor"), Decimal("0.00")),
        media_metas=Coalesce(Avg("valor"), Decimal("0.00")),
    )

    # Meta anual acumulada do ano atual (apenas como KPI de referência)
    ano_atual = date.today().year
    soma_ano_atual = (
        qs.filter(ano=ano_atual)
          .aggregate(soma=Coalesce(Sum("valor"), Decimal("0.00")))
          .get("soma", Decimal("0.00"))
    )

    indicadores = {
        "kpi_qtde": agg["total_metas"] or 0,
        "kpi_soma": Decimal(agg["soma_metas"] or 0),
        "kpi_media": Decimal(agg["media_metas"] or 0),
        "kpi_ano_atual": Decimal(soma_ano_atual or 0),
    }

    # ---- Paginação ----
    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Opções de meses (para select2 no offcanvas)
    meses_options = _meses_choices()

    context = {
        "page_obj": page_obj,
        "paginator": paginator,
        "indicadores": indicadores,
        "meses_options": meses_options,
        "filtros": {
            "ano_de": ano_de,
            "ano_ate": ano_ate,
            "mes": mes,
            "valor_min": (request.GET.get("valor_min") or ""),
            "valor_max": (request.GET.get("valor_max") or ""),
        }
    }
    return render(request, "metas/lista_metas.html", context)


# ========================= CRUD BÁSICO =========================
@login_required
@permission_required("comercial.add_metafaturamento", raise_exception=True)
def cadastrar_meta(request):
    form = MetaFaturamentoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Meta cadastrada com sucesso.")
        return redirect("lista_metas")
    return render(request, "metas/form_metas.html", {"form": form, "modo": "criar"})


@login_required
@permission_required("comercial.change_metafaturamento", raise_exception=True)
def editar_meta(request, pk: int):
    obj = get_object_or_404(MetaFaturamento, pk=pk)
    form = MetaFaturamentoForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Meta atualizada com sucesso.")
        return redirect("lista_metas")
    return render(request, "metas/form_metas.html", {"form": form, "modo": "editar", "obj": obj})


@login_required
@permission_required("comercial.delete_metafaturamento", raise_exception=True)
def excluir_meta(request, pk: int):
    obj = get_object_or_404(MetaFaturamento, pk=pk)
    obj.delete()
    messages.success(request, "Meta excluída com sucesso.")
    return redirect("lista_metas")