from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpRequest
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

from ..models.jobrotation_assessments import JobRotationAvaliacaoColaborador, JobRotationAvaliacaoGestor
from ..forms.jobrotation_assessment_forms import AvaliacaoColaboradorForm, AvaliacaoGestorForm
# Funcionario/views/jobrotation_assessment_views.py

from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages

from ..models.jobrotation_assessments import (
    JobRotationAvaliacaoColaborador, JobRotationAvaliacaoGestor
)
from ..forms.jobrotation_assessment_forms import (
    AvaliacaoColaboradorForm, AvaliacaoGestorForm
)

# =========================
# LISTA (admin) – mostra as duas listas na mesma página
# =========================
@login_required
@permission_required(
    # basta ter permissão de ver uma das duas avaliações para entrar
    perm=("Funcionario.view_jobrotationavaliacaocolaborador"),
    raise_exception=True
)
def lista_avaliacoes(request):
    # se o usuário não tiver a perm de colaborador, tenta a de gestor
    if not request.user.has_perm("Funcionario.view_jobrotationavaliacaocolaborador") \
       and not request.user.has_perm("Funcionario.view_jobrotationavaliacaogestor"):
        # força 403 se não tiver nenhuma
        return render(request, "403.html", status=403)

    qs_col = JobRotationAvaliacaoColaborador.objects.select_related(
        "jobrotation", "jobrotation__funcionario"
    ).order_by("-created")

    qs_ges = JobRotationAvaliacaoGestor.objects.select_related(
        "jobrotation", "jobrotation__gestor_responsavel"
    ).order_by("-created")

    # paginação independente
    page_col = Paginator(qs_col, 10).get_page(request.GET.get("page_col"))
    page_ges = Paginator(qs_ges, 10).get_page(request.GET.get("page_ges"))

    return render(
        request,
        "jobrotation/lista_avaliacoes_jobrotation.html",   # template genérico
        {"colabs": page_col, "gestores": page_ges, "page_col": page_col, "page_ges": page_ges},
    )


# =========================
# COLABORADOR – Visualizar / Editar (admin)
# =========================
@login_required
@permission_required("Funcionario.view_jobrotationavaliacaocolaborador", raise_exception=True)
def visualizar_avaliacao_colaborador_admin(request, pk: int):
    obj = get_object_or_404(JobRotationAvaliacaoColaborador, pk=pk)
    return render(request, "jobrotation/avaliacao_colaborador_ver.html", {"obj": obj})

@login_required
@permission_required("Funcionario.change_jobrotationavaliacaocolaborador", raise_exception=True)
def editar_avaliacao_colaborador_admin(request, pk: int):
    obj = get_object_or_404(JobRotationAvaliacaoColaborador, pk=pk)
    if request.method == "POST":
        form = AvaliacaoColaboradorForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Avaliação do colaborador atualizada.")
            return redirect("visualizar_avaliacao_colaborador", pk=obj.pk)
        messages.error(request, "Verifique os campos destacados.")
    else:
        form = AvaliacaoColaboradorForm(instance=obj)
    return render(request, "jobrotation/avaliacao_colaborador_form_admin.html", {"form": form, "obj": obj})


# =========================
# GESTOR – Visualizar / Editar (admin)
# =========================
@login_required
@permission_required("Funcionario.view_jobrotationavaliacaogestor", raise_exception=True)
def visualizar_avaliacao_gestor_admin(request, pk: int):
    obj = get_object_or_404(JobRotationAvaliacaoGestor, pk=pk)
    return render(request, "jobrotation/avaliacao_gestor_ver.html", {"obj": obj})

@login_required
@permission_required("Funcionario.change_jobrotationavaliacaogestor", raise_exception=True)
def editar_avaliacao_gestor_admin(request, pk: int):
    obj = get_object_or_404(JobRotationAvaliacaoGestor, pk=pk)
    if request.method == "POST":
        form = AvaliacaoGestorForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Avaliação do gestor atualizada.")
            return redirect("visualizar_avaliacao_gestor", pk=obj.pk)
        messages.error(request, "Verifique os campos destacados.")
    else:
        form = AvaliacaoGestorForm(instance=obj)
    return render(request, "jobrotation/avaliacao_gestor_form_admin.html", {"form": form, "obj": obj})


def preencher_avaliacao_colaborador(request: HttpRequest, token: str):
    obj = get_object_or_404(JobRotationAvaliacaoColaborador, token_publico=token)
    if request.method == "POST":
        form = AvaliacaoColaboradorForm(request.POST, instance=obj)
        if form.is_valid():
            av = form.save(commit=False)
            # assinatura no mesmo submit (opcional)
            if request.POST.get("confirmar_assinatura") == "on" and not av.assinado:
                av.marcar_como_assinado(
                    nome=av.colaborador_nome or (av.jobrotation.funcionario and av.jobrotation.funcionario.nome) or "Colaborador",
                    email=(av.jobrotation.funcionario and av.jobrotation.funcionario.email) or None,
                    ip=request.META.get("REMOTE_ADDR"),
                )
            av.save()
            messages.success(request, "Avaliação enviada com sucesso.")
            return render(request, "jobrotation/avaliacao_colaborador_sucesso.html", {"obj": av})
        messages.error(request, "Verifique os campos destacados.")
    else:
        form = AvaliacaoColaboradorForm(instance=obj)
    return render(request, "jobrotation/avaliacao_colaborador_form.html", {"form": form, "obj": obj})


def preencher_avaliacao_gestor(request: HttpRequest, token: str):
    obj = get_object_or_404(JobRotationAvaliacaoGestor, token_publico=token)
    if request.method == "POST":
        form = AvaliacaoGestorForm(request.POST, instance=obj)
        if form.is_valid():
            av = form.save(commit=False)
            if request.POST.get("confirmar_assinatura") == "on" and not av.assinado:
                av.marcar_como_assinado(
                    nome=av.gestor_nome or (av.jobrotation.gestor_responsavel and av.jobrotation.gestor_responsavel.nome) or "Gestor",
                    email=(av.jobrotation.gestor_responsavel and av.jobrotation.gestor_responsavel.email) or None,
                    ip=request.META.get("REMOTE_ADDR"),
                )
            av.save()
            messages.success(request, "Avaliação enviada com sucesso.")
            return render(request, "jobrotation/avaliacao_gestor_sucesso.html", {"obj": av})
        messages.error(request, "Verifique os campos destacados.")
    else:
        form = AvaliacaoGestorForm(instance=obj)
    return render(request, "jobrotation/avaliacao_gestor_form.html", {"form": form, "obj": obj})
