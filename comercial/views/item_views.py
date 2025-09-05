import pandas as pd
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render

from comercial.forms.item_form import ItemForm
from comercial.models import Item, Cliente, Ferramenta


@login_required
@permission_required('comercial.view_item', raise_exception=True)
def lista_itens(request):
    # 🔍 Filtros
    itens_qs = Item.objects.all().order_by('descricao')

    codigo       = request.GET.get('codigo')
    status       = request.GET.get('status')
    tipo_item    = request.GET.get('tipo_item')      # filtro 1 (já existente)
    tipo_de_peca = request.GET.get('tipo_de_peca')   # filtro 2 (novo)

    if codigo:
        itens_qs = itens_qs.filter(codigo=codigo)

    if status:
        itens_qs = itens_qs.filter(status=status)

    if tipo_item:
        itens_qs = itens_qs.filter(tipo_item=tipo_item)

    if tipo_de_peca:
        itens_qs = itens_qs.filter(tipo_de_peca=tipo_de_peca)

    # 📊 Indicadores
    total_itens = itens_qs.count()
    total_automotivo = itens_qs.filter(automotivo_oem=True).count()
    total_item_seguranca = itens_qs.filter(item_seguranca=True).count()
    total_com_desenho = itens_qs.exclude(desenho='').exclude(desenho__isnull=True).count()

    # 📄 Lista de códigos únicos para o filtro
    codigos_disponiveis = (
        Item.objects
        .exclude(codigo__isnull=True)
        .exclude(codigo="")
        .order_by("codigo")
        .values_list("codigo", flat=True)
        .distinct()
    )

    # 📄 Paginação
    paginator = Paginator(itens_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'total_itens': total_itens,
        'total_automotivo': total_automotivo,
        'total_item_seguranca': total_item_seguranca,
        'total_com_desenho': total_com_desenho,
        'codigos_disponiveis': codigos_disponiveis,
        # ✅ devolve seleções atuais para pré-selecionar no template
        'filtros': {
            'codigo': codigo or '',
            'status': status or '',
            'tipo_item': tipo_item or '',
            'tipo_de_peca': tipo_de_peca or '',
        },
    }

    return render(request, 'cadastros/itens_lista.html', context)




@login_required
@permission_required('comercial.add_item', raise_exception=True)
def cadastrar_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Item cadastrado com sucesso.")
            return redirect('lista_itens')
    else:
        form = ItemForm()

    context = {
        'form': form,
        'edicao': False,
        'titulo_pagina': 'Cadastrar Item',
        'botao_texto': 'Cadastrar'
    }
    return render(request, 'cadastros/form_item.html', context)


@login_required
@permission_required('comercial.change_item', raise_exception=True)
def editar_item(request, pk):
    item = get_object_or_404(Item, pk=pk)

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Item atualizado com sucesso.")
            return redirect('lista_itens')
    else:
        form = ItemForm(instance=item)

    context = {
        'form': form,
        'item': item,
        'edicao': True,
        'titulo_pagina': 'Editar Item',
        'botao_texto': 'Salvar Alterações'
    }
    return render(request, 'cadastros/form_item.html', context)



@login_required
@permission_required('comercial.view_item', raise_exception=True)
def visualizar_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    return render(request, 'cadastros/itens_visualizar.html', {'item': item})


@login_required
@permission_required('comercial.delete_item', raise_exception=True)
def excluir_item(request, pk):
    item = get_object_or_404(Item, pk=pk)

    if request.method == 'POST':
        try:
            item.delete()
            messages.success(request, "✅ Item excluído com sucesso.")
        except ProtectedError:
            messages.error(
                request,
                "❌ Este item não pode ser excluído porque está vinculado a uma Análise Comercial ou outro registro protegido."
            )
        return redirect('lista_itens')

    # Como o modal já envia direto via POST, não precisa renderizar nada aqui
    return redirect('lista_itens')


from decimal import Decimal, InvalidOperation
from django.db import transaction
import pandas as pd

# Mapas e utilitários
_TIPO_ITEM_MAP = {
    "cotacao": "Cotacao",
    "cotação": "Cotacao",
    "corrente": "Corrente",
}

_TIPO_PECA_MAP = {
    "mola": "Mola",
    "estampado": "Estampado",
    "estampa": "Estampado",
    "aramado": "Aramado",
}

_STATUS_MAP = {
    "ativo": "Ativo",
    "inativo": "Inativo",
}

def _to_bool(v):
    if pd.isna(v):
        return False
    s = str(v).strip().lower()
    return s in {"1", "true", "t", "y", "yes", "sim", "s"}

def _to_decimal_percent(v, *, min_allowed=0, max_allowed=100):
    """
    Converte entradas como '15', '9,75', '15%', '  9,75  ' em Decimal(2 casas).
    Ignora lixo e valores fora de faixa para evitar overflow no numeric(5,2).
    """
    if v in (None, "") or (hasattr(pd, "isna") and pd.isna(v)):
        return None

    s = str(v).strip().rstrip("%").strip()
    # mantém apenas dígitos, vírgula, ponto e sinal
    s = re.sub(r"[^0-9\.,\-]", "", s)
    # normaliza: remove milhar e usa ponto como separador decimal
    s = s.replace(".", "").replace(",", ".")

    if not any(ch.isdigit() for ch in s):
        return None

    try:
        val = Decimal(s)
    except Exception:
        return None

    # faixa segura para IPI em %
    if (min_allowed is not None and val < Decimal(min_allowed)) or \
       (max_allowed is not None and val > Decimal(max_allowed)):
        return None

    return val.quantize(Decimal("0.01"))

def _to_int_positive(v):
    if v in (None, "") or pd.isna(v):
        return None
    try:
        n = int(float(v))
        return n if n >= 0 else None
    except (ValueError, TypeError):
        return None

def _norm_choice(value, mapping, default):
    if value in (None, "") or pd.isna(value):
        return default
    return mapping.get(str(value).strip().lower(), default)

def _to_date(v):
    if v in (None, "") or pd.isna(v):
        return None
    try:
        dt = pd.to_datetime(v, dayfirst=False, errors="coerce")
        return dt.date() if pd.notna(dt) else None
    except Exception:
        return None

from decimal import Decimal, InvalidOperation
from django.db import transaction
import pandas as pd
import re

@login_required
@permission_required("comercial.importar_excel_itens", raise_exception=True)
def importar_itens_excel(request):
    if request.method != "POST" or not request.FILES.get("arquivo"):
        return render(request, "cadastros/importacoes/importar_itens.html")

    excel_file = request.FILES["arquivo"]

    try:
        # lê tudo como texto (preserva zeros à esquerda, máscara de CNPJ etc.)
        df = pd.read_excel(excel_file, dtype=str).fillna("")
    except Exception as e:
        messages.error(request, f"Não foi possível ler o arquivo Excel: {e}")
        return redirect("importar_itens_excel")

    # coluna do cliente: aceita "CNPJ do Cliente" (preferido) ou "Cliente"
    possiveis_colunas_cliente = ["CNPJ do Cliente", "Cliente"]
    coluna_cliente = next((c for c in possiveis_colunas_cliente if c in df.columns), None)
    if not coluna_cliente:
        messages.error(
            request,
            "Coluna de cliente não encontrada. Use 'CNPJ do Cliente' (recomendado) ou 'Cliente' na planilha."
        )
        return redirect("importar_itens_excel")

    # obrigatórios
    obrigatorios = ["Código", "Descrição", "NCM", "Lote Mínimo", coluna_cliente]
    ausentes = [c for c in obrigatorios if c not in df.columns]
    if ausentes:
        messages.error(request, f"Coluna(s) obrigatória(s) ausente(s): {', '.join(ausentes)}")
        return redirect("importar_itens_excel")

    # códigos existentes (já normalizados para UPPER pelo save() do modelo)
    codigos_existentes = set(Item.objects.values_list("codigo", flat=True))

    criados = 0
    ignorados_duplicado = 0
    ignorados_sem_cliente = 0
    linhas_invalidas = 0
    ipi_invalidos = 0  # diagnóstico opcional

    with transaction.atomic():
        for _, row in df.iterrows():
            codigo = (row.get("Código") or "").strip().upper()
            if not codigo:
                linhas_invalidas += 1
                continue

            if codigo in codigos_existentes:
                ignorados_duplicado += 1
                continue

            # --- cliente por CNPJ (com máscara ou só dígitos); fallback: razão social ---
            entrada_cliente = (row.get(coluna_cliente) or "").strip()
            cnpj_digitos = re.sub(r"\D", "", entrada_cliente)
            cliente = None
            if cnpj_digitos:
                cliente = Cliente.objects.filter(cnpj__in=[cnpj_digitos, entrada_cliente]).first()
            if not cliente and entrada_cliente:
                cliente = Cliente.objects.filter(razao_social__iexact=entrada_cliente).first()
            if not cliente:
                ignorados_sem_cliente += 1
                continue
            # ---------------------------------------------------------------------------

            # ferramenta (opcional)
            ferramenta_codigo = (row.get("Ferramenta") or "").strip()
            ferramenta = None
            if ferramenta_codigo:
                ferramenta = Ferramenta.objects.filter(codigo__iexact=ferramenta_codigo).first()

            # lote mínimo (obrigatório)
            lote_minimo = _to_int_positive(row.get("Lote Mínimo"))
            if lote_minimo is None:
                linhas_invalidas += 1
                continue

            # IPI robusto (evita overflow no numeric(5,2) do modelo Item.ipi):contentReference[oaicite:2]{index=2}
            ipi_val = _to_decimal_percent(row.get("IPI (%)"))
            if ipi_val is None and (row.get("IPI (%)") or "").strip() != "":
                ipi_invalidos += 1  # havia algo na célula, mas inválido/fora de faixa

            item = Item(
                codigo=codigo,
                descricao=(row.get("Descrição") or "").strip(),
                ncm=(row.get("NCM") or "").strip(),
                lote_minimo=lote_minimo,
                cliente=cliente,
                ferramenta=ferramenta,
                codigo_cliente=(row.get("Código no Cliente") or "").strip(),
                descricao_cliente=(row.get("Descrição no Cliente") or "").strip(),
                ipi=ipi_val,
                tipo_item=_norm_choice(row.get("Tipo de Item"), _TIPO_ITEM_MAP, "Cotacao"),
                tipo_de_peca=_norm_choice(row.get("Tipo de Peça"), _TIPO_PECA_MAP, "Mola"),
                status=_norm_choice(row.get("Status"), _STATUS_MAP, "Ativo"),
                automotivo_oem=_to_bool(row.get("Automotivo OEM")),
                requisito_especifico=_to_bool(row.get("Requisito Específico Cliente?")),
                item_seguranca=_to_bool(row.get("É Item de Segurança?")),
                codigo_desenho=(row.get("Código do Desenho") or "").strip(),
                revisao=(row.get("Revisão") or "").strip(),
                data_revisao=_to_date(row.get("Data da Revisão")),
            )
            item.save()
            codigos_existentes.add(codigo)
            criados += 1

    messages.success(
        request,
        (
            f"Importação concluída. Criados: {criados}. "
            f"Ignorados (código duplicado): {ignorados_duplicado}. "
            f"Ignorados (cliente não encontrado): {ignorados_sem_cliente}. "
            f"Linhas inválidas: {linhas_invalidas}. "
            f"IPI inválidos (descartados): {ipi_invalidos}."
        ),
    )
    return redirect("lista_itens")