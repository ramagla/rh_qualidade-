from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import timedelta
from django.utils import timezone

from Funcionario.models import Treinamento
from Funcionario.models import AvaliacaoTreinamento, AvaliacaoDesempenho, Funcionario, ListaPresenca
from Funcionario.forms import AvaliacaoTreinamentoForm, AvaliacaoForm,AvaliacaoAnualForm,AvaliacaoExperienciaForm


def lista_avaliacoes(request):
    avaliacoes_treinamento = AvaliacaoTreinamento.objects.all()
    avaliacoes_desempenho = AvaliacaoDesempenho.objects.all()
    today = timezone.now().date()

    # Atualizando o status de prazo e o status da avaliação
    for avaliacao in avaliacoes_treinamento:
        # Verifique se o treinamento e o tipo estão definidos
        if hasattr(avaliacao.treinamento, 'tipo'):
            dias_prazo = 30 if avaliacao.treinamento.tipo == 'EXPERIENCIA' else 365
            avaliacao.status_prazo = "Dentro do Prazo" if (avaliacao.data_avaliacao + timedelta(days=dias_prazo)) >= today else "Fora do Prazo"
        else:
            avaliacao.status_prazo = "Tipo não definido"

        # Define o status da avaliação com base na avaliação geral
        if avaliacao.avaliacao_geral <= 2:
            avaliacao.status_avaliacao = "Pouco Eficaz"
        elif 3 <= avaliacao.avaliacao_geral <= 4:
            avaliacao.status_avaliacao = "Eficaz"
        else:
            avaliacao.status_avaliacao = "Muito Eficaz"

    context = {
        'avaliacoes_treinamento': avaliacoes_treinamento,
        'avaliacoes_desempenho': avaliacoes_desempenho,
        'treinamentos': Treinamento.objects.all(),
        'funcionarios': Funcionario.objects.all(),
    }
    return render(request, 'avaliacao_treinamento/lista_avaliacao.html', context)

def cadastrar_avaliacao_experiencia(request):
    funcionarios = Funcionario.objects.all()  # Busca todos os funcionários

    if request.method == 'POST':
        form = AvaliacaoExperienciaForm(request.POST)
        if form.is_valid():
            form.save()  # Salva a avaliação
            return redirect('lista_avaliacao_desempenho')  # Redireciona para a lista após salvar
        else:
            print(form.errors)  # Adicione esta linha para verificar erros no console

    else:
        form = AvaliacaoExperienciaForm()

    return render(request, 'cadastrar_avaliacao_experiencia.html', {'form': form, 'funcionarios': funcionarios})

def cadastrar_avaliacao_anual(request):
    if request.method == 'POST':
        form = AvaliacaoAnualForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_avaliacao_desempenho')  # Redireciona para a lista após salvar
    else:
        form = AvaliacaoAnualForm()

    funcionarios = Funcionario.objects.all()  # Pegar todos os funcionários

    return render(request, 'cadastrar_avaliacao_anual.html', {
        'form': form,
        'funcionarios': funcionarios
    })


def editar_avaliacao_desempenho(request, id):
    avaliacao = get_object_or_404(AvaliacaoDesempenho, id=id)
    
    if request.method == 'POST':
        form = AvaliacaoForm(request.POST, instance=avaliacao)
        if form.is_valid():
            form.save()
            return redirect('lista_avaliacao_desempenho')  # Redireciona para a lista após edição
    else:
        form = AvaliacaoForm(instance=avaliacao)
    
    return render(request, 'editar_avaliacao_desempenho.html', {'form': form, 'avaliacao': avaliacao})

def excluir_avaliacao_desempenho(request, id):
    avaliacao = get_object_or_404(AvaliacaoDesempenho, id=id)
    if request.method == "POST":
        avaliacao.delete()
        return redirect('lista_avaliacao_desempenho')  # Redireciona para a lista após a exclusão
    return redirect('lista_avaliacao_desempenho')


def lista_avaliacao_desempenho(request):
    # Recupera todas as avaliações, tanto do tipo 'ANUAL' quanto 'EXPERIENCIA'
    avaliacoes = AvaliacaoDesempenho.objects.all()  # Isso recupera todas as avaliações

    # Se você precisar filtrar por funcionário ou data, adicione lógica aqui
    funcionario_id = request.GET.get('funcionario')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    if funcionario_id:
        avaliacoes = avaliacoes.filter(funcionario_id=funcionario_id)
    if data_inicio and data_fim:
        avaliacoes = avaliacoes.filter(data_avaliacao__range=[data_inicio, data_fim])

    # Log para verificar quantas avaliações estão sendo passadas
    print(f"Número de avaliações encontradas: {avaliacoes.count()}")

    return render(request, 'lista_avaliacao_desempenho.html', {
        'avaliacoes': avaliacoes,
        'funcionarios': Funcionario.objects.all(),  # Para o filtro
    })