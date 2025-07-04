from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from comercial.models import Item
from comercial.forms.item_form import ItemForm


from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.shortcuts import render
from comercial.models import Item

from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.shortcuts import render
from comercial.models import Item


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



from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from comercial.models import Item
from comercial.forms.item_form import ItemForm


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
        item.delete()
        messages.success(request, "Item excluído com sucesso.")
        return redirect('lista_itens')
    return render(request, 'comercial/itens_excluir.html', {'item': item})
