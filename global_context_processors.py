from datetime import datetime

def global_menu(request):
    # Definindo menus por módulo
    menu_metrologia = [
        {'name': 'Cadastros', 'icon': 'fas fa-folder', 'submenu': [
            {'name': 'Instrumentos', 'url': 'lista_tabelatecnica', 'icon': 'fas fa-ruler-combined'},
            {'name': 'Dispositivos', 'url': 'lista_dispositivos', 'icon': 'fas fa-cogs'},
        ]},
        {'name': 'Calibrações', 'icon': 'fas fa-cogs', 'submenu': [
            {'name': 'Calibrações de Instrumentos', 'url': 'calibracoes_instrumentos', 'icon': 'fas fa-tools'},
            {'name': 'Calibrações de Dispositivos', 'url': 'calibracoes_dispositivos', 'icon': 'fas fa-wrench'},
        ]},
        {'name': 'Cronogramas', 'icon': 'fas fa-calendar-alt', 'submenu': [
            {'name': 'Cronograma de Equipamentos', 'url': 'cronograma_calibracao'},
            {'name': 'Cronograma de Dispositivos', 'url': 'cronograma_dispositivos'},
        ]},
    ]
    

    menu_recursos_humanos = [ {'name': 'Dashboard', 'url': 'funcionarios_home', 'icon': 'fas fa-tachometer-alt'},
            {'name': 'Comunicados Internos', 'url': 'lista_comunicados', 'icon': 'fas fa-bullhorn'},
            {'name': 'Cargos', 'url': 'lista_cargos', 'icon': 'fas fa-briefcase'},
            {'name': 'Colaboradores', 'url': 'lista_funcionarios', 'icon': 'fas fa-user'},
            {'name': 'Integrações', 'url': 'lista_integracoes', 'icon': 'bi bi-person-badge'},
            {'name': 'Treinamentos', 'icon': 'fas fa-graduation-cap', 'submenu': [
                {'name': 'Lista de Treinamentos', 'url': 'lista_treinamentos'},
                {'name': 'Lista de Presença', 'url': 'lista_presenca'},
                {'name': 'Avaliação de Treinamentos', 'url': 'lista_avaliacoes'},
            ]},
            {'name': 'Desempenho', 'icon': 'fas fa-chart-line', 'submenu': [
                {'name': 'Anual', 'url': 'lista_avaliacao_anual'},
                {'name': 'Experiência', 'url': 'lista_avaliacao_experiencia'},
            ]},
            {'name': 'Job Rotation', 'url': 'lista_jobrotation_evaluation', 'icon': 'fas fa-sync-alt'},
            {'name': 'Matriz de Polivalência', 'icon': 'fas fa-layer-group', 'submenu': [
                {'name': 'Lista de Atividades', 'url': 'lista_atividades'},
                {'name': 'Lista de Matriz', 'url': 'lista_matriz_polivalencia'},
            ]},
            {'name': 'Relatórios', 'icon': 'fas fa-file-alt', 'submenu': [
                {'name': 'Indicador de Treinamentos', 'url': 'relatorio_indicador'},
                {'name': 'Indicador Anual', 'url': 'relatorio_indicador_anual'},
                {'name': 'Cronograma de Treinamentos', 'url': 'cronograma_treinamentos'},
                {'name': 'Cronograma de Eficácia', 'url': 'cronograma_avaliacao_eficacia'},
            ]},
            {'name': 'Formulários', 'icon': 'fas fa-edit', 'submenu': [
                {'name': 'Carta de Competência', 'url': 'filtro_funcionario'},
                {'name': 'Pesquisa de Consciência', 'url': 'formulario_pesquisa_consciencia'},
                {'name': 'Avaliação de Capacitação Prática', 'url': 'filtro_carta_competencia'},
            ]},
            {'name': 'Documentos', 'url': 'lista_documentos', 'icon': 'fas fa-folder-open'},
            {'name': 'Calendario', 'url': 'calendario', 'icon': 'fas fa-calendar-alt'},
        ]

    # Definir o menu com base no módulo ativo (pega o primeiro segmento da URL)
    active_module = request.path.split('/')[1]

    if active_module == 'metrologia':
        menu = menu_metrologia
    else:
        menu = menu_recursos_humanos

    return {
        'menu': menu,  # Menu dinâmico para o módulo
        'ano_atual': datetime.now().year,  # Ano atual
    }
