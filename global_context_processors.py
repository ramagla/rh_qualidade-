from datetime import datetime

def global_menu(request):
    user = request.user

    # Verificar permissões do usuário para os módulos
    metrologia_permitido = user.has_perm("metrologia.view_calibracaodispositivo") or user.has_perm("metrologia.view_tabelatecnica")
    recursos_humanos_permitido = user.has_perm("Funcionario.view_funcionario") or user.has_perm("Funcionario.view_treinamento")
    qualidade_fornecimento_permitido = user.has_perm("qualidade_fornecimento.view_fornecedorqualificado")

    # Menu Metrologia com permissões
    menu_metrologia = []
    if user.has_perm("metrologia.view_tabelatecnica"):
        menu_metrologia.append({
            "name": "Cadastros",
            "icon": "fas fa-folder",
            "submenu": [
                {"name": "Instrumentos", "url": "lista_tabelatecnica", "icon": "fas fa-ruler-combined"},
                {"name": "Dispositivos", "url": "lista_dispositivos", "icon": "fas fa-cogs"},
            ],
        })

    if user.has_perm("metrologia.view_calibracaodispositivo") or user.has_perm("metrologia.view_calibracao"):
        menu_metrologia.append({
            "name": "Calibrações",
            "icon": "fas fa-cogs",
            "submenu": [
                {"name": "Calibrações de Instrumentos", "url": "calibracoes_instrumentos", "icon": "fas fa-tools"},
                {"name": "Calibrações de Dispositivos", "url": "lista_calibracoes_dispositivos", "icon": "fas fa-wrench"},
            ],
        })

    if user.has_perm("metrologia.view_cronograma"):
        menu_metrologia.append({
            "name": "Cronogramas",
            "icon": "fas fa-calendar-alt",
            "submenu": [
                {"name": "Cronograma de Equipamentos", "url": "cronograma_calibracao"},
                {"name": "Cronograma de Dispositivos", "url": "cronograma_dispositivos"},
            ],
        })

    if user.has_perm("metrologia.view_relatorio"):
        menu_metrologia.append({
            "name": "Relatórios",
            "icon": "fas fa-file-alt",
            "submenu": [
                {"name": "Equipamentos a Calibrar", "url": "relatorio_equipamentos_calibrar", "icon": "fas fa-exclamation-circle"},
                {"name": "Equipamentos por Funcionário", "url": "equipamentos_por_funcionario", "icon": "fas fa-users"},
            ],
        })

        if user.has_perm("Funcionario.view_documento"):
            menu_metrologia.append({
                "name": "Documentos",
                "url": "lista_documentos",
                "icon": "fas fa-folder-open",
            })

    # Menu Recursos Humanos
    menu_recursos_humanos = []
    if recursos_humanos_permitido:
        if user.has_perm("Funcionario.view_funcionario"):
            menu_recursos_humanos.extend([
                {"name": "Dashboard", "url": "funcionarios_home", "icon": "fas fa-tachometer-alt"},
                {"name": "Comunicados Internos", "url": "lista_comunicados", "icon": "fas fa-bullhorn"},
                {"name": "Cargos", "url": "lista_cargos", "icon": "fas fa-briefcase"},
                {"name": "Colaboradores", "url": "lista_funcionarios", "icon": "fas fa-user"},
                {"name": "Integrações", "url": "lista_integracoes", "icon": "bi bi-person-badge"},
            ])

        if user.has_perm("Funcionario.view_treinamento"):
            menu_recursos_humanos.append({
                "name": "Treinamentos",
                "icon": "fas fa-graduation-cap",
                "submenu": [
                    {"name": "Lista de Treinamentos", "url": "lista_treinamentos"},
                    {"name": "Lista de Presença", "url": "lista_presenca"},
                    {"name": "Avaliação de Treinamentos", "url": "lista_avaliacoes"},
                ],
            })

        if user.has_perm("Funcionario.view_avaliacaoanual") or user.has_perm("Funcionario.view_avaliacaoexperiencia"):
            menu_recursos_humanos.append({
                "name": "Desempenho",
                "icon": "fas fa-chart-line",
                "submenu": [
                    {"name": "Anual", "url": "lista_avaliacao_anual"},
                    {"name": "Experiência", "url": "lista_avaliacao_experiencia"},
                ],
            })

        if user.has_perm("Funcionario.view_jobrotationevaluation"):
            menu_recursos_humanos.append({
                "name": "Job Rotation",
                "url": "lista_jobrotation_evaluation",
                "icon": "fas fa-sync-alt",
            })

        if user.has_perm("Funcionario.view_matrizpolivalencia"):
            menu_recursos_humanos.append({
                "name": "Matriz de Polivalência",
                "icon": "fas fa-layer-group",
                "submenu": [
                    {"name": "Lista de Atividades", "url": "lista_atividades"},
                    {"name": "Lista de Matriz", "url": "lista_matriz_polivalencia"},
                ],
            })

        if user.has_perm("Funcionario.view_treinamento") or user.has_perm("Funcionario.view_avaliacaotreinamento"):
            menu_recursos_humanos.append({
                "name": "Relatórios",
                "icon": "fas fa-file-alt",
                "submenu": [
                    {"name": "Indicador de Treinamentos", "url": "relatorio_indicador"},
                    {"name": "Indicador Anual", "url": "relatorio_indicador_anual"},
                    {"name": "Cronograma de Treinamentos", "url": "cronograma_treinamentos"},
                    {"name": "Cronograma de Eficácia", "url": "cronograma_avaliacao_eficacia"},
                ],
            })

        if user.has_perm("Funcionario.view_funcionario"):
            menu_recursos_humanos.append({
                "name": "Formulários",
                "icon": "fas fa-edit",
                "submenu": [
                    {"name": "Carta de Competência", "url": "filtro_funcionario"},
                    {"name": "Pesquisa de Consciência", "url": "formulario_pesquisa_consciencia"},
                    {"name": "Avaliação de Capacitação Prática", "url": "filtro_carta_competencia"},
                ],
            })

        if user.has_perm("Funcionario.view_documento"):
            menu_recursos_humanos.append({
                "name": "Documentos",
                "url": "lista_documentos",
                "icon": "fas fa-folder-open",
            })

        if user.has_perm("Funcionario.view_calendario"):
            menu_recursos_humanos.append({
                "name": "Calendário",
                "url": "calendario",
                "icon": "fas fa-calendar-alt",
            })

        # Menu Qualidade de Fornecimento com permissões
            menu_qualidade_fornecimento = []

            menu_qualidade_fornecimento.append({
                "name": "Dashboard",
                "url": "qualidadefornecimento_home",
                "icon": "fas fa-industry",
            })

            # Menu com submenu de cadastros
            menu_qualidade_fornecimento.append({
                "name": "Cadastros",
                "icon": "fas fa-folder-open",
                "submenu": [
                    {
                        "name": "Fornecedores",
                        "url": "lista_fornecedores",
                        "icon": "fas fa-truck",
                    },
                    {
                        "name": "Catálogo de Matéria-Prima",
                        "url": "materiaprima_catalogo_list",
                        "icon": "fas fa-tags",
                    },
                    {
                        "name": "Normas Técnicas",
                        "url": "lista_normas",
                        "icon": "fas fa-file-alt",
                    },
                ],
            })

            menu_qualidade_fornecimento.append({
                "name": "TB050 - Relação de Matérias-Primas",
                "url": "tb050_list",
                "icon": "fas fa-boxes",
            })

            # Novo item do menu abrindo diretamente a lista
            menu_qualidade_fornecimento.append({
                "name": "Controle de Serviço Externo",
                "url": "listar_controle_servico_externo",
                "icon": "fas fa-external-link-alt",
            })

            menu_qualidade_fornecimento.append({
                "name": "Relatórios",
                "icon": "fas fa-file-alt",
                "submenu": [
                    {
                        "name": "Avaliação Semestral",
                        "url": "relatorio_avaliacao",
                        "icon": "fas fa-chart-line"
                    },
                ]
            })


       


    # Módulos disponíveis no seletor superior
    modulos_disponiveis = []
    if metrologia_permitido:
        modulos_disponiveis.append({"name": "Metrologia", "url": "metrologia_home", "icon": "bi bi-rulers"})
    if recursos_humanos_permitido:
        modulos_disponiveis.append({"name": "Recursos Humanos", "url": "home", "icon": "bi bi-people"})
    if qualidade_fornecimento_permitido:
        modulos_disponiveis.append({"name": "Qualidade de Fornecimento", "url": "qualidadefornecimento_home", "icon": "fas fa-industry"})

    # Determinar menu ativo baseado na URL
    active_module = request.path.split("/")[1]
    if active_module == "metrologia":
        menu = menu_metrologia
    elif active_module == "qualidade":
        menu = menu_qualidade_fornecimento
    else:
        menu = menu_recursos_humanos

    return {
        "menu": menu,
        "modulos_disponiveis": modulos_disponiveis,
        "ano_atual": datetime.now().year,
    }
