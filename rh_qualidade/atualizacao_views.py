from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from Funcionario.models import AtualizacaoSistema
from rh_qualidade.forms.atualizacao_form import AtualizacaoSistemaForm
from django.core.paginator import Paginator
from django.utils import timezone

from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.files.base import ContentFile

def _gerar_pdf_atualizacao(atualizacao, request):
    logo_url = request.build_absolute_uri(static("logo.png"))

    context = {
        'atualizacao': atualizacao,
        'data_hoje': now(),
        'logo_url': logo_url,
    }

    html_string = render_to_string("configuracoes/atualizacoes/pdf_atualizacao.html", context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri("/"))
    pdf_bytes = html.write_pdf()

    filename = f"Atualizacao_{atualizacao.versao}.pdf"
    atualizacao.arquivo_pdf.save(filename, ContentFile(pdf_bytes))
    atualizacao.save()



@login_required
@permission_required('Funcionario.view_atualizacaosistema', raise_exception=True)
def lista_atualizacoes(request):
    # Busca todas as atualizações ordenadas por previsão (mais recente primeiro)
    atualizacoes_queryset = list(AtualizacaoSistema.objects.all())

    def versao_key(atualizacao):
        return tuple(map(int, atualizacao.versao.split('.')))

    atualizacoes_queryset.sort(key=versao_key, reverse=True)

    # Paginador — padrão do seu sistema (10 itens por página)
    paginator = Paginator(atualizacoes_queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Indicadores (para os cards no topo)
    total_concluidas = AtualizacaoSistema.objects.filter(status='concluido').count()
    total_andamento = AtualizacaoSistema.objects.filter(status='em_andamento').count()
    total_canceladas = AtualizacaoSistema.objects.filter(status='cancelado').count()
    total_proximas = AtualizacaoSistema.objects.filter(previsao__gt=timezone.now().date()).count()

    context = {
        'page_obj': page_obj,
        'total_concluidas': total_concluidas,
        'total_andamento': total_andamento,
        'total_canceladas': total_canceladas,
        'total_proximas': total_proximas,
    }

    return render(request, 'configuracoes/atualizacoes/lista.html', context)



@login_required
@permission_required('Funcionario.add_atualizacaosistema', raise_exception=True)
def cadastrar_atualizacao(request):
    if request.method == 'POST':
        form = AtualizacaoSistemaForm(request.POST)
        if form.is_valid():
            atualizacao = form.save()

            # Gerar PDF após salvar
            _gerar_pdf_atualizacao(atualizacao, request)

            messages.success(request, 'Atualização cadastrada com sucesso.')
            return redirect('lista_atualizacoes')
    else:
        form = AtualizacaoSistemaForm()

    return render(request, 'configuracoes/atualizacoes/form.html', {'form': form, 'edicao': False})


@login_required
@permission_required('Funcionario.change_atualizacaosistema', raise_exception=True)
def editar_atualizacao(request, id):
    atualizacao = get_object_or_404(AtualizacaoSistema, pk=id)

    if request.method == 'POST':
        form = AtualizacaoSistemaForm(request.POST, instance=atualizacao)
        if form.is_valid():
            # Excluir PDF antigo (se existir)
            if atualizacao.arquivo_pdf:
                atualizacao.arquivo_pdf.delete(save=False)

            atualizacao = form.save()

            # Gerar PDF novo
            _gerar_pdf_atualizacao(atualizacao, request)

            messages.success(request, 'Atualização editada com sucesso.')
            return redirect('lista_atualizacoes')
    else:
        form = AtualizacaoSistemaForm(instance=atualizacao)

    return render(request, 'configuracoes/atualizacoes/form.html', {'form': form, 'edicao': True})


@login_required
@permission_required('Funcionario.delete_atualizacaosistema', raise_exception=True)
def excluir_atualizacao(request, id):
    atualizacao = get_object_or_404(AtualizacaoSistema, pk=id)

    if request.method == 'POST':
        # Excluir PDF antes de deletar
        if atualizacao.arquivo_pdf:
            atualizacao.arquivo_pdf.delete(save=False)

        atualizacao.delete()
        messages.success(request, 'Atualização excluída com sucesso.')
        return redirect('lista_atualizacoes')

    # Em caso de GET, redireciona
    return redirect('lista_atualizacoes')


import os
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils.timezone import now
from weasyprint import HTML
from django.core.files.base import ContentFile


from Funcionario.models import AtualizacaoSistema

@login_required
@permission_required('Funcionario.view_atualizacaosistema', raise_exception=True)
def imprimir_atualizacao(request, id):
    atualizacao = get_object_or_404(AtualizacaoSistema, pk=id)

    logo_url = request.build_absolute_uri(static("logo.png"))

    context = {
        'atualizacao': atualizacao,
        'data_hoje': now(),
        'logo_url': logo_url,
    }

    html_string = render_to_string("configuracoes/atualizacoes/pdf_atualizacao.html", context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri("/"))
    pdf_bytes = html.write_pdf()

    # Salvar no campo arquivo_pdf
    filename = f"Atualizacao_{atualizacao.versao}.pdf"
    atualizacao.arquivo_pdf.save(filename, ContentFile(pdf_bytes))
    atualizacao.save()

    # Retornar para download também
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


