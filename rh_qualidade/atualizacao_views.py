from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from Funcionario.models import AtualizacaoSistema
from Funcionario.models.atualizacao_sistema import AtualizacaoLida
from rh_qualidade.forms.atualizacao_form import AtualizacaoSistemaForm
from django.core.paginator import Paginator
from django.utils import timezone

from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.files.base import ContentFile


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
        form = AtualizacaoSistemaForm(request.POST, request.FILES)
        if form.is_valid():
            atualizacao = form.save()

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
        form = AtualizacaoSistemaForm(request.POST, request.FILES, instance=atualizacao)

        if form.is_valid():
            if request.POST.get('remover_arquivo_pdf') == '1' and atualizacao.arquivo_pdf:
                atualizacao.arquivo_pdf.delete(save=False)
                atualizacao.arquivo_pdf = None

            atualizacao = form.save()

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



# atualizacao_views.py
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

@require_POST
@login_required
def marcar_atualizacao_lida(request):
    data = json.loads(request.body)
    atualizacao_id = data.get('atualizacao_id')

    try:
        atualizacao = AtualizacaoSistema.objects.get(pk=atualizacao_id)
        AtualizacaoLida.objects.get_or_create(usuario=request.user, atualizacao=atualizacao)
        return JsonResponse({'status': 'ok'})
    except AtualizacaoSistema.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Atualização não encontrada'}, status=404)


# rh_qualidade/atualizacao_views.py
from django.http import JsonResponse
from Funcionario.models import AtualizacaoSistema, AtualizacaoLida

def get_ultima_atualizacao(request):
    if request.user.is_authenticated:
        ultima_atualizacao = AtualizacaoSistema.objects.filter(status='concluido').order_by('-id').first()

        if ultima_atualizacao:
            lida = AtualizacaoLida.objects.filter(usuario=request.user, atualizacao=ultima_atualizacao).exists()

        return JsonResponse({
                'show': not lida,
                'id': ultima_atualizacao.id,  # <<< ADICIONAR AQUI
                'versao': ultima_atualizacao.versao,
                'previa': ultima_atualizacao.previa_versao,
                'pdf_url': ultima_atualizacao.arquivo_pdf.url if ultima_atualizacao.arquivo_pdf else ''
            })


    # Se não autenticado ou não tem atualização
    return JsonResponse({'show': False})

