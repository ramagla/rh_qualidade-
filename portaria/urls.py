from django.urls import path
from portaria.views import pessoa_views
from portaria.views import veiculo_views
from portaria.views import controle_visitantes_views
from portaria.views.api_views import api_veiculos_da_pessoa
from .views import atrasos_saidas_views
from portaria.views import ligacao_views
from portaria.views import ocorrencia_views
from portaria.views import consumo_agua_views 
from portaria.views import relatorios_views
from portaria.views.home_views import portaria_home, zona_monitoramento_modal

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
    path("atrasos-saidas/", atrasos_saidas_views.lista_atrasos_saidas, name="lista_atrasos_saidas"),
    path("atrasos-saidas/visualizar/<int:pk>/", atrasos_saidas_views.visualizar_atraso_saida, name="visualizar_atraso_saida"),
    path("atrasos-saidas/cadastrar/", atrasos_saidas_views.cadastrar_atraso_saida, name="cadastrar_atraso_saida"),
    path("atrasos-saidas/editar/<int:pk>/", atrasos_saidas_views.editar_atraso_saida, name="editar_atraso_saida"),
    path("atrasos-saidas/excluir/<int:pk>/", atrasos_saidas_views.excluir_atraso_saida, name="excluir_atraso_saida"),
    path("ligacoes/", ligacao_views.lista_ligacoes, name="lista_ligacoes"),
    path("ligacoes/cadastrar/", ligacao_views.cadastrar_ligacao, name="cadastrar_ligacao"),
    path("ligacoes/editar/<int:pk>/", ligacao_views.editar_ligacao, name="editar_ligacao"),
    path("ligacoes/excluir/<int:pk>/", ligacao_views.excluir_ligacao, name="excluir_ligacao"),
    path("ligacoes/<int:pk>/disparar-recado/", ligacao_views.disparar_recado, name="disparar_recado"),
    path("ocorrencias/", ocorrencia_views.listar_ocorrencias, name="listar_ocorrencias"),
    path("ocorrencias/cadastrar/", ocorrencia_views.cadastrar_ocorrencia, name="cadastrar_ocorrencia"),
    path("ocorrencias/editar/<int:pk>/", ocorrencia_views.editar_ocorrencia, name="editar_ocorrencia"),
    path("ocorrencias/visualizar/<int:pk>/", ocorrencia_views.visualizar_ocorrencia, name="visualizar_ocorrencia"),
    path("ocorrencias/excluir/<int:pk>/", ocorrencia_views.excluir_ocorrencia, name="excluir_ocorrencia"),

    path("controle-consumo-agua/", consumo_agua_views.listar_consumo_agua, name="listar_consumo_agua"),
    path("controle-consumo-agua/cadastrar/", consumo_agua_views.cadastrar_consumo_agua, name="cadastrar_consumo_agua"),
    path("controle-consumo-agua/editar/<int:pk>/", consumo_agua_views.editar_consumo_agua, name="editar_consumo_agua"),
    path("controle-consumo-agua/excluir/<int:pk>/", consumo_agua_views.excluir_consumo_agua, name="excluir_consumo_agua"),
    path("relatorio-visitantes/", relatorios_views.relatorio_visitantes, name="relatorio_visitantes"),
    path("relatorio-atrasos-saidas/", relatorios_views.relatorio_atrasos_saidas, name="relatorio_atrasos_saidas"),
    path("relatorio-ligacoes-recebidas/", relatorios_views.relatorio_ligacoes_recebidas, name="relatorio_ligacoes_recebidas"),
    path("relatorio-ocorrencias/", relatorios_views.relatorio_ocorrencias, name="relatorio_ocorrencias"),
    path("relatorio-consumo-agua/", relatorios_views.relatorio_consumo_agua, name="relatorio_consumo_agua"),
    path("relatorio-horas-extras/", relatorios_views.relatorio_horas_extras, name="relatorio_horas_extras"),
    path("dashboard/", portaria_home, name="portaria_home"),
    path("zona-monitoramento/modal/", zona_monitoramento_modal, name="zona_monitoramento_modal"),


]
