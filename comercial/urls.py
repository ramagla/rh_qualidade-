from django.urls import path
from comercial.views import centro_custo_views, cliente_views, ferramenta_views
from comercial.views import item_views
from comercial.views import dashboard_views

urlpatterns = [
    # Dashboard
    path('dashboard/', dashboard_views.dashboard_comercial, name='comercial_home'),

    # Clientes
    path("clientes/", cliente_views.lista_clientes, name="lista_clientes"),
    path("clientes/cadastrar/", cliente_views.cadastrar_cliente, name="cadastrar_cliente"),
    path("clientes/editar/<int:pk>/", cliente_views.editar_cliente, name="editar_cliente"),
    path("clientes/visualizar/<int:pk>/", cliente_views.visualizar_cliente, name="visualizar_cliente"),
    path("clientes/excluir/<int:pk>/", cliente_views.excluir_cliente, name="excluir_cliente"),

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
    path("ajax/valor_hora_centro_custo/", ferramenta_views.ajax_valor_hora_centro_custo, name="ajax_valor_hora_centro_custo"),


    # Centro de Custo
    path("centros-custo/", centro_custo_views.lista_centros_custo, name="lista_centros_custo"),
    path("centros-custo/cadastrar/", centro_custo_views.cadastrar_centro_custo, name="cadastrar_centro_custo"),
    path("centros-custo/editar/<int:pk>/", centro_custo_views.editar_centro_custo, name="editar_centro_custo"),
    path("centros-custo/visualizar/<int:pk>/", centro_custo_views.visualizar_centro_custo, name="visualizar_centro_custo"),


]
