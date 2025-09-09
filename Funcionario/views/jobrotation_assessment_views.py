# Funcionario/views/jobrotation_assessment_views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone

from ..models.job_rotation_evaluation import JobRotationEvaluation
from ..models.jobrotation_assessments import (
    JobRotationAvaliacaoColaborador,
    JobRotationAvaliacaoGestor,
)
from ..forms.jobrotation_assessment_forms import (
    AvaliacaoColaboradorForm,
    AvaliacaoGestorForm,
    SelecionarJobRotationForm,
)

# Assinatura eletrônica (mesma sistemática da OD)
from assinatura_eletronica.models import AssinaturaEletronica
from assinatura_eletronica.utils import gerar_assinatura, gerar_qrcode_base64


# ============================================================
# Helpers
# ============================================================
def _assinatura_qr_dict(request, origem_model: str, origem_id: int):
    """
    Retorna dicionário com dados/QR da última assinatura registrada
    para o par (origem_model, origem_id). Se não houver, devolve None.
    """
    try:
        assinatura = (
            AssinaturaEletronica.objects
            .filter(origem_model=origem_model, origem_id=origem_id)
            .latest("data_assinatura")
        )
        url_validacao = request.build_absolute_uri(
            reverse("validar_assinatura", args=[assinatura.hash])
        )
        return {
            "nome": assinatura.usuario.get_full_name() if assinatura.usuario else "",
            "email": assinatura.usuario.email if assinatura.usuario else "",
            "data": assinatura.data_assinatura,
            "hash": assinatura.hash,
            "qr": gerar_qrcode_base64(url_validacao),
        }
    except AssinaturaEletronica.DoesNotExist:
        return None


def _carimbar_e_assinar(model_instance, user, conteudo: str):
    """
    Carimba os campos de assinatura no objeto (quem salvou assina),
    gera hash via gerar_assinatura e registra/garante a AssinaturaEletronica.
    """
    model_instance.assinante_nome = user.get_full_name() or user.username
    model_instance.assinante_email = user.email
    model_instance.assinado_em = timezone.now()
    model_instance.assinado_ip = getattr(user, "last_login_ip", None)  # opcional
    model_instance.assinado = True
    model_instance.save()  # garante PK

    hash_valido = gerar_assinatura(model_instance, user)
    model_instance.assinado_hash = hash_valido
    model_instance.save(update_fields=["assinado_hash"])

    AssinaturaEletronica.objects.get_or_create(
        hash=hash_valido,
        defaults={
            "conteudo": conteudo,
            "usuario": user,
            "origem_model": model_instance.__class__.__name__,
            "origem_id": model_instance.pk,
        },
    )
    return hash_valido


# ============================================================
# LISTA (admin)
# ============================================================
@login_required
@permission_required("Funcionario.view_jobrotationavaliacaocolaborador", raise_exception=True)
def lista_avaliacoes(request: HttpRequest):
    """
    Lista as avaliações de Colaborador e Gestor em páginas separadas
    (duas grids na mesma tela).
    """
    # Se o usuário não tiver permissão de Gestor, tudo bem — mostramos
    # apenas o que ele pode ver. (A permissão de Colaborador já é exigida
    # pelo decorator acima.)
    qs_col = JobRotationAvaliacaoColaborador.objects.select_related(
        "jobrotation", "jobrotation__funcionario"
    ).order_by("-created")

    qs_ges = JobRotationAvaliacaoGestor.objects.select_related(
        "jobrotation", "jobrotation__gestor_responsavel"
    ).order_by("-created")

    page_col = Paginator(qs_col, 10).get_page(request.GET.get("page_col"))
    page_ges = Paginator(qs_ges, 10).get_page(request.GET.get("page_ges"))

    return render(
        request,
        "jobrotation/lista_avaliacoes_jobrotation.html",
        {
            "colabs": page_col,
            "gestores": page_ges,
            "page_col": page_col,
            "page_ges": page_ges,
        },
    )


# ============================================================
# COLABORADOR – Visualizar / Editar (admin individual)
# ============================================================
@login_required
@permission_required("Funcionario.view_jobrotationavaliacaocolaborador", raise_exception=True)
def visualizar_avaliacao_colaborador_admin(request: HttpRequest, pk: int):
    obj = get_object_or_404(JobRotationAvaliacaoColaborador, pk=pk)
    assinatura_qr = _assinatura_qr_dict(request, "JobRotationAvaliacaoColaborador", obj.pk)
    return render(
        request,
        "jobrotation/avaliacao_colaborador_ver.html",
        {"obj": obj, "assinatura_qr": assinatura_qr},
    )


@login_required
@permission_required("Funcionario.change_jobrotationavaliacaocolaborador", raise_exception=True)
def editar_avaliacao_colaborador_admin(request: HttpRequest, pk: int):
    obj = get_object_or_404(JobRotationAvaliacaoColaborador, pk=pk)

    if request.method == "POST":
        form = AvaliacaoColaboradorForm(request.POST, instance=obj)
        if form.is_valid():
            av = form.save(commit=False)
            # Assinatura automática (sem checkbox), seguindo OD
            _carimbar_e_assinar(av, request.user, f"JR_COLAB|{av.jobrotation_id}|{av.pk or 'new'}")
            messages.success(request, "Avaliação do colaborador atualizada e assinada.")
            return redirect("visualizar_avaliacao_colaborador", pk=av.pk)
        messages.error(request, "Verifique os campos destacados.")
    else:
        form = AvaliacaoColaboradorForm(instance=obj)

    assinatura_qr = _assinatura_qr_dict(request, "JobRotationAvaliacaoColaborador", obj.pk)
    return render(
        request,
        "jobrotation/avaliacao_colaborador_form_admin.html",
        {"form": form, "obj": obj, "assinatura_qr": assinatura_qr},
    )


# ============================================================
# GESTOR – Visualizar / Editar (admin individual)
# ============================================================
@login_required
@permission_required("Funcionario.view_jobrotationavaliacaogestor", raise_exception=True)
def visualizar_avaliacao_gestor_admin(request: HttpRequest, pk: int):
    obj = get_object_or_404(JobRotationAvaliacaoGestor, pk=pk)
    assinatura_qr = _assinatura_qr_dict(request, "JobRotationAvaliacaoGestor", obj.pk)
    return render(
        request,
        "jobrotation/avaliacao_gestor_ver.html",
        {"obj": obj, "assinatura_qr": assinatura_qr},
    )


@login_required
@permission_required("Funcionario.change_jobrotationavaliacaogestor", raise_exception=True)
def editar_avaliacao_gestor_admin(request: HttpRequest, pk: int):
    obj = get_object_or_404(JobRotationAvaliacaoGestor, pk=pk)

    if request.method == "POST":
        form = AvaliacaoGestorForm(request.POST, instance=obj)
        if form.is_valid():
            av = form.save(commit=False)
            _carimbar_e_assinar(av, request.user, f"JR_GESTOR|{av.jobrotation_id}|{av.pk or 'new'}")
            messages.success(request, "Avaliação do gestor atualizada e assinada.")
            return redirect("visualizar_avaliacao_gestor", pk=av.pk)
        messages.error(request, "Verifique os campos destacados.")
    else:
        form = AvaliacaoGestorForm(instance=obj)

    assinatura_qr = _assinatura_qr_dict(request, "JobRotationAvaliacaoGestor", obj.pk)
    return render(
        request,
        "jobrotation/avaliacao_gestor_form_admin.html",
        {"form": form, "obj": obj, "assinatura_qr": assinatura_qr},
    )


# ============================================================
# PREENCHIMENTO PÚBLICO (token)
# ============================================================
def preencher_avaliacao_colaborador(request: HttpRequest, token: str):
    """
    Formulário público (via link com token). Sem checkbox.
    Se o usuário estiver autenticado, já assinamos eletronicamente.
    """
    obj = get_object_or_404(JobRotationAvaliacaoColaborador, token_publico=token)

    if request.method == "POST":
        form = AvaliacaoColaboradorForm(request.POST, instance=obj)
        if form.is_valid():
            av = form.save(commit=False)
            av.save()

            # Se autenticado, aplica assinatura eletrônica
            if request.user.is_authenticated:
                _carimbar_e_assinar(av, request.user, f"JR_COLAB|{av.jobrotation_id}|{av.pk}")

            messages.success(request, "Avaliação enviada com sucesso.")
            return render(request, "jobrotation/avaliacao_colaborador_sucesso.html", {"obj": av})
        messages.error(request, "Verifique os campos destacados.")
    else:
        form = AvaliacaoColaboradorForm(instance=obj)

    return render(request, "jobrotation/avaliacao_colaborador_form.html", {"form": form, "obj": obj})


def preencher_avaliacao_gestor(request: HttpRequest, token: str):
    """
    Formulário público (via link com token). Sem checkbox.
    Se o usuário estiver autenticado, já assinamos eletronicamente.
    """
    obj = get_object_or_404(JobRotationAvaliacaoGestor, token_publico=token)

    if request.method == "POST":
        form = AvaliacaoGestorForm(request.POST, instance=obj)
        if form.is_valid():
            av = form.save(commit=False)
            av.save()

            if request.user.is_authenticated:
                _carimbar_e_assinar(av, request.user, f"JR_GESTOR|{av.jobrotation_id}|{av.pk}")

            messages.success(request, "Avaliação enviada com sucesso.")
            return render(request, "jobrotation/avaliacao_gestor_sucesso.html", {"obj": av})
        messages.error(request, "Verifique os campos destacados.")
    else:
        form = AvaliacaoGestorForm(instance=obj)

    return render(request, "jobrotation/avaliacao_gestor_form.html", {"form": form, "obj": obj})


# ============================================================
# CADASTRAR em DUAS ABAS (admin)
# ============================================================
@login_required
@permission_required("Funcionario.add_jobrotationavaliacaocolaborador", raise_exception=True)
def cadastrar_avaliacoes_tabs_admin(request: HttpRequest, jobrotation_id: int | None = None):
    """
    Cadastra as avaliações (Colaborador/Gestor) em DUAS ABAS.
    - Sem jobrotation_id: exibe seletor (Seleção do JobRotationEvaluation)
    - Com jobrotation_id: abre direto as abas
    - Salva por aba e assina automaticamente (QR) quem salvou.
    """
    # 1) Seleção do JobRotationEvaluation (quando não veio ID)
    if not jobrotation_id:
        if request.method == "POST" and request.POST.get("etapa") == "selecionar_jr":
            sel = SelecionarJobRotationForm(request.POST)
            if sel.is_valid():
                jr = sel.cleaned_data["jobrotation"]
                return redirect("cadastrar_avaliacoes_jobrotation_tabs_por_jr", jobrotation_id=jr.id)
        else:
            sel = SelecionarJobRotationForm()
        return render(request, "jobrotation/avaliacoes_selecionar_jr.html", {"form": sel})

    # 2) Com ID informado: abre as abas
    jr = get_object_or_404(JobRotationEvaluation, pk=jobrotation_id)

    col_initial = {
        "colaborador_nome": getattr(jr.funcionario, "nome", ""),
        "cargo_anterior": getattr(jr.cargo_atual, "nome", ""),
        "cargo_atual": getattr(jr.nova_funcao, "nome", "") or getattr(jr.cargo_atual, "nome", ""),
        "setor_anterior": getattr(jr, "area", ""),
        "setor_atual": getattr(jr, "local_trabalho", ""),
    }
    ges_initial = {
        "gestor_nome": getattr(jr.gestor_responsavel, "nome", ""),
        "gestor_cargo": getattr(getattr(jr.gestor_responsavel, "cargo_atual", None), "nome", ""),
        "gestor_setor": getattr(jr.gestor_responsavel, "local_trabalho", ""),
        "colaborador_treinado": True,
    }

    form_col = AvaliacaoColaboradorForm(initial=col_initial)
    form_ges = AvaliacaoGestorForm(initial=ges_initial)
    active_tab = request.GET.get("tab") or "colaborador"

    if request.method == "POST":
        aba = request.POST.get("aba") or "colaborador"

        if aba == "colaborador":
            instancia = JobRotationAvaliacaoColaborador(jobrotation=jr)
            form_col = AvaliacaoColaboradorForm(request.POST, instance=instancia)
            if form_col.is_valid():
                obj = form_col.save(commit=False)
                obj.jobrotation = jr
                obj.save()
                _carimbar_e_assinar(obj, request.user, f"JR_COLAB|{jr.pk}|{obj.pk}")
                messages.success(request, "Avaliação do COLABORADOR cadastrada e assinada.")
                active_tab = "colaborador"
            else:
                messages.error(request, "Verifique os campos do COLABORADOR.")
                active_tab = "colaborador"

        elif aba == "gestor":
            instancia = JobRotationAvaliacaoGestor(jobrotation=jr)
            form_ges = AvaliacaoGestorForm(request.POST, instance=instancia)
            if form_ges.is_valid():
                obj = form_ges.save(commit=False)
                obj.jobrotation = jr
                obj.save()
                _carimbar_e_assinar(obj, request.user, f"JR_GESTOR|{jr.pk}|{obj.pk}")
                messages.success(request, "Avaliação do GESTOR cadastrada e assinada.")
                active_tab = "gestor"
            else:
                messages.error(request, "Verifique os campos do GESTOR.")
                active_tab = "gestor"

    # QR (se já houver algum registro salvo nesta sessão, exibir)
    assinatura_colab_qr = None
    assinatura_gestor_qr = None
    col_exist = JobRotationAvaliacaoColaborador.objects.filter(jobrotation=jr).order_by("-created").first()
    ges_exist = JobRotationAvaliacaoGestor.objects.filter(jobrotation=jr).order_by("-created").first()
    if col_exist and col_exist.assinado:
        dic = _assinatura_qr_dict(request, "JobRotationAvaliacaoColaborador", col_exist.pk)
        assinatura_colab_qr = dic["qr"] if dic else None
    if ges_exist and ges_exist.assinado:
        dic = _assinatura_qr_dict(request, "JobRotationAvaliacaoGestor", ges_exist.pk)
        assinatura_gestor_qr = dic["qr"] if dic else None

    contexto = {
        "titulo": "Cadastrar Avaliações de Job Rotation",
        "jobrotation": jr,
        "form_col": form_col,
        "form_ges": form_ges,
        "active_tab": active_tab,
        "modo": "cadastrar",
        "assinatura_colab_qr": assinatura_colab_qr,
        "assinatura_gestor_qr": assinatura_gestor_qr,
    }
    return render(request, "jobrotation/avaliacoes_form_tabs.html", contexto)


# ============================================================
# EDITAR em DUAS ABAS (admin)
# ============================================================
@login_required
@permission_required("Funcionario.view_jobrotationavaliacaocolaborador", raise_exception=True)
def editar_avaliacoes_tabs_admin(request: HttpRequest, jobrotation_id: int):
    """
    Edita as avaliações (Colaborador/Gestor) em DUAS ABAS.
    Cria os registros se ainda não existirem, assina a cada salvamento.
    """
    jr = get_object_or_404(JobRotationEvaluation, pk=jobrotation_id)

    col_obj, _ = JobRotationAvaliacaoColaborador.objects.get_or_create(jobrotation=jr)
    ges_obj, _ = JobRotationAvaliacaoGestor.objects.get_or_create(jobrotation=jr)

    active_tab = request.GET.get("tab") or "colaborador"

    if request.method == "POST":
        aba = request.POST.get("aba") or "colaborador"

        if aba == "colaborador":
            form_col = AvaliacaoColaboradorForm(request.POST, instance=col_obj)
            form_ges = AvaliacaoGestorForm(instance=ges_obj)
            if form_col.is_valid():
                obj = form_col.save(commit=False)
                obj.save()
                _carimbar_e_assinar(obj, request.user, f"JR_COLAB|{jr.pk}|{obj.pk}")
                messages.success(request, "Dados do COLABORADOR salvos e assinados.")
                active_tab = "colaborador"
            else:
                messages.error(request, "Verifique os campos do COLABORADOR.")
                active_tab = "colaborador"

        elif aba == "gestor":
            form_col = AvaliacaoColaboradorForm(instance=col_obj)
            form_ges = AvaliacaoGestorForm(request.POST, instance=ges_obj)
            if form_ges.is_valid():
                obj = form_ges.save(commit=False)
                obj.save()
                _carimbar_e_assinar(obj, request.user, f"JR_GESTOR|{jr.pk}|{obj.pk}")
                messages.success(request, "Dados do GESTOR salvos e assinados.")
                active_tab = "gestor"
            else:
                messages.error(request, "Verifique os campos do GESTOR.")
                active_tab = "gestor"
    else:
        form_col = AvaliacaoColaboradorForm(instance=col_obj)
        form_ges = AvaliacaoGestorForm(instance=ges_obj)

    # Monta QR (se houver assinatura)
    assinatura_colab_qr = None
    assinatura_gestor_qr = None
    if col_obj.assinado:
        dic = _assinatura_qr_dict(request, "JobRotationAvaliacaoColaborador", col_obj.pk)
        assinatura_colab_qr = dic["qr"] if dic else None
    if ges_obj.assinado:
        dic = _assinatura_qr_dict(request, "JobRotationAvaliacaoGestor", ges_obj.pk)
        assinatura_gestor_qr = dic["qr"] if dic else None

    return render(
        request,
        "jobrotation/avaliacoes_form_tabs.html",
        {
            "titulo": "Avaliação de Job Rotation",
            "jobrotation": jr,
            "form_col": form_col,
            "form_ges": form_ges,
            "active_tab": active_tab,
            "modo": "editar",
            "assinatura_colab_qr": assinatura_colab_qr,
            "assinatura_gestor_qr": assinatura_gestor_qr,
        },
    )
