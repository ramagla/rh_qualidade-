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


    return menu
