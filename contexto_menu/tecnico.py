def menu_tecnico(user):
    if not user.has_perm("tecnico.acesso_tecnico"):
        return []

    menu = []

    # Dashboard
    menu.append({
        "name": "Dashboard",
        "url": "tecnico:tecnico_home",
        "icon": "fas fa-home",
    })

    # Máquinas
    if user.has_perm("tecnico.view_maquina"):
        menu.append({
            "name": "Máquinas",
            "url": "tecnico:tecnico_maquinas",
            "icon": "fas fa-cogs",
        })

    # Roteiros de Produção
    if user.has_perm("tecnico.view_roteiroproducao"):
        menu.append({
            "name": "Roteiros de Produção",
            "url": "tecnico:tecnico_roteiros",
            "icon": "fas fa-network-wired",
        })

    # Submenu Indicadores
    if user.has_perm("tecnico.view_indicador_tecnico"):
        submenu_indicadores = [
            {
                "name": "5.1 - Cumprimento de Prazo de Desenvolvimento",
                "url": "tecnico:indicador_51_prazo_desenvolvimento",
                "icon": "fas fa-calendar-check",
            },
        ]

        menu.append({
            "name": "Indicadores",
            "icon": "fas fa-chart-line",
            "submenu": submenu_indicadores,
        })

    return menu
