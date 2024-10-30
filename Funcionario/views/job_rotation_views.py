from datetime import timezone
from venv import logger
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from Funcionario.models import JobRotationEvaluation, Funcionario, Cargo
from Funcionario.forms import JobRotationEvaluationForm

def lista_jobrotation_evaluation(request):
    evaluations = JobRotationEvaluation.objects.all()
    return render(request, 'lista_jobrotation_evaluation.html', {'evaluations': evaluations})

def cadastrar_jobrotation_evaluation(request):
    if request.method == 'POST':
        form = JobRotationEvaluationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Avaliação de Job Rotation cadastrada com sucesso!')
            return redirect('lista_jobrotation_evaluation')
    else:
        form = JobRotationEvaluationForm()
    return render(request, 'cadastrar_jobrotation_evaluation.html', {'form': form})

def excluir_jobrotation(request, id):
    job_rotation = get_object_or_404(JobRotationEvaluation, id=id)
    if request.method == 'POST':
        job_rotation.delete()
        messages.success(request, 'Registro de Job Rotation excluído com sucesso!')
    return redirect('lista_jobrotation_evaluation')

def visualizar_jobrotation_evaluation(request, id):
    job_rotation = get_object_or_404(JobRotationEvaluation, id=id)
    cursos_realizados = job_rotation.cursos_realizados if job_rotation.cursos_realizados else []

    context = {
        'job_rotation': job_rotation,
        'cursos_realizados': cursos_realizados,
        'competencias': job_rotation.competencias or "Nenhuma competência informada",
        'data_ultima_avaliacao': job_rotation.data_ultima_avaliacao,
        'status_ultima_avaliacao': job_rotation.status_ultima_avaliacao or "Nenhum status encontrado",
        'nova_funcao': job_rotation.nova_funcao.nome if job_rotation.nova_funcao else "N/A",
        'data_geracao': timezone.now(),  # Adiciona a data atual
    }

    return render(request, 'visualizar_jobrotation_evaluation.html', context)


def lista_jobrotation_evaluation(request):
    logger.error("==> Teste de log ERROR dentro da view lista_jobrotation_evaluation.")
    logger.info("==> Teste de log INFO dentro da view lista_jobrotation_evaluation.")
    logger.debug("==> Teste de log DEBUG dentro da view lista_jobrotation_evaluation.")
    
    evaluations = JobRotationEvaluation.objects.all()
    logger.info(f"Total de avaliações encontradas: {evaluations.count()}")
    
    return render(request, 'lista_jobrotation_evaluation.html', {'evaluations': evaluations})


def editar_jobrotation_evaluation(request, id):
    evaluation = get_object_or_404(JobRotationEvaluation, id=id)
    if request.method == 'POST':
        form = JobRotationEvaluationForm(request.POST, instance=evaluation)
        if form.is_valid():
            form.save()
            messages.success(request, 'Avaliação de Job Rotation atualizada com sucesso!')
            return redirect('lista_jobrotation_evaluation')  # Redireciona para a lista após a edição
    else:
        form = JobRotationEvaluationForm(instance=evaluation)
    return render(request, 'editar_jobrotation_evaluation.html', {'form': form, 'evaluation': evaluation})