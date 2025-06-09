from django.urls import path
from comercial.views import cliente_views
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
]
