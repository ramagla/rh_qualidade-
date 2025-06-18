def menu_tecnico(user):
    menu = []

    if user.has_perm("tecnico.acesso_tecnico"):
        menu.append({
            "name": "Dashboard",
            "url": "tecnico:tecnico_home",  # ✅ com namespace
            "icon": "bi bi-speedometer2",
            "perm": "tecnico.acesso_tecnico",
        })

    if user.has_perm("tecnico.view_maquina"):
        menu.append({
            "name": "Máquinas",
            "url": "tecnico:tecnico_maquinas",  # ✅ com namespace
            "icon": "bi bi-gear-wide-connected",
            "perm": "tecnico.view_maquina",
        })

    if user.has_perm("tecnico.view_roteiroproducao"):
        menu.append({
            "name": "Roteiros de Produção",
            "url": "tecnico:tecnico_roteiros",  # ✅ com namespace
            "icon": "bi bi-diagram-3",
            "perm": "tecnico.view_roteiroproducao",
        })

    return menu
