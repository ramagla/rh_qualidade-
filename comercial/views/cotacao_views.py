# comercial/views/cotacao_views.py — PARA (trechos relevantes)

from collections import Counter
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import ProtectedError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from comercial.forms.cotacoes_form import CotacaoForm
from comercial.models import Cliente, Cotacao

# 👇 NOVO: imports para alertas
from alerts.models import AlertaConfigurado, AlertaUsuario


User = get_user_model()


def montar_status_analises_por_cotacao(cotacoes):
    from decimal import Decimal
    status_por_cotacao = {}
    total_aprovado_por_cotacao = {}
    completo_por_cotacao = {}

    for cot in cotacoes:
        contagem = Counter()
        total = Decimal("0.00")
        completos = []
        tem_precaculos = False

        for precalc in cot.precalculos.all():
            tem_precaculos = True
            analise = getattr(precalc, "analise_comercial_item", None)
            if analise and analise.status:
                contagem[analise.get_status_display()] += 1
                if analise.status == "aprovado" and precalc.preco_selecionado:
                    total += precalc.preco_selecionado

            dev = getattr(precalc, "desenvolvimento_item", None)
            if dev:
                completos.append(dev.completo)

        status_por_cotacao[cot.id] = dict(contagem)
        total_aprovado_por_cotacao[cot.id] = total
        if not tem_precaculos:
            completo_por_cotacao[cot.id] = None
        else:
            completo_por_cotacao[cot.id] = all(completos) if completos else False

    return status_por_cotacao, total_aprovado_por_cotacao, completo_por_cotacao


def montar_itens_por_cotacao(cotacoes):
    itens_por_cotacao = {}

    for cot in cotacoes:
        itens = []
        for precalc in cot.precalculos.all():
            analise = getattr(precalc, "analise_comercial_item", None)
            if analise:
                itens.append({
                    "item": str(analise.item),
                    "status": analise.get_status_display() if analise.status else "-",
                    "periodicidade": analise.get_periodo_display() if analise.periodo else "-",
                    "qtde_estimada": analise.qtde_estimada or "-",
                })
        itens_por_cotacao[cot.id] = itens

    return itens_por_cotacao


# 👇 NOVO: helper para criar alertas apenas quando a cotação for do tipo "Novo"
def _criar_alertas_cotacao_nova(cot: Cotacao) -> None:
    """
    Cria alertas In-App para destinatários configurados.
    - Tenta usar configurações existentes (SOLICITACAO_COTACAO_MATERIAL/SERVICO).
    - Se não houver configuração ativa, envia ao responsável da cotação.
    """
    cfgs = AlertaConfigurado.objects.filter(
        tipo__in=["SOLICITACAO_COTACAO_MATERIAL", "SOLICITACAO_COTACAO_SERVICO"],
        ativo=True
    )
    destinatarios = set()
    for cfg in cfgs:
        destinatarios.update(cfg.usuarios.all())
        for g in cfg.grupos.all():
            destinatarios.update(g.user_set.all())

    if not destinatarios:
        destinatarios = {cot.responsavel}

    titulo = f"🆕 Cotação #{cot.numero} criada"
    mensagem = (
        f"Cotação #{cot.numero} — {cot.cliente.razao_social} "
        f"(Tipo: {cot.tipo}) criada por "
        f"{(cot.created_by.get_full_name() or cot.created_by.username) if cot.created_by else '—'}."
    )

    for user in destinatarios:
        AlertaUsuario.objects.create(
            usuario=user,
            titulo=titulo,
            mensagem=mensagem,
            tipo="COTACAO_CRIADA",
            referencia_id=cot.id,
            url_destino=f"/comercial/cotacoes/{cot.id}/"
        )


@login_required
@permission_required("comercial.view_cotacao", raise_exception=True)
def lista_cotacoes(request):
    qs = (
        Cotacao.objects
        .select_related("responsavel", "cliente")
        .all()
        .order_by("-data_abertura")
    )

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

    total_atualizacao = Cotacao.objects.filter(tipo="Atualização").count()
    total_novos = Cotacao.objects.filter(tipo="Novo").count()
    total_cotacoes = Cotacao.objects.count()
    now = timezone.now()
    abertas_mes = Cotacao.objects.filter(
        data_abertura__year=now.year,
        data_abertura__month=now.month
    ).count()

    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    cotacoes = page_obj.object_list.select_related("cliente", "responsavel").prefetch_related(
        "precalculos__analise_comercial_item"
    )
    status_analises_dict, total_aprovado_dict, completo_dict = montar_status_analises_por_cotacao(cotacoes)
    itens_por_cotacao = montar_itens_por_cotacao(cotacoes)

    clientes = Cliente.objects.all().order_by("razao_social")
    usuarios = User.objects.filter(
        is_active=True,
        funcionario__local_trabalho__nome__icontains="Comercial",
        funcionario__status="Ativo"
    ).order_by("first_name", "last_name")

    return render(request, "cotacoes/lista_cotacoes.html", {
        "page_obj": page_obj,
        "total_atualizacao": total_atualizacao,
        "total_novos": total_novos,
        "total_cotacoes": total_cotacoes,
        "abertas_mes": abertas_mes,
        "clientes": clientes,
        "usuarios": usuarios,
        "status_analises_dict": status_analises_dict,
        "total_aprovado_dict": total_aprovado_dict,
        "completo_dict": completo_dict,
        "itens_por_cotacao": itens_por_cotacao,
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

            # ✅ Disparar alerta SOMENTE se for do tipo "Novo"
            if cot.tipo == "Novo":
                _criar_alertas_cotacao_nova(cot)

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
    cot = get_object_or_404(Cotacao, pk=pk)

    if request.method == 'POST':
        form = CotacaoForm(request.POST, instance=cot, user=request.user)
        if form.is_valid():
            cot = form.save(commit=False)
            cot.updated_by = request.user
            cot.save()
            messages.success(request, 'Cotação atualizada com sucesso.')
            return redirect('lista_cotacoes')
    else:
        form = CotacaoForm(instance=cot, user=request.user)

    return render(request, 'cotacoes/form_cotacao.html', {
        'form': form,
        'cotacao': cot,
    })


@login_required
@permission_required("comercial.delete_cotacao", raise_exception=True)
def excluir_cotacao(request, pk):
    cotacao = get_object_or_404(Cotacao, pk=pk)
    try:
        cotacao.delete()
        messages.success(request, f"Cotação Nº {cotacao.numero} excluída com sucesso.")
    except ProtectedError:
        messages.error(
            request,
            f"Não é possível excluir a Cotação Nº {cotacao.numero} pois ela está vinculada a outros registros (ex: Pré-Cálculos ou Ordens de Desenvolvimento)."
        )
    return redirect("lista_cotacoes")


@login_required
@permission_required("comercial.view_cotacao", raise_exception=True)
def visualizar_cotacao(request, pk):
    cotacao = get_object_or_404(Cotacao, pk=pk)
    return render(request, "comercial/cotacoes/visualizar.html", {"cotacao": cotacao})


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
