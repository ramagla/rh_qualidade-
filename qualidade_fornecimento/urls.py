from django.urls import path
from .views.home_views import home_qualidade
from .views.fornecedores_views import cadastrar_fornecedor,lista_fornecedores, editar_fornecedor,excluir_fornecedor,visualizar_fornecedor,importar_excel_fornecedores

urlpatterns = [
    path("home/", home_qualidade, name="qualidadefornecimento_home"),
    path("fornecedores/", lista_fornecedores, name="lista_fornecedores"),
    path("fornecedores/cadastrar/", cadastrar_fornecedor, name="cadastrar_fornecedor"),
    path('fornecedores/editar/<int:id>/', editar_fornecedor, name='editar_fornecedor'),
    path('fornecedores/excluir/<int:id>/', excluir_fornecedor, name='excluir_fornecedor'),
    path('fornecedores/visualizar/<int:id>/', visualizar_fornecedor, name='visualizar_fornecedor'),
    path('fornecedores/importar/', importar_excel_fornecedores, name='importar_excel_fornecedores'),




]
