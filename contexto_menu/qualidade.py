def menu_qualidade(user):
    if not user.has_perm("qualidade_fornecimento.acesso_qualidade"):
        return []

    menu = []

    if user.has_perm("qualidade_fornecimento.dashboard_qualidade"):
        menu.append({
            "name": "Dashboard",
            "url": "qualidadefornecimento_home",
            "icon": "fas fa-industry",
        })

    # Cadastros
    submenu_cadastros = []

    if user.has_perm("qualidade_fornecimento.view_fornecedorqualificado"):
        submenu_cadastros.append({
            "name": "Fornecedores",
            "url": "lista_fornecedores",
            "icon": "fas fa-truck",
        })

    if user.has_perm("qualidade_fornecimento.view_normatecnica"):
        submenu_cadastros.append({
            "name": "Normas Técnicas",
            "url": "lista_normas",
            "icon": "fas fa-file-alt",
        })

    if user.has_perm("qualidade_fornecimento.view_materiaprimacatalogo"):
        submenu_cadastros.append({
            "name": "Matéria-Prima",
            "url": "materiaprima_catalogo_list",
            "icon": "fas fa-tags",
        })

    if submenu_cadastros:
        menu.append({
            "name": "Cadastros",
            "icon": "fas fa-folder-open",
            "submenu": submenu_cadastros,
        })

    if user.has_perm("qualidade_fornecimento.view_relacaomateriaprima"):
        menu.append({
            "name": "TB050",
            "url": "tb050_list",
            "icon": "fas fa-boxes",
        })

    if user.has_perm("qualidade_fornecimento.view_controleservicoexterno"):
        menu.append({
            "name": "Serviço Externo",
            "url": "listar_controle_servico_externo",
            "icon": "fas fa-external-link-alt",
        })


    if user.has_perm("qualidade_fornecimento.view_fornecedorqualificado"):
        menu.append({
            "name": "Relatórios",
            "icon": "fas fa-file-alt",
            "submenu": [
                {
                    "name": "Avaliação Semestral",
                    "url": "relatorio_avaliacao",
                    "icon": "fas fa-chart-line",
                },
                {
                    "name": "8.1 - IQF - Índice de Qualidade de Fornecimento",
                    "url": "relatorio_iqf",
                    "icon": "fas fa-tachometer-alt",
                },
                {
                    "name": "6.5 - ICTE",
                    "url": "relatorio_ppm",
                    "icon": "fas fa-chart-bar",
                },
                {
                    "name": "Relatório Analítico de Inspeções",
                    "url": "relatorio_inspecao_analitico",
                    "icon": "fas fa-chart-pie",
                },
                

            ],
        })



    
    # Tabela de Correlação (menu direto com modal)
    menu.append({
        "name": "TB070 - Correlação",
        "url": "",  # Não use "#", apenas string vazia ou None
        "icon": "fas fa-table",
        "modal": "modalTabelaCorrelacao",  # Este é o ID da modal
    })

    if user.has_perm("qualidade_fornecimento.view_inspecao10"):
        menu.append({
            "name": "F223 -  Controle  Acompanhamento",
            "url": "listar_inspecoes10",
            "icon": "fas fa-clipboard-check",
        })




    return menu
