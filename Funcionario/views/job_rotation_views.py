from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponse,Http404
from weasyprint import HTML

from django.contrib import messages
from django.urls import reverse_lazy
from datetime import timezone, timedelta
from Funcionario.models import JobRotationEvaluation, Funcionario, Cargo
from Funcionario.forms import JobRotationEvaluationForm
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required


@login_required
def lista_jobrotation_evaluation(request):
    # Obtem todas as avaliações
    evaluations = JobRotationEvaluation.objects.select_related('cargo_atual').all()

    # Filtros opcionais
    funcionario_id = request.GET.get('funcionario')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    # Filtrar por funcionário
    if funcionario_id:
        evaluations = evaluations.filter(funcionario_id=funcionario_id)

    # Filtrar por data
    if data_inicio and data_fim:
        evaluations = evaluations.filter(data_inicio__range=[data_inicio, data_fim])

    # Paginação
    paginator = Paginator(evaluations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Filtra funcionários que têm avaliações
    funcionarios = Funcionario.objects.filter(
        id__in=evaluations.values_list('funcionario_id', flat=True)
    )

    # Dados para os cards
    total_avaliacoes = evaluations.count()
    apto = evaluations.filter(avaliacao_rh="Apto").count()
    prorrogar = evaluations.filter(avaliacao_rh="Prorrogar TN").count()
    inapto = evaluations.filter(avaliacao_rh="Inapto").count()

    # Adiciona lógica para campos opcionais
    for evaluation in evaluations:
        evaluation.nova_funcao_nome = (
            evaluation.nova_funcao.nome if evaluation.nova_funcao else "Não informado"
        )
        evaluation.local_trabalho_nome = (
            evaluation.local_trabalho if evaluation.local_trabalho else "Não informado"
        )


    # Renderiza o template
    return render(request, 'jobrotation/lista_jobrotation_evaluation.html', {
        'evaluations': page_obj,
        'page_obj': page_obj,
        'funcionarios': funcionarios,
        'total_avaliacoes': total_avaliacoes,
        'apto': apto,
        'prorrogar': prorrogar,
        'inapto': inapto,
    })


# Cadastra nova avaliação de Job Rotation
@login_required
def cadastrar_jobrotation_evaluation(request):
    if request.method == 'POST':
        form = JobRotationEvaluationForm(request.POST)
        if form.is_valid():
            job_rotation = form.save()

            # Verifica se a avaliação do RH é "Prorrogar"
            if form.cleaned_data['avaliacao_rh'] == 'Prorrogar':
                dias_prorrogacao = form.cleaned_data.get('dias_prorrogacao', 0)
                print("Dias de Prorrogação:", dias_prorrogacao)  # Log para verificar o valor

                # Lógica para tratar prorrogação, caso haja necessidade de atualização
                # Exemplo: Atualize o campo 'termino_previsto' com a prorrogação de dias
                if dias_prorrogacao > 0:
                    novo_termino = job_rotation.termino_previsto + timedelta(days=dias_prorrogacao)
                    job_rotation.termino_previsto = novo_termino
                    job_rotation.save()

            # Verifica se a avaliação do RH é "Apto"
            elif form.cleaned_data['avaliacao_rh'] == 'Apto':
                funcionario_id = form.cleaned_data['funcionario'].id
                novo_cargo_id = form.cleaned_data['nova_funcao'].id
                Funcionario.objects.filter(id=funcionario_id).update(cargo_atual_id=novo_cargo_id)
                messages.success(request, 'Cargo do funcionário atualizado com sucesso!')

            # Caso a avaliação do RH seja 'EmAndamento' ou 'Inapto', outros tratamentos podem ser aplicados
            # Se desejar adicionar outra lógica, como tratar datas, etc, também pode ser feito aqui

            return redirect('lista_jobrotation_evaluation')
        else:
            messages.error(request, 'Erro ao salvar a avaliação de Job Rotation.')
    else:
        form = JobRotationEvaluationForm()

    lista_cargos = Cargo.objects.all().order_by('nome')
    funcionarios = Funcionario.objects.filter(status='Ativo').order_by('nome')


    return render(request, 'jobrotation/cadastrar_jobrotation_evaluation.html', {
        'form': form,
        'lista_cargos': lista_cargos,
        'funcionarios': funcionarios
    })

# Exclui uma avaliação de Job Rotation
@login_required
def excluir_jobrotation(request, id):
    job_rotation = get_object_or_404(JobRotationEvaluation, id=id)
    if request.method == 'POST':
        job_rotation.delete()
        messages.success(request, 'Registro de Job Rotation excluído com sucesso!')
    return redirect(reverse_lazy('lista_jobrotation_evaluation'))
@login_required
def visualizar_jobrotation_evaluation(request, id):
    evaluation = get_object_or_404(JobRotationEvaluation, id=id)
    return render(request, 'jobrotation/visualizar_jobrotation_evaluation.html', {'evaluation': evaluation})
@login_required
def editar_jobrotation_evaluation(request, id):
    # Carregar a avaliação de Job Rotation que será editada
    evaluation = get_object_or_404(JobRotationEvaluation, id=id)

    if request.method == 'POST':
        form = JobRotationEvaluationForm(request.POST, instance=evaluation)
        
        if form.is_valid():
            form.save()  # Salva a avaliação atualizada
            messages.success(request, 'Avaliação de Job Rotation atualizada com sucesso!')
            return redirect('lista_jobrotation_evaluation')  # Redireciona para a lista de avaliações
        else:
            # Caso o formulário não seja válido, exibe uma mensagem de erro
            messages.error(request, 'Erro ao atualizar a avaliação de Job Rotation.')
            print(form.errors)  # Verifique os erros do formulário no terminal

    else:
        # Se o método for GET, carregue a avaliação e o formulário correspondente
        form = JobRotationEvaluationForm(instance=evaluation)

    # Carregar os dados adicionais para o template, como lista de cargos e funcionários
    lista_cargos = Cargo.objects.all()
    funcionarios = Funcionario.objects.all()

    # Enviar os dados para o template de edição
    return render(request, 'jobrotation/editar_jobrotation_evaluation.html', {
        'form': form,
        'evaluation': evaluation,
        'lista_cargos': lista_cargos,
        'funcionarios': funcionarios
    })

@login_required
def imprimir_jobrotation_evaluation(request, id):
    # Obtenha a avaliação de Job Rotation usando o ID
    evaluation = get_object_or_404(JobRotationEvaluation, id=id)

    # Obtenha a última revisão associada ao novo cargo (nova_funcao)
    ultima_revisao = (
        evaluation.nova_funcao.revisoes.order_by('-data_revisao').first()
        if evaluation.nova_funcao else None
    )

    # Formatar a descrição conforme o formato solicitado
    descricao_cargo = "Descrição de cargo não disponível"
    if evaluation.nova_funcao and ultima_revisao:
        numero_dc = evaluation.nova_funcao.numero_dc
        nome_cargo = evaluation.nova_funcao.nome
        numero_revisao = ultima_revisao.numero_revisao
        descricao_cargo = f"Conforme: Descrição de cargo N° {numero_dc} - Nome: {nome_cargo}, Última Revisão N° {numero_revisao}"

        

    # Verifica se o usuário solicitou o download em PDF
    if request.GET.get('download') == 'pdf':
        # Renderiza o HTML para o PDF
        html_string = render_to_string('jobrotation/imprimir_jobrotation_evaluation.html', {
            'evaluation': evaluation,
            'ultima_revisao': ultima_revisao,
            'descricao_cargo': descricao_cargo,
        })
        html = HTML(string=html_string)
        pdf = html.write_pdf()

        # Retorna o PDF como resposta
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="avaliacao_job_rotation_{evaluation.funcionario.nome}.pdf"'
        return response
    else:
        # Renderiza o HTML normalmente para visualização
        return render(request, 'jobrotation/imprimir_jobrotation_evaluation.html', {
            'evaluation': evaluation,
            'ultima_revisao': ultima_revisao,
            'descricao_cargo': descricao_cargo,
        })