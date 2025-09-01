from django.urls import path
from comercial.views import centro_custo_views, cliente_views, ferramenta_views, metas_views, viabilidade_views
from comercial.views import item_views
from comercial.views import dashboard_views
from comercial.views import cotacao_views, precalc_views
from comercial.views import ajax_views
from comercial.utils.email_cotacao_utils import (
    responder_cotacao_materia_prima,
    responder_cotacao_servico_lote,
)
from comercial.views import ordem_desenvolvimento_views
from comercial.views import indicadores_views
from comercial.views import api_views
from comercial.views import faturamento_views

urlpatterns = [
    # Dashboard
    path('dashboard/', dashboard_views.dashboard_comercial, name='comercial_home'),

    # Clientes
    path("clientes/", cliente_views.lista_clientes, name="lista_clientes"),
    path("clientes/cadastrar/", cliente_views.cadastrar_cliente, name="cadastrar_cliente"),
    path("clientes/editar/<int:pk>/", cliente_views.editar_cliente, name="editar_cliente"),
    path("clientes/visualizar/<int:pk>/", cliente_views.visualizar_cliente, name="visualizar_cliente"),
    path("clientes/excluir/<int:pk>/", cliente_views.excluir_cliente, name="excluir_cliente"),
    path("clientes/verificar-cnpj/", cliente_views.verificar_cnpj_existente, name="verificar_cnpj_existente"),

    # Itens
    path("itens/", item_views.lista_itens, name="lista_itens"),
    path("itens/cadastrar/", item_views.cadastrar_item, name="cadastrar_item"),
    path("itens/editar/<int:pk>/", item_views.editar_item, name="editar_item"),
    path("itens/visualizar/<int:pk>/", item_views.visualizar_item, name="visualizar_item"),
    path("itens/excluir/<int:pk>/", item_views.excluir_item, name="excluir_item"),

    # Ferramentas
    path("ferramentas/", ferramenta_views.lista_ferramentas, name="lista_ferramentas"),
    path("ferramentas/cadastrar/", ferramenta_views.cadastrar_ferramenta, name="cadastrar_ferramenta"),
    path("ferramentas/editar/<int:pk>/", ferramenta_views.editar_ferramenta, name="editar_ferramenta"),
    path("ferramentas/excluir/<int:pk>/", ferramenta_views.excluir_ferramenta, name="excluir_ferramenta"),
    path("ferramentas/cotacao/<uuid:token>/", ferramenta_views.formulario_cotacao, name="responder_cotacao"),
    path("ferramentas/enviar-cotacao/<int:pk>/", ferramenta_views.enviar_cotacao_ferramenta, name="enviar_cotacao_ferramenta"),
    path("ferramentas/visualizar/<int:pk>/", ferramenta_views.visualizar_ferramenta, name="visualizar_ferramenta"),
    path("ferramentas/blocos/", ferramenta_views.lista_blocos, name="lista_blocos"),
    path("ferramentas/blocos/novo/", ferramenta_views.cadastrar_bloco, name="cadastrar_bloco"),
    path("ferramentas/blocos/<int:pk>/editar/", ferramenta_views.editar_bloco, name="editar_bloco"),
    path("ferramentas/blocos/<int:pk>/excluir/", ferramenta_views.excluir_bloco, name="excluir_bloco"),
    path("ajax/valor_hora_centro_custo/", ferramenta_views.ajax_valor_hora_centro_custo, name="ajax_valor_hora_centro_custo"),
    path("ajax/materiais-do-bloco/<int:bloco_id>/", ferramenta_views.ajax_materiais_do_bloco, name="ajax_materiais_do_bloco"),

    # Centro de Custo
    path("centros-custo/", centro_custo_views.lista_centros_custo, name="lista_centros_custo"),
    path("centros-custo/cadastrar/", centro_custo_views.cadastrar_centro_custo, name="cadastrar_centro_custo"),
    path("centros-custo/editar/<int:pk>/", centro_custo_views.editar_centro_custo, name="editar_centro_custo"),
    path("centros-custo/visualizar/<int:pk>/", centro_custo_views.visualizar_centro_custo, name="visualizar_centro_custo"),

    # Cotações
    path("cotacoes/", cotacao_views.lista_cotacoes, name="lista_cotacoes"),
    path("cotacoes/cadastrar/", cotacao_views.cadastrar_cotacao, name="cadastrar_cotacao"),
    path("cotacoes/editar/<int:pk>/", cotacao_views.editar_cotacao, name="editar_cotacao"),
    path("cotacoes/excluir/<int:pk>/", cotacao_views.excluir_cotacao, name="excluir_cotacao"),
    path("cotacoes/visualizar/<int:pk>/", cotacao_views.visualizar_cotacao, name="visualizar_cotacao"),
    path("cotacoes/ajax/dados-cliente/", cotacao_views.dados_cliente_ajax, name="dados_cliente_ajax"),

    # Pré-Cálculo
    path("cotacoes/<int:pk>/precalculo/", precalc_views.itens_precaculo, name="itens_precaculo"),
    path("cotacoes/<int:pk>/precalculo/editar/", precalc_views.editar_precaculo, name="editar_precalculo"),
    path("cotacoes/<int:pk>/precalculo/criar/", precalc_views.criar_precaculo, name="criar_precalculo"),
    path("cotacoes/precalculo/<int:pk>/excluir/", precalc_views.excluir_precalculo, name="excluir_precalculo"),

    # Resposta das Cotações
    path("precalculo/servico/<int:pk>/responder/", responder_cotacao_servico_lote, name="responder_cotacao_servico_lote"),
    path("precalculo/materia/<int:pk>/responder/", responder_cotacao_materia_prima, name="responder_cotacao_materia_prima"),

    # Ajax
    path("ajax/codigo-materia-prima/", ajax_views.ajax_codigo_materia_prima_por_roteiro, name="ajax_codigo_materia_prima"),
    path("ajax/valor_ferramenta/", ajax_views.ajax_valor_ferramenta, name="ajax_valor_ferramenta"),
    path('ajax/precalculo/<int:pk>/dados/', ajax_views.dados_precalculo, name='ajax_dados_precalculo'),
    path("ajax/roteiros-por-item/", ajax_views.ajax_roteiros_por_item, name="ajax_roteiros_por_item"),
    path("ajax/dados-cliente/", ajax_views.dados_cliente_ajax, name="dados_cliente_ajax"),

    # Relatorios 
    path("cotacoes/precalculo/<int:pk>/visualizar/", precalc_views.visualizar_precalculo, name="visualizar_precalculo"),
    path("cotacoes/precalculo/<int:pk>/precificacao/", precalc_views.precificacao_produto, name="precificacao_produto"),
    path("cotacao/<int:cotacao_id>/gerar_proposta/", precalc_views.gerar_proposta_view, name="gerar_proposta"),
    path("cotacoes/precalculo/<int:pk>/duplicar/", precalc_views.duplicar_precaculo, name="duplicar_precalculo"),
    path("comercial/precalculo/<int:pk>/roteiros/", precalc_views.opcoes_roteiro_precalculo, name="opcoes_roteiro_precalculo"),

    path("clientes/importar/", cliente_views.importar_clientes_excel, name="importar_clientes_excel"),
    path("itens/importar/", item_views.importar_itens_excel, name="importar_itens_excel"),

    # Ordens de Desenvolvimento
    path("ordens-desenvolvimento/", ordem_desenvolvimento_views.lista_ordens_desenvolvimento, name="lista_ordens_desenvolvimento"),
    path("ordens-desenvolvimento/cadastrar/", ordem_desenvolvimento_views.cadastrar_ordem_desenvolvimento, name="cadastrar_ordem_desenvolvimento"),
    path("ordens-desenvolvimento/editar/<int:pk>/", ordem_desenvolvimento_views.editar_ordem_desenvolvimento, name="editar_ordem_desenvolvimento"),
    path("ordens-desenvolvimento/visualizar/<int:pk>/", ordem_desenvolvimento_views.visualizar_ordem_desenvolvimento, name="visualizar_ordem_desenvolvimento"),
    path("ordens-desenvolvimento/excluir/<int:pk>/", ordem_desenvolvimento_views.excluir_ordem_desenvolvimento, name="excluir_ordem_desenvolvimento"),
    
    # Viabilidade / Análise de Risco
    path("viabilidades/", viabilidade_views.lista_viabilidades, name="lista_viabilidades"),
    path("viabilidades/cadastrar/", viabilidade_views.cadastrar_viabilidade, name="cadastrar_viabilidade"),
    path("viabilidades/editar/<int:pk>/", viabilidade_views.editar_viabilidade, name="editar_viabilidade"),
    path("viabilidades/visualizar/<int:pk>/", viabilidade_views.visualizar_viabilidade, name="visualizar_viabilidade"),
    path("viabilidades/excluir/<int:pk>/", viabilidade_views.excluir_viabilidade, name="excluir_viabilidade"),

    # Indicadores
    path("indicadores/1.1-indice-faturamento/", indicadores_views.indicador_indice_faturamento, name="indicador_indice_faturamento"),
    path("indicadores/1.1.1-faturamento-mensal/", indicadores_views.indicador_faturamento, name="indicador_faturamento_mensal"),

    path("indicadores/4.1-prazo-cotacao/", indicadores_views.indicador_prazo_cotacao, name="indicador_prazo_cotacao"),
    path("indicadores/4.2-itens-novos/", indicadores_views.indicador_itens_novos, name="indicador_itens_novos"),
    path("indicadores/4.3-cotacoes-funcionario/", indicadores_views.indicador_cotacoes_funcionario, name="indicador_cotacoes_funcionario"),
    path("indicadores/4.4-taxa-aprovacao/", indicadores_views.indicador_taxa_aprovacao, name="indicador_taxa_aprovacao"),


    path("dashboard/mapa-clientes/", dashboard_views.mapa_clientes_por_regiao, name="mapa_clientes"),
    path("dashboard/cidades-clientes/", dashboard_views.listar_cidades_clientes, name="listar_cidades_clientes"),
    # Dashboard de Faturamento
    path('dashboard/faturamento/',dashboard_views.dashboard_faturamento, name='dashboard_faturamento'  ),
    path("dashboard/cidades-nomes/", dashboard_views.listar_cidades_nomes, name="listar_cidades_nomes"),
    path("api/getVendas", api_views.get_vendas, name="api_get_vendas"),
    path("api/getNotasFiscais", api_views.get_notas_fiscais, name="api_get_notas_fiscais"),
    path("faturamento/", faturamento_views.lista_faturamento, name="lista_faturamento"),
    path("faturamento/sync/", faturamento_views.sync_faturamento, name="sync_faturamento"),
    path("faturamento/sync-notas/", faturamento_views.sync_faturamento_notas, name="sync_faturamento_notas"),
    path("faturamento/novo/", faturamento_views.criar_faturamento, name="criar_faturamento"),
    path("faturamento/<int:pk>/editar/", faturamento_views.editar_faturamento, name="editar_faturamento"),
    path("faturamento/<int:pk>/excluir/", faturamento_views.excluir_faturamento, name="excluir_faturamento"),
    path("faturamento/relatorio/", faturamento_views.relatorio_faturamento, name="relatorio_faturamento"),
    path("faturamento/relatorio-duplicatas/", faturamento_views.relatorio_duplicatas, name="relatorio_duplicatas"),
        path('dashboard/precalculo/tempo-real/', 
            dashboard_views.acompanhamento_precalculo, 
            name='acompanhamento_precalculo'),

        # AJAX: carregar pré-cálculos de uma cotação
        path('dashboard/precalculo/ajax/precalculos/<int:cotacao_id>/',
            dashboard_views.ajax_precalculos_por_cotacao,
            name='ajax_precalculos_por_cotacao'),

        # AJAX: status por etapa (fluxo)
        path('dashboard/precalculo/ajax/status/<int:pk>/',
            dashboard_views.ajax_status_precalculo,
            name='ajax_status_precalculo'),
    
        path("ajax/valores-forma-calculo/", ferramenta_views.ajax_valores_forma_calculo, name="ajax_valores_forma_calculo"),


     # Metas de Faturamento (CRUD)
    path("metas/", metas_views.lista_metas, name="lista_metas"),
    path("metas/cadastrar/", metas_views.cadastrar_meta, name="cadastrar_meta"),
    path("metas/editar/<int:pk>/", metas_views.editar_meta, name="editar_meta"),
    path("metas/excluir/<int:pk>/", metas_views.excluir_meta, name="excluir_meta"),
]
