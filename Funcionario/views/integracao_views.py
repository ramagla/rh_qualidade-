# Django - Funcionalidades principais
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.timezone import now

# App Interno - Formulários e modelos
from Funcionario.forms import IntegracaoFuncionarioForm
from Funcionario.models import IntegracaoFuncionario

# Utilitários locais
from Funcionario.utils.integracao_utils import (
    filtrar_integracoes,
    obter_contexto_lista_integracoes
)

@login_required
def lista_integracoes(request):
    """Renderiza a listagem de integrações com filtros e cards."""
    integracoes = filtrar_integracoes(request)
    contexto = obter_contexto_lista_integracoes(request, integracoes)
    return render(request, "integracao/lista_integracoes.html", contexto)


@login_required
def visualizar_integracao(request, integracao_id):
    """Exibe os detalhes de uma integração específica."""
    integracao = get_object_or_404(IntegracaoFuncionario, id=integracao_id)
    return render(
        request,
        "integracao/visualizar_integracao.html",
        {"integracao": integracao, "now": now()},
    )


@login_required
def cadastrar_integracao(request):
    """Realiza o cadastro de uma nova integração de funcionário."""
    if request.method == "POST":
        form = IntegracaoFuncionarioForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Integração cadastrada com sucesso.")
            return redirect(reverse("lista_integracoes"))
    else:
        form = IntegracaoFuncionarioForm()
    return render(request, "integracao/form_integracao.html", {"form": form})


@login_required
def editar_integracao(request, integracao_id):
    """Edita os dados de uma integração existente."""
    integracao = get_object_or_404(IntegracaoFuncionario, id=integracao_id)
    if request.method == "POST":
        form = IntegracaoFuncionarioForm(request.POST, request.FILES, instance=integracao)
        if form.is_valid():
            form.save()
            messages.success(request, "Integração atualizada com sucesso.")
            return redirect(reverse("lista_integracoes"))
    else:
        form = IntegracaoFuncionarioForm(instance=integracao)
    return render(request, "integracao/form_integracao.html", {"form": form, "integracao": integracao})


@login_required
def excluir_integracao(request, integracao_id):
    """Exclui uma integração específica."""
    integracao = get_object_or_404(IntegracaoFuncionario, id=integracao_id)
    if request.method == "POST":
        integracao.delete()
        messages.success(request, "Integração excluída com sucesso.")
    return redirect(reverse("lista_integracoes"))


@login_required
def imprimir_integracao(request, integracao_id):
    """Gera a visualização para impressão da integração."""
    integracao = get_object_or_404(IntegracaoFuncionario, id=integracao_id)
    return render(request, "integracao/imprimir_integracao.html", {"integracao": integracao})
