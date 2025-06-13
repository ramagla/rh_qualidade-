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
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from datetime import date

from assinatura_eletronica.models import AssinaturaEletronica
from assinatura_eletronica.utils import gerar_assinatura, gerar_qrcode_base64


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
from django.utils.timezone import now


from assinatura_eletronica.models import AssinaturaEletronica
from assinatura_eletronica.utils import gerar_assinatura, gerar_qrcode_base64

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
            inspecao.assinatura_nome = request.user.get_full_name()
            inspecao.assinatura_email = request.user.email
            inspecao.assinatura_data = now()
            inspecao.save()

            # Gera o hash de assinatura e salva no app assinatura_eletronica
            hash_assinatura = gerar_assinatura(inspecao, request.user)
            AssinaturaEletronica.objects.create(
                hash=hash_assinatura,
                conteudo=f"Relatório de inspeção do pedido {servico.pedido} aprovado.",
                usuario=request.user,
                origem_model="InspecaoServicoExterno",
                origem_id=inspecao.id,
            )

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
        form = InspecaoServicoExternoForm(request.POST, request.FILES, instance=inspecao)

        if form.is_valid():
            form.save()
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

from django.conf import settings
import os

@login_required
def visualizar_inspecao_servico_externo(request, id):
    inspecao = get_object_or_404(InspecaoServicoExterno, pk=id)
    servico = inspecao.servico

    logo_url = f"file://{os.path.join(settings.STATIC_ROOT, 'img', 'logo.png')}"

    # Busca a assinatura eletrônica
    assinatura = AssinaturaEletronica.objects.filter(
        origem_model="InspecaoServicoExterno",
        origem_id=inspecao.id
    ).first()

    qr_base64 = None
    url_validacao = None
    assinatura_hash = None
    assinatura_departamento = "Não informado"

    if assinatura:
        url_validacao = request.build_absolute_uri(f"/assinatura/validar/{assinatura.hash}/")
        qr_base64 = gerar_qrcode_base64(url_validacao)
        assinatura_hash = assinatura.hash

        # Tentativa de obter o departamento do usuário que assinou
        usuario = assinatura.usuario
        funcionario = getattr(usuario, "funcionario", None)
        if funcionario and funcionario.local_trabalho:
            assinatura_departamento = funcionario.local_trabalho.nome

    return render(
        request,
        "inspecao_servico_externo/relatorio_inspecao.html",
        {
            "inspecao": inspecao,
            "servico": servico,
            "logo_url": logo_url,
            "assinatura_nome": inspecao.assinatura_nome,
            "assinatura_email": inspecao.assinatura_email,
            "assinatura_data": inspecao.assinatura_data,
            "assinatura_hash": assinatura_hash,
            "assinatura_departamento": assinatura_departamento,
            "qr_base64": qr_base64,
            "url_validacao": url_validacao,
        },
    )