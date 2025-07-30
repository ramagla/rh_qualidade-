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

    codigo = request.GET.get('codigo')
    status = request.GET.get('status')
    tipo_item = request.GET.get('tipo_item')

    if codigo:
        itens_qs = itens_qs.filter(codigo=codigo)

    if status:
        itens_qs = itens_qs.filter(status=status)

    if tipo_item:
        itens_qs = itens_qs.filter(tipo_item=tipo_item)

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
        'codigos_disponiveis': codigos_disponiveis,  # ✅ para o select
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


@login_required
@permission_required("comercial.importar_excel_itens", raise_exception=True)
def importar_itens_excel(request):
    if request.method == "POST" and request.FILES.get("arquivo"):
        excel_file = request.FILES["arquivo"]
        try:
            df = pd.read_excel(excel_file)

            obrigatorios = ["Código", "Descrição", "NCM", "Lote Mínimo", "Cliente"]

            for col in obrigatorios:
                if col not in df.columns:
                    messages.error(request, f"Coluna obrigatória ausente: {col}")
                    return redirect("importar_itens_excel")

            criados = 0
            ignorados = 0

            for _, row in df.iterrows():
                codigo = str(row["Código"]).strip()
                if Item.objects.filter(codigo=codigo).exists():
                    ignorados += 1
                    continue

                cliente = Cliente.objects.filter(razao_social__iexact=row["Cliente"]).first()
                ferramenta = Ferramenta.objects.filter(codigo__iexact=row.get("Ferramenta", "")).first()

                if not cliente:
                    continue  # ignora se cliente não encontrado

                Item.objects.create(
                    codigo=codigo,
                    descricao=row["Descrição"],
                    ncm=row["NCM"],
                    lote_minimo=row["Lote Mínimo"],
                    cliente=cliente,
                    ferramenta=ferramenta,
                    codigo_cliente=row.get("Código no Cliente", ""),
                    descricao_cliente=row.get("Descrição no Cliente", ""),
                    ipi=row.get("IPI (%)", None),
                    tipo_item=row.get("Tipo de Item", "Cotacao"),
                    status=row.get("Status", "Ativo"),
                    automotivo_oem=bool(row.get("Automotivo OEM", False)),
                    requisito_especifico=bool(row.get("Requisito Específico Cliente?", False)),
                    item_seguranca=bool(row.get("É Item de Segurança?", False)),
                    codigo_desenho=row.get("Código do Desenho", ""),
                    revisao=row.get("Revisão", ""),
                    data_revisao=row.get("Data da Revisão", None),
                )
                criados += 1

            messages.success(request, f"Importação concluída: {criados} item(ns) criado(s), {ignorados} ignorados (código duplicado).")
            return redirect("lista_itens")

        except Exception as e:
            messages.error(request, f"Erro ao importar: {e}")
            return redirect("importar_itens_excel")

    return render(request, "cadastros/importacoes/importar_itens.html")

