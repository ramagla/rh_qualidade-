metrologia_permissions = {
    # Dashboard e Home
    "home_metrologia": "metrologia.acesso_metrologia",
    "dashboard_qualidade_view": "metrologia.view_tabelatecnica",

    # Tabela Técnica
    "lista_tabelatecnica": "metrologia.view_tabelatecnica",
    "cadastrar_tabelatecnica": "metrologia.add_tabelatecnica",
    "editar_tabelatecnica": "metrologia.change_tabelatecnica",
    "visualizar_tabelatecnica": "metrologia.view_tabelatecnica",
    "excluir_tabelatecnica": "metrologia.delete_tabelatecnica",
    "imprimir_tabelatecnica": "metrologia.imprimir_tabelatecnica",


    # Calibração de Instrumentos
    "lista_calibracoes": "metrologia.view_calibracao",
    "metrologia_calibracoes": "metrologia.view_calibracao",  # redundante, mas pode manter
    "cadastrar_calibracao": "metrologia.add_calibracao",
    "editar_calibracao": "metrologia.change_calibracao",
    "excluir_calibracao": "metrologia.delete_calibracao",

    # API / AJAX
    "obter_exatidao_requerida": "metrologia.view_tabelatecnica",


   # Dispositivos
    "lista_dispositivos": "metrologia.view_dispositivo",
    "cadastrar_dispositivo": "metrologia.add_dispositivo",
    "editar_dispositivo": "metrologia.change_dispositivo",
    "visualizar_dispositivo": "metrologia.view_dispositivo",
    "excluir_dispositivo": "metrologia.delete_dispositivo",
    "imprimir_calibracao_dispositivo": "metrologia.imprimir_calibracao_dispositivo",
    "imprimir_dispositivo": "metrologia.relatorio_equipamentos_calibrar",  # Permissão customizada já existente

    # Movimentações de Dispositivos
    "historico_movimentacoes": "metrologia.view_controleentradasaida",
    "cadastrar_movimentacao": "metrologia.add_controleentradasaida",
    "excluir_movimentacao": "metrologia.delete_controleentradasaida",


    # Calibração de Dispositivos
    "lista_calibracoes_dispositivos": "metrologia.view_calibracaodispositivo",
    "cadastrar_calibracao_dispositivo": "metrologia.add_calibracaodispositivo",
    "editar_calibracao_dispositivo": "metrologia.change_calibracaodispositivo",
    "excluir_calibracao_dispositivo": "metrologia.delete_calibracaodispositivo",
    "imprimir_calibracao_dispositivo": "metrologia.view_calibracaodispositivo",
    "get_dispositivo_info": "metrologia.view_dispositivo",


    # Calibração de Instrumentos
    "lista_calibracoes": "metrologia.view_calibracao",
    "metrologia_calibracoes": "metrologia.view_calibracao",
    "cadastrar_calibracao": "metrologia.add_calibracao",
    "editar_calibracao": "metrologia.change_calibracao",
    "excluir_calibracao": "metrologia.delete_calibracao",

   # Cronogramas
    "cronograma_equipamentos": "metrologia.cronograma_calibracao_equipamentos",
    "cronograma_dispositivos": "metrologia.cronograma_calibracao_dispositivos",


    # Relatórios
    "lista_equipamentos_a_calibrar": "metrologia.relatorio_equipamentos_calibrar",
    "listar_equipamentos_funcionario": "metrologia.relatorio_equipamentos_por_funcionario",
    "listar_funcionarios_ativos": "metrologia.relatorio_equipamentos_por_funcionario",
    "equipamentos_por_funcionario": "metrologia.relatorio_equipamentos_por_funcionario",
    "equipamentos_para_calibracao": "metrologia.relatorio_f062",
    "gerar_f062": "metrologia.gerar_f062",

    # Informações via API / AJAX
    "get_dispositivo_info": "metrologia.view_dispositivo",

    "lista_analise_critica": "metrologia.view_análisecrítica",


  # PARA (exemplo de ajustes no mapa)
    "lista_analise_critica": "metrologia.view_analisecriticametrologia",
    "cadastrar_analise_critica": "metrologia.add_analisecriticametrologia",
    "editar_analise_critica": "metrologia.change_analisecriticametrologia",
    "visualizar_analise_critica": "metrologia.view_analisecriticametrologia",
    "excluir_analise_critica": "metrologia.delete_analisecriticametrologia",





}
