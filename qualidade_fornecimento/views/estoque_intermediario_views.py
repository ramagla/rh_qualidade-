# qualidade_fornecimento/views/estoque_intermediario_views.py — IMPORTS (PARA)

from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET

from qualidade_fornecimento.forms.estoque_intermediario_forms import (
    EstoqueIntermediarioForm,
    ApontarRetornoForm,
    EIItemFormSet,
    EIItemRetornoFormSet,
)
from qualidade_fornecimento.models import MateriaPrimaCatalogo
from qualidade_fornecimento.models.estoque_intermediario import EstoqueIntermediario
from qualidade_fornecimento.models.rolo import RoloMateriaPrima

from decimal import Decimal
from django.db.models import F, Value, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce


# ======== Listagens ========
@login_required
@permission_required("qualidade_fornecimento.view_estoqueintermediario", raise_exception=True)
def ei_list_em_fabrica(request):
    now = timezone.now()  # usado nos filtros e no fallback dos KPIs

    # ===== Base queryset (com relacionamentos para a LISTA/PAGINAÇÃO) =====
    qs = (
        EstoqueIntermediario.objects
        .select_related("materia_prima", "maquina")
        .prefetch_related("itens__lote", "itens__tb050__fornecedor")
        .filter(status="EM_FABRICA")
        .order_by("-data_envio", "-id")
    )

    qs = qs.annotate(
        previsto_kg=ExpressionWrapper(
            Coalesce(F("qtde_op_prevista"), Value(Decimal("0"))) * Decimal("1.05"),
            output_field=DecimalField(max_digits=14, decimal_places=3),
        )
    )


    # -------- Filtros --------
    op = (request.GET.get("op") or "").strip()
    mp = (request.GET.get("mp") or "").strip()  # id da MP
    de = (request.GET.get("de") or "").strip()
    ate = (request.GET.get("ate") or "").strip()
    acima_dias = (request.GET.get("acima_dias") or "").strip()

    if op:
        qs = qs.filter(op__icontains=op)

    if mp:
        try:
            qs = qs.filter(materia_prima_id=int(mp))
        except ValueError:
            pass

    # Período por data_envio (date)
    if de:
        qs = qs.filter(data_envio__date__gte=de)
    if ate:
        qs = qs.filter(data_envio__date__lte=ate)

    # "Acima de N dias" (filtra pela data_envio)
    if acima_dias:
        try:
            n = int(acima_dias)
            limite = now - timedelta(days=n)
            qs = qs.filter(data_envio__lte=limite)
        except ValueError:
            pass

    # -------- KPIs (sobre a queryset filtrada) --------
    total = qs.count()
    dias_list = []
    if total:
        # ⚠️ Para evitar o erro "deferred + select_related", zere os relacionamentos
        # e traga somente os campos necessários para o cálculo.
        qs_kpi = (
            qs.select_related(None)
              .prefetch_related(None)
              .only("data_envio", "created_at", "data_retorno", "status")
        )

        for obj in qs_kpi.iterator():
            try:
                dias_list.append(int(obj.dias_em_fabrica()))
            except Exception:
                # fallback por segurança
                ref = obj.data_envio or obj.created_at
                fim = now
                dias_list.append(max((fim.date() - ref.date()).days, 0))

    media_dias = round(sum(dias_list) / len(dias_list), 1) if dias_list else 0
    acima_20dias = sum(1 for d in dias_list if d > 10)  # regra atual: > 10 dias

    kpis = {
        "total": total,
        "media_dias": media_dias,
        "acima_20dias": acima_20dias,  # mantém a mesma chave usada no template
    }

    # -------- Paginação --------
    page_number = request.GET.get("page") or 1
    per_page = 10
    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(page_number)

    # MP para filtros (Select2)
    materias_primas = MateriaPrimaCatalogo.objects.filter(tipo="Materia-Prima").order_by("descricao")

    context = {
        "page_obj": page_obj,
        "kpis": kpis,
        "materias_primas": materias_primas,
    }
    return render(request, "estoque_intermediario/list_em_fabrica.html", context)


# IMPORTS que você provavelmente vai precisar no topo do arquivo (além dos que já tem)
from decimal import Decimal
from django.core.paginator import Paginator
from django.db.models import Sum, Avg, Count, DecimalField, Value
from django.db.models.functions import Coalesce


# IMPORTS (além dos que você já usa no arquivo)
from decimal import Decimal
from django.core.paginator import Paginator
from django.db.models import F, Value, Sum, Avg, Count, Case, When, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce

# ajuste o caminho conforme seu projeto


@login_required
@permission_required("qualidade_fornecimento.view_estoqueintermediario", raise_exception=True)
def ei_list_historico(request):
    # ===== Query base =====
    qs = (
        EstoqueIntermediario.objects
        .select_related("materia_prima", "maquina")
        .prefetch_related("itens__lote", "itens__tb050__fornecedor")
        .filter(status="RETORNADO")
        .order_by("-data_retorno", "-id")
    )

    # ===== Filtros =====
    op  = (request.GET.get("op")  or "").strip()
    mp  = (request.GET.get("mp")  or "").strip()
    de  = (request.GET.get("de")  or "").strip()
    ate = (request.GET.get("ate") or "").strip()

    if op:
        qs = qs.filter(op__icontains=op)
    if mp:
        try:
            qs = qs.filter(materia_prima_id=int(mp))
        except ValueError:
            pass
    if de:
        qs = qs.filter(data_retorno__date__gte=de)
    if ate:
        qs = qs.filter(data_retorno__date__lte=ate)

    # ===== Anotação: % sucata calculada (para poder fazer AVG no banco) =====
    qs_annot = qs.annotate(
        perc_sucata_calc=Case(
            When(
                enviado__gt=0,
                then=ExpressionWrapper(
                    F("sucata") * Value(Decimal("100.0")) / F("enviado"),
                    output_field=DecimalField(max_digits=8, decimal_places=2),
                ),
            ),
            default=Value(Decimal("0.00")),
            output_field=DecimalField(max_digits=8, decimal_places=2),
        )
    )

    # ===== KPIs (sobre a queryset filtrada) =====
    agg = qs_annot.aggregate(
        total=Count("id"),
        retorno_total=Coalesce(
            Sum("retorno"),
            Value(Decimal("0.000")),
            output_field=DecimalField(max_digits=14, decimal_places=3),
        ),
        consumo_real_total=Coalesce(
            Sum("consumo_real_kg"),
            Value(Decimal("0.000")),
            output_field=DecimalField(max_digits=14, decimal_places=3),
        ),
        media_sucata=Coalesce(
            Avg("perc_sucata_calc"),
            Value(Decimal("0.00")),
            output_field=DecimalField(max_digits=8, decimal_places=2),
        ),
    )
    kpis = {
        "total": agg["total"] or 0,
        "retorno_total": agg["retorno_total"] or Decimal("0.000"),
        "consumo_real_total": agg["consumo_real_total"] or Decimal("0.000"),
        "media_sucata": agg["media_sucata"] or Decimal("0.00"),
    }

    # ===== Paginação =====
    page_number = request.GET.get("page") or 1
    per_page = 10
    paginator = Paginator(qs_annot, per_page)
    page_obj = paginator.get_page(page_number)

    # ===== Auxiliares (filtros) =====
    materias_primas = (
        MateriaPrimaCatalogo.objects
        .filter(tipo="Materia-Prima")
        .order_by("descricao")
    )

    context = {
        "page_obj": page_obj,              # usado na tabela/partials
        "kpis": kpis,                      # cards
        "materias_primas": materias_primas # select2 no offcanvas
    }
    return render(request, "estoque_intermediario/list_historico.html", context)




# ======== CRUD / Ações ========
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from qualidade_fornecimento.forms.estoque_intermediario_forms import (
    EstoqueIntermediarioForm,
    EIItemFormSet,
)

@login_required
@permission_required("qualidade_fornecimento.add_estoqueintermediario", raise_exception=True)
@transaction.atomic
def ei_create(request):
    if request.method == "POST":
        form = EstoqueIntermediarioForm(request.POST, request.FILES)
        formset = EIItemFormSet(request.POST, prefix="itens")

        if form.is_valid() and formset.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.updated_by = request.user
            obj.responsavel_envio = request.user
            obj.status = "EM_FABRICA"
            if not obj.data_envio:
                obj.data_envio = timezone.now()
            obj.save()

            formset.instance = obj
            formset.save()

            obj.recalc_totais(save=True)
            messages.success(request, "Envio registrado com sucesso.")
            return redirect("ei_list_em_fabrica")

        # ⚠️ POST inválido → mostra toast e mantém erros no form
        messages.error(request, "Corrija os campos destacados para prosseguir.")
    else:
        form = EstoqueIntermediarioForm(initial={"data_envio": timezone.now()})
        formset = EIItemFormSet(prefix="itens")

    return render(
        request,
        "estoque_intermediario/form_create.html",
        {"form": form, "formset": formset},
    )


from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from qualidade_fornecimento.models.estoque_intermediario import EstoqueIntermediario
from qualidade_fornecimento.forms.estoque_intermediario_forms import (
    ApontarRetornoForm,
    EIItemRetornoFormSet,
)

@login_required
@permission_required("qualidade_fornecimento.change_estoqueintermediario", raise_exception=True)
@transaction.atomic
def ei_apontar_retorno(request, pk):
    obj = get_object_or_404(
        EstoqueIntermediario.objects.select_related("maquina", "materia_prima")
        .prefetch_related("itens__lote", "itens__tb050__fornecedor"),
        pk=pk,
    )

    if obj.status != "EM_FABRICA":
        messages.warning(request, "Este item não está 'Em Fábrica'.")
        return redirect("ei_list_em_fabrica")

    if request.method == "POST":
        form = ApontarRetornoForm(request.POST, request.FILES, instance=obj)
        formset = EIItemRetornoFormSet(request.POST, instance=obj, prefix="itens")

        if form.is_valid() and formset.is_valid():
            tmp = form.save(commit=False)
            tmp.updated_by = request.user

            # grava retornos/sucata/refugo por lote
            formset.save()

            # recalcula KPIs no cabeçalho (sem salvar ainda)
            tmp.recalc_totais(save=False)

            # valida tolerância de sucata
            tol = (tmp.tolerancia_sucata_percentual or Decimal("3.00")).quantize(Decimal("0.01"))
            if tmp.perc_sucata > tol and not (tmp.justificativa_excesso or "").strip():
                form.add_error(
                    "justificativa_excesso",
                    f"Percentual de sucata {tmp.perc_sucata}% excede tolerância {tol}%. Informe justificativa.",
                )
                # reflete totais calculados na tela
                obj.enviado = tmp.enviado
                obj.retorno = tmp.retorno
                obj.sucata = tmp.sucata
                obj.refugo = tmp.refugo
                obj.consumo_inferido_kg = tmp.consumo_inferido_kg
                obj.consumo_balanca_kg = tmp.consumo_balanca_kg
                obj.consumo_real_kg = tmp.consumo_real_kg
                messages.error(request, "Corrija os campos destacados para prosseguir.")
                return render(
                    request,
                    "estoque_intermediario/form_apontar_retorno.html",
                    {"form": form, "formset": formset, "obj": obj},
                )

            # fecha o envio
            tmp.status = "RETORNADO"
            tmp.responsavel_retorno = request.user
            if not tmp.data_retorno:
                tmp.data_retorno = timezone.now()

            try:
                tmp.full_clean()
                tmp.save()  # atomic: salva cabeçalho com os totais já consistentes
            except ValidationError as e:
                # propaga erros de modelo para o form
                for field, msgs in e.message_dict.items():
                    for m in msgs:
                        (form.add_error(field, m) if field in form.fields else form.add_error(None, m))
                # garante KPIs na tela
                obj.enviado = tmp.enviado
                obj.retorno = tmp.retorno
                obj.sucata = tmp.sucata
                obj.refugo = tmp.refugo
                obj.consumo_inferido_kg = tmp.consumo_inferido_kg
                obj.consumo_balanca_kg = tmp.consumo_balanca_kg
                obj.consumo_real_kg = tmp.consumo_real_kg
                messages.error(request, "Corrija os campos destacados para prosseguir.")
                return render(
                    request,
                    "estoque_intermediario/form_apontar_retorno.html",
                    {"form": form, "formset": formset, "obj": obj},
                )

            messages.success(request, "Item fechado e enviado ao Histórico.")
            return redirect("ei_list_historico")

        # POST inválido (form e/ou formset)
        messages.error(request, "Corrija os campos destacados para prosseguir.")
    else:
        form = ApontarRetornoForm(instance=obj, initial={"data_retorno": timezone.now()})
        formset = EIItemRetornoFormSet(instance=obj, prefix="itens")

    return render(
        request,
        "estoque_intermediario/form_apontar_retorno.html",
        {"form": form, "formset": formset, "obj": obj},
    )




@login_required
@permission_required("qualidade_fornecimento.change_estoqueintermediario", raise_exception=True)
def ei_estornar_para_em_fabrica(request, pk):
    obj = get_object_or_404(EstoqueIntermediario, pk=pk)
    if request.method == "POST":
        obj.status = "EM_FABRICA"
        obj.data_retorno = None
        obj.aprovado_por = None
        obj.updated_by = request.user
        obj.save()
        messages.info(request, "Item estornado para 'Em Fábrica'.")
        return redirect("ei_list_em_fabrica")
    return render(request, "estoque_intermediario/confirm_estornar.html", {"obj": obj})


# ======== API dependente (Select2) ========
@login_required
@require_GET
def api_rolos_por_mp(request):
    mp_id = request.GET.get("mp")
    termo = (request.GET.get("q") or "").strip()

    if not mp_id:
        return JsonResponse({"results": []})

    qs = RoloMateriaPrima.objects.select_related("tb050").filter(tb050__materia_prima_id=mp_id)
    if termo:
        qs = qs.filter(nro_rolo__icontains=termo)
    qs = qs.order_by("-nro_rolo")[:500]

    data = []
    for r in qs:
        # ✅ Somente o número do rolo
        texto_rolo = str(r.nro_rolo)
        # ✅ Somente o número do relatório TB050
        tb_label = ""
        if getattr(r, "tb050", None):
            tb_label = str(getattr(r.tb050, "nro_relatorio", r.tb050_id or ""))

        data.append(
            {
                "id": str(r.pk),        # usa o PK real do rolo (pode não ser 'id')
                "texto": texto_rolo,    # rótulo do Select2
                "tb050_id": r.tb050_id, # para autopreencher
                "tb050_label": tb_label # label “limpo” para TB050
            }
        )
    return JsonResponse({"results": data})

from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.contrib import messages


@login_required
@permission_required("qualidade_fornecimento.change_estoqueintermediario", raise_exception=True)
@require_POST
def ei_upload_anexo(request, pk):
    obj = get_object_or_404(EstoqueIntermediario, pk=pk)

    # Remover anexo
    if "remover" in request.POST:
        if obj.anexo:
            obj.anexo.delete(save=False)
            obj.anexo = None
            obj.updated_by = request.user
            obj.save(update_fields=["anexo", "updated_by", "updated_at"])
            messages.info(request, "Anexo removido.")
        else:
            messages.warning(request, "Não há anexo para remover.")
        return redirect(request.META.get("HTTP_REFERER", "ei_list_historico"))

    # Enviar/substituir anexo
    file = request.FILES.get("anexo")
    if file:
        obj.anexo = file
        obj.updated_by = request.user
        obj.save(update_fields=["anexo", "updated_by", "updated_at"])
        messages.success(request, "Anexo salvo com sucesso.")
    else:
        messages.warning(request, "Selecione um arquivo para enviar.")
    return redirect(request.META.get("HTTP_REFERER", "ei_list_historico"))


from decimal import Decimal
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone

from qualidade_fornecimento.models.estoque_intermediario import EstoqueIntermediario


# WeasyPrint
try:
    from weasyprint import HTML  # pip install weasyprint
except Exception as e:  # pragma: no cover
    HTML = None


@login_required
@permission_required("qualidade_fornecimento.view_estoqueintermediario", raise_exception=True)
def ei_relatorio_pdf(request, pk: int):
    """
    Relatório PDF de um item do Estoque Intermediário (preferencialmente do histórico).
    Gera um PDF com cabeçalho, KPIs, e tabela de lotes (enviado/retorno/sucata/refugo).
    """
    obj = get_object_or_404(
        EstoqueIntermediario.objects
        .select_related("materia_prima", "maquina")
        .prefetch_related("itens__lote", "itens__tb050__fornecedor"),
        pk=pk
    )

    # Dias em produção (de envio até retorno, quando houver)
    dias_producao = None
    if obj.data_envio and obj.data_retorno:
        dias_producao = max((obj.data_retorno.date() - obj.data_envio.date()).days, 0)

    # Consumo previsto ajustado por peças (+5%) — se tivermos as 3 infos
    previsto_ajustado_kg = None
    try:
        if obj.qtde_op_prevista and obj.pecas_planejadas_op and obj.pecas_apontadas:
            prev_ajustado = (Decimal(obj.qtde_op_prevista) / Decimal(obj.pecas_planejadas_op)) * Decimal(obj.pecas_apontadas)
            previsto_ajustado_kg = (prev_ajustado * Decimal("1.05")).quantize(Decimal("0.001"))
    except Exception:
        previsto_ajustado_kg = None

    context = {
        "item": obj,
        "dias_producao": dias_producao,
        "previsto_ajustado_kg": previsto_ajustado_kg,
        "gerado_em": timezone.now(),
        # fallback de previsto (planejado +5%) caso você envie item.previsto_kg no contexto padrão
        "previsto_kg": getattr(obj, "previsto_kg", None) or getattr(obj, "qtde_op_prevista", None),
    }

    # Se WeasyPrint não estiver disponível, retorna HTML "imprimível"
    if HTML is None:
        html = render_to_string("estoque_intermediario/relatorio_pdf.html", context, request=request)
        return HttpResponse(html)

    # Renderiza PDF
    html = render_to_string("estoque_intermediario/relatorio_pdf.html", context, request=request)
    pdf = HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    filename = f"relatorio_OP_{obj.op or obj.pk}.pdf"
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response

# + adicionar
@login_required
@permission_required("qualidade_fornecimento.change_estoqueintermediario", raise_exception=True)
def ei_update(request, pk):
    obj = get_object_or_404(
        EstoqueIntermediario.objects.select_related("materia_prima", "maquina"),
        pk=pk
    )
    if obj.status != "EM_FABRICA":
        messages.warning(request, "Só é possível editar envios que estejam 'Em Fábrica'.")
        return redirect("ei_list_em_fabrica")

    if request.method == "POST":
        form = EstoqueIntermediarioForm(request.POST, request.FILES, instance=obj)
        formset = EIItemFormSet(request.POST, instance=obj, prefix="itens")
        if form.is_valid() and formset.is_valid():
            obj = form.save(commit=False)
            obj.updated_by = request.user
            obj.save()
            formset.save()
            obj.recalc_totais(save=True)
            messages.success(request, "Envio atualizado com sucesso.")
            return redirect("ei_list_em_fabrica")
    else:
        form = EstoqueIntermediarioForm(instance=obj)
        formset = EIItemFormSet(instance=obj, prefix="itens")

    return render(request, "estoque_intermediario/form_create.html", {"form": form, "formset": formset})
