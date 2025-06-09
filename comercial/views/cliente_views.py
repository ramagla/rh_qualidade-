from pyexpat.errors import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from comercial.models import Cliente
from comercial.forms.cliente_form import ClienteDocumentoFormSet, ClienteForm
from django.core.paginator import Paginator

from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.shortcuts import render
from comercial.models import Cliente
from comercial.models.clientes import ClienteDocumento

@login_required
@permission_required('comercial.view_cliente', raise_exception=True)
def lista_clientes(request):
    clientes = Cliente.objects.all()

    # Filtros
    razao_social = request.GET.get('razao_social', '')
    cnpj = request.GET.get('cnpj', '')
    status = request.GET.get('status', '')

    if razao_social:
        clientes = clientes.filter(razao_social__icontains=razao_social)

    if cnpj:
        clientes = clientes.filter(cnpj__icontains=cnpj)

    if status:
        clientes = clientes.filter(status=status)

    # Indicadores
    total_clientes = clientes.count()
    total_ativos = clientes.filter(status='Ativo').count()
    total_inativos = clientes.filter(status='Inativo').count()

    # Paginação
    paginator = Paginator(clientes.order_by('razao_social'), 10)  # 10 por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'total_clientes': total_clientes,
        'total_ativos': total_ativos,
        'total_inativos': total_inativos,
    }

    return render(request, 'cadastros/lista_clientes.html', context)

def cadastrar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES)
        formset = ClienteDocumentoFormSet(request.POST, request.FILES, queryset=ClienteDocumento.objects.none())

        if form.is_valid() and formset.is_valid():
            cliente = form.save()

            documentos = formset.save(commit=False)
            for doc in documentos:
                doc.cliente = cliente
                doc.save()

            # Excluir os que foram marcados para remoção
            for deleted_doc in formset.deleted_objects:
                deleted_doc.delete()

            messages.success(request, 'Cliente cadastrado com sucesso.')
            return redirect('lista_clientes')
    else:
        form = ClienteForm()
        formset = ClienteDocumentoFormSet(queryset=ClienteDocumento.objects.none())

    context = {
        'form': form,
        'formset': formset,
        'edicao': False,
    }
    return render(request, 'cadastros/form_clientes.html', context)




@login_required
@permission_required('comercial.change_cliente', raise_exception=True)
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else:
        form = ClienteForm(instance=cliente)

        return render(request, 'cadastros/form_clientes.html', {
        'form': form,
        'edicao': True,
        'url_voltar': 'lista_clientes',  # CERTO! confere com seu urls.py
    })


@login_required
@permission_required('comercial.view_cliente', raise_exception=True)
def visualizar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, 'comercial/clientes_visualizar.html', {'cliente': cliente})

@login_required
@permission_required('comercial.delete_cliente', raise_exception=True)
def excluir_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        return redirect('lista_clientes')
    return render(request, 'comercial/clientes_excluir.html', {'cliente': cliente})
