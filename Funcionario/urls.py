from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from . import views
from .views import (
    get_cargo,
    sucesso_view,
    cadastrar_treinamento,
    lista_treinamentos,
    gerar_pdf,
    lista_avaliacoes,    
    cadastrar_avaliacao,
    cadastrar_avaliacao_anual,
    cadastrar_avaliacao_experiencia,
)

urlpatterns = [
    path('home/', views.home, name='home'),
    
    # Funcionários
    path('funcionarios/', views.lista_funcionarios, name='lista_funcionarios'),
    path('funcionarios/cadastrar/', views.cadastrar_funcionario, name='cadastrar_funcionario'),
    path('funcionarios/editar/<int:funcionario_id>/', views.editar_funcionario, name='editar_funcionario'),
    path('funcionarios/excluir/<int:funcionario_id>/', views.excluir_funcionario, name='excluir_funcionario'),
    path('funcionarios/<int:funcionario_id>/cargos/', get_cargo, name='get_cargo'),
    
    # Cargos
    path('cargos/', views.lista_cargos, name='lista_cargos'),
    path('cargos/cadastrar/', views.cadastrar_cargo, name='cadastrar_cargo'),
    path('cargos/<int:cargo_id>/revisoes/', views.historico_revisoes, name='historico_revisoes'),
    path('cargos/<int:cargo_id>/revisoes/adicionar/', views.adicionar_revisao, name='adicionar_revisao'),
    path('cargos/editar/<int:cargo_id>/', views.editar_cargo, name='editar_cargo'),

    # Sucesso
    path('sucesso/', sucesso_view, name='url_sucesso'),

    # Treinamentos
    path('treinamentos/', lista_treinamentos, name='lista_treinamentos'),
    path('cadastrar-treinamento/', cadastrar_treinamento, name='cadastrar_treinamento'),
    path('treinamentos/editar/<int:id>/', views.editar_treinamento, name='editar_treinamento'),
    path('treinamentos/excluir/<int:id>/', views.excluir_treinamento, name='excluir_treinamento'),
    path('treinamentos/imprimir_f003/<int:funcionario_id>/', views.imprimir_f003, name='imprimir_f003'),
    path('gerar_relatorio_f003/', views.gerar_relatorio_f003, name='gerar_relatorio_f003'),
    path('relatorio/<int:funcionario_id>/pdf/', gerar_pdf, name='gerar_pdf'),

    # Lista de Presença
    path('lista-presenca/', views.lista_presenca, name='lista_presenca'),
    path('lista-presenca/cadastrar/', views.cadastrar_lista_presenca, name='cadastrar_lista_presenca'),
    path('lista-presenca/editar/<int:id>/', views.editar_lista_presenca, name='editar_lista_presenca'),
    path('lista-presenca/excluir/<int:id>/', views.excluir_lista_presenca, name='excluir_lista_presenca'),

    # Avaliação de Treinamentos
    path('avaliacoes/', lista_avaliacoes, name='lista_avaliacoes'),
    path('avaliacoes/cadastrar/', views.cadastrar_avaliacao, name='avaliacao_create'),
    path('avaliacoes/editar/<int:id>/', views.editar_avaliacao, name='editar_avaliacao'),
    path('avaliacoes/excluir/<int:id>/', views.excluir_avaliacao, name='excluir_avaliacao'),
    path('get-cargo/<int:funcionario_id>/', views.get_cargo, name='get_cargo'),

    # Avaliação de Desempenho
    path('avaliacoes-desempenho/cadastrar/experiencia/', views.cadastrar_avaliacao_experiencia, name='cadastrar_avaliacao_experiencia'),
    path('avaliacoes-desempenho/cadastrar/anual/', views.cadastrar_avaliacao_anual, name='cadastrar_avaliacao_anual'),
    path('avaliacoes-desempenho/editar/<int:id>/', views.editar_avaliacao_desempenho, name='editar_avaliacao_desempenho'),  # Adicione esta linha
    path('avaliacoes-desempenho/', views.lista_avaliacao_desempenho, name='lista_avaliacao_desempenho'),
    path('avaliacoes-desempenho/excluir/<int:id>/', views.excluir_avaliacao_desempenho, name='excluir_avaliacao_desempenho'),



]
    




if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
