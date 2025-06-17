from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404, redirect
from comercial.models import Cotacao  # Supondo que o model exista
from comercial.forms.cotacoes_form import CotacaoForm

@login_required
@permission_required("comercial.view_cotacao", raise_exception=True)
def lista_cotacoes(request):
    cotacoes = Cotacao.objects.all()
    return render(request, "comercial/cotacoes/lista.html", {"cotacoes": cotacoes})

@login_required
@permission_required("comercial.add_cotacao", raise_exception=True)
def cadastrar_cotacao(request):
    form = CotacaoForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        return redirect("lista_cotacoes")
    return render(request, "comercial/cotacoes/form.html", {"form": form})

@login_required
@permission_required("comercial.change_cotacao", raise_exception=True)
def editar_cotacao(request, pk):
    cotacao = get_object_or_404(Cotacao, pk=pk)
    form = CotacaoForm(request.POST or None, request.FILES or None, instance=cotacao)
    if form.is_valid():
        form.save()
        return redirect("lista_cotacoes")
    return render(request, "comercial/cotacoes/form.html", {"form": form})

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
