from datetime import timedelta

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
    - Tabela: ATIVOS + QUALIFICADOS (com filtros opcionais)
    - Filtros GET:
        fornecedor = nome exato (via select2)
        produto     = value de TIPO_PRODUTO
        cert        = value de TIPO_CERTIFICACAO
    """
    hoje = timezone.now().date()
    janela_alerta_dias = 30  # até 30 dias = alerta "próximo de vencer"

    # Base: somente ATIVOS
    ativos = FornecedorQualificado.objects.filter(ativo__iexact="Ativo")

    # KPI's (sempre sobre ATIVOS)
    kpi_total = ativos.count()
    kpi_qualificados = ativos.filter(status__iexact="Qualificado").count()
    kpi_condicionais = ativos.filter(status__icontains="Condicional").count()
    kpi_reprovados = 0  # TB001 não deve conflitar com a tabela (apenas Qualificados)

    # Tabela: ATIVOS + QUALIFICADOS (ordem padrão pelo nome)
    qs = ativos.filter(status__iexact="Qualificado").order_by("nome")

    # -------- Filtros GET --------
    fornecedor = (request.GET.get("fornecedor") or "").strip()  # select2
    produto = (request.GET.get("produto") or "").strip()
    cert = (request.GET.get("cert") or "").strip()

    if fornecedor:
        # Select2 envia o texto exato do option; igualdade evita falsos positivos
        qs = qs.filter(nome=fornecedor)
    if produto:
        qs = qs.filter(produto_servico=produto)
    if cert:
        qs = qs.filter(tipo_certificacao=cert)

    # -------- Flags de alerta (evita aritmética no template) --------
    limite_proximo = hoje + timedelta(days=janela_alerta_dias)
    # Materializa o queryset para podermos anexar atributos dinâmicos
    fornecedores_lista = list(qs)

    for f in fornecedores_lista:
        # F211 - Avaliação de Risco (próxima avaliação)
        f.alerta_avaliacao = None
        if getattr(f, "proxima_avaliacao_risco", None):
            if f.proxima_avaliacao_risco < hoje:
                f.alerta_avaliacao = "vencido"
            elif f.proxima_avaliacao_risco <= limite_proximo:
                f.alerta_avaliacao = "proximo"

        # F154/CQI - Auditoria de Processo (próxima auditoria)
        f.alerta_auditoria = None
        if getattr(f, "proxima_auditoria", None):
            if f.proxima_auditoria < hoje:
                f.alerta_auditoria = "vencido"
            elif f.proxima_auditoria <= limite_proximo:
                f.alerta_auditoria = "proximo"

    # -------- Opções para selects (vindas do model) --------
    field_prod = FornecedorQualificado._meta.get_field("produto_servico")
    field_cert = FornecedorQualificado._meta.get_field("tipo_certificacao")
    produtos_opcoes = field_prod.choices            # [(value, label), ...]
    certificacoes_opcoes = field_cert.choices       # [(value, label), ...]

    # Opções do select2 (somente ATIVOS + QUALIFICADOS, nome completo, sem duplicados)
    fornecedores_opcoes = (
        ativos.filter(status__iexact="Qualificado")
              .order_by("nome")
              .values_list("nome", flat=True)
              .distinct()
    )

    contexto = {
        "today": hoje,
        "fornecedores": fornecedores_lista,  # passa a lista com flags
        # KPI's
        "kpi_total": kpi_total,
        "kpi_qualificados": kpi_qualificados,
        "kpi_condicionais": kpi_condicionais,
        "kpi_reprovados": kpi_reprovados,
        # filtros/estado
        "filtros": {
            "fornecedor": fornecedor,
            "produto": produto,
            "cert": cert,
        },
        # opções para os selects no template
        "produtos_opcoes": produtos_opcoes,
        "certificacoes_opcoes": certificacoes_opcoes,
        "fornecedores_opcoes": fornecedores_opcoes,
        # parâmetros de apresentação (se quiser usar no template)
        "janela_alerta_dias": janela_alerta_dias,
    }
    return render(request, "qualidade_fornecimento/tb001.html", contexto)
