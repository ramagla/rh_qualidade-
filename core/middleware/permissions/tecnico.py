# core/middleware/permissions/tecnico.py

"""
Mapeamento das permissões necessárias para acessar
as views do módulo Técnico.
"""

tecnico_permissions = {
    # Dashboard
    "tecnico:tecnico_home": "tecnico.acesso_tecnico",

    # Indicadores Técnicos
    "tecnico:indicador_51_prazo_desenvolvimento": "tecnico.view_indicador_tecnico",

    # Máquinas
    "tecnico:tecnico_maquinas":           "tecnico.view_maquina",
    "tecnico:tecnico_cadastrar_maquina":  "tecnico.add_maquina",
    "tecnico:tecnico_editar_maquina":     "tecnico.change_maquina",
    "tecnico:tecnico_excluir_maquina":    "tecnico.delete_maquina",

    # AJAX – serviços realizados (apenas login_required)
    "tecnico:ajax_listar_servicos":       None,
    "tecnico:ajax_adicionar_servico":     None,
    "tecnico:ajax_editar_servico":        None,
    "tecnico:ajax_excluir_servico":       None,

    # Roteiros
    "tecnico:tecnico_roteiros":           "tecnico.view_roteiroproducao",
    "tecnico:tecnico_visualizar_roteiro": "tecnico.view_roteiroproducao",
    "tecnico:tecnico_excluir_roteiro":    "tecnico.delete_roteiroproducao",
    "tecnico:tecnico_cadastrar_roteiro":  "tecnico.add_roteiroproducao",
    "tecnico:tecnico_editar_roteiro":     "tecnico.change_roteiroproducao",
    "tecnico:aprovar_roteiros_lote":      "tecnico.change_roteiroproducao",
    "tecnico:clonar_roteiro":             "tecnico.add_roteiroproducao",
    "tecnico:importar_roteiros_excel":    "tecnico.add_roteiroproducao",
}
