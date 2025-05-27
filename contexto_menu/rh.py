def menu_rh(user):
    if not user.has_perm("Funcionario.acesso_rh"):
        return []

    menu = []

    if user.has_perm("Funcionario.view_funcionario"):
        menu.append({
            "name": "Dashboard",
            "url": "funcionarios_home",
            "icon": "fas fa-tachometer-alt",
        })

        menu.append({
            "name": "Colaboradores",
            "url": "lista_funcionarios",
            "icon": "fas fa-user",
        })

    if user.has_perm("Funcionario.view_integracaofuncionario"):
        menu.append({
            "name": "Integrações",
            "url": "lista_integracoes",
            "icon": "bi bi-person-badge",
        })

    if user.has_perm("Funcionario.view_comunicado"):
        menu.append({
            "name": "Comunicados Internos",
            "url": "lista_comunicados",
            "icon": "fas fa-bullhorn",
        })

    if user.has_perm("Funcionario.view_cargo") or user.has_perm("Funcionario.add_cargo"):
        menu.append({
            "name": "Cargos",
            "url": "lista_cargos",
            "icon": "fas fa-briefcase",
        })

    # Treinamentos
    submenu_treinamentos = []
    if user.has_perm("Funcionario.view_treinamento"):
        submenu_treinamentos.append({
            "name": "Lista de Treinamentos",
            "url": "lista_treinamentos"
        })
    if user.has_perm("Funcionario.view_listapresenca"):
        submenu_treinamentos.append({
            "name": "Lista de Presença",
            "url": "lista_presenca"
        })
    if user.has_perm("Funcionario.view_avaliacaotreinamento"):
        submenu_treinamentos.append({
            "name": "Avaliação de Treinamentos",
            "url": "lista_avaliacoes"
        })
    if submenu_treinamentos:
        menu.append({
            "name": "Treinamentos",
            "icon": "fas fa-graduation-cap",
            "submenu": submenu_treinamentos,
        })

    # Desempenho
    if user.has_perm("Funcionario.view_avaliacaoanual") or user.has_perm("Funcionario.view_avaliacaoexperiencia"):
        menu.append({
            "name": "Desempenho",
            "icon": "fas fa-chart-line",
            "submenu": [
                {"name": "Anual", "url": "lista_avaliacao_anual"},
                {"name": "Experiência", "url": "lista_avaliacao_experiencia"},
            ],
        })

    if user.has_perm("Funcionario.view_jobrotationevaluation"):
        menu.append({
            "name": "Job Rotation",
            "url": "lista_jobrotation_evaluation",
            "icon": "fas fa-sync-alt",
        })

    if user.has_perm("Funcionario.view_matrizpolivalencia"):
        menu.append({
            "name": "Matriz de Polivalência",
            "icon": "fas fa-layer-group",
            "submenu": [
                {"name": "Lista de Atividades", "url": "lista_atividades"},
                {"name": "Lista de Matriz", "url": "lista_matriz_polivalencia"},
            ],
        })

    # Relatórios
    submenu_relatorios = []
    if user.has_perm("Funcionario.relatorio_indicador"):
        submenu_relatorios.append({
            "name": "Indicador de Treinamentos",
            "url": "relatorio_indicador"
        })
    if user.has_perm("Funcionario.cronograma_treinamentos"):
        submenu_relatorios.append({
            "name": "Cronograma de Treinamentos",
            "url": "cronograma_treinamentos"
        })
    if user.has_perm("Funcionario.cronograma_avaliacao_eficacia"):
        submenu_relatorios.append({
            "name": "Acompanhamento de Eficácia",
            "url": "cronograma_avaliacao_eficacia"
        })
    if user.has_perm("Funcionario.relatorio_indicador_anual"):
        submenu_relatorios.append({
            "name": "Indicador Anual",
            "url": "relatorio_indicador_anual"
        })
    if user.has_perm("Funcionario.relatorio_aniversariantes"):
        submenu_relatorios.append({
            "name": "Aniversariantes do Mês",
            "url": "relatorio_aniversariantes"
        })

    if user.has_perm("Funcionario.relatorio_banco_horas"):
        submenu_relatorios.append({
            "name": "Banco de Horas",
            "url": "relatorio_banco_horas"
        })

    if submenu_relatorios:
        menu.append({
            "name": "Relatórios",
            "icon": "fas fa-file-alt",
            "submenu": submenu_relatorios,
        })

   # Formulários
    submenu_formularios = []

    if user.has_perm("Funcionario.emitir_carta_competencia"):
        submenu_formularios.append({
            "name": "Carta de Competência",
            "url": "filtro_funcionario_generico",
            "params": "?next_view=formulario_carta_competencia&texto_botao=Gerar+Carta&titulo=Selecionar+Funcionário+para+Carta&icone=bi bi-envelope-paper-fill&emoji=✉️"
        })

    if user.has_perm("Funcionario.emitir_pesquisa_consciencia"):
        submenu_formularios.append({
            "name": "Pesquisa de Consciência",
            "url": "formulario_pesquisa_consciencia"
        })

    if user.has_perm("Funcionario.emitir_capacitacao_pratica"):
        submenu_formularios.append({
            "name": "Avaliação de Capacitação Prática",
            "url": "filtro_funcionario_generico",
            "params": "?next_view=carta_avaliacao_capacitacao&texto_botao=Gerar+Avaliação&titulo=Avaliação+de+Capacitação+Prática&icone=bi bi-person-check&emoji=🧰"
        })

    if user.has_perm("Funcionario.emitir_f033"):
        submenu_formularios.append({
            "name": "Solicitação de Bolsa-Treinamento (F033)",
            "url": "filtro_funcionario_generico",
            "params": "?next_view=formulario_f033&texto_botao=Gerar+F033&titulo=Selecionar+Funcionário+para+F033&icone=bi bi-journal-richtext&emoji=📝"
        })

    if user.has_perm("Funcionario.emitir_saida_antecipada"):
        submenu_formularios.append({
            "name": "Saída Antecipada",
            "url": "filtro_funcionario_generico",
            "params": "?next_view=formulario_saida_antecipada&texto_botao=Gerar+Saída&titulo=Funcionário+para+Saída+Antecipada&icone=bi bi-door-open-fill&emoji=🚪"
        })

    if submenu_formularios:
        menu.append({
            "name": "Formulários",
            "icon": "fas fa-edit",
            "submenu": submenu_formularios,
        })                  

    if user.has_perm("Funcionario.view_bancohoras"):
        menu.append({
            "name": "Banco de Horas",
            "url": "listar_banco_horas",
            "icon": "bi bi-clock-history",
        })

   
    if user.has_perm("Funcionario.view_calendario"):
        menu.append({
            "name": "Calendário",
            "url": "calendario",
            "icon": "fas fa-calendar-alt",
        })

    return menu
