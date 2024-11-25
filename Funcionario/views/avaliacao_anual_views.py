from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from Funcionario.models import AvaliacaoAnual, Funcionario
from Funcionario.forms import AvaliacaoAnualForm
from datetime import datetime



def lista_avaliacao_anual(request):
    # Obtém todas as avaliações anuais
    avaliacoes = AvaliacaoAnual.objects.all()
    
    # Obtém os parâmetros de filtro da requisição GET
    funcionario_id = request.GET.get('funcionario')
    departamento = request.GET.get('departamento')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    # Aplica o filtro por funcionário, se selecionado
    if funcionario_id:
        avaliacoes = avaliacoes.filter(funcionario_id=funcionario_id)

    # Aplica o filtro por departamento, se preenchido
    if departamento:
        avaliacoes = avaliacoes.filter(funcionario__local_trabalho__icontains=departamento)

    # Aplica o filtro por data de avaliação, se ambas as datas de início e fim estiverem presentes
    if data_inicio and data_fim:
        try:
            # Converte as strings de data para objetos de data
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            avaliacoes = avaliacoes.filter(data_avaliacao__range=[data_inicio, data_fim])
        except ValueError:
            messages.error(request, "Formato de data inválido. Use o formato AAAA-MM-DD.")

    # Classifica as avaliações por nome do funcionário
    avaliacoes = avaliacoes.order_by('funcionario__nome')

    # Adiciona a classificação como um atributo, incluindo a classificação e percentual
    for avaliacao in avaliacoes:
        classificacao_data = avaliacao.calcular_classificacao()  # Chama o método corretamente
        avaliacao.classificacao = classificacao_data['status']  # Armazena o status
        avaliacao.percentual = classificacao_data['percentual']  # Armazena o percentual

    # Obtém a lista de funcionários para o filtro
    funcionarios = Funcionario.objects.all()
    
    # Obtém a lista de departamentos únicos para o filtro
    departamentos = Funcionario.objects.values_list('local_trabalho', flat=True).distinct()

    # Renderiza o template com as avaliações filtradas e a lista de funcionários e departamentos para o filtro
    return render(request, 'avaliacao_desempenho_anual/lista_avaliacao_anual.html', {
        'avaliacoes': avaliacoes,
        'funcionarios': funcionarios,
        'departamentos': departamentos,
    })







def cadastrar_avaliacao_anual(request):
    if request.method == 'POST':
        form = AvaliacaoAnualForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_avaliacao_anual')
    else:
        form = AvaliacaoAnualForm()

    # Ordenar os funcionários por nome
    funcionarios = Funcionario.objects.all().order_by('nome')

    return render(request, 'avaliacao_desempenho_anual/cadastrar_avaliacao_anual.html', {
        'form': form,
        'funcionarios': funcionarios,
    })


def editar_avaliacao_anual(request, id):
    avaliacao = get_object_or_404(AvaliacaoAnual, id=id)
    
    if request.method == 'POST':
        form = AvaliacaoAnualForm(request.POST, instance=avaliacao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Avaliação anual atualizada com sucesso!')
            return redirect('lista_avaliacao_anual')
        else:
            # Se o formulário não for válido, você pode optar por adicionar uma mensagem de erro
            messages.error(request, 'Erro ao atualizar a avaliação. Verifique os campos.')

    else:
        form = AvaliacaoAnualForm(instance=avaliacao)

    return render(request, 'avaliacao_desempenho_anual/editar_avaliacao_anual.html', {
        'form': form,
        'avaliacao': avaliacao,
        'funcionarios': Funcionario.objects.all(),  # Se necessário, para o select
    })


def excluir_avaliacao_anual(request, id):
    avaliacao = get_object_or_404(AvaliacaoAnual, id=id)
    if request.method == "POST":
        avaliacao.delete()
        return redirect('lista_avaliacao_anual')
    return redirect('lista_avaliacao_anual')

def imprimir_avaliacao(request, avaliacao_id):
    # Obtém a avaliação anual pelo ID
    avaliacao = get_object_or_404(AvaliacaoAnual, id=avaliacao_id)

    # Chama o método calcular_classificacao
    classificacao = avaliacao.calcular_classificacao()

    # Passa a classificação e a avaliação para o template
    return render(request, 'avaliacao_desempenho_anual/imprimir_avaliacao_anual.html', {
        'avaliacao': avaliacao,
        'percentual': classificacao['percentual'],
        'status': classificacao['status'],
    })

def visualizar_avaliacao_anual(request, id):
    avaliacao = get_object_or_404(AvaliacaoAnual, id=id)

    # Mapeando os textos do status para cada campo
    campos = [
        'postura_seg_trabalho',
        'qualidade_produtividade',
        'trabalho_em_equipe',
        'comprometimento',
        'disponibilidade_para_mudancas',
        'disciplina',
        'rendimento_sob_pressao',
        'proatividade',
        'comunicacao',
        'assiduidade',
    ]

    status_campos = {
        campo: AvaliacaoAnual.get_status_text(getattr(avaliacao, campo))
        for campo in campos
    }

    # Calcula a classificação e percentual
    classificacao = avaliacao.calcular_classificacao()

    context = {
        'avaliacao': avaliacao,
        'status_campos': status_campos,
        'classificacao': classificacao['status'],
        'percentual': classificacao['percentual'],
    }
    return render(request, 'avaliacao_desempenho_anual/visualizar_avaliacao_anual.html', context)


def imprimir_simplificado(request, avaliacao_id):
    # Obtém a avaliação anual pelo ID
    avaliacao = get_object_or_404(AvaliacaoAnual, id=avaliacao_id)

    return render(request, 'avaliacao_desempenho_anual/template_simplificado.html', {
        'avaliacao': avaliacao,
    })