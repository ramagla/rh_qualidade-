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

from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils import timezone
from comercial.models import Cliente

@login_required
@permission_required('comercial.view_cliente', raise_exception=True)
def lista_clientes(request):
    clientes_all = Cliente.objects.all()

    # Parâmetros GET
    razao_social_id = request.GET.get('razao_social')
    cnpj = request.GET.get('cnpj', '')
    status = request.GET.get('status')  # pode ser vazio (Todos)
    tipo_cadastro = request.GET.get('tipo_cadastro', 'Cliente')
    cidade = request.GET.get('cidade', '')
    tipo_cliente = request.GET.get('tipo_cliente', '')  # novo filtro

    cidades_distintas = clientes_all.values_list('cidade', flat=True).distinct().order_by('cidade')

    # Filtros
    qs = clientes_all
    if razao_social_id and razao_social_id.isdigit():
        qs = qs.filter(id=razao_social_id)
    if cnpj:
        qs = qs.filter(cnpj__icontains=cnpj)
    if status:
        qs = qs.filter(status=status)
    else:
        qs = qs.filter(status='Ativo')  # padrão
    if tipo_cadastro:
        qs = qs.filter(tipo_cadastro=tipo_cadastro)
    if cidade:
        qs = qs.filter(cidade__icontains=cidade)
    if tipo_cliente:
        qs = qs.filter(tipo_cliente=tipo_cliente)

    # Indicadores
    clientes_ativos = clientes_all.filter(status='Ativo')
    total_clientes = clientes_ativos.count()  # apenas ativos
    total_automotivo = clientes_ativos.filter(tipo_cliente='Automotivo').count()
    total_nao_automotivo = clientes_ativos.filter(tipo_cliente='Não Automotivo').count()
    total_reposicao = clientes_ativos.filter(tipo_cliente='Reposição').count()

    mes_atual = timezone.now().month
    atualizadas_mes = clientes_ativos.filter(atualizado_em__month=mes_atual).count()
    mes_ano = timezone.now().strftime('%m/%Y')

    ultimo = clientes_all.order_by('-atualizado_em').first()
    ultimo_nome = ultimo.razao_social if ultimo else '-'
    ultimo_data = ultimo.atualizado_em.strftime('%d/%m/%Y %H:%M') if ultimo else '-'
    subtitle_atualizadas = f"Atualizadas em {mes_ano}"

    # Paginação
    paginator = Paginator(qs.order_by('razao_social'), 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'cadastros/lista_clientes.html', {
        'page_obj': page_obj,
        'total_clientes': total_clientes,
        'total_automotivo': total_automotivo,
        'total_nao_automotivo': total_nao_automotivo,
        'total_reposicao': total_reposicao,
        'atualizadas_mes': atualizadas_mes,
        'mes_ano': mes_ano,
        'ultimo_nome': ultimo_nome,
        'ultimo_data': ultimo_data,
        'subtitle_atualizadas': subtitle_atualizadas,
        'clientes_all': clientes_all,
        'cidades_distintas': cidades_distintas,
    })


from django.contrib import messages
from django.shortcuts import render, redirect
from comercial.forms.cliente_form import ClienteForm, ClienteDocumentoFormSet
from comercial.models.clientes import ClienteDocumento

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required, permission_required
from comercial.forms.cliente_form import ClienteForm, ClienteDocumentoFormSet
from comercial.models.clientes import Cliente, ClienteDocumento

@login_required
@permission_required('comercial.add_cliente', raise_exception=True)
def cadastrar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES)
        formset = ClienteDocumentoFormSet(request.POST, request.FILES, queryset=ClienteDocumento.objects.none())

        print("📥 POST recebido no cadastro")
        print("📄 Form válido?", form.is_valid())
        print("📎 Formset válido?", formset.is_valid())

        if form.is_valid() and formset.is_valid():
            try:
                cliente = form.save()

                documentos = formset.save(commit=False)
                for doc in documentos:
                    doc.cliente = cliente
                    doc.save()

                for deleted_doc in formset.deleted_objects:
                    deleted_doc.delete()

                messages.success(request, 'Cliente cadastrado com sucesso.')
                return redirect('lista_clientes')

            except IntegrityError:
                messages.error(request, 'Já existe um cliente com esse CNPJ cadastrado.')

        else:
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
            try:
                cliente = form.save()

                documentos = formset.save(commit=False)
                for doc in documentos:
                    doc.cliente = cliente
                    doc.save()

                for deleted_doc in formset.deleted_objects:
                    deleted_doc.delete()

                messages.success(request, 'Cliente atualizado com sucesso.')
                return redirect('lista_clientes')

            except IntegrityError:
                messages.error(request, 'Já existe outro cliente com esse CNPJ.')

        else:
            if form.errors:
                messages.error(request, 'Erros no formulário. Verifique os campos obrigatórios.')
            if formset.errors:
                messages.warning(request, 'Há erros nos documentos anexados.')

    else:
        form = ClienteForm(instance=cliente)
        formset = ClienteDocumentoFormSet(queryset=ClienteDocumento.objects.filter(cliente=cliente))

    return render(request, 'cadastros/form_clientes.html', {
        'form': form,
        'formset': formset,
        'edicao': True,
        'url_voltar': 'lista_clientes',
    })


from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render
from comercial.models import Cliente

@login_required
@permission_required('comercial.view_cliente', raise_exception=True)
def visualizar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    itens = cliente.itens.all()
    ferramentas = cliente.ferramentas.all()

    return render(request, 'cadastros/clientes_visualizar.html', {
        'cliente': cliente,
        'itens': itens,
        'ferramentas': ferramentas,
    })



@login_required
@permission_required('comercial.delete_cliente', raise_exception=True)
def excluir_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        return redirect('lista_clientes')
    return render(request, 'comercial/clientes_excluir.html', {'cliente': cliente})


from django.http import JsonResponse
from comercial.models import Cliente

# cliente_views.py
def verificar_cnpj_existente(request):
    cnpj = request.GET.get("cnpj")
    existe = Cliente.objects.filter(cnpj=cnpj).exists()
    return JsonResponse({"existe": existe})
