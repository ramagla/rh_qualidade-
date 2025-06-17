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
from django.utils import timezone

@login_required
@permission_required('comercial.view_cliente', raise_exception=True)
def lista_clientes(request):
    qs           = Cliente.objects.all()
    razao_social = request.GET.get('razao_social', '')
    cnpj         = request.GET.get('cnpj', '')
    status       = request.GET.get('status', '')

    if razao_social:
        qs = qs.filter(razao_social__icontains=razao_social)
    if cnpj:
        qs = qs.filter(cnpj__icontains=cnpj)
    if status:
        qs = qs.filter(status=status)

    # Indicadores fixos
    total_clientes = qs.count()
    total_ativos   = qs.filter(status='Ativo').count()
    total_inativos = qs.filter(status='Inativo').count()

    # “Atualizadas este Mês”
    mes_atual        = timezone.now().month
    atualizadas_mes  = qs.filter(atualizado_em__month=mes_atual).count()
    mes_ano          = timezone.now().strftime('%m/%Y')

    # “Última Alteração”
    ultimo = qs.order_by('-atualizado_em').first()
    if ultimo:
        ultimo_nome = ultimo.razao_social
        ultimo_data = ultimo.atualizado_em.strftime('%d/%m/%Y %H:%M')
    else:
        ultimo_nome = '-'
        ultimo_data = '-'
    
    subtitle_atualizadas = f"Atualizadas em {mes_ano}"

    # Paginação
    paginator   = Paginator(qs.order_by('razao_social'), 10)
    page_obj    = paginator.get_page(request.GET.get('page'))

    return render(request, 'cadastros/lista_clientes.html', {
        'page_obj':        page_obj,
        'total_clientes':  total_clientes,
        'total_ativos':    total_ativos,
        'total_inativos':  total_inativos,
        'atualizadas_mes': atualizadas_mes,
        'mes_ano':         mes_ano,
        'ultimo_nome':     ultimo_nome,
        'ultimo_data':     ultimo_data,
        'subtitle_atualizadas': subtitle_atualizadas,

    })


from django.contrib import messages
from django.shortcuts import render, redirect
from comercial.forms.cliente_form import ClienteForm, ClienteDocumentoFormSet
from comercial.models.clientes import ClienteDocumento

def cadastrar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES)
        formset = ClienteDocumentoFormSet(request.POST, request.FILES, queryset=ClienteDocumento.objects.none())

        # Diagnóstico: mostra no terminal se algo estiver inválido
        print("📥 POST recebido no cadastro")
        print("📄 Form válido?", form.is_valid())
        print("📎 Formset válido?", formset.is_valid())

        if form.is_valid() and formset.is_valid():
            cliente = form.save()

            documentos = formset.save(commit=False)
            for doc in documentos:
                doc.cliente = cliente
                doc.save()

            # Excluir os que foram marcados para remoção (em cadastro normalmente vazio)
            for deleted_doc in formset.deleted_objects:
                deleted_doc.delete()

            messages.success(request, 'Cliente cadastrado com sucesso.')
            return redirect('lista_clientes')
        else:
            # Exibe mensagens de erro na interface
            if form.errors:
                messages.error(request, 'Erros no formulário. Verifique os campos obrigatórios.')
            if formset.errors:
                messages.warning(request, 'Há erros nos documentos anexados.')

    else:
        form = ClienteForm()
        formset = ClienteDocumentoFormSet(queryset=ClienteDocumento.objects.none())

    context = {
        'form': form,
        'formset': formset,
        'edicao': False,
        'url_voltar': 'lista_clientes'
    }
    return render(request, 'cadastros/form_clientes.html', context)





@login_required
@permission_required('comercial.change_cliente', raise_exception=True)
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES, instance=cliente)
        formset = ClienteDocumentoFormSet(request.POST, request.FILES, queryset=ClienteDocumento.objects.filter(cliente=cliente))

        if form.is_valid() and formset.is_valid():
            cliente = form.save()

            documentos = formset.save(commit=False)
            for doc in documentos:
                doc.cliente = cliente
                doc.save()

            for deleted_doc in formset.deleted_objects:
                deleted_doc.delete()

            messages.success(request, 'Cliente atualizado com sucesso.')
            return redirect('lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
        formset = ClienteDocumentoFormSet(queryset=ClienteDocumento.objects.filter(cliente=cliente))

    return render(request, 'cadastros/form_clientes.html', {
        'form': form,
        'formset': formset,
        'edicao': True,
        'url_voltar': 'lista_clientes',
    })


@login_required
@permission_required('comercial.view_cliente', raise_exception=True)
def visualizar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    print(f"ICMS do cliente {cliente.razao_social}: {cliente.icms}")
    print(f"IPI do cliente {cliente.razao_social}: {cliente.ipi}")
    print(f"Observação do cliente {cliente.razao_social}: {cliente.observacao}") # Verifique a observação também

    return render(request, 'cadastros/clientes_visualizar.html', {'cliente': cliente})

@login_required
@permission_required('comercial.delete_cliente', raise_exception=True)
def excluir_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        return redirect('lista_clientes')
    return render(request, 'comercial/clientes_excluir.html', {'cliente': cliente})
