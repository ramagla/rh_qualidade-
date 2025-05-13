metrologia_permissions = {
    # Dashboard e Home
    "home_metrologia": "metrologia.view_tabelatecnica",
    "dashboard_qualidade_view": "metrologia.view_tabelatecnica",

    # Tabela Técnica
    "lista_tabelatecnica": "metrologia.view_tabelatecnica",
    "cadastrar_tabelatecnica": "metrologia.add_tabelatecnica",
    "editar_tabelatecnica": "metrologia.change_tabelatecnica",
    "visualizar_tabelatecnica": "metrologia.view_tabelatecnica",
    "excluir_tabelatecnica": "metrologia.delete_tabelatecnica",
    "imprimir_tabelatecnica": "metrologia.view_tabelatecnica",

    # Dispositivos
    "lista_dispositivos": "metrologia.view_dispositivo",
    "cadastrar_dispositivo": "metrologia.add_dispositivo",
    "editar_dispositivo": "metrologia.change_dispositivo",
    "visualizar_dispositivo": "metrologia.view_dispositivo",
    "excluir_dispositivo": "metrologia.delete_dispositivo",
    "imprimir_dispositivo": "metrologia.view_dispositivo",

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

    # Calibração de Instrumentos
    "lista_calibracoes": "metrologia.view_calibracao",
    "metrologia_calibracoes": "metrologia.view_calibracao",
    "cadastrar_calibracao": "metrologia.add_calibracao",
    "editar_calibracao": "metrologia.change_calibracao",
    "excluir_calibracao": "metrologia.delete_calibracao",

    # Cronogramas
    "cronograma_equipamentos": "metrologia.view_tabelatecnica",
    "cronograma_dispositivos": "metrologia.view_dispositivo",

    # Relatórios
    "lista_equipamentos_a_calibrar": "metrologia.view_tabelatecnica",
    "listar_equipamentos_funcionario": "metrologia.view_tabelatecnica",
    "equipamentos_por_funcionario": "metrologia.view_tabelatecnica",

    # Informações via API / AJAX
    "obter_exatidao_requerida": "metrologia.view_tabelatecnica",
    "get_dispositivo_info": "metrologia.view_dispositivo",
}
