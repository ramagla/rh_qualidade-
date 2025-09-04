from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from comercial.forms.cliente_form import ClienteDocumentoFormSet, ClienteForm
from comercial.models import Cliente
from comercial.models.clientes import ClienteDocumento

import pandas as pd


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
    cod_bm = request.GET.get('cod_bm', '')  # 👈 novo parâmetro

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
    if cod_bm:  # 👈 aplica o novo filtro
        qs = qs.filter(cod_bm__icontains=cod_bm)

    # Indicadores
    clientes_indicadores = qs.filter(tipo_cadastro="Cliente", status__in=["Ativo", "Reativado"])
    total_clientes = clientes_indicadores.count()
    total_automotivo = clientes_indicadores.filter(tipo_cliente='Automotivo').count()
    total_nao_automotivo = clientes_indicadores.filter(tipo_cliente='Não Automotivo').count()
    total_reposicao = clientes_indicadores.filter(tipo_cliente='Reposição').count()

    mes_atual = timezone.now().month
    atualizadas_mes = clientes_indicadores.filter(atualizado_em__month=mes_atual).count()

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
import logging


# Configura logger para debug
logger = logging.getLogger(__name__)

@login_required
@permission_required('comercial.change_cliente', raise_exception=True)
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == 'POST':
        mgmt_keys = [
            'form-TOTAL_FORMS', 'form-INITIAL_FORMS',
            'form-MIN_NUM_FORMS', 'form-MAX_NUM_FORMS'
        ]
        mgmt = {k: request.POST.get(k) for k in mgmt_keys}
        print("Management form data:", mgmt)

        form = ClienteForm(request.POST, request.FILES, instance=cliente)
        formset = ClienteDocumentoFormSet(
            request.POST, request.FILES,
            queryset=ClienteDocumento.objects.filter(cliente=cliente)
        )

        is_form_valid = form.is_valid()
        is_formset_valid = formset.is_valid()
        print("Form valid?:", is_form_valid)
        print("Form errors:", form.errors)
        print("Formset valid?:", is_formset_valid)
        print("Formset errors:", formset.errors)

        deleted_forms = [
            f for f in formset.forms
            if f.cleaned_data.get('DELETE')
        ]
        print("Forms marcados para deleção:", deleted_forms)

        if is_form_valid and is_formset_valid:
            try:
                cliente = form.save()

                documentos = formset.save(commit=False)
                for doc in documentos:
                    doc.cliente = cliente
                    doc.save()

                for f in deleted_forms:
                    arquivo = f.cleaned_data.get('arquivo')
                    if not arquivo:
                        f.instance.delete()

                messages.success(request, 'Cliente atualizado com sucesso.')
                print("===== FIM editar_cliente (POST): SUCESSO =====")
                return redirect('lista_clientes')

            except IntegrityError:
                messages.error(request, 'Já existe outro cliente com esse CNPJ.')
                print("===== FIM editar_cliente (POST): ERRO DE INTEGRIDADE =====")

        else:
            if form.errors:
                messages.error(request, 'Erros no formulário. Verifique os campos obrigatórios.')
            if formset.errors:
                messages.warning(request, 'Há erros nos documentos anexados.')
            print("===== FIM editar_cliente (POST): VALIDAÇÃO FALHOU =====")

    else:
        form = ClienteForm(instance=cliente)
        formset = ClienteDocumentoFormSet(queryset=ClienteDocumento.objects.filter(cliente=cliente))

    print("⚠️ Dados do cliente carregados para edição:")
    print("CNPJ:", form.instance.cnpj)
    print("Razão Social:", form.instance.razao_social)
    print("Cidade:", form.instance.cidade)

    return render(request, 'cadastros/form_clientes.html', {
        'form': form,
        'formset': formset,
        'edicao': True,
        'cliente': cliente,
        'url_voltar': 'lista_clientes',
    })




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



@permission_required("comercial.delete_cliente")
def excluir_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == "POST":
        try:
            cliente.delete()
            messages.success(request, "✅ Cliente excluído com sucesso.")
        except ProtectedError:
            messages.error(
                request,
                "❌ Este cliente não pode ser excluído pois está vinculado a registros no sistema (como cotações, análises ou itens)."
            )
        return redirect("lista_clientes")



# cliente_views.py
def verificar_cnpj_existente(request):
    cnpj = request.GET.get("cnpj")
    cliente_id = request.GET.get("cliente_id")

    if not cnpj:
        return JsonResponse({"existe": False})

    qs = Cliente.objects.filter(cnpj=cnpj)
    if cliente_id:
        qs = qs.exclude(id=cliente_id)

    return JsonResponse({"existe": qs.exists()})


@login_required
@permission_required("comercial.importar_excel_clientes", raise_exception=True)
def importar_clientes_excel(request):
    if request.method == "POST" and request.FILES.get("arquivo"):
        excel_file = request.FILES["arquivo"]
        try:
            df = pd.read_excel(excel_file)

            obrigatorios = ["Razão Social", "Nome Fantasia", "CNPJ", "Endereço", "Número", "Bairro", "Cidade", "CEP", "UF", "Tipo Cliente"]

            for col in obrigatorios:
                if col not in df.columns:
                    messages.error(request, f"Coluna obrigatória ausente: {col}")
                    return redirect("importar_clientes_excel")

            criados = 0
            ignorados = 0

            for _, row in df.iterrows():
                cnpj = str(row["CNPJ"]).strip()
                if Cliente.objects.filter(cnpj=cnpj).exists():
                    ignorados += 1
                    continue

                Cliente.objects.create(
                    razao_social=row["Razão Social"],
                    nome_fantasia=row.get("Nome Fantasia", ""),
                    cnpj=cnpj,
                    endereco=row["Endereço"],
                    numero=str(row["Número"]),
                    bairro=row["Bairro"],
                    cidade=row["Cidade"],
                    cep=row["CEP"],
                    uf=row["UF"],
                    tipo_cliente=row["Tipo Cliente"],  # deve estar em conformidade com os choices
                    tipo_cadastro=row.get("Tipo Cadastro", "Cliente"),
                    telefone=row.get("Telefone", ""),
                    email=row.get("Email", ""),
                    status=row.get("Status", "Ativo"),
                    ie=row.get("IE", ""),
                    complemento=row.get("Complemento", ""),
                    nome_contato=row.get("Contato Nome", ""),
                    email_contato=row.get("Contato Email", ""),
                    telefone_contato=row.get("Contato Telefone", ""),
                    cargo_contato=row.get("Contato Cargo", ""),
                    departamento_contato=row.get("Contato Departamento", ""),
                    icms=row.get("ICMS", None),
                    cfop=row.get("CFOP", ""),
                    cond_pagamento=row.get("Cond Pagamento", ""),
                    cod_bm=row.get("Cod BM", ""),
                )
                criados += 1

            messages.success(request, f"Importação concluída: {criados} cliente(s) criados, {ignorados} ignorados (CNPJ duplicado).")
            return redirect("lista_clientes")

        except Exception as e:
            messages.error(request, f"Erro ao importar: {e}")
            return redirect("importar_clientes_excel")

    return render(request, "cadastros/importacoes/importar_clientes.html")