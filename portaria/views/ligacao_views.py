from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from portaria.models.ligacao import LigacaoPortaria
from portaria.forms.ligacao_form import LigacaoPortariaForm
from django.utils.timezone import now
from datetime import datetime, date

@login_required
@permission_required("portaria.view_ligacaoportaria", raise_exception=True)
def lista_ligacoes(request):
    ligacoes = LigacaoPortaria.objects.select_related("falar_com").order_by("-data", "-horario")

    # Filtros
    nome = request.GET.get("nome")
    empresa = request.GET.get("empresa")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    if nome:
        ligacoes = ligacoes.filter(nome=nome)
    if empresa:
        ligacoes = ligacoes.filter(empresa=empresa)
    if data_inicio:
        ligacoes = ligacoes.filter(data__gte=data_inicio)
    if data_fim:
        ligacoes = ligacoes.filter(data__lte=data_fim)

    # Indicadores
    total_ligacoes = ligacoes.count()
    total_hoje = LigacaoPortaria.objects.filter(data=date.today()).count()

    # Listas únicas para os filtros
    nomes = LigacaoPortaria.objects.values_list("nome", flat=True).distinct()
    empresas = LigacaoPortaria.objects.values_list("empresa", flat=True).exclude(empresa="").distinct()

    context = {
        "ligacoes": ligacoes,
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
        message=ligacao.recado,  # Texto simples como fallback
        from_email="no-reply@brasmol.com.br",
        recipient_list=[user_destino.email],
        fail_silently=True,
        html_message=html_email,
    )

    ligacao.recado_enviado = True
    ligacao.save()

    messages.success(request, "Recado enviado com sucesso.")
    return redirect("lista_ligacoes")