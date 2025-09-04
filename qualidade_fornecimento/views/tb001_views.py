# qualidade_fornecimento/views/tb001_views.py
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.utils import timezone

from qualidade_fornecimento.models import FornecedorQualificado


@login_required
@permission_required("qualidade_fornecimento.relatorio_avaliacao_view", raise_exception=True)
def tb001_view(request):
    """
    TB001 - Relatório de Qualificação de Fornecedores
    - KPI's: baseados em todos os fornecedores ATIVOS
    - Tabela: ATIVOS + QUALIFICADOS, com filtros opcionais
    - Filtros GET:
        fornecedor = nome exato (via select2)
        produto     = value de TIPO_PRODUTO
        cert        = value de TIPO_CERTIFICACAO
    """
    hoje = timezone.now().date()

    # Base: somente ATIVOS
    ativos = FornecedorQualificado.objects.filter(ativo__iexact="Ativo")

    # KPI's (sempre sobre ATIVOS, independentemente dos filtros)
    kpi_total = ativos.count()
    kpi_qualificados = ativos.filter(status__iexact="Qualificado").count()
    kpi_condicionais = ativos.filter(status__icontains="Condicional").count()
    kpi_reprovados = ativos.filter(status__iexact="Reprovado").count()

    # Tabela: ATIVOS + QUALIFICADOS (ordem padrão pelo nome)
    qs = ativos.filter(status__iexact="Qualificado").order_by("nome")

    # -------- Filtros GET --------
    fornecedor = request.GET.get("fornecedor", "").strip()  # select2
    produto = request.GET.get("produto", "").strip()
    cert = request.GET.get("cert", "").strip()

    if fornecedor:
        # Select2 envia o texto exato do option; filtra por igualdade para evitar falsos-positivos
        qs = qs.filter(nome=fornecedor)
    if produto:
        qs = qs.filter(produto_servico=produto)
    if cert:
        qs = qs.filter(tipo_certificacao=cert)

    # Opções para selects (vindas do model)
    field_prod = FornecedorQualificado._meta.get_field("produto_servico")
    field_cert = FornecedorQualificado._meta.get_field("tipo_certificacao")
    produtos_opcoes = field_prod.choices            # [(value, label), ...]
    certificacoes_opcoes = field_cert.choices       # [(value, label), ...]

    # Opções do select2 de fornecedores (somente ATIVOS + QUALIFICADOS, sem duplicados)
    fornecedores_opcoes = (
        ativos.filter(status__iexact="Qualificado")
              .order_by("nome")
              .values_list("nome", flat=True)
              .distinct()
    )

    contexto = {
        "today": hoje,
        "fornecedores": qs,
        # KPI's
        "kpi_total": kpi_total,
        "kpi_qualificados": kpi_qualificados,
        "kpi_condicionais": kpi_condicionais,
        "kpi_reprovados": kpi_reprovados,
        # filtros/estado
        "filtros": {"fornecedor": fornecedor, "produto": produto, "cert": cert},
        # opções para os selects no template
        "produtos_opcoes": produtos_opcoes,
        "certificacoes_opcoes": certificacoes_opcoes,
        "fornecedores_opcoes": fornecedores_opcoes,
    }
    return render(request, "qualidade_fornecimento/tb001.html", contexto)
