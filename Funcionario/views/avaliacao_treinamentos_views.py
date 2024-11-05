



from datetime import timedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages  # Corrige o import de mensagens para o correto
from Funcionario.forms import AvaliacaoTreinamentoForm
from Funcionario.models import AvaliacaoDesempenho, AvaliacaoTreinamento, Funcionario, Treinamento


from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
from Funcionario.models import AvaliacaoDesempenho, AvaliacaoTreinamento, Funcionario, Treinamento


from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
from Funcionario.models import AvaliacaoTreinamento, AvaliacaoDesempenho, Treinamento, Funcionario

def lista_avaliacoes(request):
    avaliacoes_treinamento = AvaliacaoTreinamento.objects.all()
    avaliacoes_desempenho = AvaliacaoDesempenho.objects.all()
    today = timezone.now().date()

    # Atualizando o status de prazo e o status da avaliação
    for avaliacao in avaliacoes_treinamento:
        # Determina o status de prazo
        dias_prazo = 30 if avaliacao.treinamento.tipo == 'EXPERIENCIA' else 365
        avaliacao.status_prazo = "Dentro do Prazo" if (avaliacao.data_avaliacao + timedelta(days=dias_prazo)) >= today else "Em Atraso"
        
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



def cadastrar_avaliacao(request):
    if request.method == 'POST':
        form = AvaliacaoTreinamentoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Avaliação cadastrada com sucesso!")
            return redirect('lista_avaliacoes')
    else:
        form = AvaliacaoTreinamentoForm()
    return render(request, 'avaliacao_treinamento/cadastrar_avaliacao.html', {'form': form})

def editar_avaliacao(request, id):
    avaliacao = get_object_or_404(AvaliacaoTreinamento, id=id)
    if request.method == 'POST':
        form = AvaliacaoTreinamentoForm(request.POST, instance=avaliacao)
        if form.is_valid():
            form.save()
            return redirect('lista_avaliacoes')
    else:
        form = AvaliacaoTreinamentoForm(instance=avaliacao)
    return render(request, 'avaliacao_treinamento/editar_avaliacao.html', {'form': form})

def excluir_avaliacao(request, id):
    avaliacao = get_object_or_404(AvaliacaoTreinamento, id=id)
    if request.method == 'POST':
        avaliacao.delete()
        messages.success(request, "Avaliação excluída com sucesso!")
    return redirect('lista_avaliacoes')

def visualizar_avaliacao(request, id):
    avaliacao = get_object_or_404(AvaliacaoTreinamento, id=id)

    # Coletando os responsáveis como um dicionário
    responsaveis = [
        {
            'nome': avaliacao.responsavel_1_nome,
            'cargo': avaliacao.responsavel_1_cargo,
        },
        {
            'nome': avaliacao.responsavel_2_nome,
            'cargo': avaliacao.responsavel_2_cargo,
        },
        {
            'nome': avaliacao.responsavel_3_nome,
            'cargo': avaliacao.responsavel_3_cargo,
        }
    ]

    # Coletando as respostas das perguntas
    grau_conhecimento = avaliacao.pergunta_1  # Supondo que seja um campo de resposta
    aplicacao_conceitos = avaliacao.pergunta_2  # Supondo que seja um campo de resposta
    resultados_obtidos = avaliacao.pergunta_3  # Supondo que seja um campo de resposta
    melhorias = avaliacao.descricao_melhorias
    avaliacao_geral = avaliacao.avaliacao_geral

    return render(request, 'avaliacao_treinamento/visualizar_avaliacao.html', {
        'avaliacao': avaliacao,
        'responsaveis': responsaveis,
        'grau_conhecimento': grau_conhecimento,
        'aplicacao_conceitos': aplicacao_conceitos,
        'resultados_obtidos': resultados_obtidos,
        'melhorias': melhorias,
        'avaliacao_geral': avaliacao_geral,
    })