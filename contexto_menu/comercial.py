def menu_comercial(user):
    menu = []

    # Dashboard
    if user.has_perm("comercial.acesso_comercial"):
        menu.append({
            "name": "Dashboard",
            "url": "comercial_home",
            "icon": "fas fa-home",
            "perm": "comercial.acesso_comercial",
        })

    # Cadastro (submenu)
    cadastro_submenu = []

    if user.has_perm("comercial.view_cliente"):
        cadastro_submenu.append({
            "name": "Clientes",
            "url": "lista_clientes",
            "icon": "fas fa-user-tag",
            "perm": "comercial.view_cliente",
        })

    if user.has_perm("comercial.view_item"):
        cadastro_submenu.append({
            "name": "Itens",
            "url": "lista_itens",
            "icon": "fas fa-box-open",
            "perm": "comercial.view_item",
        })


    if user.has_perm("comercial.view_ferramenta"):
        cadastro_submenu.append({
            "name": "Ferramentas",
            "url": "lista_ferramentas",
            "icon": "fas fa-tools",
            "perm": "comercial.view_ferramenta",
        })

    if user.has_perm("Funcionario.view_centrodecusto"):
        cadastro_submenu.append({
            "name": "Centros de Custo",
            "url": "lista_centros_custo",
            "icon": "fas fa-cash-register",
            "perm": "Funcionario.view_centrodecusto",
        })


    if cadastro_submenu:
        menu.append({
            "name": "Cadastro",
            "icon": "fas fa-folder-open",
            "perm": None,  # deixa como None pois o submenu já tem permissões
            "submenu": cadastro_submenu,
        })

    return menu
