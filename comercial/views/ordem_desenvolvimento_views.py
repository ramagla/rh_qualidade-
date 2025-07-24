from datetime import timezone
from pyexpat.errors import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from comercial.forms.ordem_desenvolvimento_form import OrdemDesenvolvimentoForm
from comercial.models import OrdemDesenvolvimento
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.shortcuts import render
from comercial.models import OrdemDesenvolvimento
from comercial.models.clientes import Cliente
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.utils.timezone import make_aware
from datetime import datetime

from comercial.models import OrdemDesenvolvimento, Cliente
@login_required
@permission_required("comercial.view_ordemdesenvolvimento", raise_exception=True)
def lista_ordens_desenvolvimento(request):
    ordens = OrdemDesenvolvimento.objects.select_related("item", "cliente").all()

    # Filtros
    data_de = request.GET.get("data_criacao_de")
    data_ate = request.GET.get("data_criacao_ate")
    cliente_id = request.GET.get("cliente")
    razao = request.GET.get("razao")
    oem = request.GET.get("oem")
    metodologia = request.GET.get("metodologia")

    if data_de:
        try:
            data_inicio = make_aware(datetime.strptime(data_de, "%Y-%m-%d"))
            ordens = ordens.filter(created_at__gte=data_inicio)
        except:
            pass

    if data_ate:
        try:
            data_fim = make_aware(datetime.strptime(data_ate, "%Y-%m-%d"))
            ordens = ordens.filter(created_at__lte=data_fim)
        except:
            pass

    if cliente_id:
        ordens = ordens.filter(cliente_id=cliente_id)

    if razao:
        ordens = ordens.filter(razao=razao)

    if oem in ["0", "1"]:
        ordens = ordens.filter(automotivo_oem=bool(int(oem)))

    if metodologia:
        ordens = ordens.filter(metodologia_aprovacao__icontains=metodologia)

    # Ordenação
    ordens = ordens.order_by("-numero")

    # Paginação
    paginator = Paginator(ordens, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Indicadores
    total_ordens = ordens.count()
    total_com_amostra = ordens.exclude(qtde_amostra__isnull=True).count()
    total_com_ferramenta = ordens.filter(ferramenta="sim").count()
    total_com_prazo = ordens.exclude(prazo_solicitado__isnull=True).count()

    context = {
        "page_obj": page_obj,
        "total_ordens": total_ordens,
        "total_com_amostra": total_com_amostra,
        "total_com_ferramenta": total_com_ferramenta,
        "total_com_prazo": total_com_prazo,
        "clientes": Cliente.objects.all(),
        "ordem_model": OrdemDesenvolvimento,  # usado no template para acessar RAZOES
        "metodologias": (
        OrdemDesenvolvimento.objects.order_by()
        .exclude(metodologia_aprovacao__isnull=True)
        .exclude(metodologia_aprovacao__exact="")
        .values_list("metodologia_aprovacao", flat=True)
        .distinct()
),
    }

    return render(request, "ordens_desenvolvimento/lista_ordens.html", context)


from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from comercial.forms.ordem_desenvolvimento_form import OrdemDesenvolvimentoForm
from comercial.models.ordem_desenvolvimento import OrdemDesenvolvimento



@login_required
@permission_required("comercial.add_ordemdesenvolvimento", raise_exception=True)
def cadastrar_ordem_desenvolvimento(request):
    if request.method == "POST":
        form = OrdemDesenvolvimentoForm(request.POST)
        aba = request.POST.get("aba")

        if form.is_valid():
            ordem = form.save(commit=False)

            # Assinatura da aba salva
            if aba == "comercial":
                ordem.assinatura_comercial_nome = request.user.get_full_name()
                ordem.assinatura_comercial_email = request.user.email
                ordem.assinatura_comercial_data = timezone.now()
            elif aba == "tecnica":
                ordem.assinatura_tecnica_nome = request.user.get_full_name()
                ordem.assinatura_tecnica_email = request.user.email
                ordem.assinatura_tecnica_data = timezone.now()

            ordem.save()
            messages.success(request, "Ordem cadastrada com sucesso.")
            return redirect("lista_ordens_desenvolvimento")  # 🔁 Redireciona para a lista
    else:
        form = OrdemDesenvolvimentoForm()

    return render(request, "ordens_desenvolvimento/form_ordem_desenvolvimento.html", {
        "form": form,
        "titulo": "Cadastrar Ordem de Desenvolvimento",
        "ordem": None,
    })




@login_required
@permission_required("comercial.change_ordemdesenvolvimento", raise_exception=True)
def editar_ordem_desenvolvimento(request, pk):
    ordem = get_object_or_404(OrdemDesenvolvimento, pk=pk)
    aba = request.POST.get("aba") if request.method == "POST" else "comercial"

    if request.method == "POST":
        form = OrdemDesenvolvimentoForm(request.POST, instance=ordem)
        if form.is_valid():
            instancia = form.save(commit=False)

            # Atualiza assinatura da aba ativa
            if aba == "comercial":
                instancia.assinatura_comercial_nome = request.user.get_full_name()
                instancia.assinatura_comercial_email = request.user.email
                instancia.assinatura_comercial_data = timezone.now()
                instancia.assinatura_tecnica_nome = ordem.assinatura_tecnica_nome
                instancia.assinatura_tecnica_email = ordem.assinatura_tecnica_email
                instancia.assinatura_tecnica_data = ordem.assinatura_tecnica_data

            elif aba == "tecnica":
                instancia.assinatura_tecnica_nome = request.user.get_full_name()
                instancia.assinatura_tecnica_email = request.user.email
                instancia.assinatura_tecnica_data = timezone.now()
                instancia.assinatura_comercial_nome = ordem.assinatura_comercial_nome
                instancia.assinatura_comercial_email = ordem.assinatura_comercial_email
                instancia.assinatura_comercial_data = ordem.assinatura_comercial_data

            # debug: logar campo
            print("🟡 DEBUG — prazo_amostra:", form.cleaned_data.get("prazo_amostra"))

            instancia.save()
            messages.success(request, "Ordem atualizada com sucesso.")
            return redirect("lista_ordens_desenvolvimento")

    else:
        form = OrdemDesenvolvimentoForm(instance=ordem)

    return render(request, "ordens_desenvolvimento/form_ordem_desenvolvimento.html", {
        "form": form,
        "titulo": f"Editar Ordem de Desenvolvimento Nº {ordem.numero:03d}",
        "ordem": ordem,
    })






from comercial.models import OrdemDesenvolvimento

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404
from comercial.models import OrdemDesenvolvimento


@login_required
@permission_required("comercial.view_ordemdesenvolvimento", raise_exception=True)
def visualizar_ordem_desenvolvimento(request, pk):
    ordem = get_object_or_404(
        OrdemDesenvolvimento.objects.select_related(
            "precalculo__cotacao",
            "usuario_comercial__funcionario__cargo_atual",
            "usuario_tecnico__funcionario__cargo_atual"
        ),
        pk=pk
    )

    razoes_choices = OrdemDesenvolvimento._meta.get_field("razao").choices

    cotacao_numero = ordem.precalculo.cotacao.numero if ordem.precalculo and ordem.precalculo.cotacao else None
    precalculo_numero = ordem.precalculo.numero if ordem.precalculo else None

    return render(request, "ordens_desenvolvimento/visualizar_f017.html", {
        "ordem": ordem,
        "razoes_choices": razoes_choices,
        "cotacao_numero": cotacao_numero,
        "precalculo_numero": precalculo_numero,
    })






@login_required
@permission_required("comercial.delete_ordemdesenvolvimento", raise_exception=True)
def excluir_ordem_desenvolvimento(request, pk):
    ordem = get_object_or_404(OrdemDesenvolvimento, pk=pk)
    if request.method == "POST":
        ordem.delete()
        return redirect("lista_ordens_desenvolvimento")
    return render(request, "partials/global/_modal_exclusao.html", {
        "objeto": ordem,
        "url_exclusao": "excluir_ordem_desenvolvimento",
        "titulo": "Excluir Ordem de Desenvolvimento"
    })
