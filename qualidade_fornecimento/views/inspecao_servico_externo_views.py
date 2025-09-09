# qualidade_fornecimento/views/inspecao_servico_externo_views.py

import os

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now

from assinatura_eletronica.models import AssinaturaEletronica
from assinatura_eletronica.utils import gerar_assinatura, gerar_qrcode_base64
from qualidade_fornecimento.forms.inspecao_servico_externo_form import (
    InspecaoServicoExternoForm,
)
from qualidade_fornecimento.models.controle_servico_externo import (
    ControleServicoExterno,
)
from qualidade_fornecimento.models.inspecao_servico_externo import (
    InspecaoServicoExterno,
)



from django.templatetags.static import static

@login_required
@permission_required('qualidade_fornecimento.view_inspecaoservicoexterno', raise_exception=True)
def visualizar_inspecao_servico_externo(request, id):
    inspecao = get_object_or_404(InspecaoServicoExterno, pk=id)
    servico = inspecao.servico

    # Logo pela STATIC_URL (HTTP/CDN) – robusto em produção
    logo_url = static('img/logo.png')  # use 'logo.png' se o arquivo estiver na raiz de static

    # ✅ Calcula a última data entre os retornos do serviço
    ultimo_retorno = servico.retornos.order_by('data').last()
    data_retorno_ultima = ultimo_retorno.data if ultimo_retorno else None

    # Assinatura eletrônica
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
            "data_retorno_ultima": data_retorno_ultima,  # 👈 novo
            "assinatura_nome": inspecao.assinatura_nome,
            "assinatura_email": inspecao.assinatura_email,
            "assinatura_data": inspecao.assinatura_data,
            "assinatura_hash": assinatura_hash,
            "assinatura_departamento": assinatura_departamento,
            "qr_base64": qr_base64,
            "url_validacao": url_validacao,
        },
    )



@login_required
@permission_required('qualidade_fornecimento.add_inspecaoservicoexterno', raise_exception=True)
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
@permission_required('qualidade_fornecimento.change_inspecaoservicoexterno', raise_exception=True)
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


@login_required
@permission_required('qualidade_fornecimento.view_inspecaoservicoexterno', raise_exception=True)
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





