from django.urls import path
from tecnico.views.home import home_tecnico
from tecnico.views import indicadores_views, maquina_views
from tecnico.views import roteiros_views

app_name = "tecnico"  # ✅ ESSA LINHA É FUNDAMENTAL

urlpatterns = [
    path("", home_tecnico, name="tecnico_home"),  

    path("maquinas/", maquina_views.lista_maquinas, name="tecnico_maquinas"),
    path("maquinas/cadastrar/", maquina_views.cadastrar_maquina, name="tecnico_cadastrar_maquina"),
    path("maquinas/<int:pk>/editar/", maquina_views.editar_maquina, name="tecnico_editar_maquina"),
    path("maquinas/<int:pk>/excluir/", maquina_views.excluir_maquina, name="tecnico_excluir_maquina"),

    path("roteiros/", roteiros_views.lista_roteiros, name="tecnico_roteiros"),
    path("roteiros/<int:pk>/visualizar/", roteiros_views.visualizar_roteiro, name="tecnico_visualizar_roteiro"),
    path("roteiros/<int:pk>/excluir/", roteiros_views.excluir_roteiro, name="tecnico_excluir_roteiro"),
    path("roteiros/cadastrar/", roteiros_views.cadastrar_roteiro, name="tecnico_cadastrar_roteiro"),
    path("roteiros/<int:pk>/editar/", roteiros_views.editar_roteiro, name="tecnico_editar_roteiro"),
    path('roteiros/aprovar/', roteiros_views.aprovar_roteiros_lote, name='aprovar_roteiros_lote'),
    path("servicos/", maquina_views.ajax_listar_servicos, name="ajax_listar_servicos"),
    path("servicos/<int:pk>/editar/", maquina_views.ajax_editar_servico, name="ajax_editar_servico"),
    path("servicos/<int:pk>/excluir/", maquina_views.ajax_excluir_servico, name="ajax_excluir_servico"),
    path("servicos/adicionar/", maquina_views.ajax_adicionar_servico, name="ajax_adicionar_servico"),
    path("roteiros/clonar/<int:pk>/", roteiros_views.clonar_roteiro, name="clonar_roteiro"),
    path("roteiros/importar/", roteiros_views.importar_roteiros_excel, name="importar_roteiros_excel"),
    path("indicadores/5.1-prazo-desenvolvimento/",indicadores_views.indicador_51_prazo_desenvolvimento, name="indicador_51_prazo_desenvolvimento",
),

]
