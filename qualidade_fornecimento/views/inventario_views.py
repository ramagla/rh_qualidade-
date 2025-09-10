from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone

from qualidade_fornecimento.models import (
    Inventario, InventarioItem, Contagem, Divergencia, InventarioExportacao
)
from qualidade_fornecimento.forms.inventario_forms import InventarioForm, ContagemForm


# =========================
# Helpers de QR e resolução
# =========================
def _parse_qr(origem: str):
    """
    Espera strings como 'CODIGO;ROLO;PESO;LOCAL;FORNECEDOR'.
    Retorna (codigo, etiqueta) usando os 2 primeiros campos quando disponíveis.
    """
    if not origem:
        return None, None
    partes = [p.strip() for p in str(origem).split(";")]
    if len(partes) >= 2:
        return partes[0], partes[1]  # codigo, rolo/lote
    # fallback: um campo só → trata como etiqueta
    return None, partes[0]


def _resolver_item_por_qr(inv: Inventario, origem: str) -> InventarioItem | None:
    """
    Busca o item do inventário a partir do QR. Se não encontrar, cria um InventarioItem.
    Regra funciona para MP (TB050) e PA (mesmo formato).
    """
    codigo, etiqueta = _parse_qr(origem)

    # 1) Tenta por etiqueta (mais específico)
    if etiqueta:
        it = inv.itens.filter(etiqueta=etiqueta).first()
        if it:
            if codigo and not it.codigo_item:
                it.codigo_item = codigo
                it.save(update_fields=["codigo_item"])
            return it

    # 2) Tenta por código
    if codigo:
        it = inv.itens.filter(codigo_item=codigo).first()
        if it:
            if etiqueta and not it.etiqueta:
                it.etiqueta = etiqueta
                it.save(update_fields=["etiqueta"])
            return it

    # 3) Não achou → cria automaticamente (mantém fluxo ágil de contagem)
    return InventarioItem.objects.create(
        inventario=inv,
        codigo_item=codigo or etiqueta or "DESCONHECIDO",
        etiqueta=etiqueta or "",
        unidade="",
        local="",
    )


# ==========
# List / New
# ==========
@login_required
@permission_required("qualidade_fornecimento.view_inventario", raise_exception=True)
def inventario_list(request):
    qs = Inventario.objects.all().order_by("-criado_em")
    return render(request, "inventarios/inventario_list.html", {"inventarios": qs})


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
@login_required
@permission_required("qualidade_fornecimento.view_inventario", raise_exception=True)
def inventario_detail(request, pk):
    inv = get_object_or_404(Inventario, pk=pk)
    itens = (
        inv.itens
        .select_related()
        .prefetch_related("contagens")
        .all()
        .order_by("codigo_item")
    )

    # Expor contagens para o template
    for it in itens:
        mapa = {c.ordem: c.quantidade for c in it.contagens.all()}
        it.c1 = mapa.get(1)
        it.c2 = mapa.get(2)
        it.c3 = mapa.get(3)

    divergentes = Divergencia.objects.filter(
        inventario_item__inventario=inv, houve_divergencia=True
    )

    return render(request, "inventarios/inventario_detail.html", {
        "inventario": inv,
        "itens": itens,
        "divergentes": divergentes,
    })


# ==================
# Contagens 1 / 2 / 3
# ==================
def _registrar_contagem(inv: Inventario, request, ordem_contagem: int):
    if inv.status not in ["ABERTO", "EM_CONTAGEM_1", "EM_CONTAGEM_2"] and ordem_contagem != 3:
        messages.warning(request, "Inventário não está em fase de contagem.")
        return redirect("inventario_detail", pk=inv.pk)

    if request.method == "POST":
        form = ContagemForm(request.POST)
        if form.is_valid():
            origem = form.cleaned_data["origem_qrcode"]
            qtd = form.cleaned_data["quantidade"]

            # Resolver item automaticamente pelo QR (CODIGO;ROLO;...)
            item = _resolver_item_por_qr(inv, origem)
            if not item:
                messages.error(request, "Não foi possível identificar a etiqueta/item a partir do QR.")
                return redirect(request.path)

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
    # Monta/atualiza Divergências com base nas contagens 1 e 2
    for item in inv.itens.all():
        c1 = item.contagens.filter(ordem=1).first()
        c2 = item.contagens.filter(ordem=2).first()
        if not (c1 and c2):
            continue
        houve_div = (c1.quantidade != c2.quantidade)
        div, _ = Divergencia.objects.get_or_create(inventario_item=item)
        div.qtd_contagem1 = c1.quantidade
        div.qtd_contagem2 = c2.quantidade
        div.houve_divergencia = houve_div
        div.save()

    inv.status = "EM_CONFERENCIA"
    inv.updated_by = request.user
    inv.save(update_fields=["status", "updated_by"])

    divergentes = Divergencia.objects.filter(inventario_item__inventario=inv, houve_divergencia=True)
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
        qtd = request.POST.get("qtd")
        justificativa = request.POST.get("justificativa", "")
        item = get_object_or_404(InventarioItem, pk=item_id, inventario=inv)

        Contagem.objects.update_or_create(
            inventario_item=item,
            ordem=3,
            defaults={"quantidade": Decimal(qtd), "usuario": request.user, "origem_qrcode": "AJUSTE_MANUAL"},
        )

        div = getattr(item, "divergencia", None)
        if div:
            div.qtd_contagem3 = Decimal(qtd)
            div.resolvido_por_ajuste = True
            div.justificativa_ajuste = justificativa
            div.resolvido_em = timezone.now()
            div.resolvido_por = request.user
            div.houve_divergencia = False
            div.save()

        messages.success(request, "Ajuste aplicado.")
        return redirect("inventario_confronto", pk=inv.pk)

    # GET
    divergentes = Divergencia.objects.filter(inventario_item__inventario=inv, houve_divergencia=True)
    return render(request, "inventarios/inventario_divergencias.html", {
        "inventario": inv,
        "divergentes": divergentes,
    })


# ===========
# Consolidação
# ===========
from django.views.decorators.http import require_POST

@login_required
@permission_required("qualidade_fornecimento.consolidar_inventario", raise_exception=True)
def inventario_consolidar_confirm(request, pk):
    inv = get_object_or_404(Inventario, pk=pk)
    divergentes = Divergencia.objects.filter(inventario_item__inventario=inv, houve_divergencia=True).count()
    # quantidade de itens e cobertura de contagens (opcional, só para informar)
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

@login_required
@permission_required("qualidade_fornecimento.consolidar_inventario", raise_exception=True)
@require_POST
def inventario_consolidar(request, pk):
    inv = get_object_or_404(Inventario, pk=pk)

    # Bloqueia se houver divergências não resolvidas
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



# ===========
# Exportação
# ===========
@login_required
@permission_required("qualidade_fornecimento.exportar_inventario", raise_exception=True)
def inventario_exportar(request, pk):
    inv = get_object_or_404(Inventario, pk=pk)

    # Geração de CSV simplificado para ERP
    import csv, io
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=';')
    w.writerow(["CODIGO_ITEM", "ETIQUETA", "QTD_CONSOLIDADA", "UNIDADE", "LOCAL", "DATA_CORTE"])
    for it in inv.itens.order_by("codigo_item"):
        w.writerow([
            it.codigo_item,
            it.etiqueta,
            it.quantidade_consolidada or "",
            it.unidade,
            it.local,
            inv.data_corte.isoformat()
        ])
    content = buf.getvalue().encode("utf-8-sig")

    exp = InventarioExportacao.objects.create(inventario=inv, criado_por=request.user, formato="CSV")

    from django.core.files.base import ContentFile
    exp.arquivo.save(
        f"inventario_{inv.pk}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv",
        ContentFile(content)
    )
    exp.save()

    inv.status = "EXPORTADO"
    inv.updated_by = request.user
    inv.save(update_fields=["status", "updated_by"])

    messages.success(request, "Arquivo de inventário gerado e salvo no histórico.")
    return redirect("inventario_exportacoes")


@login_required
@permission_required("qualidade_fornecimento.view_inventarioexportacao", raise_exception=True)
def inventario_exportacoes(request):
    rows = InventarioExportacao.objects.select_related("inventario").order_by("-criado_em")
    return render(request, "inventarios/inventario_exportacoes.html", {"exportacoes": rows})


# ===========
# API de Scan
# ===========
from decimal import Decimal, InvalidOperation
# ... (demais imports permanecem)

# ---------- helpers p/ QR ----------
def _to_decimal_safe(value, default=None):
    if value is None:
        return default
    try:
        return Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError):
        return default

def _parse_qr(origem: str):
    """
    Formato TB050 (ex.): CODIGO;ROLO;PESO;LOCAL;FORNECEDOR
    Retorna (codigo, etiqueta, peso_dec_or_None)
    """
    if not origem:
        return None, None, None
    partes = [p.strip() for p in str(origem).split(";")]
    codigo = partes[0] if len(partes) >= 1 else None
    etiqueta = partes[1] if len(partes) >= 2 else None
    peso = _to_decimal_safe(partes[2], None) if len(partes) >= 3 else None
    return codigo, etiqueta, peso

def _resolver_item_por_qr(inv: Inventario, origem: str) -> InventarioItem | None:
    codigo, etiqueta, _ = _parse_qr(origem)
    if etiqueta:
        it = inv.itens.filter(etiqueta=etiqueta).first()
        if it:
            if codigo and not it.codigo_item:
                it.codigo_item = codigo
                it.save(update_fields=["codigo_item"])
            return it
    if codigo:
        it = inv.itens.filter(codigo_item=codigo).first()
        if it:
            if etiqueta and not it.etiqueta:
                it.etiqueta = etiqueta
                it.save(update_fields=["etiqueta"])
            return it
    return InventarioItem.objects.create(
        inventario=inv,
        codigo_item=codigo or etiqueta or "DESCONHECIDO",
        etiqueta=etiqueta or "",
        unidade="",
        local="",
    )

# ---------- API AJAX chamada a cada leitura ----------
@login_required
@permission_required("qualidade_fornecimento.view_inventario", raise_exception=True)
def api_scan_qrcode(request, pk):
    if request.method != "POST":
        return HttpResponseForbidden("Método não permitido")

    inv = get_object_or_404(Inventario, pk=pk)
    origem = request.POST.get("qrcode", "")  # valor integral do QR
    ordem = int(request.POST.get("ordem", "1"))

    # quantidade enviada pelo front (opcional); se ausente, usa o peso do QR; se ausente também, usa 1
    quantidade_raw = request.POST.get("quantidade", "").strip()
    _, _, peso_qr = _parse_qr(origem)
    quantidade = _to_decimal_safe(quantidade_raw, None) or peso_qr or Decimal("1")

    # segurança mínima
    if ordem not in (1, 2, 3):
        return JsonResponse({"ok": False, "erro": "Ordem de contagem inválida."}, status=400)

    # resolve/cria item pelo QR
    item = _resolver_item_por_qr(inv, origem)
    if not item:
        return JsonResponse({"ok": False, "erro": "Não foi possível identificar a etiqueta/item."}, status=400)

    # grava a contagem (idempotente por item+ordem; última leitura prevalece)
    Contagem.objects.update_or_create(
        inventario_item=item,
        ordem=ordem,
        defaults={"quantidade": quantidade, "usuario": request.user, "origem_qrcode": origem},
    )

    # avança status automaticamente na 1ª/2ª contagem
    if ordem == 1 and inv.status == "ABERTO":
        inv.status = "EM_CONTAGEM_1"
        inv.updated_by = request.user
        inv.save(update_fields=["status", "updated_by"])
    elif ordem == 2 and inv.status in ["ABERTO", "EM_CONTAGEM_1"]:
        inv.status = "EM_CONTAGEM_2"
        inv.updated_by = request.user
        inv.save(update_fields=["status", "updated_by"])

    return JsonResponse({"ok": True})

# ---------- finalizar a contagem (1 ou 2) ----------
@login_required
@permission_required("qualidade_fornecimento.view_inventario", raise_exception=True)
def finalizar_contagem(request, pk, ordem):
    inv = get_object_or_404(Inventario, pk=pk)
    if request.method != "POST":
        return HttpResponseForbidden("Método não permitido")

    if ordem == 1:
        if inv.status in ["ABERTO", "EM_CONTAGEM_1"]:
            inv.status = "EM_CONTAGEM_2"
            inv.updated_by = request.user
            inv.save(update_fields=["status", "updated_by"])
            messages.success(request, "1ª contagem finalizada. Você já pode iniciar a 2ª contagem.")
    elif ordem == 2:
        if inv.status == "EM_CONTAGEM_2":
            inv.status = "EM_CONFERENCIA"
            inv.updated_by = request.user
            inv.save(update_fields=["status", "updated_by"])
            messages.success(request, "2ª contagem finalizada. Vá para Confronto.")
    else:
        messages.error(request, "Ordem inválida.")

    return redirect("inventario_detail", pk=inv.pk)
