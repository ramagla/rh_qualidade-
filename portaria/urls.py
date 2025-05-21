from django.urls import path
from portaria.views import pessoa_views
from portaria.views import veiculo_views
from portaria.views import controle_visitantes_views
from portaria.views.api_views import api_veiculos_da_pessoa


urlpatterns = [
    path("pessoas/", pessoa_views.lista_pessoas, name="lista_pessoas"),
    path("pessoas/cadastrar/", pessoa_views.cadastrar_pessoa, name="cadastrar_pessoa"),
    path("pessoas/editar/<int:pk>/", pessoa_views.editar_pessoa, name="editar_pessoa"),
    path("pessoas/<int:pk>/visualizar/", pessoa_views.visualizar_pessoa, name="visualizar_pessoa"),
    path("pessoas/<int:pk>/excluir/", pessoa_views.excluir_pessoa, name="excluir_pessoa"),
    path("veiculos/cadastrar/", veiculo_views.cadastrar_veiculo, name="cadastrar_veiculo"),
    path("veiculos/", veiculo_views.lista_veiculos, name="lista_veiculos"),
    path("veiculos/editar/<int:pk>/", veiculo_views.editar_veiculo, name="editar_veiculo"),
    path("veiculos/excluir/<int:pk>/", veiculo_views.excluir_veiculo, name="excluir_veiculo"),
   
    path("controle-visitantes/", controle_visitantes_views.listar_controle_visitantes, name="listar_controle_visitantes"),
    path("controle-visitantes/cadastrar/", controle_visitantes_views.cadastrar_entrada_visitante, name="cadastrar_entrada_visitante"),
    path("controle-visitantes/editar/<int:pk>/", controle_visitantes_views.editar_entrada_visitante, name="editar_entrada_visitante"),
    path("controle-visitantes/visualizar/<int:pk>/", controle_visitantes_views.visualizar_entrada_visitante, name="visualizar_entrada_visitante"),
    path("controle-visitantes/excluir/<int:pk>/", controle_visitantes_views.excluir_entrada_visitante, name="excluir_entrada_visitante"),
    path("api/pessoa/<int:pk>/foto/", controle_visitantes_views.obter_foto_pessoa, name="obter_foto_pessoa"),
    path("api/pessoa/<int:pessoa_id>/veiculos/", api_veiculos_da_pessoa, name="api_veiculos_da_pessoa"),
    path("controle-visitantes/<int:pk>/saida/", controle_visitantes_views.registrar_saida_visitante, name="registrar_saida_visitante"),

]
