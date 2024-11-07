


from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from Funcionario import models
from Funcionario.forms import AvaliacaoTreinamentoForm
from Funcionario.models import AvaliacaoTreinamento, Funcionario, ListaPresenca
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

def lista_avaliacoes(request):
    # Busca todas as avaliações de treinamento no banco de dados
    avaliacoes_treinamento = AvaliacaoTreinamento.objects.all()
    
    # Filtra por treinamento, se selecionado
    treinamento_id = request.GET.get('treinamento')
    if treinamento_id:
        avaliacoes_treinamento = avaliacoes_treinamento.filter(treinamento_id=treinamento_id)

    # Filtra por funcionário, se selecionado
    funcionario_id = request.GET.get('funcionario')
    if funcionario_id:
        avaliacoes_treinamento = avaliacoes_treinamento.filter(funcionario_id=funcionario_id)

    # Filtra por período de data, se ambos os campos forem preenchidos
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    if data_inicio and data_fim:
        avaliacoes_treinamento = avaliacoes_treinamento.filter(data_avaliacao__range=[data_inicio, data_fim])

    # Busca apenas funcionários ativos
    funcionarios_ativos = Funcionario.objects.filter(status="Ativo")
    
    # Busca todos os treinamentos para o filtro
    listas_presenca = ListaPresenca.objects.all()

    # Renderiza o template com os filtros aplicados
    return render(request, 'avaliacao_treinamento/lista_avaliacao.html', {
        'avaliacoes_treinamento': avaliacoes_treinamento,
        'funcionarios_ativos': funcionarios_ativos,
        'listas_presenca': listas_presenca
    })


from django.shortcuts import redirect, render
from django.contrib import messages
from Funcionario.forms import AvaliacaoTreinamentoForm
from Funcionario.models import Funcionario

def cadastrar_avaliacao(request):
    # Carregar todos os funcionários
    funcionarios = Funcionario.objects.all()

    # Define as opções para os campos de questionário
    opcoes_conhecimento = [
        (1, "Muito baixo"),
        (2, "Baixo"),
        (3, "Médio"),
        (4, "Bom"),
        (5, "Excelente")
    ]
    
    opcoes_aplicacao = [
        (1, "Muito baixo"),
        (2, "Baixo"),
        (3, "Médio"),
        (4, "Bom"),
        (5, "Excelente")
    ]
    
    opcoes_resultados = [
        (1, "Muito baixo"),
        (2, "Baixo"),
        (3, "Médio"),
        (4, "Bom"),
        (5, "Excelente")
    ]

    if request.method == 'POST':
        # Processar a submissão do formulário
        form = AvaliacaoTreinamentoForm(request.POST)
        
        if form.is_valid():
            form.save()
            messages.success(request, "Avaliação cadastrada com sucesso!")
            return redirect('lista_avaliacoes')  # Redireciona para a lista de avaliações
        else:
            messages.error(request, "Erro ao cadastrar a avaliação. Verifique os campos.")
    
    else:
        # Inicializa o formulário vazio para o GET
        form = AvaliacaoTreinamentoForm()

    # Renderiza o template com o formulário e opções necessárias
    return render(request, 'avaliacao_treinamento/cadastrar_avaliacao.html', {
        'form': form,
        'funcionarios': funcionarios,
        'opcoes_conhecimento': opcoes_conhecimento,
        'opcoes_aplicacao': opcoes_aplicacao,
        'opcoes_resultados': opcoes_resultados,
    })



def editar_avaliacao(request, id):
    # Busca a avaliação de treinamento com o ID fornecido
    avaliacao = get_object_or_404(AvaliacaoTreinamento, id=id)
    funcionarios = Funcionario.objects.all()  # Todos os funcionários disponíveis
    treinamentos = ListaPresenca.objects.all()  # Todos os treinamentos disponíveis

    # Mapeamento das respostas para texto
    opcoes_conhecimento = {
        1: "Não possui conhecimento mínimo da metodologia para sua aplicação.",
        2: "Apresenta deficiências nos conceitos, o que compromete a aplicação.",
        3: "Possui noções básicas, mas necessita de acompanhamento e suporte na aplicação.",
        4: "Possui domínio necessário da metodologia e a utiliza adequadamente.",
        5: "Possui completo domínio e utiliza a metodologia com excelência."
    }
    opcoes_aplicacao = {
        1: "Está muito abaixo do esperado.",
        2: "Aplicação está abaixo do esperado.",
        3: "Aplicação é razoável, mas não dentro do esperado.",
        4: "Aplicação está adequada e corresponde às expectativas.",
        5: "Aplicação excede as expectativas."
    }
    opcoes_resultados = {
        1: "Nenhum resultado foi obtido efetivamente até o momento.",
        2: "As melhorias obtidas estão muito abaixo do esperado.",
        3: "As melhorias obtidas são consideráveis, mas não dentro do esperado.",
        4: "As melhorias obtidas são boas e estão dentro do esperado.",
        5: "As melhorias obtidas excederam as expectativas."
    }

    if request.method == 'POST':
        form = AvaliacaoTreinamentoForm(request.POST, instance=avaliacao)
        if form.is_valid():
            form.save()
            messages.success(request, "Avaliação atualizada com sucesso!")
            return redirect('lista_avaliacoes')  # Redireciona para a lista de avaliações
        else:
            messages.error(request, "Erro ao atualizar a avaliação. Verifique os campos.")
    else:
        form = AvaliacaoTreinamentoForm(instance=avaliacao)

    # Renderiza o template com os dados da avaliação e as opções de questionário
    return render(request, 'avaliacao_treinamento/editar_avaliacao.html', {
        'form': form,
        'avaliacao': avaliacao,
        'funcionarios': funcionarios,
        'treinamentos': treinamentos,
        'opcoes_conhecimento': AvaliacaoTreinamento.OPCOES_CONHECIMENTO,
        'opcoes_aplicacao': AvaliacaoTreinamento.OPCOES_APLICACAO,
        'opcoes_resultados': AvaliacaoTreinamento.OPCOES_RESULTADOS,
        'grau_conhecimento': opcoes_conhecimento.get(avaliacao.pergunta_1, "Resposta não especificada"),
        'aplicacao_conceitos': opcoes_aplicacao.get(avaliacao.pergunta_2, "Resposta não especificada"),
        'resultados_obtidos': opcoes_resultados.get(avaliacao.pergunta_3, "Resposta não especificada"),
        'avaliacao_geral': avaliacao.get_avaliacao_geral_display(),
    })

    # Função para verificar e buscar um Funcionario pelo ID
    def get_responsavel(responsavel_id, cargo):
        try:
            # Verifica se o valor do ID é um número
            responsavel_id = int(responsavel_id)
            responsavel = Funcionario.objects.get(id=responsavel_id)
            return {'nome': responsavel.nome, 'cargo': cargo}
        except (ValueError, TypeError, Funcionario.DoesNotExist):
            # Retorna valores padrão se não for um número ou não existir
            return {'nome': 'Não selecionado', 'cargo': cargo}

    # Coletando dados dos responsáveis
    responsaveis = [
        get_responsavel(avaliacao.responsavel_1_nome, avaliacao.responsavel_1_cargo),
        get_responsavel(avaliacao.responsavel_2_nome, avaliacao.responsavel_2_cargo),
        get_responsavel(avaliacao.responsavel_3_nome, avaliacao.responsavel_3_cargo),
    ]

    # Traduzindo respostas para texto
    grau_conhecimento = opcoes_conhecimento.get(avaliacao.pergunta_1, "Resposta não especificada")
    aplicacao_conceitos = opcoes_aplicacao.get(avaliacao.pergunta_2, "Resposta não especificada")
    resultados_obtidos = opcoes_resultados.get(avaliacao.pergunta_3, "Resposta não especificada")

    # Avaliação geral - Mapeamento do número para o texto correspondente
    avaliacao_geral_map = {
        1: "Pouco Eficaz",
        2: "Eficaz",
        5: "Muito Eficaz"
    }
    avaliacao_geral = avaliacao_geral_map.get(avaliacao.avaliacao_geral, "Indeterminado")

    if request.method == 'POST':
        form = AvaliacaoTreinamentoForm(request.POST, instance=avaliacao)
        if form.is_valid():
            form.save()
            return redirect('lista_avaliacoes')  # Redireciona para a lista de avaliações
    else:
        form = AvaliacaoTreinamentoForm(instance=avaliacao)

    context = {
        'form': form,
        'avaliacao': avaliacao,
        'funcionarios': funcionarios,
        'treinamentos': treinamentos,
        'opcoes_conhecimento': AvaliacaoTreinamento.OPCOES_CONHECIMENTO,
        'opcoes_aplicacao': AvaliacaoTreinamento.OPCOES_APLICACAO,
        'opcoes_resultados': AvaliacaoTreinamento.OPCOES_RESULTADOS,
        'responsaveis': responsaveis,
        'grau_conhecimento': grau_conhecimento,
        'aplicacao_conceitos': aplicacao_conceitos,
        'resultados_obtidos': resultados_obtidos,
        'avaliacao_geral': avaliacao_geral,
    }
    return render(request, 'avaliacao_treinamento/editar_avaliacao.html', context)



def visualizar_avaliacao(request, id):
    avaliacao = get_object_or_404(AvaliacaoTreinamento, id=id)
    
    # Mapeamento das respostas para texto
    opcoes_conhecimento = {
        1: "Não possui conhecimento mínimo da metodologia para sua aplicação.",
        2: "Apresenta deficiências nos conceitos, o que compromete a aplicação.",
        3: "Possui noções básicas, mas necessita de acompanhamento e suporte na aplicação.",
        4: "Possui domínio necessário da metodologia e a utiliza adequadamente.",
        5: "Possui completo domínio e utiliza a metodologia com excelência."
    }
    opcoes_aplicacao = {
        1: "Está muito abaixo do esperado.",
        2: "Aplicação está abaixo do esperado.",
        3: "Aplicação é razoável, mas não dentro do esperado.",
        4: "Aplicação está adequada e corresponde às expectativas.",
        5: "Aplicação excede as expectativas."
    }
    opcoes_resultados = {
        1: "Nenhum resultado foi obtido efetivamente até o momento.",
        2: "As melhorias obtidas estão muito abaixo do esperado.",
        3: "As melhorias obtidas são consideráveis, mas não dentro do esperado.",
        4: "As melhorias obtidas são boas e estão dentro do esperado.",
        5: "As melhorias obtidas excederam as expectativas."
    }

    # Traduzindo respostas para texto
    grau_conhecimento = opcoes_conhecimento.get(avaliacao.pergunta_1, "Resposta não especificada")
    aplicacao_conceitos = opcoes_aplicacao.get(avaliacao.pergunta_2, "Resposta não especificada")
    resultados_obtidos = opcoes_resultados.get(avaliacao.pergunta_3, "Resposta não especificada")

    # Avaliação geral - Mapeamento do número para o texto correspondente
    avaliacao_geral_map = {
        1: "Pouco Eficaz",
        2: "Eficaz",
        5: "Muito Eficaz"
    }
    avaliacao_geral = avaliacao_geral_map.get(avaliacao.avaliacao_geral, "Indeterminado")

    return render(request, 'avaliacao_treinamento/visualizar_avaliacao.html', {
        'avaliacao': avaliacao,
        'grau_conhecimento': grau_conhecimento,
        'aplicacao_conceitos': aplicacao_conceitos,
        'resultados_obtidos': resultados_obtidos,
        'melhorias': avaliacao.descricao_melhorias,
        'avaliacao_geral': avaliacao_geral,
    })

def get_treinamentos_por_funcionario(request, funcionario_id):
    treinamentos = ListaPresenca.objects.filter(participantes__id=funcionario_id)
    data = [
        {
            'id': treinamento.id,
            'treinamento': treinamento.treinamento,
            'data_realizacao': treinamento.data_realizacao.strftime('%Y-%m-%d'),
            'assunto': treinamento.assunto
        }
        for treinamento in treinamentos
    ]
    return JsonResponse(data, safe=False)


# views.py

def imprimir_treinamento(request, treinamento_id):
    # Corrigido para utilizar o parâmetro correto treinamento_id
    avaliacao = get_object_or_404(AvaliacaoTreinamento, id=treinamento_id)
    funcionario = avaliacao.funcionario  
    
    context = {
        'avaliacao': avaliacao,
        'opcoes_conhecimento': AvaliacaoTreinamento.OPCOES_CONHECIMENTO,
        'opcoes_aplicacao': AvaliacaoTreinamento.OPCOES_APLICACAO,
        'opcoes_resultados': AvaliacaoTreinamento.OPCOES_RESULTADOS,
        'responsavel_funcionario': funcionario.responsavel,

    }
    return render(request, 'avaliacao_treinamento/impressao_treinamento.html', context)



def excluir_avaliacao(request, id):
    avaliacao = get_object_or_404(AvaliacaoTreinamento, id=id)
    avaliacao.delete()
    return redirect('lista_avaliacoes')