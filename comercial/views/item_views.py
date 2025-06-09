from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from comercial.models import Item
from comercial.forms.item_form import ItemForm

@login_required
@permission_required('comercial.view_item', raise_exception=True)
def lista_itens(request):
    itens = Item.objects.all().order_by('descricao')
    return render(request, 'comercial/itens_lista.html', {'itens': itens})

@login_required
@permission_required('comercial.add_item', raise_exception=True)
def cadastrar_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_itens')
    else:
        form = ItemForm()

    return render(request, 'comercial/itens_form.html', {'form': form, 'edicao': False})

@login_required
@permission_required('comercial.change_item', raise_exception=True)
def editar_item(request, pk):
    item = get_object_or_404(Item, pk=pk)

    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('lista_itens')
    else:
        form = ItemForm(instance=item)

    return render(request, 'comercial/itens_form.html', {'form': form, 'item': item, 'edicao': True})

@login_required
@permission_required('comercial.view_item', raise_exception=True)
def visualizar_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    return render(request, 'comercial/itens_visualizar.html', {'item': item})

@login_required
@permission_required('comercial.delete_item', raise_exception=True)
def excluir_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        item.delete()
        return redirect('lista_itens')
    return render(request, 'comercial/itens_excluir.html', {'item': item})
