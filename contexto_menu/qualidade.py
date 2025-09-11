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
                # {
                #     "name": "8.2 - Compras x Faturamento",
                #     "url": "indicador_8_2",
                #     "icon": "fas fa-balance-scale",
                # },
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


    # Inventários (novo menu)
    # Inventários (novo menu)
    if user.has_perm("qualidade_fornecimento.view_inventario"):
        submenu_inventario = [
            {
                "name": "Inventários",
                "url": "inventario_list",
                "icon": "fas fa-clipboard-list",
            }
        ]
        if user.has_perm("qualidade_fornecimento.add_inventario"):
            submenu_inventario.append({
                "name": "Novo Inventário",
                "url": "inventario_create",
                "icon": "fas fa-plus-circle",
            })
        # ▼ aqui estava "view_inventarioexportacao"; alinhar com as views
        if user.has_perm("qualidade_fornecimento.exportar_inventario"):
            submenu_inventario.append({
                "name": "Exportações ERP",
                "url": "inventario_exportacoes",
                "icon": "fas fa-file-export",
            })

        menu.append({
            "name": "Inventários",
            "icon": "fas fa-boxes-stacked",
            "submenu": submenu_inventario,
        })


# qualidade_fornecimento/apps/qualidade.py (ou onde fica o menu) — PARA
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
        "url": "",
        "icon": "fas fa-table",
        "modal": "modalTabelaCorrelacao",
    })

    if user.has_perm("qualidade_fornecimento.view_inspecao10"):
        menu.append({
            "name": "F223 -  Controle  Acompanhamento",
            "url": "listar_inspecoes10",
            "icon": "fas fa-clipboard-check",
        })

    # Inventários (novo menu)
    if user.has_perm("qualidade_fornecimento.view_inventario"):
        submenu_inventario = [
            {
                "name": "Inventários",
                "url": "inventario_list",
                "icon": "fas fa-clipboard-list",
            }
        ]
        if user.has_perm("qualidade_fornecimento.add_inventario"):
            submenu_inventario.append({
                "name": "Novo Inventário",
                "url": "inventario_create",
                "icon": "fas fa-plus-circle",
            })
        if user.has_perm("qualidade_fornecimento.exportar_inventario"):
            submenu_inventario.append({
                "name": "Exportações ERP",
                "url": "inventario_exportacoes",
                "icon": "fas fa-file-export",
            })

        menu.append({
            "name": "Inventários",
            "icon": "fas fa-boxes-stacked",
            "submenu": submenu_inventario,
        })

    # ✅ Estoque Intermediário (novo menu)
    if user.has_perm("qualidade_fornecimento.view_estoqueintermediario"):
        submenu_ei = [
            {
                "name": "Em Fábrica",
                "url": "ei_list_em_fabrica",
                "icon": "fas fa-industry",
            },
            {
                "name": "Histórico",
                "url": "ei_list_historico",
                "icon": "fas fa-clock-rotate-left",
            },
        ]
        if user.has_perm("qualidade_fornecimento.add_estoqueintermediario"):
            submenu_ei.insert(0, {
                "name": "Novo Envio",
                "url": "ei_create",
                "icon": "fas fa-plus-circle",
            })

        menu.append({
            "name": "Estoque Intermediário",
            "icon": "fas fa-warehouse",
            "submenu": submenu_ei,
        })
        
    return menu
