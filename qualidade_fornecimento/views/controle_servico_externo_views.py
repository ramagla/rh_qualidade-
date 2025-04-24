# qualidade_fornecimento/views/controle_servico_externo_views.py

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from qualidade_fornecimento.models.controle_servico_externo import ControleServicoExterno

from django.shortcuts import render, redirect, get_object_or_404
from qualidade_fornecimento.forms.controle_servico_externo_form import ControleServicoExternoForm
from qualidade_fornecimento.models.controle_servico_externo import ControleServicoExterno
from qualidade_fornecimento.forms.controle_servico_externo_form import (
    ControleServicoExternoForm,
    RetornoDiarioFormSet
)

@login_required
def cadastrar_controle_servico_externo(request):
    if request.method == "POST":
        form = ControleServicoExternoForm(request.POST)
        formset = RetornoDiarioFormSet(request.POST, prefix="retornos")

        if form.is_valid() and formset.is_valid():
            servico = form.save(commit=False)
            servico.save()

            formset.instance = servico
            formset.save()

            servico.total = servico.calcular_total()
            servico.status2 = servico.calcular_status2()
            servico.atraso_em_dias = servico.calcular_atraso_em_dias()
            servico.ip = servico.calcular_ip()
            servico.save()

            return redirect("listar_controle_servico_externo")

    else:
        form = ControleServicoExternoForm()
        formset = RetornoDiarioFormSet(prefix="retornos")

    # Pega o status da inspeção relacionada, se existir
    status_inspecao = None
    if 'servico_id' in request.GET:
        try:
            servico = ControleServicoExterno.objects.get(pk=request.GET['servico_id'])
            if hasattr(servico, 'inspecao'):
                status_inspecao = servico.inspecao.status_geral()
        except ControleServicoExterno.DoesNotExist:
            status_inspecao = None

    return render(request, "controle_servico_externo/controle_servico_externo_form.html", {
        "form": form,
        "formset": formset,
        "status_inspecao": status_inspecao
    })


@login_required
def editar_controle_servico_externo(request, id):
    servico = get_object_or_404(ControleServicoExterno, id=id)

    if request.method == "POST":
        form = ControleServicoExternoForm(request.POST, instance=servico)
        formset = RetornoDiarioFormSet(request.POST, instance=servico, prefix="retornos")

        if form.is_valid() and formset.is_valid():
            servico = form.save(commit=False)
            servico.save()

            formset.save()

            # Atualizar campos automáticos
            servico.total = servico.calcular_total()
            servico.status2 = servico.calcular_status2()
            servico.atraso_em_dias = servico.calcular_atraso_em_dias()
            servico.ip = servico.calcular_ip()
            servico.save()

            return redirect("listar_controle_servico_externo")
    else:
        form = ControleServicoExternoForm(instance=servico)
        formset = RetornoDiarioFormSet(instance=servico, prefix="retornos")

    return render(request, "controle_servico_externo/controle_servico_externo_form.html", {
        "form": form,
        "formset": formset
    })

@login_required
def listar_controle_servico_externo(request):
    qs = ControleServicoExterno.objects.all().order_by('-data_envio')

    pedido     = request.GET.get('pedido')
    codigo_bm  = request.GET.get('codigo_bm')
    fornecedor = request.GET.get('fornecedor')
    status2    = request.GET.get('status2')

    if pedido:
        qs = qs.filter(pedido__icontains=pedido)

    if codigo_bm:
        qs = qs.filter(codigo_bm__codigo__icontains=codigo_bm)

    if fornecedor:
        qs = qs.filter(fornecedor__nome__icontains=fornecedor)

    if status2:
        qs = qs.filter(status2=status2)

    paginator = Paginator(qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_enviados  = qs.count()
    total_ok        = qs.filter(status2="OK").count()
    total_pendentes = qs.filter(status2="Atenção Saldo").count()
    total_atrasados = qs.filter(atraso_em_dias__gt=0).count()

    # 🆕 Aqui buscamos somente serviços que ainda NÃO têm inspeção feita
    servicos_disponiveis = ControleServicoExterno.objects.filter(inspecao__isnull=True)

    context = {
        'servicos_paginados': page_obj,
        'total_enviados': total_enviados,
        'total_ok': total_ok,
        'total_pendentes': total_pendentes,
        'total_atrasados': total_atrasados,
        'servicos_disponiveis': servicos_disponiveis,  # Adicionado para o select2 da modal
    }

    return render(request, "controle_servico_externo/controle_servico_externo_list.html", context)


@login_required
def excluir_controle_servico_externo(request, id):
    servico = get_object_or_404(ControleServicoExterno, id=id)

    if request.method == "POST":
        servico.delete()
        return redirect("listar_controle_servico_externo")

    return render(request, "controle_servico_externo/controle_servico_externo_confirm_delete.html", {
        "servico": servico
    })

from django.http import JsonResponse
from qualidade_fornecimento.models import FornecedorQualificado

@login_required
def api_leadtime(request, pk):
    try:
        fornecedor = FornecedorQualificado.objects.get(pk=pk)
        return JsonResponse({"lead_time": fornecedor.lead_time})
    except FornecedorQualificado.DoesNotExist:
        return JsonResponse({"lead_time": None})