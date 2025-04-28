# qualidade_fornecimento/views/inspecao_servico_externo_views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from qualidade_fornecimento.forms.inspecao_servico_externo_form import (
    InspecaoServicoExternoForm,
)
from qualidade_fornecimento.models.controle_servico_externo import (
    ControleServicoExterno,
)
from qualidade_fornecimento.models.inspecao_servico_externo import (
    InspecaoServicoExterno,
)
from qualidade_fornecimento.services.pdf_inspecao_servico_externo import (  # 🆕 Importa o gerador de PDF
    gerar_pdf_inspecao_servico_externo,
)


@login_required
def selecionar_servico_para_inspecao(request):
    """
    Tela que lista serviços externos para o usuário escolher qual inspecionar.
    """
    servicos = ControleServicoExterno.objects.all().order_by("-data_envio")

    return render(
        request,
        "inspecao_servico_externo/selecionar_servico.html",
        {"servicos": servicos},
    )


# qualidade_fornecimento/views/inspecao_servico_externo_views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from qualidade_fornecimento.forms.inspecao_servico_externo_form import (
    InspecaoServicoExternoForm,
)
from qualidade_fornecimento.models.controle_servico_externo import (
    ControleServicoExterno,
)
from qualidade_fornecimento.models.inspecao_servico_externo import (
    InspecaoServicoExterno,
)
from qualidade_fornecimento.tasks import (  # 🆕 Importa a task
    gerar_pdf_inspecao_servico_background,
)


@login_required
def cadastrar_inspecao_servico_externo(request, servico_id):
    servico = get_object_or_404(ControleServicoExterno, id=servico_id)

    if hasattr(servico, "inspecao"):
        return redirect("editar_inspecao_servico_externo", id=servico.inspecao.id)

    if request.method == "POST":
        form = InspecaoServicoExternoForm(request.POST, request.FILES)

        if form.is_valid():
            inspecao = form.save(commit=False)
            inspecao.servico = servico
            inspecao.save()

            # Gera o PDF em background
            gerar_pdf_inspecao_servico_background.delay(servico.id)

            # 🔥 Sinaliza que tem uma inspeção pendente na sessão
            request.session["inspecao_pending"] = servico.id

            return redirect("listar_controle_servico_externo")
    else:
        form = InspecaoServicoExternoForm()

    return render(
        request,
        "inspecao_servico_externo/inspecao_servico_externo_form.html",
        {
            "form": form,
            "servico": servico,
            "modo": "Cadastro",
        },
    )


@login_required
def editar_inspecao_servico_externo(request, id):
    inspecao = get_object_or_404(InspecaoServicoExterno, id=id)

    if request.method == "POST":
        form = InspecaoServicoExternoForm(
            request.POST, request.FILES, instance=inspecao
        )

        if form.is_valid():
            form.save()

            # ⚡ Atualiza PDF em background também
            gerar_pdf_inspecao_servico_background.delay(inspecao.servico.id)

            return redirect("listar_controle_servico_externo")
    else:
        form = InspecaoServicoExternoForm(instance=inspecao)

    return render(
        request,
        "inspecao_servico_externo/inspecao_servico_externo_form.html",
        {
            "form": form,
            "servico": inspecao.servico,
            "modo": "Edição",
        },
    )


from django.http import JsonResponse


@login_required
def inspecao_status(request, servico_id):
    """
    Retorna {"ready": true, "url": "<pdf_url>"} quando o PDF da inspeção estiver gerado
    """
    try:
        servico = ControleServicoExterno.objects.get(pk=servico_id)
        if hasattr(servico, "inspecao") and servico.inspecao.pdf:
            return JsonResponse({"ready": True, "url": servico.inspecao.pdf.url})
    except ControleServicoExterno.DoesNotExist:
        pass
    return JsonResponse({"ready": False})
