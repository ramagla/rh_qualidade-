def menu_metrologia(user):
    if not user.has_perm("metrologia.acesso_metrologia"):
        return []

    menu = []

    menu.append({
        "name": "Dashboard",
        "url": "metrologia_home",
        "icon": "fas fa-tachometer-alt",
    })

    if user.has_perm("metrologia.view_tabelatecnica"):
        menu.append({
            "name": "Cadastros",
            "icon": "fas fa-folder",
            "submenu": [
                {
                    "name": "Instrumentos",
                    "url": "lista_tabelatecnica",
                    "icon": "fas fa-ruler-combined",
                    "perm": "metrologia.view_tabelatecnica",
                },
                {
                    "name": "Dispositivos",
                    "url": "lista_dispositivos",
                    "icon": "fas fa-cogs",
                    "perm": "metrologia.view_dispositivo",
                },
            ],
        })

    if user.has_perm("metrologia.view_calibracao") or user.has_perm("metrologia.view_calibracaodispositivo"):
        menu.append({
            "name": "Calibrações",
            "icon": "fas fa-cogs",
            "submenu": [
                {
                    "name": "Calibrações de Instrumentos",
                    "url": "calibracoes_instrumentos",
                    "icon": "fas fa-tools",
                    "perm": "metrologia.view_calibracao",
                },
                {
                    "name": "Calibrações de Dispositivos",
                    "url": "lista_calibracoes_dispositivos",
                    "icon": "fas fa-wrench",
                    "perm": "metrologia.view_calibracaodispositivo",
                },
            ],
        })

    cronogramas = []
    if user.has_perm("metrologia.cronograma_calibracao_equipamentos"):
        cronogramas.append({
            "name": "Cronograma de Equipamentos",
            "url": "cronograma_calibracao",
            "icon": "bi bi-calendar-check",
            "perm": "metrologia.cronograma_calibracao_equipamentos",
        })
    if user.has_perm("metrologia.cronograma_calibracao_dispositivos"):
        cronogramas.append({
            "name": "Cronograma de Dispositivos",
            "url": "cronograma_dispositivos",
            "icon": "bi bi-calendar-range",
            "perm": "metrologia.cronograma_calibracao_dispositivos",
        })
    if cronogramas:
        menu.append({
            "name": "Cronogramas",
            "icon": "fas fa-calendar-alt",
            "submenu": cronogramas,
        })

    relatorios = []
    if user.has_perm("metrologia.relatorio_equipamentos_calibrar"):
        relatorios.append({
            "name": "Equipamentos a Calibrar",
            "url": "relatorio_equipamentos_calibrar",
            "icon": "fas fa-exclamation-circle",
            "perm": "metrologia.relatorio_equipamentos_calibrar",
        })
    if user.has_perm("metrologia.relatorio_equipamentos_por_funcionario"):
        relatorios.append({
            "name": "Equipamentos por Funcionário",
            "url": "equipamentos_por_funcionario",
            "icon": "fas fa-users",
            "perm": "metrologia.relatorio_equipamentos_por_funcionario",
        })
    if relatorios:
        menu.append({
            "name": "Relatórios",
            "icon": "fas fa-file-alt",
            "submenu": relatorios,
        })

    return menu
