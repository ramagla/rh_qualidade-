


from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from Funcionario import models
from Funcionario.forms import AvaliacaoTreinamentoForm
from Funcionario.models import AvaliacaoTreinamento, Funcionario, ListaPresenca
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator


def lista_avaliacoes(request):
    avaliacoes_treinamento = AvaliacaoTreinamento.objects.all().order_by('funcionario__nome')  # Ordena por nome do funcionário
    
    
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

    # Contadores para os cards
    total_avaliacoes = avaliacoes_treinamento.count()
    muito_eficaz = avaliacoes_treinamento.filter(avaliacao_geral=5).count()
    eficaz = avaliacoes_treinamento.filter(avaliacao_geral=2).count()
    pouco_eficaz = avaliacoes_treinamento.filter(avaliacao_geral=1).count()

    # Paginação
    paginator = Paginator(avaliacoes_treinamento, 10)  # 10 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

     # Busca apenas funcionários e treinamentos com avaliações no conjunto filtrado
    funcionarios_ativos = Funcionario.objects.filter(id__in=avaliacoes_treinamento.values_list('funcionario_id', flat=True).distinct())
    listas_presenca = Treinamento.objects.filter(
        id__in=AvaliacaoTreinamento.objects.values_list('treinamento_id', flat=True).distinct()
    )

    # Renderiza o template com os filtros aplicados
    return render(request, 'avaliacao_treinamento/lista_avaliacao.html', {
        'avaliacoes_treinamento': page_obj,  # Paginação aplicada
        'funcionarios_ativos': funcionarios_ativos,
        'listas_presenca': listas_presenca,
        'total_avaliacoes': total_avaliacoes,
        'muito_eficaz': muito_eficaz,
        'eficaz': eficaz,
        'pouco_eficaz': pouco_eficaz,
        'page_obj': page_obj  # Enviado para o template para controle do paginator
    })


from django.shortcuts import render, redirect
from django.contrib import messages
from Funcionario.forms import AvaliacaoTreinamentoForm
from Funcionario.models import Funcionario, Treinamento

def cadastrar_avaliacao(request):
    # Carregar todos os funcionários ordenados por nome
    funcionarios = Funcionario.objects.filter(status="Ativo").order_by('nome')


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
        # Captura o ID do funcionário selecionado
        funcionario_id = request.POST.get('funcionario')

        # Cria o formulário com os dados do POST
        form = AvaliacaoTreinamentoForm(request.POST)

        # Ajusta o queryset dinamicamente para o campo treinamento
        if funcionario_id:
            form.fields['treinamento'].queryset = Treinamento.objects.filter(funcionarios__id=funcionario_id)

        # Verifica se o formulário é válido
        if form.is_valid():
            form.save()
            messages.success(request, "Avaliação cadastrada com sucesso!")
            return redirect('lista_avaliacoes')
        else:
            messages.error(request, "Erro ao cadastrar a avaliação. Verifique os campos.")
    else:
        # Cria um formulário vazio para o GET
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
    funcionarios = Funcionario.objects.order_by('nome')  # Carrega todos os funcionários ordenados por nome

    # Inicializa os treinamentos vinculados ao funcionário da avaliação
    treinamentos = Treinamento.objects.filter(funcionarios=avaliacao.funcionario)

    if request.method == 'POST':
        # Carrega o formulário com os dados enviados
        form = AvaliacaoTreinamentoForm(request.POST, instance=avaliacao)

        # Obtém o funcionário selecionado no formulário
        funcionario_id = request.POST.get('funcionario')

        # Ajusta dinamicamente o queryset do campo treinamento com base no funcionário selecionado
        if funcionario_id:
            form.fields['treinamento'].queryset = Treinamento.objects.filter(funcionarios__id=funcionario_id)
        else:
            form.fields['treinamento'].queryset = Treinamento.objects.none()

        if form.is_valid():
            # Salva a avaliação com os dados atualizados
            form.save()
            messages.success(request, "Avaliação atualizada com sucesso!")
            return redirect('lista_avaliacoes')  # Redireciona para a lista de avaliações
        else:
            messages.error(request, "Erro ao atualizar a avaliação. Verifique os campos.")
    else:
        # Inicializa o formulário com os dados existentes
        form = AvaliacaoTreinamentoForm(instance=avaliacao)

        # Define o queryset do treinamento com base no funcionário da avaliação existente
        form.fields['treinamento'].queryset = treinamentos

    # Renderiza o template com os dados necessários
    return render(request, 'avaliacao_treinamento/editar_avaliacao.html', {
        'form': form,
        'avaliacao': avaliacao,
        'funcionarios': funcionarios,
        'treinamentos': treinamentos,  # Envia os treinamentos disponíveis para o template
        'opcoes_conhecimento': AvaliacaoTreinamento.OPCOES_CONHECIMENTO,
        'opcoes_aplicacao': AvaliacaoTreinamento.OPCOES_APLICACAO,
        'opcoes_resultados': AvaliacaoTreinamento.OPCOES_RESULTADOS,
    })
    



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

     # Verifica se há um treinamento associado
    treinamento = avaliacao.treinamento if avaliacao.treinamento else None

    return render(request, 'avaliacao_treinamento/visualizar_avaliacao.html', {
        'avaliacao': avaliacao,
        'grau_conhecimento': grau_conhecimento,
        'aplicacao_conceitos': aplicacao_conceitos,
        'resultados_obtidos': resultados_obtidos,
        'melhorias': avaliacao.descricao_melhorias,
        'avaliacao_geral': avaliacao_geral,
        'treinamento': treinamento,
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


def imprimir_treinamento(request, treinamento_id):
    # Obtém a avaliação de treinamento ou retorna 404
    avaliacao = get_object_or_404(AvaliacaoTreinamento, id=treinamento_id)

    # Verifica se o funcionário relacionado existe
    funcionario = avaliacao.funcionario if avaliacao.funcionario else None

    # Define o contexto para o template
    context = {
        'avaliacao': avaliacao,
        'opcoes_conhecimento': AvaliacaoTreinamento.OPCOES_CONHECIMENTO,
        'opcoes_aplicacao': AvaliacaoTreinamento.OPCOES_APLICACAO,
        'opcoes_resultados': AvaliacaoTreinamento.OPCOES_RESULTADOS,
        'responsavel_funcionario': funcionario.responsavel if funcionario else "Não definido",
    }

    # Renderiza o template de impressão
    return render(request, 'avaliacao_treinamento/impressao_treinamento.html', context)


def excluir_avaliacao(request, id):
    # Obtém a avaliação ou retorna 404
    avaliacao = get_object_or_404(AvaliacaoTreinamento, id=id)

    # Exclui a avaliação e redireciona para a lista
    avaliacao.delete()
    return redirect('lista_avaliacoes')
