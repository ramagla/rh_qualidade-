from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from Funcionario.models import Documento, RevisaoDoc
from Funcionario.forms import DocumentoForm, RevisaoDocForm


from django.core.paginator import Paginator

def lista_documentos(request):
    nome = request.GET.get('nome', '')
    status = request.GET.get('status', '')

    documentos = Documento.objects.all()
    if nome:
        documentos = documentos.filter(nome__icontains=nome)
    if status:
        documentos = documentos.filter(status=status)

    # Nomes únicos para o filtro
    documentos_distinct = Documento.objects.values('nome').distinct()
    status_choices = Documento.STATUS_CHOICES

    # Dados para os cards
    total_documentos = documentos.count()
    total_aprovados = documentos.filter(status='aprovado').count()
    total_em_revisao = documentos.filter(status='em_revisao').count()
    total_inativos = documentos.filter(status='inativo').count()  # Ajustado para 'inativo'

    # Paginação
    paginator = Paginator(documentos, 10)  # 10 documentos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'documentos': page_obj,
        'documentos_distinct': documentos_distinct,
        'status_choices': status_choices,
        'total_documentos': total_documentos,
        'total_aprovados': total_aprovados,
        'total_em_revisao': total_em_revisao,
        'total_inativos': total_inativos,  # Corrigido
    }
    return render(request, 'documentos/lista_documentos.html', context)



def cadastrar_documento(request):
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Documento cadastrado com sucesso!")
            return redirect('lista_documentos')
    else:
        form = DocumentoForm()
    return render(request, 'documentos/cadastrar_documento.html', {'form': form})


def editar_documento(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES, instance=documento)
        if form.is_valid():
            form.save()
            messages.success(request, "Documento atualizado com sucesso!")
            return redirect('lista_documentos')
    else:
        form = DocumentoForm(instance=documento)
    return render(request, 'documentos/editar_documento.html', {'form': form})


def excluir_documento(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)
    documento.delete()
    messages.success(request, "Documento excluído com sucesso!")
    return redirect('lista_documentos')


def historico_documentos(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)
    revisoes = RevisaoDoc.objects.filter(documento=documento, status='ativo')  # Exibe apenas revisões ativas
    return render(request, 'documentos/historico_revisoes.html', {'documento': documento, 'revisoes': revisoes})



def adicionar_documento(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)
    if request.method == "POST":
        form = RevisaoDocForm(request.POST)
        if form.is_valid():
            revisao = form.save(commit=False)
            revisao.documento = documento
            revisao.save()
            messages.success(request, "Revisão adicionada com sucesso.")
            return redirect('historico_documentos', documento_id=documento.id)
    else:
        form = RevisaoDocForm()
    return render(request, 'documentos/adicionar_revisao.html', {'form': form, 'documento': documento})



def excluir_revisao2(request, revisao_id):
    revisao = get_object_or_404(RevisaoDoc, id=revisao_id)
    documento_id = revisao.documento.id  # Salva o ID do documento antes da exclusão
    revisao.delete()  # Exclui a revisão do banco de dados
    messages.success(request, 'Revisão excluída com sucesso.')
    return redirect('historico_documentos', documento_id=documento_id)
