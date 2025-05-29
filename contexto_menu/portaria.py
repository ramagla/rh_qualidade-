def menu_portaria(user):
    if not user.has_perm("portaria.acesso_portaria"):
        return []

    menu = []

    # Dashboard
    menu.append({
        "name": "Dashboard",
        "url": "portaria_home",
        "icon": "fas fa-tachometer-alt"
    })

    # Submenu Cadastros agrupado
    submenu_cadastros = []

    if user.has_perm("portaria.view_pessoaportaria"):
        submenu_cadastros.append({
            "name": "Pessoas",
            "url": "lista_pessoas",
            "icon": "fas fa-door-open",
        })

    if user.has_perm("portaria.view_veiculoportaria"):
        submenu_cadastros.append({
            "name": "Veículos",
            "url": "lista_veiculos",
            "icon": "fas fa-car-side",
        })

    if submenu_cadastros:
        menu.append({
            "name": "Cadastros",
            "icon": "fas fa-folder-open",
            "submenu": submenu_cadastros,
        })

    # Menus diretos (sem submenu)
    if user.has_perm("portaria.view_entradavisitante"):
        menu.append({
            "name": "Controle de Visitantes",
            "url": "listar_controle_visitantes",
            "icon": "fas fa-user-check",
        })

    if user.has_perm("portaria.view_atrasosaida"):
        menu.append({
            "name": "Atrasos e Saídas Antecipadas",
            "url": "lista_atrasos_saidas",
            "icon": "fas fa-user-clock",
        })

    if user.has_perm("portaria.view_ligacaoportaria"):
        menu.append({
            "name": "Controle de Ligações",
            "url": "lista_ligacoes",
            "icon": "fas fa-phone-alt",
        })

    if user.has_perm("portaria.view_ocorrenciaportaria"):
        menu.append({
            "name": "Ocorrências da Portaria",
            "url": "listar_ocorrencias",
            "icon": "fas fa-exclamation-triangle",
        })

    if user.has_perm("portaria.view_registroconsumoagua"):
        menu.append({
            "name": "Controle de Consumo de Água",
            "url": "listar_consumo_agua",
            "icon": "fas fa-tint",
        })

    # Relatórios
    submenu_relatorios = []

    if user.has_perm("portaria.relatorio_visitantes"):
        submenu_relatorios.append({
            "name": "Visitantes",
            "url": "relatorio_visitantes",
            "icon": "fas fa-user-check",
        })

    if user.has_perm("portaria.relatorio_atrasos_saidas"):
        submenu_relatorios.append({
            "name": "Atrasos e Saídas",
            "url": "relatorio_atrasos_saidas",
            "icon": "fas fa-user-clock",
        })

    if user.has_perm("portaria.relatorio_ligacoes_recebidas"):
        submenu_relatorios.append({
            "name": "Ligações Recebidas",
            "url": "relatorio_ligacoes_recebidas",
            "icon": "fas fa-phone",
        })

    if user.has_perm("portaria.relatorio_ocorrencias"):
        submenu_relatorios.append({
            "name": "Ocorrências",
            "url": "relatorio_ocorrencias",
            "icon": "fas fa-exclamation-triangle",
        })

    if user.has_perm("portaria.relatorio_consumo_agua"):
        submenu_relatorios.append({
            "name": "Análise de Consumo de Água",
            "url": "relatorio_consumo_agua",
            "icon": "fas fa-water",
        })

    if user.has_perm("portaria.relatorio_horas_extras"):
        submenu_relatorios.append({
            "name": "Horas Extras",
            "url": "relatorio_horas_extras",
            "icon": "bi bi-clock-history",
        })

    if submenu_relatorios:
        menu.append({
            "name": "Relatórios",
            "icon": "fas fa-file-alt",
            "submenu": submenu_relatorios,
        })

    return menu
