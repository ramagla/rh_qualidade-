def menu_comercial(user):
    if not user.has_perm("comercial.acesso_comercial"):
        return []

    menu = []

    # =========================
    # Dashboards
    # =========================
    submenu_dashboards = []

    # Dashboard de Cotações
    if user.has_perm("comercial.view_cotacao"):
        submenu_dashboards.append({
            "name": "Dashboard de Cotações",
            "url": "comercial_home",
            "icon": "fas fa-file-signature",
        })

    # Dashboard de Faturamento (perm custom correta)
    if user.has_perm("comercial.view_dashboard_faturamento"):
        submenu_dashboards.append({
            "name": "Dashboard de Faturamento",
            "url": "dashboard_faturamento",
            "icon": "fas fa-file-invoice-dollar",
        })

    if submenu_dashboards:
        menu.append({
            "name": "Dashboards",
            "icon": "fas fa-home",
            "submenu": submenu_dashboards,
        })

    # =========================
    # Cadastros
    # =========================
    submenu_cadastros = []

    if user.has_perm("comercial.view_cliente"):
        submenu_cadastros.append({
            "name": "Clientes",
            "url": "lista_clientes",
            "icon": "fas fa-user-tag",
        })

    if user.has_perm("comercial.view_item"):
        submenu_cadastros.append({
            "name": "Itens",
            "url": "lista_itens",
            "icon": "fas fa-box-open",
        })

    if user.has_perm("comercial.view_ferramenta"):
        submenu_cadastros.append({
            "name": "Ferramentas",
            "url": "lista_ferramentas",
            "icon": "fas fa-tools",
        })

    if user.has_perm("Funcionario.view_centrodecusto"):
        submenu_cadastros.append({
            "name": "Centros de Custo",
            "url": "lista_centros_custo",
            "icon": "fas fa-cash-register",
        })

    if submenu_cadastros:
        menu.append({
            "name": "Cadastros",
            "icon": "fas fa-folder-open",
            "submenu": submenu_cadastros,
        })

    # =========================
    # Módulos
    # =========================

    # Cotações
    if user.has_perm("comercial.view_cotacao"):
        menu.append({
            "name": "Cotações",
            "url": "lista_cotacoes",
            "icon": "fas fa-file-signature",
        })

    # Ordem de Desenvolvimento
    if user.has_perm("comercial.view_ordemdesenvolvimento"):
        menu.append({
            "name": "Ordem de Desenvolvimento",
            "url": "lista_ordens_desenvolvimento",
            "icon": "fas fa-project-diagram",
        })

    # Viabilidade / Análise de Risco
    if user.has_perm("comercial.view_viabilidadeanaliserisco"):
        menu.append({
            "name": "Viabilidade / Análise de Risco",
            "url": "lista_viabilidades",
            "icon": "fas fa-shield-alt",
        })

    # Faturamento (lista)
    if user.has_perm("comercial.view_faturamentoregistro"):
        menu.append({
            "name": "Faturamento",
            "url": "lista_faturamento",
            "icon": "fas fa-file-invoice-dollar",
        })

    # =========================
    # Indicadores
    # =========================
    submenu_indicadores = []

    # 1.1 - Faturamento
    if user.has_perm("comercial.view_indicador_faturamento"):
        submenu_indicadores.append({
            "name": "1.1 - Faturamento",
            "url": "indicador_faturamento",
            "icon": "fas fa-file-invoice-dollar",
        })

    # 4.1 - Atendimento do Prazo de Cotação
    if user.has_perm("comercial.view_indicador_prazo_cotacao"):
        submenu_indicadores.append({
            "name": "4.1 - Atendimento do Prazo de Cotação",
            "url": "indicador_prazo_cotacao",
            "icon": "fas fa-clock",
        })

    # 4.2 - Nº de Itens Novos Vendidos
    if user.has_perm("comercial.view_indicador_itens_novos"):
        submenu_indicadores.append({
            "name": "4.2 - Nº de Itens Novos Vendidos",
            "url": "indicador_itens_novos",
            "icon": "fas fa-cubes",
        })

    # 4.3 - Nº de Cotações por Funcionário
    if user.has_perm("comercial.view_indicador_cotacoes_funcionario"):
        submenu_indicadores.append({
            "name": "4.3 - Nº de Cotações por Funcionário",
            "url": "indicador_cotacoes_funcionario",
            "icon": "fas fa-user-friends",
        })

    # 4.4 - Taxa de Orçamentos Aprovados
    if user.has_perm("comercial.view_indicador_taxa_aprovacao"):
        submenu_indicadores.append({
            "name": "4.4 - Taxa de Orçamentos Aprovados",
            "url": "indicador_taxa_aprovacao",
            "icon": "fas fa-percentage",
        })

    if submenu_indicadores:
        menu.append({
            "name": "Indicadores",
            "icon": "fas fa-chart-line",
            "submenu": submenu_indicadores,
        })

    return menu
