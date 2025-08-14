def menu_comercial(user):
    if not user.has_perm("comercial.acesso_comercial"):
        return []

    menu = []

    # Dashboard
    menu.append({
        "name": "Dashboard",
        "url": "comercial_home",
        "icon": "fas fa-home",
    })

    # Submenu Cadastros
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


    if user.has_perm("comercial.view_viabilidadeanaliserisco"):
        menu.append({
            "name": "Viabilidade / Análise de Risco",
            "url": "lista_viabilidades",
            "icon": "fas fa-shield-alt",
        })

    if user.has_perm("comercial.view_cotacao"):  # ou outra permissão adequada
        submenu_indicadores = [
            {
                "name": "4.1 - Atendimento do Prazo de Cotação",
                "url": "indicador_prazo_cotacao",
                "icon": "fas fa-clock",
            },
            {
                "name": "4.2 - Nº de Itens Novos Vendidos",
                "url": "indicador_itens_novos",
                "icon": "fas fa-cubes",
            },
            {
                "name": "4.3 - Nº de Cotações por Funcionário",
                "url": "indicador_cotacoes_funcionario",
                "icon": "fas fa-user-friends",
            },
            {
                "name": "4.4 - Taxa de Orçamentos Aprovados",
                "url": "indicador_taxa_aprovacao",
                "icon": "fas fa-percentage",
            },
        ]
    # Faturamento
        if user.has_perm("comercial.view_faturamento"):  # ajuste a permissão ao seu model real
            menu.append({
                "name": "Faturamento",
                "url": "lista_faturamento",
                "icon": "fas fa-file-invoice-dollar",  # ícone sugestão
            })
        menu.append({
            "name": "Indicadores",
            "icon": "fas fa-chart-line",
            "submenu": submenu_indicadores,
        })


    return menu
