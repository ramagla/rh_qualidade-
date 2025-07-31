from decimal import Decimal, InvalidOperation

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


from decimal import Decimal
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from qualidade_fornecimento.models import FornecedorQualificado
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo
from comercial.models.precalculo import PreCalculoMaterial, PreCalculoServicoExterno

def responder_cotacao_materia_prima(request, pk):
    """
    View pública para que fornecedores preencham os dados de cotação da matéria-prima.
    Quando todos os preços já estiverem preenchidos, exibe a página de cotação finalizada.
    """
    # Busca o material e todas as “cópias” dele no mesmo pré-cálculo
    material = get_object_or_404(PreCalculoMaterial, pk=pk)
    codigo = material.codigo
    materiais = PreCalculoMaterial.objects.filter(
        precalculo=material.precalculo,
        codigo=codigo
    ).order_by("pk")

    # Se não houver nenhum preço em branco, renderiza página finalizada
    if not materiais.filter(preco_kg__isnull=True).exists():
        return render(request,
                      "cotacoes/cotacao_material_finalizada.html",
                      {"material": material})

    # Dados de apoio para o formulário
    fornecedores = FornecedorQualificado.objects.filter(
        produto_servico__in=["Fita de Aço/Inox", "Arame de Aço", "Arame de Inox"],
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
        # Percorre cada instância e salva os valores vindos do form
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
                except (InvalidOperation, ValueError):
                    mat.preco_kg = None

            mat.save()

        messages.success(request, "Cotações salvas com sucesso.")
        # Redireciona para a mesma URL, disparando um novo GET
        return redirect(request.path)

    # Renderiza o formulário de cotação
    return render(request,
                  "cotacoes/responder_cotacao_material.html",
                  {
                      "materiais": materiais,
                      "fornecedores": fornecedores,
                      "cotacao_numero": cotacao_numero,
                      "precalculo_numero": precalculo_numero,
                      "materia_prima": materia_prima,
                      "observacoes_gerais": observacoes_gerais,
                      "codigo": codigo,
                  })



from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings

def disparar_emails_cotacao_servicos(request, precalc):
    """
    Dispara e-mails de cotação de serviços externos agrupados por insumo.
    """
    grupos = {}
    for servico in precalc.servicos.all():
        insumo = servico.insumo
        if insumo not in grupos:
            grupos[insumo] = []
        grupos[insumo].append(servico)

    for insumo, lista in grupos.items():
        pk_primeiro = lista[0].pk  # usado no link de resposta

        try:
            mp = insumo.materia_prima
            codigo = mp.codigo
            descricao = mp.descricao
        except Exception:
            codigo = "sem código"
            descricao = "---"

        link = request.build_absolute_uri(
            reverse("responder_cotacao_servico_lote", args=[pk_primeiro])
        )

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


from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from qualidade_fornecimento.models import FornecedorQualificado
from comercial.models.precalculo import PreCalculoServicoExterno
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo

def responder_cotacao_servico_lote(request, pk):
    """
    View pública para que fornecedores preencham os dados de cotação de serviços em lote.
    Quando todos os preços já estiverem preenchidos, exibe a página de cotação finalizada.
    """
    # Busca o serviço e todos os serviços do mesmo insumo (mesmo código de MP)
    servico = get_object_or_404(PreCalculoServicoExterno, pk=pk)
    codigo = servico.insumo.materia_prima.codigo

    servicos = PreCalculoServicoExterno.objects.filter(
        precalculo=servico.precalculo,
        insumo__materia_prima__codigo=codigo
    ).select_related("insumo", "insumo__materia_prima").order_by("pk")

    # Se não houver nenhum preço em branco, renderiza página finalizada
    if not servicos.filter(preco_kg__isnull=True).exists():
        return render(
            request,
            "cotacoes/cotacao_servico_lote_finalizada.html",
            {"servico": servico}
        )

    # Dados de apoio para o formulário
    fornecedores = FornecedorQualificado.objects.filter(
        produto_servico__icontains="Trat",
        status__in=["Qualificado", "Qualificado Condicional"]
    ).order_by("nome")

    try:
        materia_prima = servico.insumo.materia_prima
    except MateriaPrimaCatalogo.DoesNotExist:
        materia_prima = None

    cotacao_numero     = servico.precalculo.cotacao.numero if servico.precalculo else None
    precalculo_numero  = servico.precalculo.numero if servico.precalculo else None
    observacoes_gerais = servico.precalculo.observacoes_servicos if servico.precalculo else ""

    if request.method == "POST":
        for i, sev in enumerate(servicos):
            sev.fornecedor_id = request.POST.get(f"fornecedor_{i}") or None
            sev.icms          = request.POST.get(f"icms_{i}") or None
            sev.lote_minimo   = request.POST.get(f"lote_minimo_{i}") or None
            sev.entrega_dias  = request.POST.get(f"entrega_dias_{i}") or None

            preco_raw = request.POST.get(f"preco_kg_{i}") or None
            if preco_raw:
                preco_raw = preco_raw.replace(",", ".")
                try:
                    sev.preco_kg = Decimal(preco_raw)
                except (InvalidOperation, ValueError):
                    sev.preco_kg = None

            sev.save()

        messages.success(request, "Cotações salvas com sucesso.")
        # Redireciona para forçar novo GET e cair na condição de finalização quando completo
        return redirect(request.path)

    return render(
        request,
        "cotacoes/responder_cotacao_servico_lote.html",
        {
            "servicos": servicos,
            "fornecedores": fornecedores,
            "cotacao_numero": cotacao_numero,
            "precalculo_numero": precalculo_numero,
            "materia_prima": materia_prima,
            "observacoes_gerais": observacoes_gerais,
            "codigo": codigo,
        }
    )

