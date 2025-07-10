from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib import messages

from qualidade_fornecimento.models.fornecedor import FornecedorQualificado
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo
from comercial.models.precalculo import PreCalculoMaterial, PreCalculoServicoExterno


def disparar_email_cotacao_material(request, material):
    """
    Envia e-mail para solicitar resposta de cotação da matéria-prima.
    """
    link = request.build_absolute_uri(
        reverse("responder_cotacao_materia_prima", args=[material.pk])
    )

    try:
        mp = MateriaPrimaCatalogo.objects.get(codigo=material.codigo)
        descricao = mp.descricao
    except MateriaPrimaCatalogo.DoesNotExist:
        descricao = "---"

    corpo = f"""
🧪 Solicitação de Cotação - Matéria-Prima

📦 Código: {material.codigo}
📝 Descrição: {descricao}

🔗 Responder: {link}
"""

    send_mail(
        subject="📨 Cotação de Matéria-Prima",
        message=corpo.strip(),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["rafael.almeida@brasmol.com.br"],
        fail_silently=False,
    )


def responder_cotacao_materia_prima(request, pk):
    """
    View pública para que fornecedores preencham os dados de cotação da matéria-prima.
    """
    material = get_object_or_404(PreCalculoMaterial, pk=pk)
    codigo = material.codigo
    materiais = PreCalculoMaterial.objects.filter(codigo=codigo).order_by("pk")

    fornecedores = FornecedorQualificado.objects.filter(
        produto_servico__in=["Fita de Aço/Inox", "Arame de Aço", "Arame de inox"],
        ativo="Ativo"
    ).order_by("nome")

    try:
        materia_prima = MateriaPrimaCatalogo.objects.get(codigo=codigo)
    except MateriaPrimaCatalogo.DoesNotExist:
        materia_prima = None

    cotacao_numero = material.precalculo.cotacao.numero if material.precalculo else None
    precalculo_numero = material.precalculo.numero if material.precalculo else None
    observacoes_gerais = material.precalculo.observacoes_materiais if material.precalculo else ""

    if request.method == "POST":
        for i, mat in enumerate(materiais):
            if mat.status == "ok":
                continue

            mat.fornecedor_id = request.POST.get(f"fornecedor_{i}") or None
            mat.icms = request.POST.get(f"icms_{i}") or None
            mat.lote_minimo = request.POST.get(f"lote_minimo_{i}") or None
            mat.entrega_dias = request.POST.get(f"entrega_dias_{i}") or None
            preco_raw = request.POST.get(f"preco_kg_{i}") or None
            if preco_raw:
                preco_raw = preco_raw.replace(",", ".")
                try:
                    mat.preco_kg = Decimal(preco_raw)
                except:
                    mat.preco_kg = None
            mat.save()

        messages.success(request, "Cotações salvas com sucesso.")
        return redirect(request.path)

    return render(request, "cotacoes/responder_cotacao_material.html", {
        "materiais": materiais,
        "fornecedores": fornecedores,
        "cotacao_numero": cotacao_numero,
        "precalculo_numero": precalculo_numero,
        "materia_prima": materia_prima,
        "observacoes_gerais": observacoes_gerais,
        "codigo": codigo,
    })


def disparar_email_cotacao_servico(request, servico):
    """
    Envia e-mail para solicitar resposta de cotação de serviço externo.
    """
    link = request.build_absolute_uri(
        reverse("responder_cotacao_servico_lote", args=[servico.pk])
    )

    try:
        mp = servico.insumo.materia_prima
        descricao = mp.descricao
        codigo = mp.codigo
    except Exception:
        descricao = "---"
        codigo = "sem código"

    corpo = f"""
🔧 Cotação de Serviço Externo – Tratamento

📦 Código: {codigo}
📝 Descrição: {descricao}

🔗 Link para resposta: {link}
"""

    send_mail(
        subject="📨 Cotação de Serviço Externo",
        message=corpo.strip(),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["rafael.almeida@brasmol.com.br"],
        fail_silently=False,
    )


def responder_cotacao_servico_lote(request, pk):
    """
    View pública para que fornecedores preencham os dados de cotação de serviço externo.
    """
    servico = get_object_or_404(PreCalculoServicoExterno, pk=pk)
    codigo = servico.insumo.materia_prima.codigo
    servicos = PreCalculoServicoExterno.objects.filter(
        insumo__materia_prima__codigo=codigo
    ).order_by("pk")

    fornecedores = FornecedorQualificado.objects.filter(
        produto_servico__icontains="Trat",
        status__in=["Qualificado", "Qualificado Condicional"]
    ).order_by("nome")

    try:
        materia_prima = servico.insumo.materia_prima
    except Exception:
        materia_prima = None

    cotacao_numero = servico.precalculo.cotacao.numero if servico.precalculo else None
    precalculo_numero = servico.precalculo.numero if servico.precalculo else None
    observacoes_gerais = servico.precalculo.observacoes_materiais if servico.precalculo else ""

    if request.method == "POST":
        for i, sev in enumerate(servicos):
            sev.fornecedor_id = request.POST.get(f"fornecedor_{i}") or None
            sev.lote_minimo = request.POST.get(f"lote_minimo_{i}") or None
            sev.entrega_dias = request.POST.get(f"entrega_dias_{i}") or None
            preco_raw = request.POST.get(f"preco_kg_{i}") or None
            if preco_raw:
                preco_raw = preco_raw.replace(",", ".")
                try:
                    sev.preco_kg = Decimal(preco_raw)
                except:
                    sev.preco_kg = None
            sev.save()

        messages.success(request, "Cotações salvas com sucesso.")
        return redirect(request.path)

    return render(request, "cotacoes/responder_cotacao_servico_lote.html", {
        "servicos": servicos,
        "fornecedores": fornecedores,
        "cotacao_numero": cotacao_numero,
        "precalculo_numero": precalculo_numero,
        "materia_prima": materia_prima,
        "observacoes_gerais": observacoes_gerais,
        "codigo": codigo,
    })
