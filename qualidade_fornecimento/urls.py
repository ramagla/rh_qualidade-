# qualidade_fornecimento/urls.py
from django.urls import path
from .views.home_views import home_qualidade
from .views.fornecedores_views import (
    cadastrar_fornecedor, lista_fornecedores, editar_fornecedor,
    excluir_fornecedor, visualizar_fornecedor, importar_excel_fornecedores
)
from qualidade_fornecimento.views.materiaprima_views import (
    lista_tb050, cadastrar_tb050, editar_tb050, excluir_tb050,
    visualizar_tb050, importar_excel_tb050,imprimir_etiquetas_tb050,selecionar_etiquetas_tb050,get_rolos_peso,imprimir_etiquetas_pdf
)

from qualidade_fornecimento.views import materiaprima_catalogo_views as mp_views

from qualidade_fornecimento.views import norma_views

from qualidade_fornecimento.views.f045_views import gerar_f045,f045_status
from qualidade_fornecimento.views.f045_pdf import gerar_pdf_f045, visualizar_f045_pdf
from qualidade_fornecimento.views.controle_servico_externo_views import cadastrar_controle_servico_externo, listar_controle_servico_externo, api_leadtime,editar_controle_servico_externo,excluir_controle_servico_externo
from qualidade_fornecimento.views.inspecao_servico_externo_views import cadastrar_inspecao_servico_externo, editar_inspecao_servico_externo,selecionar_servico_para_inspecao,inspecao_status
from qualidade_fornecimento.views.relatorio_avaliacao import relatorio_avaliacao_view

urlpatterns = [
    # Home
    path("home/", home_qualidade, name="qualidadefornecimento_home"),

    # Fornecedores
    path("fornecedores/", lista_fornecedores, name="lista_fornecedores"),
    path("fornecedores/cadastrar/", cadastrar_fornecedor, name="cadastrar_fornecedor"),
    path("fornecedores/editar/<int:id>/", editar_fornecedor, name='editar_fornecedor'),
    path("fornecedores/excluir/<int:id>/", excluir_fornecedor, name='excluir_fornecedor'),
    path("fornecedores/visualizar/<int:id>/", visualizar_fornecedor, name='visualizar_fornecedor'),
    path("fornecedores/importar/", importar_excel_fornecedores, name='importar_excel_fornecedores'),

    # TB050
    path("tb050/", lista_tb050, name="tb050_list"),
    path("tb050/cadastrar/", cadastrar_tb050, name="tb050_cadastrar"),
    path("tb050/<int:id>/editar/", editar_tb050, name="tb050_editar"),
    path("tb050/<int:id>/excluir/", excluir_tb050, name="tb050_excluir"),
    path("tb050/<int:id>/", visualizar_tb050, name="tb050_visualizar"),
    path("tb050/importar/", importar_excel_tb050, name="tb050_importar_excel"),

     path('materia-prima/', mp_views.listar_materia_prima_catalogo, name='materiaprima_catalogo_list'),
    path('materia-prima/cadastrar/', mp_views.cadastrar_materia_prima_catalogo, name='materiaprima_catalogo_create'),
    path('materia-prima/importar/', mp_views.importar_materia_prima_excel, name='materiaprima_importar'),
    path('materia-prima/editar/<int:pk>/', mp_views.editar_materia_prima, name='materiaprima_editar'),
    path('materia-prima/deletar/<int:pk>/', mp_views.deletar_materia_prima, name='materiaprima_deletar'),
     path("tb050/<int:id>/selecionar-etiquetas/", selecionar_etiquetas_tb050, name="tb050_selecionar_etiquetas"),
    path("tb050/<int:id>/imprimir-etiquetas/", imprimir_etiquetas_tb050, name="tb050_imprimir_etiquetas"),
    path('tb050/get-rolos-peso/<int:id>/', get_rolos_peso, name='get_rolos_peso'),
    path("tb050/<int:id>/etiquetas-pdf/", imprimir_etiquetas_pdf, name="tb050_etiquetas_pdf"),

    # Normas de Composição Química
    path("normas/", norma_views.lista_normas, name="lista_normas"),
    path("normas/cadastrar/", norma_views.cadastrar_norma, name="cadastrar_norma"),
    path("normas/editar/<int:id>/", norma_views.editar_norma, name="editar_norma"),
    path("normas/excluir/<int:id>/", norma_views.excluir_norma, name="excluir_norma"),
    path("normas/visualizar/<int:id>/", norma_views.visualizar_norma, name="visualizar_norma"),
    path("normas/get-tipos-abnt/", norma_views.get_tipos_abnt, name="get_tipos_abnt"),

    path("tb050/<int:relacao_id>/f045/", gerar_f045, name="tb050_f045"),

    path("qualidade/tb050/<int:relacao_id>/f045/pdf/", gerar_pdf_f045, name="gerar_pdf_f045"),
    path("tb050/<int:relacao_id>/f045/pdf/preview/", visualizar_f045_pdf, name="visualizar_pdf_f045"),
    path("f045_status/<int:f045_id>/", f045_status, name="f045_status"),
    path('controle-servico-externo/', listar_controle_servico_externo, name='listar_controle_servico_externo'),
    path('controle-servico-externo/cadastrar/', cadastrar_controle_servico_externo, name='cadastrar_controle_servico_externo'),
    path('controle-servico-externo/editar/<int:id>/', editar_controle_servico_externo, name='editar_controle_servico_externo'),  # ✅ NOVA
    path('controle-servico-externo/excluir/<int:id>/', excluir_controle_servico_externo, name='excluir_controle_servico_externo'), # ✅ NOVA

    # urls.py
    path("api/fornecedor/<int:pk>/leadtime/", api_leadtime, name="api_leadtime"),


    path('controle-servico-externo/inspecao/cadastrar/<int:servico_id>/', cadastrar_inspecao_servico_externo, name="cadastrar_inspecao_servico_externo"),
    path('controle-servico-externo/inspecao/editar/<int:id>/', editar_inspecao_servico_externo, name="editar_inspecao_servico_externo"),
    path('controle-servico-externo/inspecao/', selecionar_servico_para_inspecao, name='selecionar_servico_para_inspecao'),
    path('inspecao/status/<int:servico_id>/', inspecao_status, name='inspecao_status'),
    path("relatorio-avaliacao/", relatorio_avaliacao_view, name="relatorio_avaliacao"),




]


