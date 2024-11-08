from django.shortcuts import render, redirect, get_object_or_404
from Funcionario.models import AvaliacaoExperiencia, Funcionario
from Funcionario.forms import AvaliacaoExperienciaForm
from django.contrib import messages
from django.urls import reverse


def lista_avaliacao_experiencia(request):
    # Recupera todas as avaliações de experiência
    avaliacoes = AvaliacaoExperiencia.objects.all()

    # Filtros opcionais
    funcionario_id = request.GET.get('funcionario')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    # Aplica o filtro por funcionário, se fornecido
    if funcionario_id:
        avaliacoes = avaliacoes.filter(funcionario_id=funcionario_id)
    
    # Aplica o filtro por período de data, se fornecido
    if data_inicio and data_fim:
        avaliacoes = avaliacoes.filter(data_avaliacao__range=[data_inicio, data_fim])

    # Debug: Verifica o conteúdo de orientacao em cada avaliação
    for avaliacao in avaliacoes:
        print(f"Avaliação ID: {avaliacao.id}, Orientação: {avaliacao.orientacao}")  # <-- Verificação

    # Renderiza o template com as avaliações filtradas e todos os funcionários
    return render(request, 'avaliacao_desempenho_experiencia/lista_avaliacao_experiencia.html', {
        'avaliacoes': avaliacoes,
        'funcionarios': Funcionario.objects.all(),
    })

def cadastrar_avaliacao_experiencia(request):
    if request.method == 'POST':
        form = AvaliacaoExperienciaForm(request.POST)
        if form.is_valid():
            avaliacao = form.save(commit=False)  # Salva o formulário sem enviar para o banco ainda
            # Captura o valor do campo `status` do POST e atribui ao campo `orientacao`
            avaliacao.orientacao = request.POST.get('status')  # Usa o valor calculado pelo JS
            avaliacao.save()  # Salva no banco de dados
            return redirect('lista_avaliacao_experiencia')
    else:
        form = AvaliacaoExperienciaForm()

    return render(request, 'avaliacao_desempenho_experiencia/cadastrar_avaliacao_experiencia.html', {
        'form': form,
        'funcionarios': Funcionario.objects.all(),
    })

def editar_avaliacao_experiencia(request, id):
    # Busca a avaliação pelo ID ou retorna 404 se não encontrada
    avaliacao = get_object_or_404(AvaliacaoExperiencia, id=id)
    
    # Carrega o formulário com os dados da avaliação existente
    if request.method == 'POST':
        form = AvaliacaoExperienciaForm(request.POST, instance=avaliacao)
        if form.is_valid():
            # Salva as alterações no banco de dados
            form.save()
            messages.success(request, "Avaliação atualizada com sucesso!")
            return redirect(reverse('visualizar_avaliacao_experiencia', args=[avaliacao.id]))
        else:
            messages.error(request, "Erro ao atualizar a avaliação. Verifique os dados informados.")
    else:
        form = AvaliacaoExperienciaForm(instance=avaliacao)
    
    # Pega todos os funcionários para preencher o select de avaliador e avaliado
    funcionarios = Funcionario.objects.all()
    
    # Renderiza o template de edição com o formulário preenchido
    return render(request, 'avaliacao_desempenho_experiencia/editar_avaliacao_experiencia.html', {
        'form': form,
        'avaliacao': avaliacao,
        'funcionarios': funcionarios
    })

def excluir_avaliacao_experiencia(request, id):
    # Exclui uma avaliação de experiência
    avaliacao = get_object_or_404(AvaliacaoExperiencia, id=id)
    if request.method == "POST":
        avaliacao.delete()
        return redirect('lista_avaliacao_experiencia')
    return redirect('lista_avaliacao_experiencia')


def visualizar_avaliacao_experiencia(request, id):
    avaliacao = get_object_or_404(AvaliacaoExperiencia, id=id)

    # Passa o objeto de avaliação para o template
    return render(request, 'avaliacao_desempenho_experiencia/visualizar_avaliacao_experiencia.html', {
        'avaliacao': avaliacao
    })

def imprimir_avaliacao_experiencia(request, avaliacao_id):
    # Busca a avaliação pelo ID ou retorna 404 se não for encontrada
    avaliacao = get_object_or_404(AvaliacaoExperiencia, id=avaliacao_id)

    # Dados que serão passados para o template de impressão, ajustados conforme o conteúdo da imagem
    context = {
        'avaliacao': avaliacao,
        'opcoes_adaptacao_trabalho': {
            4: "Está plenamente identificado com as atividades do seu cargo e integrou-se perfeitamente às normas da Bras-Mol.",
            3: "Tem feito o possível para integrar-se no seu cargo e no próprio trabalho, tentando se adaptar às características da Bras-Mol.",
            2: "Precisa muito esforço para conseguir integrar-se ao seu cargo e aos requisitos administrativos da Bras-Mol.",
            1: "Mantém um comportamento oposto ao solicitado para seu cargo e demonstra ter sérias dificuldades de aceitação das características da Bras-Mol."
        },
        'opcoes_interesse': {
            4: "Parece vivamente interessado por seu novo trabalho.",
            3: "Apresenta um entusiasmo adequado, tendo em vista o seu pouco tempo de Bras-Mol.",
            2: "Dá a impressão de ser um funcionário que não entende a necessidade de estímulo para poder interessar-se pelo seu trabalho.",
            1: "Em várias ocasiões, apresenta uma falta total de entusiasmo e vontade de trabalhar."
        },
        'opcoes_relacionamento_social': {
            4: "Apresentou grande habilidade em conseguir amigos, mesmo com pouco tempo de Bras-Mol; todos já gostaram muito dele(a).",
            3: "Entrosou-se bem com os demais, foi aceito sem resistências.",
            2: "Está fazendo muito esforço para conseguir maior integração social com os colegas.",
            1: "Sente-se perdido entre os colegas, parece não ter sido aceito pelo grupo de trabalho."
        },
        'opcoes_capacidade_aprendizagem': {
            4: "Parece especialmente habilitado para o cargo em que está, tem facilidade em aprender, permitindo-lhe executar sem falhas.",
            3: "Parece adequado para o cargo ao qual foi encaminhado, aprende suas tarefas sem grandes problemas.",
            2: "Está conseguindo compreender o que lhe foi ensinado à custa de grande esforço pessoal, necessitando repetir-se a mesma coisa várias vezes.",
            1: "É tão difícil de compreender o que o estão ensinando que parece não ter a mínima capacidade para o trabalho."
        }
    }
    
    # Renderiza o template com os dados
    return render(request, 'avaliacao_desempenho_experiencia/impressao_avaliacao_experiencia.html', context)