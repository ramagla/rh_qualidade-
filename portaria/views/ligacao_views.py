from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from portaria.models.ligacao import LigacaoPortaria
from portaria.forms.ligacao_form import LigacaoPortariaForm
from django.utils.timezone import now
from datetime import datetime, date
from django.core.paginator import Paginator

from django.core.mail import send_mail


@login_required
@permission_required("portaria.view_ligacaoportaria", raise_exception=True)
def lista_ligacoes(request):
    ligacoes_queryset = LigacaoPortaria.objects.select_related("falar_com").filter(falar_com__status="Ativo").order_by("-data", "-horario")

    # Filtros
    nome = request.GET.get("nome")
    empresa = request.GET.get("empresa")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    if nome:
        ligacoes_queryset = ligacoes_queryset.filter(nome=nome)
    if empresa:
        ligacoes_queryset = ligacoes_queryset.filter(empresa=empresa)
    if data_inicio:
        ligacoes_queryset = ligacoes_queryset.filter(data__gte=data_inicio)
    if data_fim:
        ligacoes_queryset = ligacoes_queryset.filter(data__lte=data_fim)

    # Indicadores
    total_ligacoes = ligacoes_queryset.count()
    total_hoje = LigacaoPortaria.objects.filter(data=date.today()).count()

    # Paginação
    paginator = Paginator(ligacoes_queryset, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Listas únicas para os filtros
    nomes = LigacaoPortaria.objects.filter(falar_com__status="Ativo").values_list("nome", flat=True).distinct().order_by("nome")
    empresas = LigacaoPortaria.objects.exclude(empresa="").values_list("empresa", flat=True).distinct().order_by("empresa")

    context = {
        "ligacoes": page_obj,         # usado no for
        "page_obj": page_obj,         # usado no _paginacao.html
        "total_ligacoes": total_ligacoes,
        "total_hoje": total_hoje,
        "nomes": nomes,
        "empresas": empresas,
    }

    return render(request, "ligacoes/lista_ligacoes.html", context)

@login_required
@permission_required("portaria.add_ligacaoportaria", raise_exception=True)
def cadastrar_ligacao(request):
    if request.method == "POST":
        form = LigacaoPortariaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("lista_ligacoes")
    else:
        form = LigacaoPortariaForm(initial={
            "data": now().date(),
            "horario": now().strftime("%H:%M")
        })

    return render(request, "ligacoes/cadastrar_ligacao.html", {"form": form})
@login_required
@permission_required("portaria.change_ligacaoportaria", raise_exception=True)
def editar_ligacao(request, pk):
    ligacao = get_object_or_404(LigacaoPortaria, pk=pk)
    if request.method == "POST":
        form = LigacaoPortariaForm(request.POST, instance=ligacao)
        if form.is_valid():
            form.save()
            return redirect("lista_ligacoes")
    else:
        form = LigacaoPortariaForm(instance=ligacao)

    return render(request, "ligacoes/cadastrar_ligacao.html", {"form": form})


@login_required
@permission_required("portaria.delete_ligacaoportaria", raise_exception=True)
def excluir_ligacao(request, pk):
    ligacao = get_object_or_404(LigacaoPortaria, pk=pk)
    if request.method == "POST":
        ligacao.delete()
        return redirect("lista_ligacoes")
    return render(request, "partials/global/_modal_exclusao.html", {
        "objeto": ligacao,
        "url_excluir": "excluir_ligacao"
    })

from alerts.models import AlertaUsuario
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.timezone import now

@login_required
@permission_required("portaria.change_ligacaoportaria", raise_exception=True)
def disparar_recado(request, pk):
    ligacao = get_object_or_404(LigacaoPortaria, pk=pk)

    if not ligacao.falar_com or not ligacao.falar_com.user:
        messages.error(request, "Funcionário não vinculado a um usuário do sistema.")
        return redirect("lista_ligacoes")

    user_destino = ligacao.falar_com.user


    # Alerta in-app
    AlertaUsuario.objects.create(
        usuario=user_destino,
        titulo="📞 Novo Recado Recebido",
        mensagem=f"{ligacao.nome} da empresa {ligacao.empresa} deixou um recado para você:\n\n{ligacao.recado}",
        tipo="recado",
        referencia_id=ligacao.id,
    )

    # E-mail
    html_email = render_to_string("emails/recado_ligacao_email.html", {
    "ligacao": ligacao,
    "ano": now().year,
    })

    send_mail(
        subject="📞 Recado Recebido",
        message=ligacao.recado,
        from_email="no-reply@brasmol.com.br",
        recipient_list=[user_destino.email],
        fail_silently=False,
        html_message=html_email,
    )

    ligacao.recado_enviado = True
    ligacao.save()

    messages.success(request, "Recado enviado com sucesso.")
    return redirect("lista_ligacoes")