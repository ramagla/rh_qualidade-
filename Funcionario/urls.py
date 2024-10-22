from django.urls import path
from . import views
from .views import sucesso_view


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

]
