from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from . import views
from .views import sucesso_view,cadastrar_treinamento,lista_treinamentos, gerar_pdf


urlpatterns = [
    path('home/', views.home, name='home'),
    path('funcionarios/', views.lista_funcionarios, name='lista_funcionarios'),
    path('funcionarios/cadastrar/', views.cadastrar_funcionario, name='cadastrar_funcionario'),
    path('funcionarios/editar/<int:funcionario_id>/', views.editar_funcionario, name='editar_funcionario'),
    path('funcionarios/excluir/<int:funcionario_id>/', views.excluir_funcionario, name='excluir_funcionario'),
    path('funcionarios/<int:funcionario_id>/cargos/', views.buscar_cargos, name='buscar_cargos'),
    path('cargos/', views.lista_cargos, name='lista_cargos'),
    path('cargos/cadastrar/', views.cadastrar_cargo, name='cadastrar_cargo'),
    path('cargos/<int:cargo_id>/revisoes/', views.historico_revisoes, name='historico_revisoes'),
    path('cargos/<int:cargo_id>/revisoes/adicionar/', views.adicionar_revisao, name='adicionar_revisao'),
    path('sucesso/', sucesso_view, name='url_sucesso'),
    path('cargos/editar/<int:cargo_id>/', views.editar_cargo, name='editar_cargo'),
    path('treinamentos/', lista_treinamentos, name='lista_treinamentos'),
    path('cadastrar-treinamento/', cadastrar_treinamento, name='cadastrar_treinamento'),
    path('treinamentos/editar/<int:id>/', views.editar_treinamento, name='editar_treinamento'),
    path('treinamentos/excluir/<int:id>/', views.excluir_treinamento, name='excluir_treinamento'),
    path('treinamentos/imprimir_f003/<int:funcionario_id>/', views.imprimir_f003, name='imprimir_f003'),
    path('gerar_relatorio_f003/', views.gerar_relatorio_f003, name='gerar_relatorio_f003'), 
    path('relatorio/<int:funcionario_id>/pdf/', gerar_pdf, name='gerar_pdf'),   

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)