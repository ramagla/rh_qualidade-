import pandas as pd

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

def _to_decimal(v):
    if v in (None, "") or pd.isna(v):
        return None
    s = str(v).strip().replace(".", "").replace(",", ".") if isinstance(v, str) else str(v)
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None

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

@login_required
@permission_required("comercial.importar_excel_itens", raise_exception=True)
def importar_itens_excel(request):
    if request.method != "POST" or not request.FILES.get("arquivo"):
        return render(request, "cadastros/importacoes/importar_itens.html")

    excel_file = request.FILES["arquivo"]

    try:
        df = pd.read_excel(excel_file)
    except Exception as e:
        messages.error(request, f"Não foi possível ler o arquivo Excel: {e}")
        return redirect("importar_itens_excel")

    obrigatorios = ["Código", "Descrição", "NCM", "Lote Mínimo", "Cliente"]
    ausentes = [c for c in obrigatorios if c not in df.columns]
    if ausentes:
        messages.error(request, f"Coluna(s) obrigatória(s) ausente(s): {', '.join(ausentes)}")
        return redirect("importar_itens_excel")

    # Normalização prévia dos códigos existentes (já salvos em MAIÚSCULO pelo save())
    codigos_existentes = set(Item.objects.values_list("codigo", flat=True))

    criados = 0
    ignorados_duplicado = 0
    ignorados_sem_cliente = 0
    linhas_invalidas = 0

    with transaction.atomic():
        for _, row in df.iterrows():
            codigo = str(row["Código"]).strip().upper()
            if not codigo:
                linhas_invalidas += 1
                continue

            if codigo in codigos_existentes:
                ignorados_duplicado += 1
                continue

            # Cliente
            cliente_nome = str(row["Cliente"]).strip()
            cliente = Cliente.objects.filter(razao_social__iexact=cliente_nome).first()
            if not cliente:
                ignorados_sem_cliente += 1
                continue

            # Ferramenta (opcional)
            ferramenta_codigo = str(row.get("Ferramenta", "") or "").strip()
            ferramenta = None
            if ferramenta_codigo:
                ferramenta = Ferramenta.objects.filter(codigo__iexact=ferramenta_codigo).first()

            lote_minimo = _to_int_positive(row["Lote Mínimo"])
            if lote_minimo is None:
                linhas_invalidas += 1
                continue

            item = Item(
                codigo=codigo,
                descricao=str(row["Descrição"]).strip() if not pd.isna(row["Descrição"]) else "",
                ncm=str(row["NCM"]).strip() if not pd.isna(row["NCM"]) else "",
                lote_minimo=lote_minimo,
                cliente=cliente,
                ferramenta=ferramenta,
                codigo_cliente=str(row.get("Código no Cliente", "") or "").strip(),
                descricao_cliente=str(row.get("Descrição no Cliente", "") or "").strip(),
                ipi=_to_decimal(row.get("IPI (%)", None)),
                tipo_item=_norm_choice(row.get("Tipo de Item", None), _TIPO_ITEM_MAP, "Cotacao"),
                tipo_de_peca=_norm_choice(row.get("Tipo de Peça", None), _TIPO_PECA_MAP, "Mola"),
                status=_norm_choice(row.get("Status", None), _STATUS_MAP, "Ativo"),
                automotivo_oem=_to_bool(row.get("Automotivo OEM", False)),
                requisito_especifico=_to_bool(row.get("Requisito Específico Cliente?", False)),
                item_seguranca=_to_bool(row.get("É Item de Segurança?", False)),
                codigo_desenho=str(row.get("Código do Desenho", "") or "").strip(),
                revisao=str(row.get("Revisão", "") or "").strip(),
                data_revisao=_to_date(row.get("Data da Revisão", None)),
            )
            # O save() já normaliza campos em maiúsculo onde aplicável
            item.save()
            codigos_existentes.add(codigo)
            criados += 1

    messages.success(
        request,
        (
            f"Importação concluída. Criados: {criados}. "
            f"Ignorados (código duplicado): {ignorados_duplicado}. "
            f"Ignorados (cliente não encontrado): {ignorados_sem_cliente}. "
            f"Linhas inválidas: {linhas_invalidas}."
        ),
    )
    return redirect("lista_itens")
