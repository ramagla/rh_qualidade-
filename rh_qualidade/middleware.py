from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import resolve


class PermissionMiddleware:
    """
    Middleware para verificar autenticação e permissões com base nas URLs acessadas.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar se o usuário está autenticado
        if not request.user.is_authenticated:
            if not request.path.startswith("/login/"):
                return redirect("login")


        # Resolver a view correspondente à URL atual
        resolver_match = resolve(request.path)
        view_name = resolver_match.view_name  # Nome da view

        # Mapeamento de permissões
        permission_map = {
            # APP Metrologia
            # Calibrações de Dispositivos
            "lista_calibracoes_dispositivos": "metrologia.view_calibracaodispositivo",
            "cadastrar_calibracao_dispositivo": "metrologia.add_calibracaodispositivo",
            "editar_calibracao_dispositivo": "metrologia.change_calibracaodispositivo",
            "excluir_calibracao_dispositivo": "metrologia.delete_calibracaodispositivo",
            "imprimir_calibracao_dispositivo": "metrologia.view_calibracaodispositivo",
            "get_dispositivo_info": "metrologia.view_dispositivo",
            # Calibrações de Instrumentos
            "lista_calibracoes": "metrologia.view_calibracao",
            "metrologia_calibracoes": "metrologia.view_calibracao",
            "cadastrar_calibracao": "metrologia.add_calibracao",
            "editar_calibracao": "metrologia.change_calibracao",
            "excluir_calibracao": "metrologia.delete_calibracao",
            "obter_exatidao_requerida": "metrologia.view_tabelatecnica",
            # Cronogramas de Equipamentos e Dispositivos
            "cronograma_equipamentos": "metrologia.view_tabelatecnica",
            "cronograma_dispositivos": "metrologia.view_dispositivo",
            # Dispositivos e Movimentações
            "lista_dispositivos": "metrologia.view_dispositivo",
            "cadastrar_dispositivo": "metrologia.add_dispositivo",
            "editar_dispositivo": "metrologia.change_dispositivo",
            "excluir_dispositivo": "metrologia.delete_dispositivo",
            "visualizar_dispositivo": "metrologia.view_dispositivo",
            "imprimir_dispositivo": "metrologia.view_dispositivo",
            "historico_movimentacoes": "metrologia.view_controleentradasaida",
            "cadastrar_movimentacao": "metrologia.add_controleentradasaida",
            "excluir_movimentacao": "metrologia.delete_controleentradasaida",
            # Home - Metrologia
            "home_metrologia": "metrologia.view_tabelatecnica",
            # Relatórios de Equipamentos e Funcionários
            "lista_equipamentos_a_calibrar": "metrologia.view_tabelatecnica",
            "listar_equipamentos_funcionario": "metrologia.view_tabelatecnica",
            "listar_funcionarios_ativos": "Funcionario.view_funcionario",
            "equipamentos_por_funcionario": "metrologia.view_tabelatecnica",
            # Tabela Técnica e Alertas
            "lista_tabelatecnica": "metrologia.view_tabelatecnica",
            "cadastrar_tabelatecnica": "metrologia.add_tabelatecnica",
            "editar_tabelatecnica": "metrologia.change_tabelatecnica",
            "visualizar_tabelatecnica": "metrologia.view_tabelatecnica",
            "excluir_tabelatecnica": "metrologia.delete_tabelatecnica",
            "imprimir_tabelatecnica": "metrologia.view_tabelatecnica",
            "enviar_alertas_calibracao": "metrologia.view_tabelatecnica",
            # APP Funcionario
            # API
            "get_funcionario_info": "Funcionario.view_funcionario",
            "get_treinamentos": "Funcionario.view_treinamento",
            "get_treinamentos_por_funcionario": "Funcionario.view_treinamento",
            "get_competencias": "Funcionario.view_cargo",
            "get_cargo": "Funcionario.view_cargo",
            "get_funcionario_ficha": "Funcionario.view_funcionario",
            "atualizar_cargo_funcionario": "Funcionario.change_funcionario",
            "funcionario_api": "Funcionario.view_funcionario",
            # Avaliação Anual
            "lista_avaliacao_anual": "Funcionario.view_avaliacaoanual",
            "cadastrar_avaliacao_anual": "Funcionario.add_avaliacaoanual",
            "editar_avaliacao_anual": "Funcionario.change_avaliacaoanual",
            "excluir_avaliacao_anual": "Funcionario.delete_avaliacaoanual",
            "imprimir_avaliacao": "Funcionario.view_avaliacaoanual",
            "visualizar_avaliacao_anual": "Funcionario.view_avaliacaoanual",
            "imprimir_simplificado": "Funcionario.view_avaliacaoanual",
            "cadastrar_type_avaliacao": "Funcionario.add_avaliacaoanual",
            # Avaliação de Experiência
            "lista_avaliacao_experiencia": "Funcionario.view_avaliacaoexperiencia",
            "cadastrar_avaliacao_experiencia": "Funcionario.add_avaliacaoexperiencia",
            "editar_avaliacao_experiencia": "Funcionario.change_avaliacaoexperiencia",
            "excluir_avaliacao_experiencia": "Funcionario.delete_avaliacaoexperiencia",
            "visualizar_avaliacao_experiencia": "Funcionario.view_avaliacaoexperiencia",
            "imprimir_avaliacao_experiencia": "Funcionario.view_avaliacaoexperiencia",
            # Avaliação de Treinamento
            "lista_avaliacoes": "Funcionario.view_avaliacaotreinamento",
            "cadastrar_avaliacao": "Funcionario.add_avaliacaotreinamento",
            "editar_avaliacao": "Funcionario.change_avaliacaotreinamento",
            "visualizar_avaliacao": "Funcionario.view_avaliacaotreinamento",
            "imprimir_treinamento": "Funcionario.view_avaliacaotreinamento",
            "excluir_avaliacao": "Funcionario.delete_avaliacaotreinamento",
            "get_treinamentos_por_funcionario": "Funcionario.view_treinamento",
            # Cargos e Revisões
            "lista_cargos": "Funcionario.view_cargo",
            "cadastrar_cargo": "Funcionario.add_cargo",
            "excluir_cargo": "Funcionario.delete_cargo",
            "historico_revisoes": "Funcionario.view_revisao",
            "adicionar_revisao": "Funcionario.add_revisao",
            "excluir_revisao": "Funcionario.delete_revisao",
            "obter_cargos": "Funcionario.view_cargo",
            "buscar_cargos": "Funcionario.view_cargo",
            "editar_cargo": "Funcionario.change_cargo",
            "imprimir_cargo": "Funcionario.view_cargo",
            # Comunicados
            "lista_comunicados": "Funcionario.view_comunicado",
            "imprimir_comunicado": "Funcionario.view_comunicado",
            "cadastrar_comunicado": "Funcionario.add_comunicado",
            "visualizar_comunicado": "Funcionario.view_comunicado",
            "editar_comunicado": "Funcionario.change_comunicado",
            "excluir_comunicado": "Funcionario.delete_comunicado",
            "imprimir_assinaturas": "Funcionario.view_comunicado",
            # Documentos e Revisões
            "lista_documentos": "Funcionario.view_documento",
            "cadastrar_documento": "Funcionario.add_documento",
            "editar_documento": "Funcionario.change_documento",
            "excluir_documento": "Funcionario.delete_documento",
            "historico_documentos": "Funcionario.view_revisao",
            "adicionar_documento": "Funcionario.add_revisao",
            "excluir_revisao2": "Funcionario.delete_revisao",
            # Formulários e Avaliação de Capacitação
            "avaliacao_capacitacao": "Funcionario.view_funcionario",
            "formulario_pesquisa_consciencia": "Funcionario.view_funcionario",
            "formulario_carta_competencia": "Funcionario.view_funcionario",
            "filtro_funcionario": "Funcionario.view_funcionario",
            "filtro_carta_competencia": "Funcionario.view_funcionario",
            # Funcionários e Histórico de Cargos
            "lista_funcionarios": "Funcionario.view_funcionario",
            "visualizar_funcionario": "Funcionario.view_funcionario",
            "cadastrar_funcionario": "Funcionario.add_funcionario",
            "editar_funcionario": "Funcionario.change_funcionario",
            "excluir_funcionario": "Funcionario.delete_funcionario",
            "imprimir_ficha": "Funcionario.view_funcionario",
            "organograma_view": "Funcionario.view_funcionario",
            "listar_historico_cargo": "Funcionario.view_historico",
            "adicionar_historico_cargo": "Funcionario.add_historico",
            "excluir_historico_cargo": "Funcionario.delete_historico",
            # Funcionalidades Gerais e Eventos
            "home": "Funcionario.view_funcionario",
            "sucesso_view": "Funcionario.view_funcionario",
            "login_view": None,  # Nenhuma permissão necessária
            "calendario_view": "Funcionario.view_evento",
            "adicionar_evento": "Funcionario.add_evento",
            "excluir_evento": "Funcionario.delete_evento",
            "editar_evento": "Funcionario.change_evento",
            "exportar_calendario": "Funcionario.view_evento",
            "imprimir_calendario": "Funcionario.view_evento",
            # Integração de Funcionários
            "lista_integracoes": "Funcionario.view_integracaofuncionario",
            "visualizar_integracao": "Funcionario.view_integracaofuncionario",
            "cadastrar_integracao": "Funcionario.add_integracaofuncionario",
            "editar_integracao": "Funcionario.change_integracaofuncionario",
            "excluir_integracao": "Funcionario.delete_integracaofuncionario",
            "imprimir_integracao": "Funcionario.view_integracaofuncionario",
            # Avaliações de Job Rotation
            "lista_jobrotation_evaluation": "Funcionario.view_jobrotationevaluation",
            "cadastrar_jobrotation_evaluation": "Funcionario.add_jobrotationevaluation",
            "editar_jobrotation_evaluation": "Funcionario.change_jobrotationevaluation",
            "excluir_jobrotation": "Funcionario.delete_jobrotationevaluation",
            "visualizar_jobrotation_evaluation": "Funcionario.view_jobrotationevaluation",
            "imprimir_jobrotation_evaluation": "Funcionario.view_jobrotationevaluation",
            # Listas de Presença
            "lista_presenca": "Funcionario.view_listapresenca",
            "cadastrar_lista_presenca": "Funcionario.add_listapresenca",
            "editar_lista_presenca": "Funcionario.change_listapresenca",
            "excluir_lista_presenca": "Funcionario.delete_listapresenca",
            "visualizar_lista_presenca": "Funcionario.view_listapresenca",
            "imprimir_lista_presenca": "Funcionario.view_listapresenca",
            "exportar_listas_presenca": "Funcionario.view_listapresenca",
            # Matriz de Polivalência e Atividades
            "lista_matriz_polivalencia": "Funcionario.view_matrizpolivalencia",
            "cadastrar_matriz_polivalencia": "Funcionario.add_matrizpolivalencia",
            "editar_matriz_polivalencia": "Funcionario.change_matrizpolivalencia",
            "excluir_matriz_polivalencia": "Funcionario.delete_matrizpolivalencia",
            "imprimir_matriz": "Funcionario.view_matrizpolivalencia",
            "lista_atividades": "Funcionario.view_atividade",
            "cadastrar_atividade": "Funcionario.add_atividade",
            "editar_atividade": "Funcionario.change_atividade",
            "excluir_atividade": "Funcionario.delete_atividade",
            "visualizar_atividade": "Funcionario.view_atividade",
            "gerenciar_notas": "Funcionario.change_nota",
            "get_atividades_por_departamento": "Funcionario.view_atividade",
            "get_atividades_e_funcionarios_por_departamento": "Funcionario.view_atividade",
            # Relatórios e Cronogramas
            "relatorio_planilha_treinamentos": "Funcionario.view_treinamento",
            "relatorio_indicador_anual": "Funcionario.view_avaliacaoanual",
            "cronograma_treinamentos": "Funcionario.view_treinamento",
            "cronograma_avaliacao_eficacia": "Funcionario.view_avaliacaotreinamento",
            # Treinamentos
            "lista_treinamentos": "Funcionario.view_treinamento",
            "cadastrar_treinamento": "Funcionario.add_treinamento",
            "editar_treinamento": "Funcionario.change_treinamento",
            "excluir_treinamento": "Funcionario.delete_treinamento",
            "visualizar_treinamento": "Funcionario.view_treinamento",
            "imprimir_f003": "Funcionario.view_treinamento",
            "gerar_pdf": "Funcionario.view_treinamento",
            "gerar_relatorio_f003": "Funcionario.view_treinamento",
            "exportar_treinamentos_csv": "Funcionario.view_treinamento",
            "levantamento_treinamento": "Funcionario.view_treinamento",
        }

        # Verificar se a view exige permissão
        required_permission = permission_map.get(view_name)

        # Se uma permissão é exigida e o usuário não a possui, negar acesso
        if required_permission and not request.user.has_perm(required_permission):
            return redirect("acesso_negado")

        # Continuar com a resposta
        return self.get_response(request)
