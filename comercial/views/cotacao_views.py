from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404, redirect
from comercial.models import Cotacao  # Supondo que o model exista
from comercial.forms.cotacoes_form import CotacaoForm
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from django.contrib import messages

from comercial.models import Cotacao, Cliente

User = get_user_model()

@login_required
@permission_required("comercial.view_cotacao", raise_exception=True)
def lista_cotacoes(request):
    """
    Exibe lista de cotações com filtros, indicadores e paginação.
    """
    qs = (
        Cotacao.objects
        .select_related("responsavel", "cliente")
        .all()
        .order_by("-data_abertura")
    )

    # --- Aplicar filtros da offcanvas ---
    data_de = request.GET.get("data_abertura_de")
    if data_de:
        qs = qs.filter(data_abertura__date__gte=data_de)

    data_ate = request.GET.get("data_abertura_ate")
    if data_ate:
        qs = qs.filter(data_abertura__date__lte=data_ate)

    tipo = request.GET.get("tipo")
    if tipo:
        qs = qs.filter(tipo=tipo)

    cliente_id = request.GET.get("cliente")
    if cliente_id:
        qs = qs.filter(cliente_id=cliente_id)

    responsavel_id = request.GET.get("responsavel")
    if responsavel_id:
        qs = qs.filter(responsavel_id=responsavel_id)

    frete = request.GET.get("frete")
    if frete:
        qs = qs.filter(frete=frete)

    # --- Indicadores ---
    total_atualizacao = Cotacao.objects.filter(tipo="Atualização").count()
    total_novos        = Cotacao.objects.filter(tipo="Novo").count()
    total_cotacoes     = Cotacao.objects.count()
    now = timezone.now()
    abertas_mes        = Cotacao.objects.filter(
        data_abertura__year=now.year,
        data_abertura__month=now.month
    ).count()

    # --- Paginação ---
    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # --- Dados para filtros ---
    clientes = Cliente.objects.all().order_by("razao_social")
    usuarios = User.objects.filter(is_active=True).order_by("first_name", "last_name")

    return render(request, "cotacoes/lista_cotacoes.html", {
        "page_obj": page_obj,
        "total_atualizacao": total_atualizacao,
        "total_novos": total_novos,
        "total_cotacoes": total_cotacoes,
        "abertas_mes": abertas_mes,
        "clientes": clientes,
        "usuarios": usuarios,
    })
@login_required
@permission_required('comercial.add_cotacao', raise_exception=True)
def cadastrar_cotacao(request):
    if request.method == 'POST':
        form = CotacaoForm(request.POST, user=request.user)
        if form.is_valid():
            cot = form.save(commit=False)
            cot.created_by = request.user
            cot.updated_by = request.user
            cot.data_abertura = timezone.now()
            cot.save()


            messages.success(request, 'Cotação criada com sucesso.')
            return redirect('lista_cotacoes')
    else:
            form = CotacaoForm(user=request.user)
    return render(request, 'cotacoes/form_cotacao.html', {
        'form': form,
        'cotacao': None,
    })




@login_required
@permission_required('comercial.change_cotacao', raise_exception=True)
def editar_cotacao(request, pk):
    """
    Edita os dados básicos de uma cotação existente.
    """
    cot = get_object_or_404(Cotacao, pk=pk)

    if request.method == 'POST':
        form = CotacaoForm(request.POST, instance=cot, user=request.user)
        if form.is_valid():
            cot = form.save(commit=False)
            cot.updated_by = request.user  # mantém histórico
            # ❌ não reatribui `responsavel` nem `created_by`
            cot.save()
            messages.success(request, 'Cotação atualizada com sucesso.')
            return redirect('lista_cotacoes')
    else:
        form = CotacaoForm(instance=cot, user=request.user)

    return render(request, 'cotacoes/form_cotacao.html', {
        'form': form,
        'cotacao': cot,  # usado no template para exibir botão "Itens"
    })


@login_required
@permission_required("comercial.delete_cotacao", raise_exception=True)
def excluir_cotacao(request, pk):
    cotacao = get_object_or_404(Cotacao, pk=pk)
    cotacao.delete()
    return redirect("lista_cotacoes")

@login_required
@permission_required("comercial.view_cotacao", raise_exception=True)
def visualizar_cotacao(request, pk):
    cotacao = get_object_or_404(Cotacao, pk=pk)
    return render(request, "comercial/cotacoes/visualizar.html", {"cotacao": cotacao})


from django.http import JsonResponse
from comercial.models import Cliente

@login_required
def dados_cliente_ajax(request):
    cliente_id = request.GET.get("cliente_id")
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        return JsonResponse({
            "cond_pagamento": cliente.cond_pagamento or "",
            "icms": float(cliente.icms or 0),
        })
    except Cliente.DoesNotExist:
        return JsonResponse({"cond_pagamento": "", "icms": 0})




