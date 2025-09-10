from typing import Optional, Tuple
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from qualidade_fornecimento.forms.inventario_forms import InventarioForm, ContagemForm
from qualidade_fornecimento.models import (
    Inventario,
    InventarioItem,
    Contagem,
    Divergencia,
    InventarioExportacao,
)

# =========================
# Helpers de QR e resolução
# =========================

def _to_decimal_safe(value, default: Optional[Decimal] = None) -> Optional[Decimal]:
    if value is None:
        return default
    try:
        return Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError, TypeError):
        return default

def _parse_qr(origem: str) -> Tuple[Optional[str], Optional[str], Optional[Decimal], Optional[str], Optional[str]]:
    """
    Formato esperado (TB050): CODIGO;ETIQUETA;PESO;LOCAL;FORNECEDOR
    Retorna: (codigo, etiqueta, peso_decimal_ou_None, local, fornecedor)
    - Tolerante a vírgula/ponto no peso.
    - Campos ausentes retornam None.
    """
    if not origem:
        return None, None, None, None, None
    partes = [p.strip() for p in str(origem).split(";")]
    codigo      = partes[0] if len(partes) >= 1 else None
    etiqueta    = partes[1] if len(partes) >= 2 else None
    peso        = _to_decimal_safe(partes[2], None) if len(partes) >= 3 else None
    local       = partes[3] if len(partes) >= 4 else None
    fornecedor  = partes[4] if len(partes) >= 5 else None
    return codigo, etiqueta, peso, local, fornecedor


def _resolver_item_por_qr(inv: Inventario, origem: str) -> Optional[InventarioItem]:
    """
    Regra revisada:
      - Se a ETIQUETA veio no QR:
          * tenta achar por etiqueta;
          * se NÃO existir, CRIA novo item (mesmo que já exista outro com o mesmo código).
      - Só usa busca por CÓDIGO quando a etiqueta NÃO veio.
    """
    codigo, etiqueta, _, local, fornecedor = _parse_qr(origem)

    # 1) ETIQUETA presente => é a identidade do rolo/lote
    if etiqueta:
        it = inv.itens.filter(etiqueta=etiqueta).first()
        if it:
            updates = []
            if codigo and not it.codigo_item:
                it.codigo_item = codigo
                updates.append("codigo_item")
            if local and not it.local:
                it.local = local
                updates.append("local")
            # preencher fornecedor se o modelo tiver o campo e ele estiver vazio
            if fornecedor and hasattr(it, "fornecedor") and not getattr(it, "fornecedor"):
                it.fornecedor = fornecedor
                updates.append("fornecedor")
            if updates:
                it.save(update_fields=updates)
            return it

        # etiqueta não existe ainda -> cria novo item para essa etiqueta
        campos = {
            "inventario": inv,
            "codigo_item": codigo or etiqueta or "DESCONHECIDO",
            "etiqueta": etiqueta,
            "unidade": "",
            "local": local or "",
        }
        if hasattr(InventarioItem, "fornecedor"):
            campos["fornecedor"] = fornecedor or ""
        return InventarioItem.objects.create(**campos)

    # 2) Sem etiqueta no QR -> tenta por código; se não achar, cria
    if codigo:
        it = inv.itens.filter(codigo_item=codigo).first()
        if it:
            updates = []
            if local and not it.local:
                it.local = local
                updates.append("local")
            if fornecedor and hasattr(it, "fornecedor") and not getattr(it, "fornecedor"):
                it.fornecedor = fornecedor
                updates.append("fornecedor")
            if updates:
                it.save(update_fields=updates)
            return it

        campos = {
            "inventario": inv,
            "codigo_item": codigo,
            "etiqueta": "",
            "unidade": "",
            "local": local or "",
        }
        if hasattr(InventarioItem, "fornecedor"):
            campos["fornecedor"] = fornecedor or ""
        return InventarioItem.objects.create(**campos)

    # 3) Sem código e sem etiqueta -> cria genérico
    return InventarioItem.objects.create(
        inventario=inv,
        codigo_item="DESCONHECIDO",
        etiqueta="",
        unidade="",
        local=local or "",
        **({"fornecedor": fornecedor or ""} if hasattr(InventarioItem, "fornecedor") else {})
    )


# ==========
# List / New
# ==========

from django.core.paginator import Paginator
from django.db.models import Q, Count

from django.core.paginator import Paginator
from django.db.models import Q, Count

@login_required
@permission_required("qualidade_fornecimento.view_inventario", raise_exception=True)
def inventario_list(request):
    qs = Inventario.objects.all().order_by("-criado_em")

    # ===== Filtros =====
    titulo = (request.GET.get("titulo") or "").strip()
    status = (request.GET.get("status") or "").strip()
    dt_de = (request.GET.get("data_corte_de") or "").strip()
    dt_ate = (request.GET.get("data_corte_ate") or "").strip()

    if titulo:
        qs = qs.filter(titulo__icontains=titulo)

    if status:
        qs = qs.filter(status=status)

    if dt_de:
        qs = qs.filter(data_corte__gte=dt_de)

    if dt_ate:
        qs = qs.filter(data_corte__lte=dt_ate)

    # ===== Totais para cards =====
    # Observando os status já utilizados nas views existentes
    # (ABERTO, EM_CONTAGEM_1, EM_CONTAGEM_2, EM_CONFERENCIA, EXPORTADO)
    base = Inventario.objects.all()
    totais = {
        "total": base.count(),
        "abertos": base.filter(status="ABERTO").count(),
        "em_contagem": base.filter(status__in=["EM_CONTAGEM_1", "EM_CONTAGEM_2"]).count(),
        "em_conferencia": base.filter(status="EM_CONFERENCIA").count(),
        "exportados": base.filter(status="EXPORTADO").count(),
    }

    # ===== Paginação =====
    paginator = Paginator(qs, 20)  # 20 por página (ajuste conforme necessidade)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # ===== Choices de status (reutiliza as choices do modelo)
    status_choices = getattr(Inventario, "STATUS_CHOICES", ())
    # Fallback: pode inferir de rótulos já usados
    if not status_choices:
        status_choices = (
            ("ABERTO", "Aberto"),
            ("EM_CONTAGEM_1", "Em Contagem (1ª)"),
            ("EM_CONTAGEM_2", "Em Contagem (2ª)"),
            ("EM_CONFERENCIA", "Em Conferência"),
            ("EXPORTADO", "Exportado"),
        )

    ctx = {
        "page_obj": page_obj,
        "status_choices": status_choices,
        "totais": totais,
    }
    return render(request, "inventarios/inventario_list.html", ctx)


@login_required
@permission_required("qualidade_fornecimento.add_inventario", raise_exception=True)
def inventario_create(request):
    if request.method == "POST":
        form = InventarioForm(request.POST)
        if form.is_valid():
            inv = form.save(commit=False)
            inv.created_by = request.user
            inv.updated_by = request.user
            inv.save()
            messages.success(request, "Inventário criado.")
            return redirect("inventario_detail", pk=inv.pk)
    else:
        form = InventarioForm()
    return render(request, "inventarios/inventario_form.html", {"form": form})

# ==============
# Detalhe / Itens
# ==============

from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render

from qualidade_fornecimento.models import Inventario, InventarioItem, Contagem, Divergencia

@login_required
@permission_required("qualidade_fornecimento.view_inventario", raise_exception=True)
def inventario_detail(request, pk):
    inv = get_object_or_404(Inventario, pk=pk)

    # Itens e paginação (mantém seu fluxo atual)
    qs_itens = inv.itens.order_by("pk")
    per_page = int(request.GET.get("per_page") or 30)
    paginator = Paginator(qs_itens, per_page)
    page_obj_itens = paginator.get_page(request.GET.get("page"))
    itens_pagina = list(page_obj_itens.object_list)

    # Carrega contagens da página e injeta c1/c2/c3
    ids_pagina = [it.pk for it in itens_pagina]
    conts = (
        Contagem.objects
        .filter(inventario_item_id__in=ids_pagina)
        .only("inventario_item_id", "ordem", "quantidade", "id")
        .order_by("inventario_item_id", "ordem", "id")
    )
    mapa = {}
    for c in conts:
        mapa[(c.inventario_item_id, c.ordem)] = c.quantidade
    for it in itens_pagina:
        it.c1 = mapa.get((it.pk, 1))
        it.c2 = mapa.get((it.pk, 2))
        it.c3 = mapa.get((it.pk, 3))
    page_obj_itens.object_list = itens_pagina

    # Indicadores (cards)
    total_itens = qs_itens.count()
    com_c1 = inv.itens.filter(contagens__ordem=1).distinct().count()
    com_c2 = inv.itens.filter(contagens__ordem=2).distinct().count()
    totais_itens = {
        "total": total_itens,
        "pend_c1": max(total_itens - com_c1, 0),
        "pend_c2": max(total_itens - com_c2, 0),
    }

    divergencias_abertas = Divergencia.objects.filter(
        inventario_item__inventario=inv,
        houve_divergencia=True
    ).count()

    # Botões por STATUS
    can_show_confronto  = inv.status in ["EM_CONFERENCIA", "DIVERGENTE", "CONSOLIDADO", "EXPORTADO"]
    can_show_consolidar = (inv.status in ["EM_CONFERENCIA", "DIVERGENTE"]) and (divergencias_abertas == 0)

    # ✅ Exportar habilitado quando CONSOLIDADO **ou** EXPORTADO
    can_show_exportar   = inv.status in ["CONSOLIDADO", "EXPORTADO"]

    context = {
        "inventario": inv,
        "page_obj_itens": page_obj_itens,
        "totais_itens": totais_itens,
        "divergencias_abertas": divergencias_abertas,
        "can_show_confronto": can_show_confronto,
        "can_show_consolidar": can_show_consolidar,
        "can_show_exportar": can_show_exportar,
    }
    return render(request, "inventarios/inventario_detail.html", context)


# ==================
# Contagens 1 / 2 / 3
# ==================

def _registrar_contagem(inv: Inventario, request, ordem_contagem: int):
    if inv.status not in ["ABERTO", "EM_CONTAGEM_1", "EM_CONTAGEM_2"] and ordem_contagem != 3:
        messages.warning(
            request,
            f"O inventário está em '{inv.get_status_display()}'. Reabra para registrar {['','1ª','2ª','3ª'][ordem_contagem]} contagem."
        )
        return redirect("inventario_detail", pk=inv.pk)

    if request.method == "POST":
        form = ContagemForm(request.POST)
        if form.is_valid():
            origem = form.cleaned_data["origem_qrcode"]
            qtd = form.cleaned_data["quantidade"]

            item = _resolver_item_por_qr(inv, origem)
            if not item:
                messages.error(request, "Não foi possível identificar a etiqueta/item a partir do QR.")
                return redirect(request.path)

            if inv.tipo == "PA":
                c_obj, created = Contagem.objects.get_or_create(
                    inventario_item=item,
                    ordem=ordem_contagem,
                    defaults={"quantidade": qtd, "usuario": request.user, "origem_qrcode": origem},
                )
                if not created:
                    c_obj.quantidade = (c_obj.quantidade or 0) + (qtd or 0)
                    c_obj.usuario = request.user
                    c_obj.origem_qrcode = origem or c_obj.origem_qrcode
                    c_obj.save(update_fields=["quantidade", "usuario", "origem_qrcode"])
            else:
                Contagem.objects.update_or_create(
                    inventario_item=item,
                    ordem=ordem_contagem,
                    defaults={"quantidade": qtd, "usuario": request.user, "origem_qrcode": origem},
                )

            # Avança status automaticamente
            if ordem_contagem == 1 and inv.status == "ABERTO":
                inv.status = "EM_CONTAGEM_1"
            elif ordem_contagem == 2 and inv.status in ["ABERTO", "EM_CONTAGEM_1"]:
                inv.status = "EM_CONTAGEM_2"

            inv.updated_by = request.user
            inv.save(update_fields=["status", "updated_by"])

            messages.success(request, f"{['','1ª','2ª','3ª'][ordem_contagem]} contagem registrada.")
            return redirect(request.path)
    else:
        form = ContagemForm()

    return form

@login_required
@permission_required("qualidade_fornecimento.view_inventario", raise_exception=True)
def contagem_primeira(request, pk):
    inv = get_object_or_404(Inventario, pk=pk)
    ordem = 1
    form = _registrar_contagem(inv, request, ordem)
    if hasattr(form, "is_valid"):  # GET
        ctx = {"inventario": inv, "form": form, "ordem": ordem, "ordem_label": "1ª Contagem"}
        return render(request, "inventarios/inventario_form_contagem.html", ctx)
    return form  # POST tratou

@login_required
@permission_required("qualidade_fornecimento.view_inventario", raise_exception=True)
def contagem_segunda(request, pk):
    inv = get_object_or_404(Inventario, pk=pk)
    ordem = 2
    form = _registrar_contagem(inv, request, ordem)
    if hasattr(form, "is_valid"):
        ctx = {"inventario": inv, "form": form, "ordem": ordem, "ordem_label": "2ª Contagem"}
        return render(request, "inventarios/inventario_form_contagem.html", ctx)
    return form

@login_required
@permission_required("qualidade_fornecimento.view_inventario", raise_exception=True)
def contagem_terceira(request, pk):
    inv = get_object_or_404(Inventario, pk=pk)
    ordem = 3
    form = _registrar_contagem(inv, request, ordem)
    if hasattr(form, "is_valid"):
        ctx = {"inventario": inv, "form": form, "ordem": ordem, "ordem_label": "3ª Contagem / Ajuste"}
        return render(request, "inventarios/inventario_form_contagem.html", ctx)
    return form

# ===========
# Confronto
# ===========

@login_required
@permission_required("qualidade_fornecimento.view_inventario", raise_exception=True)
def confronto_view(request, pk):
    inv = get_object_or_404(Inventario, pk=pk)

    # Recalcula/atualiza divergências considerando a 3ª contagem como resolução
    for item in inv.itens.prefetch_related("contagens"):
        mapa = {c.ordem: c for c in item.contagens.all()}
        c1 = mapa.get(1)
        c2 = mapa.get(2)
        c3 = mapa.get(3)

        # Regras:
        # - Se existir 3ª contagem -> RESOLVIDO (houve_divergencia = False)
        # - Senão, é divergente se faltar 1ª OU 2ª, ou se 1ª != 2ª
        if c3:
            houve_div = False
        else:
            incompleto = (c1 is None) or (c2 is None)
            diferentes = (c1 is not None and c2 is not None and c1.quantidade != c2.quantidade)
            houve_div = incompleto or diferentes

        div, _ = Divergencia.objects.get_or_create(inventario_item=item)
        div.qtd_contagem1 = (c1.quantidade if c1 else None)
        div.qtd_contagem2 = (c2.quantidade if c2 else None)
        div.qtd_contagem3 = (c3.quantidade if c3 else None)

        # Não desfaça marcações de resolução manual; a 3ª contagem (ou ajuste) zera a divergência
        div.houve_divergencia = houve_div
        div.save()

    # Mantém status
    inv.status = "EM_CONFERENCIA"
    inv.updated_by = request.user
    inv.save(update_fields=["status", "updated_by"])

    # Mostra apenas pendências reais (sem 3ª contagem)
    divergentes = (Divergencia.objects
                   .filter(inventario_item__inventario=inv, houve_divergencia=True)
                   .select_related("inventario_item"))

    return render(request, "inventarios/inventario_divergencias.html", {
        "inventario": inv,
        "divergentes": divergentes,
    })



# ===========
# Ajustes
# ===========

@login_required
@permission_required("qualidade_fornecimento.view_inventario", raise_exception=True)
def ajustes_manuais_view(request, pk):
    inv = get_object_or_404(Inventario, pk=pk)
    if request.method == "POST":
        item_id = request.POST.get("item_id")
        acao = (request.POST.get("acao") or "C3").upper()  # "C3" | "AJUSTE"
        qtd_raw = (request.POST.get("qtd") or "").strip()
        justificativa = (request.POST.get("justificativa") or "").strip()

        if not item_id or not qtd_raw:
            messages.error(request, "Informe o item e a quantidade.")
            return redirect("inventario_confronto", pk=inv.pk)

        try:
            qtd = Decimal(str(qtd_raw).replace(",", "."))
        except Exception:
            messages.error(request, "Quantidade inválida.")
            return redirect("inventario_confronto", pk=inv.pk)

        if acao == "AJUSTE" and not justificativa:
            messages.error(request, "Justificativa é obrigatória para ajuste manual.")
            return redirect("inventario_confronto", pk=inv.pk)

        item = get_object_or_404(InventarioItem, pk=item_id, inventario=inv)

        Contagem.objects.update_or_create(
            inventario_item=item,
            ordem=3,
            defaults={
                "quantidade": qtd,
                "usuario": request.user,
                "origem_qrcode": "AJUSTE_MANUAL" if acao == "AJUSTE" else "TERCEIRA_CONTAGEM",
            },
        )

        div, _ = Divergencia.objects.get_or_create(inventario_item=item)
        div.qtd_contagem3 = qtd
        div.resolvido_por_ajuste = (acao == "AJUSTE")
        div.justificativa_ajuste = justificativa if acao == "AJUSTE" else ""
        div.resolvido_em = timezone.now()
        div.resolvido_por = request.user
        div.houve_divergencia = False
        div.save()

        messages.success(request, "Registro aplicado.")
        return redirect("inventario_confronto", pk=inv.pk)

    divergentes = Divergencia.objects.filter(inventario_item__inventario=inv, houve_divergencia=True)
    return render(request, "inventarios/inventario_divergencias.html", {
        "inventario": inv,
        "divergentes": divergentes,
    })


# ======================
# Consolidação (confirm)
# ======================

@login_required
@permission_required("qualidade_fornecimento.consolidar_inventario", raise_exception=True)
def inventario_consolidar_confirm(request, pk):
    inv = get_object_or_404(Inventario, pk=pk)
    divergentes = Divergencia.objects.filter(inventario_item__inventario=inv, houve_divergencia=True).count()
    total_itens = inv.itens.count()
    c1_preenchidas = Contagem.objects.filter(inventario_item__inventario=inv, ordem=1).count()
    c2_preenchidas = Contagem.objects.filter(inventario_item__inventario=inv, ordem=2).count()
    ctx = {
        "inventario": inv,
        "divergentes": divergentes,
        "total_itens": total_itens,
        "c1_preenchidas": c1_preenchidas,
        "c2_preenchidas": c2_preenchidas,
    }
    return render(request, "inventarios/inventario_confirm_consolidar.html", ctx)

# ======================
# Consolidação (POST)
# ======================

@login_required
@permission_required("qualidade_fornecimento.consolidar_inventario", raise_exception=True)
@require_POST
def inventario_consolidar(request, pk):
    inv = get_object_or_404(Inventario, pk=pk)

    # Bloqueia se houver divergências
    if Divergencia.objects.filter(inventario_item__inventario=inv, houve_divergencia=True).exists():
        messages.error(request, "Há divergências não resolvidas. Resolva-as antes de consolidar.")
        return redirect("inventario_consolidar_confirm", pk=inv.pk)

    # Consolidação
    for item in inv.itens.all():
        c1 = item.contagens.filter(ordem=1).first()
        c2 = item.contagens.filter(ordem=2).first()
        c3 = item.contagens.filter(ordem=3).first()

        if c3:
            final = c3.quantidade
        elif c1 and c2 and c1.quantidade == c2.quantidade:
            final = c1.quantidade
        else:
            if c1 and c2:
                final = (c1.quantidade + c2.quantidade) / Decimal("2")
            else:
                final = (c1.quantidade if c1 else Decimal("0"))

        item.quantidade_consolidada = final
        item.save(update_fields=["quantidade_consolidada"])

    inv.marcar_consolidado(request.user)
    messages.success(request, "Inventário consolidado com sucesso.")
    return redirect("inventario_detail", pk=inv.pk)

# ==============
# Exportação ERP
# ==============

@login_required
@permission_required("qualidade_fornecimento.exportar_inventario", raise_exception=True)
def inventario_exportar(request, pk):
    inv = get_object_or_404(Inventario, pk=pk)

    # Geração de CSV para ERP (sem UNIDADE; com FORNECEDOR)
    import csv
    import io

    buf = io.StringIO()
    w = csv.writer(buf, delimiter=';')

    # Cabeçalho atualizado
    w.writerow(["CODIGO_ITEM", "ETIQUETA", "QTD_CONSOLIDADA", "LOCAL", "FORNECEDOR", "DATA_CORTE"])

    # Linhas
    for it in inv.itens.order_by("codigo_item"):
        fornecedor = getattr(it, "fornecedor", "") or ""
        w.writerow([
            it.codigo_item,
            it.etiqueta,
            it.quantidade_consolidada or "",
            it.local,
            fornecedor,
            inv.data_corte.isoformat()
        ])

    content = buf.getvalue().encode("utf-8-sig")

    # Registro histórico da exportação
    exp = InventarioExportacao.objects.create(
        inventario=inv,
        criado_por=request.user,
        formato="CSV"
    )

    from django.core.files.base import ContentFile
    exp.arquivo.save(
        f"inventario_{inv.pk}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv",
        ContentFile(content)
    )
    exp.save()

    # Atualiza status do inventário
    inv.status = "EXPORTADO"
    inv.updated_by = request.user
    inv.save(update_fields=["status", "updated_by"])

    messages.success(request, "Arquivo de inventário gerado e salvo no histórico.")
    return redirect("inventario_exportacoes")


@login_required
@permission_required("qualidade_fornecimento.exportar_inventario", raise_exception=True)
def inventario_exportacoes(request):
    exportacoes = (
        InventarioExportacao.objects
        .select_related("inventario")
        .order_by("-criado_em")
    )
    ultimo_consolidado = (
        Inventario.objects
        .filter(status__in=["CONSOLIDADO", "EXPORTADO"])
        .order_by("-consolidado_em", "-criado_em")
        .first()
    )
    return render(request, "inventarios/inventario_exportacoes.html", {
        "exportacoes": exportacoes,
        "ultimo_consolidado": ultimo_consolidado,
    })

# ===========
# API de Scan
# ===========

# inventario_views.py — PARA (substitua a função inteira)

from decimal import Decimal, InvalidOperation
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required

def _up(v):
    return v.strip().upper() if isinstance(v, str) else v

def _dec(s):
    if s is None:
        return None
    try:
        # aceita "219,2" e "219.2"
        return Decimal(str(s).strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        return None

@login_required
@permission_required("qualidade_fornecimento.view_inventario", raise_exception=True)
def api_scan_qrcode(request, pk):
    """
    QR esperado: CODIGO;ETIQUETA;PESO;LOCAL;FORNECEDOR
    - Manual:
        - 'qrcode' sem ';' = ETIQUETA (ex.: 50007)
        - 'codigo_item' (POST) = CÓDIGO DO ITEM (ex.: AACSØ1,20-02)
    - Scanner (com ';'): sempre faz split seguro por ';' (não usa o texto bruto como código).
    """
    if request.method != "POST":
        return HttpResponseForbidden("Método não permitido")

    inv = get_object_or_404(Inventario, pk=pk)

    origem    = (request.POST.get("qrcode") or "").strip()
    qtd_raw   = (request.POST.get("quantidade") or "").strip()
    ordem_raw = (request.POST.get("ordem") or "1").strip()

    codigo_post     = _up(request.POST.get("codigo_item") or "")
    fornecedor_post = _up(request.POST.get("fornecedor") or "")
    local_post      = _up(request.POST.get("localizacao") or "")

    try:
        ordem = int(ordem_raw)
        assert ordem in (1, 2, 3)
    except Exception:
        return JsonResponse({"ok": False, "erro": "Ordem de contagem inválida."}, status=400)

    # -------- Parse ROBUSTO do QR --------
    codigo_qr = etiqueta_qr = local_qr = fornecedor_qr = None
    peso_qr = None

    if ";" in origem:
        # split simples e determinístico
        parts = [p.strip() for p in origem.split(";")]
        if len(parts) >= 1 and parts[0]:
            codigo_qr = _up(parts[0])
        if len(parts) >= 2 and parts[1]:
            etiqueta_qr = _up(parts[1])
        if len(parts) >= 3 and parts[2]:
            peso_qr = _dec(parts[2])
        if len(parts) >= 4 and parts[3]:
            local_qr = _up(parts[3])
        if len(parts) >= 5 and parts[4]:
            fornecedor_qr = _up(parts[4])

    # -------- Resolver campos finais --------
    if ";" not in origem:
        # Manual simples: QR é ETIQUETA; código vem do POST
        etiqueta = _up(origem) if origem else None
        codigo   = codigo_post or None
    else:
        # Estruturado: usa tokens do QR; complementa com POST se faltarem
        etiqueta = etiqueta_qr or None
        codigo   = (codigo_qr or codigo_post or None)

    # Normaliza complemento de local/fornecedor (POST > QR)
    local_final      = local_post or local_qr or ""
    fornecedor_final = fornecedor_post or fornecedor_qr or ""

    # Nunca forçar "código = etiqueta"
    if codigo and etiqueta and codigo == etiqueta:
        # Se por algum motivo vierem iguais, mantemos etiqueta e limpamos código
        codigo = codigo_post or codigo_qr or None

    # Quantidade: POST > peso do QR > 1
    quantidade = _dec(qtd_raw) or (peso_qr if peso_qr is not None else None) or Decimal("1")

    # -------- Resolver/criar item --------
    if etiqueta:
        item = inv.itens.filter(etiqueta=etiqueta).first()
        if not item:
            campos = {
                "inventario": inv,
                "codigo_item": (codigo or ""),
                "etiqueta": etiqueta,
                "unidade": "",
                "local": local_final,
            }
            if hasattr(InventarioItem, "fornecedor"):
                campos["fornecedor"] = fornecedor_final
            item = InventarioItem.objects.create(**campos)
        else:
            updates = []
            if codigo and not item.codigo_item:
                item.codigo_item = codigo; updates.append("codigo_item")
            if local_final and not item.local:
                item.local = local_final; updates.append("local")
            if fornecedor_final and hasattr(item, "fornecedor") and not getattr(item, "fornecedor", ""):
                item.fornecedor = fornecedor_final; updates.append("fornecedor")
            if updates:
                item.save(update_fields=updates)
    else:
        # Sem etiqueta no QR: identifica pelo código do item (se houver)
        item = inv.itens.filter(codigo_item=codigo or "").first() if codigo else None
        if not item:
            campos = {
                "inventario": inv,
                "codigo_item": (codigo or ""),
                "etiqueta": "",
                "unidade": "",
                "local": local_final,
            }
            if hasattr(InventarioItem, "fornecedor"):
                campos["fornecedor"] = fornecedor_final
            item = InventarioItem.objects.create(**campos)
        else:
            updates = []
            if local_final and not item.local:
                item.local = local_final; updates.append("local")
            if fornecedor_final and hasattr(item, "fornecedor") and not getattr(item, "fornecedor", ""):
                item.fornecedor = fornecedor_final; updates.append("fornecedor")
            if updates:
                item.save(update_fields=updates)

    # -------- Dedup --------
    if etiqueta:
        existe = Contagem.objects.filter(
            inventario_item__inventario=inv,
            inventario_item__etiqueta=etiqueta,
            ordem=ordem,
        ).exists()
    else:
        existe = Contagem.objects.filter(inventario_item=item, ordem=ordem).exists()

    if existe:
        return JsonResponse({"ok": False, "erro": f"Etiqueta {etiqueta or 's/etiqueta'} já lida na {ordem}ª contagem."}, status=200)

    # -------- Gravar contagem --------
    Contagem.objects.create(
        inventario_item=item,
        ordem=ordem,
        quantidade=quantidade,
        usuario=request.user,
        origem_qrcode=origem,
    )

    # -------- Avançar status (mesma lógica anterior) --------
    if ordem == 1 and inv.status == "ABERTO":
        inv.status = "EM_CONTAGEM_1"; inv.updated_by = request.user
        inv.save(update_fields=["status", "updated_by"])
    elif ordem == 2 and inv.status in ["ABERTO", "EM_CONTAGEM_1"]:
        inv.status = "EM_CONTAGEM_2"; inv.updated_by = request.user
        inv.save(update_fields=["status", "updated_by"])

    return JsonResponse({
        "ok": True,
        "item": {
            "codigo": item.codigo_item or "",
            "etiqueta": item.etiqueta or "",
            "local": item.local or "",
            "fornecedor": getattr(item, "fornecedor", "") or "",
            "ordem": ordem,
            "quantidade": str(quantidade),
        }
    })



# -----------------------------
# Finalizar contagem (1 ou 2)
# -----------------------------

@login_required
@permission_required("qualidade_fornecimento.view_inventario", raise_exception=True)
def finalizar_contagem(request, pk, ordem):
    inv = get_object_or_404(Inventario, pk=pk)
    ordem = int(ordem)

    if ordem == 1:
        # Finalizou 1ª → vai para 2ª
        if inv.status in ["ABERTO", "EM_CONTAGEM_1"]:
            inv.status = "EM_CONTAGEM_2"
            inv.updated_by = request.user
            inv.save(update_fields=["status", "updated_by"])
            messages.success(request, "1ª contagem finalizada. Status avançou para 2ª contagem.")
    elif ordem == 2:
        # Finalizou 2ª → vai para Conferência
        if inv.status in ["EM_CONTAGEM_2"]:
            inv.status = "EM_CONFERENCIA"
            inv.updated_by = request.user
            inv.save(update_fields=["status", "updated_by"])
            messages.success(request, "2ª contagem finalizada. Status avançou para Confronto/Conferência.")
    else:
        messages.warning(request, "Ordem de contagem inválida.")

    return redirect("inventario_detail", pk=inv.pk)



# inventario_views.py — adicionar abaixo das demais imports
import io, csv
from decimal import Decimal
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import timezone
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.contrib import messages

# opcional: WeasyPrint para PDF (pip install weasyprint)
try:
    from weasyprint import HTML, CSS
    _HAS_WEASY = True
except Exception:
    _HAS_WEASY = False

# -------- Helpers --------
def _pick_inventario_para_exportar(request):
    inv_id = request.GET.get("inv") or request.POST.get("inv")
    if inv_id:
        return get_object_or_404(Inventario, pk=inv_id)
    # Fallback mais robusto: último CONSOLIDADO ou EXPORTADO
    return (
        Inventario.objects
        .filter(status__in=["CONSOLIDADO", "EXPORTADO"])
        .order_by("-consolidado_em", "-criado_em")
        .first()
    )

def _contagem_map(item):
    # exige prefetch de "contagens" para não gerar N+1
    c1 = c2 = c3 = None
    for c in item.contagens.all():
        if c.ordem == 1: c1 = c.quantidade
        elif c.ordem == 2: c2 = c.quantidade
        elif c.ordem == 3: c3 = c.quantidade
    return c1, c2, c3

# -------- CSV --------
@login_required
@permission_required("qualidade_fornecimento.exportar_inventario", raise_exception=True)
def exportar_csv(request):
    inv = _pick_inventario_para_exportar(request)
    if not inv:
        messages.error(request, "Não há inventário consolidado para exportar. Informe ?inv=<id> ou consolide um inventário.")
        return HttpResponseBadRequest("Inventário não encontrado para exportação.")

    itens = (inv.itens
             .prefetch_related("contagens")
             .order_by("codigo_item", "etiqueta"))

    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";", lineterminator="\n")
    w.writerow(["Inventário", "Código", "Etiqueta", "Local", "Fornecedor", "1ª", "2ª", "3ª", "Final"])
    for it in itens:
        c1, c2, c3 = _contagem_map(it)
        w.writerow([
            inv.titulo,
            it.codigo_item or "",
            it.etiqueta or "",
            it.local or "",
            getattr(it, "fornecedor", "") or "",
            c1 if c1 is not None else "",
            c2 if c2 is not None else "",
            c3 if c3 is not None else "",
            it.quantidade_consolidada if it.quantidade_consolidada is not None else "",
        ])

    # salva registro e arquivo
    now = timezone.now()
    fname = f"{slugify(inv.titulo)}_{now:%Y%m%d_%H%M%S}.csv"
    payload = buf.getvalue().encode("utf-8-sig")

    exp = InventarioExportacao.objects.create(
        inventario=inv,
        criado_por=request.user,
        formato="CSV",
    )
    exp.arquivo.save(fname, ContentFile(payload))
    exp.save()

    # devolve download direto
    resp = HttpResponse(payload, content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{fname}"'
    return resp

# -------- PDF --------
@login_required
@permission_required("qualidade_fornecimento.exportar_inventario", raise_exception=True)
def exportar_pdf(request):
    inv = _pick_inventario_para_exportar(request)
    if not inv:
        messages.error(request, "Não há inventário consolidado para exportar. Informe ?inv=<id> ou consolide um inventário.")
        return HttpResponseBadRequest("Inventário não encontrado para exportação.")

    if not _HAS_WEASY:
        return HttpResponseBadRequest(
            "WeasyPrint não está disponível no servidor. Instale com: pip install weasyprint"
        )

    itens = (inv.itens
             .prefetch_related("contagens")
             .order_by("codigo_item", "etiqueta"))

    # monta dados já com c1/c2/c3
    linhas = []
    for it in itens:
        c1, c2, c3 = _contagem_map(it)
        linhas.append({
            "codigo": it.codigo_item or "",
            "etiqueta": it.etiqueta or "",
            "local": it.local or "",
            "fornecedor": getattr(it, "fornecedor", "") or "",
            "c1": c1,
            "c2": c2,
            "c3": c3,
            "final": it.quantidade_consolidada,
        })

    html = render(request, "inventarios/relatorio_pdf.html", {
        "inventario": inv,
        "linhas": linhas,
        "gerado_em": timezone.now(),
    }).content.decode("utf-8")

    # gera PDF
    pdf_bytes = HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()

    now = timezone.now()
    fname = f"{slugify(inv.titulo)}_{now:%Y%m%d_%H%M%S}.pdf"

    # registra e anexa arquivo
    exp = InventarioExportacao.objects.create(
        inventario=inv,
        criado_por=request.user,
        formato="PDF",
    )
    exp.arquivo.save(fname, ContentFile(pdf_bytes))
    exp.save()

    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{fname}"'
    return resp
