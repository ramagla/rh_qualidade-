from django.shortcuts import render, redirect, get_object_or_404
from Funcionario.models import AvaliacaoAnual, Funcionario
from Funcionario.forms import AvaliacaoAnualForm

def lista_avaliacao_anual(request):
    avaliacoes = AvaliacaoAnual.objects.all()
    funcionario_id = request.GET.get('funcionario')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    if funcionario_id:
        avaliacoes = avaliacoes.filter(funcionario_id=funcionario_id)
    if data_inicio and data_fim:
        avaliacoes = avaliacoes.filter(data_avaliacao__range=[data_inicio, data_fim])

    return render(request, 'avaliacao_desempenho/lista_avaliacao_anual.html', {
        'avaliacoes': avaliacoes,
        'funcionarios': Funcionario.objects.all(),
    })

def cadastrar_avaliacao_anual(request):
    if request.method == 'POST':
        form = AvaliacaoAnualForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_avaliacao_anual')
    else:
        form = AvaliacaoAnualForm()
    return render(request, 'avaliacao_desempenho/cadastrar_avaliacao_anual.html', {
        'form': form,
        'funcionarios': Funcionario.objects.all(),
    })

def editar_avaliacao_anual(request, id):
    avaliacao = get_object_or_404(AvaliacaoAnual, id=id)
    if request.method == 'POST':
        form = AvaliacaoAnualForm(request.POST, instance=avaliacao)
        if form.is_valid():
            form.save()
            return redirect('lista_avaliacao_anual')
    else:
        form = AvaliacaoAnualForm(instance=avaliacao)
    return render(request, 'avaliacao_desempenho/editar_avaliacao_anual.html', {'form': form})

def excluir_avaliacao_anual(request, id):
    avaliacao = get_object_or_404(AvaliacaoAnual, id=id)
    if request.method == "POST":
        avaliacao.delete()
        return redirect('lista_avaliacao_anual')
    return redirect('lista_avaliacao_anual')
