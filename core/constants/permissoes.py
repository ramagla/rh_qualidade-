from django.apps import AppConfig
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver


CUSTOM_PERMISSOES = [
    # Qualidade de Fornecimento
    ("qualidade_fornecimento", "normatecnica", "aprovar_normatecnica", "Pode aprovar norma técnica"),
    ("qualidade_fornecimento", "relatoriof045", "f045_status", "Pode alterar status do F045"),
    ("qualidade_fornecimento", "materiaprimacatalogo", "importar_materia_prima_excel", "Pode importar matéria-prima via Excel"),
    ("qualidade_fornecimento", "relacaomateriaprima", "importar_excel_tb050", "Pode importar TB050 via Excel"),
    ("qualidade_fornecimento", "relacaomateriaprima", "selecionar_etiquetas_tb050", "Pode selecionar etiquetas do TB050"),
    ("qualidade_fornecimento", "relacaomateriaprima", "imprimir_etiquetas_tb050", "Pode imprimir etiquetas do TB050"),
    ("qualidade_fornecimento", "relacaomateriaprima", "imprimir_etiquetas_pdf", "Pode gerar PDF de etiquetas do TB050"),
    ("qualidade_fornecimento", "materiaprimacatalogo", "visualizar_materia_prima", "Pode visualizar matéria-prima"),
    ("qualidade_fornecimento", "relacaomateriaprima", "get_rolos_peso", "Pode obter peso dos rolos"),
    ("qualidade_fornecimento", "normatecnica", "norma_aprovada", "Pode verificar se norma está aprovada"),
    ("qualidade_fornecimento", "fornecedorqualificado", "relatorio_avaliacao_view", "Pode visualizar relatório de avaliação semestral"),
    ("qualidade_fornecimento", "relacaomateriaprima", "gerar_f045", "Pode gerar relatório F045"),
    ("qualidade_fornecimento", "relatoriof045", "acesso_qualidade", "Pode acessar o módulo Qualidade de Fornecimento"),
    ("qualidade_fornecimento", "relatoriof045", "dashboard_qualidade", "Pode acessar o dashboard de Qualidade de Fornecimento"),
    ("qualidade_fornecimento", "fornecedorqualificado", "importar_excel_fornecedores", "Pode importar fornecedores via Excel"),
    ("qualidade_fornecimento", "controleservicoexterno", "add_controleservicoexterno", "Pode adicionar Controle de Serviço Externo"),
    ("qualidade_fornecimento", "relatorioinspecaoservico", "add_relatorioinspecaoservico", "Pode adicionar Relatório de Inspeção de Serviço"),
    ("qualidade_fornecimento", "relatorioiqf", "view_relatorioiqf", "Pode visualizar o relatório 8.1 - IQF"),
    ("qualidade_fornecimento", "inspecao10", "importar_excel_inspecao10", "Pode importar inspeções 10 via Excel"),
    ("qualidade_fornecimento", "relatorioinspecaoanalitico", "view_relatorioinspecaoanalitico", "Pode visualizar relatório analítico de inspeções"),
    ("qualidade_fornecimento", "relatorioppm", "view_relatorio_ppm", "Pode visualizar o relatório 6.4 - PPM"),



    # Funcionário
    ("Funcionario", "avaliacaotreinamento", "imprimir_treinamento", "Pode imprimir avaliação de treinamento"),
    ("Funcionario", "listapresenca", "exportar_listas_presenca", "Pode exportar listas de presença"),
    ("Funcionario", "avaliacaoanual", "imprimir_avaliacao", "Pode imprimir avaliação anual"),
    ("Funcionario", "avaliacaoanual", "imprimir_simplificado", "Pode imprimir avaliação anual simplificada"),
    ("Funcionario", "avaliacaoexperiencia", "imprimir_avaliacao_experiencia", "Pode imprimir avaliação de experiência"),
    ("Funcionario", "jobrotationevaluation", "imprimir_jobrotation_evaluation", "Pode imprimir avaliação de Job Rotation"),
    ("Funcionario", "cargo", "imprimir_cargo", "Pode imprimir cargo"),
    ("Funcionario", "comunicado", "imprimir_comunicado", "Pode imprimir comunicado"),
    ("Funcionario", "comunicado", "imprimir_assinaturas", "Pode imprimir lista de assinaturas do comunicado"),
    ("Funcionario", "funcionario", "imprimir_ficha", "Pode imprimir ficha do funcionário"),
    ("Funcionario", "funcionario", "formulario_carta_competencia", "Pode emitir carta de competência"),
    ("Funcionario", "funcionario", "formulario_pesquisa_consciencia", "Pode emitir pesquisa de consciência"),
    ("Funcionario", "funcionario", "avaliacao_capacitacao", "Pode emitir avaliação de capacitação"),
    ("Funcionario", "funcionario", "filtro_funcionario", "Pode usar filtro de funcionário"),
    ("Funcionario", "funcionario", "filtro_carta_competencia", "Pode usar filtro da carta de competência"),
    ("Funcionario", "evento", "exportar_calendario", "Pode exportar o calendário"),
    ("Funcionario", "evento", "imprimir_calendario", "Pode imprimir o calendário"),
    ("Funcionario", "funcionario", "acesso_rh", "Pode acessar o módulo RH"),
    ("Funcionario", "cargo", "visualizar_organograma", "Pode visualizar o organograma de cargos"),
    ("metrologia", "tabelatecnica", "acesso_metrologia", "Pode acessar o módulo Metrologia"),
    ("Funcionario", "revisao", "view_revisao", "Pode visualizar descrição da revisão"),
    ("Funcionario", "integracaofuncionario", "imprimir_integracao", "Pode imprimir integração"),
    ("Funcionario", "listapresenca", "imprimir_lista_presenca", "Pode imprimir lista de presença"),

    # Relatórios RH
    ("Funcionario", "relatorio", "relatorio_indicador", "Pode acessar o Indicador de Treinamentos"),
    ("Funcionario", "relatorio", "relatorio_indicador_anual", "Pode acessar o Indicador Anual"),
    ("Funcionario", "relatorio", "cronograma_treinamentos", "Pode acessar o Cronograma de Treinamentos"),
    ("Funcionario", "relatorio", "cronograma_avaliacao_eficacia", "Pode acessar o Cronograma de Avaliação de Eficácia"),
    ("Funcionario", "relatorio", "relatorio_aniversariantes", "Pode acessar o Relatório de Aniversariantes"),
    ("Funcionario", "relatorio", "relatorio_banco_horas", "Pode acessar relatório de Banco de Horas"),


    # Formulários RH
    ("Funcionario", "funcionario", "emitir_carta_competencia", "Pode emitir carta de competência"),
    ("Funcionario", "funcionario", "emitir_pesquisa_consciencia", "Pode emitir pesquisa de consciência"),
    ("Funcionario", "funcionario", "emitir_capacitacao_pratica", "Pode emitir avaliação de capacitação prática"),
    ("Funcionario", "funcionario", "emitir_f033", "Pode emitir Solicitação de Bolsa-Treinamento (F033)"),
    ("Funcionario", "funcionario", "emitir_saida_antecipada", "Pode emitir formulário de Saída Antecipada"),
    ("Funcionario", "funcionario", "emitir_ficha_epi", "Pode emitir Ficha de EPIs"),
    ("Funcionario", "recibopagamento", "importar_recibo_pagamento", "Pode importar recibo de pagamento"),


    ("portaria", "pessoaportaria", "acesso_portaria", "Pode acessar o módulo Portaria"),

    # Portaria – Relatórios
    ("portaria", "relatorio", "relatorio_visitantes", "Pode acessar relatório de visitantes"),
    ("portaria", "relatorio", "relatorio_atrasos_saidas", "Pode acessar relatório de atrasos e saídas"),
    ("portaria", "relatorio", "relatorio_ligacoes_recebidas", "Pode acessar relatório de ligações"),
    ("portaria", "relatorio", "relatorio_ocorrencias", "Pode acessar relatório de ocorrências"),
    ("portaria", "relatorio", "relatorio_consumo_agua", "Pode acessar relatório de consumo de água"),
    ("portaria", "relatorio", "relatorio_horas_extras", "Pode acessar relatório de horas extras"),

    # Acesso ao módulo
    ("metrologia", "tabelatecnica", "acesso_metrologia", "Pode acessar o módulo Metrologia"),

    # Relatórios
    ("metrologia", "relatorio", "relatorio_equipamentos_calibrar", "Pode acessar o relatório de Equipamentos a Calibrar"),
    ("metrologia", "relatorio", "relatorio_equipamentos_por_funcionario", "Pode acessar o relatório de Equipamentos por Funcionário"),

    # Cronogramas
    ("metrologia", "cronograma", "cronograma_calibracao_equipamentos", "Pode acessar o cronograma de Calibração de Equipamentos"),
    ("metrologia", "cronograma", "cronograma_calibracao_dispositivos", "Pode acessar o cronograma de Calibração de Dispositivos"),

    ("comercial", "dashboard", "acesso_comercial", "Pode acessar o módulo Comercial"),
    ("comercial", "ferramenta", "enviar_cotacao", "Pode enviar cotação de ferramenta"),
    ("comercial", "precalculo", "gerar_proposta", "Pode gerar proposta comercial"),
    ("comercial", "precalculo", "ver_precificacao", "Pode acessar precificação detalhada do produto"),
    ("comercial", "precalculo", "duplicar_precalculo", "Pode duplicar pré-cálculo"),
    ("comercial", "cliente", "importar_excel_clientes", "Pode importar clientes via Excel"),
    ("comercial", "item", "importar_excel_itens", "Pode importar itens via Excel"),

    ("metrologia", "relatorio", "relatorio_f062", "Pode acessar o relatório Solicitação de Orçamento para Calibração (F062)"),
    ("metrologia", "relatorio", "gerar_f062", "Pode gerar a Solicitação de Orçamento para Calibração (F062)"),
    ("metrologia", "controleentradasaida", "view_controleentradasaida", "Pode visualizar movimentações de dispositivo"),



]