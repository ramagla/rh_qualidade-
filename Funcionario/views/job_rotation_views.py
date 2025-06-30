# Standard
from datetime import timedelta

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.timezone import now

# Terceiros
from weasyprint import HTML

# Local
from Funcionario.forms import JobRotationEvaluationForm
from Funcionario.models import Cargo, Funcionario, JobRotationEvaluation
from Funcionario.utils.jobrotation_utils import (
    filtrar_avaliacoes,
    obter_totais,
    gerar_descricao_cargo
)


@login_required
def lista_jobrotation_evaluation(request):
    """Lista todas as avaliações de Job Rotation com filtros e paginação."""
    evaluations = filtrar_avaliacoes(request)
    paginator = Paginator(evaluations, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    funcionarios = Funcionario.objects.filter(
        id__in=evaluations.values_list("funcionario_id", flat=True)
    )

    totais = obter_totais(evaluations)

    return render(
        request,
        "jobrotation/lista_jobrotation_evaluation.html",
        {
            "evaluations": page_obj,
            "page_obj": page_obj,
            "funcionarios": funcionarios,
            **totais,
        },
    )


@login_required
def cadastrar_jobrotation_evaluation(request):
    """Cadastra uma nova avaliação de Job Rotation."""
    if request.method == "POST":
        form = JobRotationEvaluationForm(request.POST)
        if form.is_valid():
            job_rotation = form.save()
            if form.cleaned_data["avaliacao_rh"] == "Prorrogar":
                dias = form.cleaned_data.get("dias_prorrogacao", 0)
                if dias > 0:
                    job_rotation.termino_previsto += timedelta(days=dias)
                    job_rotation.save()

            elif form.cleaned_data["avaliacao_rh"] == "Apto":
                funcionario_id = form.cleaned_data["funcionario"].id
                novo_cargo_id = form.cleaned_data["nova_funcao"].id
                Funcionario.objects.filter(id=funcionario_id).update(
                    cargo_atual_id=novo_cargo_id
                )
                messages.success(request, "Cargo do funcionário atualizado com sucesso!")

            return redirect("lista_jobrotation_evaluation")
        messages.error(request, "Erro ao salvar a avaliação de Job Rotation.")
    else:
        form = JobRotationEvaluationForm()

    lista_cargos = Cargo.objects.order_by("nome")
    funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")

    return render(
        request,
        "jobrotation/form_jobrotation_evaluation.html",
        {"form": form, "lista_cargos": lista_cargos, "funcionarios": funcionarios},
    )


@login_required
def editar_jobrotation_evaluation(request, id):
    """Edita uma avaliação de Job Rotation existente."""
    evaluation = get_object_or_404(JobRotationEvaluation, id=id)
    if request.method == "POST":
        form = JobRotationEvaluationForm(request.POST, instance=evaluation)
        if form.is_valid():
            form.save()
            messages.success(request, "Avaliação de Job Rotation atualizada com sucesso!")
            return redirect("lista_jobrotation_evaluation")
        messages.error(request, "Erro ao atualizar a avaliação de Job Rotation.")
    else:
        form = JobRotationEvaluationForm(instance=evaluation)

    lista_cargos = Cargo.objects.all()
    funcionarios = Funcionario.objects.all()

    return render(
        request,
        "jobrotation/form_jobrotation_evaluation.html",
        {
            "form": form,
            "evaluation": evaluation,
            "lista_cargos": lista_cargos,
            "funcionarios": funcionarios,
            "edicao": True,
        },
    )


@login_required
def excluir_jobrotation(request, id):
    """Exclui uma avaliação de Job Rotation."""
    job_rotation = get_object_or_404(JobRotationEvaluation, id=id)
    if request.method == "POST":
        job_rotation.delete()
        messages.success(request, "Registro de Job Rotation excluído com sucesso!")
    return redirect(reverse_lazy("lista_jobrotation_evaluation"))


@login_required
def visualizar_jobrotation_evaluation(request, id):
    """Exibe os detalhes de uma avaliação de Job Rotation."""
    evaluation = get_object_or_404(JobRotationEvaluation, id=id)
    return render(
        request,
        "jobrotation/visualizar_jobrotation_evaluation.html",
        {"evaluation": evaluation, "now": now()},
    )


@login_required
def imprimir_jobrotation_evaluation(request, id):
    """Imprime (ou exporta em PDF) os dados de uma avaliação de Job Rotation."""
    evaluation = get_object_or_404(JobRotationEvaluation, id=id)
    descricao_cargo, ultima_revisao = gerar_descricao_cargo(evaluation)

    context = {
        "evaluation": evaluation,
        "ultima_revisao": ultima_revisao,
        "descricao_cargo": descricao_cargo,
    }

    if request.GET.get("download") == "pdf":
        html_string = render_to_string("jobrotation/imprimir_jobrotation_evaluation.html", context)
        pdf = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="avaliacao_job_rotation_{evaluation.funcionario.nome}.pdf"'
        )
        return response

    return render(request, "jobrotation/imprimir_jobrotation_evaluation.html", context)
