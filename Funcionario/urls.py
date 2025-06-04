from datetime import date

from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import get_object_or_404, render
from django.urls import path
from Funcionario.views import banco_horas_views
from Funcionario.views.funcionario_views import gerar_mensagem_acesso,gerar_mensagem_acesso_redirect, selecionar_funcionario_mensagem_acesso



from Funcionario import views
from Funcionario.models import Cargo, Funcionario
from Funcionario.views.avaliacao_anual_views import (
    cadastrar_avaliacao_anual,
    cadastrar_type_avaliacao,
    editar_avaliacao_anual,
    excluir_avaliacao_anual,
    imprimir_avaliacao,
    imprimir_simplificado,
    lista_avaliacao_anual,
    visualizar_avaliacao_anual,
)
from Funcionario.views.avaliacao_experiencia_views import (
    cadastrar_avaliacao_experiencia,
    editar_avaliacao_experiencia,
    excluir_avaliacao_experiencia,
    imprimir_avaliacao_experiencia,
    lista_avaliacao_experiencia,
    visualizar_avaliacao_experiencia,
)

from .views.api_views import (
    funcionario_api,
    get_cargo,
    get_competencias,
    get_funcionario_ficha,
    get_funcionario_info,
    get_treinamentos,
    get_treinamentos_por_funcionario,
)
from .views.avaliacao_treinamentos_views import (
    cadastrar_avaliacao,
    editar_avaliacao,
    excluir_avaliacao,
    get_treinamentos_por_funcionario,
    imprimir_treinamento,
    lista_avaliacoes,
    visualizar_avaliacao,
)
from .views.cargos_views import (
    cadastrar_cargo,
    editar_cargo,
    excluir_cargo,
    historico_revisoes,
    imprimir_cargo,
    lista_cargos,
    organograma_cargos
)
from .views.comunicados_views import (
    cadastrar_comunicado,
    editar_comunicado,
    excluir_comunicado,
    imprimir_assinaturas,
    imprimir_comunicado,
    lista_comunicados,
    visualizar_comunicado,
)

from .views.formularios_views import (
    FormularioCartaCompetenciaView,
    FormularioPesquisaConscienciaView,
    avaliacao_capacitacao,  
    formulario_f033,
    formulario_saida_antecipada,
    filtro_funcionario_generico
)
from .views.funcionario_views import (
    ImprimirFichaView,
    adicionar_historico_cargo,
    cadastrar_funcionario,
    editar_funcionario,
    excluir_funcionario,
    excluir_historico_cargo,
    lista_funcionarios,
    listar_historico_cargo,
    organograma_view,
    visualizar_funcionario,
    imprimir_organograma
)

# Import das views organizadas por funcionalidade
from .views.home_views import (
    adicionar_evento,
    calendario_view,
    editar_evento,
    eventos_json,
    excluir_evento,
    exportar_calendario,
    home,
    imprimir_calendario,
    marcar_alertas_como_lidos,
)
from .views.integracao_views import (
    cadastrar_integracao,
    editar_integracao,
    excluir_integracao,
    imprimir_integracao,
    lista_integracoes,
    visualizar_integracao,
)
from .views.job_rotation_views import (
    cadastrar_jobrotation_evaluation,
    editar_jobrotation_evaluation,
    excluir_jobrotation,
    imprimir_jobrotation_evaluation,
    lista_jobrotation_evaluation,
    visualizar_jobrotation_evaluation,
)
from .views.lista_presenca_views import (
    cadastrar_lista_presenca,
    editar_lista_presenca,
    excluir_lista_presenca,
    exportar_listas_presenca,
    imprimir_lista_presenca,
    lista_presenca,
    visualizar_lista_presenca,
)
from .views.matriz_polivalencia_views import (
    cadastrar_atividade,
    cadastrar_matriz_polivalencia,
    editar_atividade,
    editar_matriz_polivalencia,
    excluir_atividade,
    excluir_matriz_polivalencia,
    gerenciar_notas,
    get_atividades_e_funcionarios_por_departamento,
    get_atividades_por_departamento,
    imprimir_matriz,
    lista_atividades,
    lista_matriz_polivalencia,
    importar_atividades
)
from .views.relatorios_views import (
    RelatorioIndicadorAnualView,
    RelatorioPlanilhaTreinamentosView,
    cronograma_avaliacao_eficacia,
    cronograma_treinamentos,
    relatorio_aniversariantes,
    relatorio_banco_horas
)
from .views.treinamento_views import (
    cadastrar_treinamento,
    editar_treinamento,
    excluir_treinamento,
    exportar_treinamentos_csv,
    gerar_pdf,
    gerar_relatorio_f003,
    imprimir_f003,
    levantamento_treinamento,
    lista_treinamentos,
    visualizar_treinamento,
)

# Definição das `urlpatterns`
urlpatterns = [
    # Home
    path("", home, name="funcionarios_home"),
    path("", home, name="home"),
    path("home/", home, name="home"),
    path("marcar_lidos/", marcar_alertas_como_lidos, name="marcar_alertas_como_lidos"),
    path("banco-horas/", banco_horas_views.listar_banco_horas, name="listar_banco_horas"),
    path("banco-horas/cadastrar/", banco_horas_views.cadastrar_banco_horas, name="cadastrar_banco_horas"),
    path("banco-horas/editar/<int:pk>/", banco_horas_views.editar_banco_horas, name="editar_banco_horas"),    
    path("banco-horas/visualizar/<int:pk>/", banco_horas_views.visualizar_banco_horas, name="visualizar_banco_horas"),
    path("banco-horas/excluir/<int:pk>/", banco_horas_views.excluir_banco_horas, name="excluir_banco_horas"),
    path("banco-horas/ocorrencias/<int:funcionario_id>/", banco_horas_views.buscar_ocorrencias_portaria, name="buscar_ocorrencias_portaria"),
    path("relatorios/banco-horas/", relatorio_banco_horas, name="relatorio_banco_horas"),
    path("atividades/importar/", importar_atividades, name="importar_atividades"),
    path('funcionario/<int:funcionario_id>/gerar_mensagem_acesso/', gerar_mensagem_acesso, name='gerar_mensagem_acesso'),
    path('gerar_mensagem_acesso/', selecionar_funcionario_mensagem_acesso, name='selecionar_funcionario_mensagem_acesso'),
    path('gerar_mensagem_acesso_redirect/', gerar_mensagem_acesso_redirect, name='gerar_mensagem_acesso_redirect'),
    path('funcionario/<int:funcionario_id>/gerar_mensagem_acesso/', gerar_mensagem_acesso, name='gerar_mensagem_acesso'),

    # Funcionários
    path("funcionarios/", lista_funcionarios, name="lista_funcionarios"),
    path(
        "funcionarios/<int:funcionario_id>/",
        visualizar_funcionario,
        name="visualizar_funcionario",
    ),
    path("formularios/filtro-generico/", filtro_funcionario_generico, name="filtro_funcionario_generico"),

    path("saida-antecipada/<int:funcionario_id>/", formulario_saida_antecipada, name="formulario_saida_antecipada"),

    path(
        "funcionarios/cadastrar/", cadastrar_funcionario, name="cadastrar_funcionario"
    ),
    path(
        "funcionarios/editar/<int:funcionario_id>/",
        editar_funcionario,
        name="editar_funcionario",
    ),
    path(
        "funcionarios/excluir/<int:funcionario_id>/",
        excluir_funcionario,
        name="excluir_funcionario",
    ),
    # Imprimir ficha
    path("imprimir-ficha/", ImprimirFichaView.as_view(), name="imprimir_ficha"),
    path(
        "imprimir-ficha/<int:funcionario_id>/",
        ImprimirFichaView.as_view(),
        name="imprimir_ficha",
    ),
    # Cargos
    path("cargos/", lista_cargos, name="lista_cargos"),
    path("cargos/cadastrar/", cadastrar_cargo, name="cadastrar_cargo"),
    path("cargos/<int:cargo_id>/editar/", editar_cargo, name="editar_cargo"),
    path("cargos/<int:cargo_id>/excluir/", excluir_cargo, name="excluir_cargo"),
    path(
        "cargos/<int:cargo_id>/historico-revisoes/",
        historico_revisoes,
        name="historico_revisoes",
    ),
    path(
        "revisoes/<int:revisao_id>/excluir/",
        views.excluir_revisao,
        name="excluir_revisao",
    ),
    path(
        "cargos/<int:cargo_id>/adicionar-revisao/",
        views.adicionar_revisao,
        name="adicionar_revisao",
    ),
    path("imprimir_cargo/<int:cargo_id>/", imprimir_cargo, name="imprimir_cargo"),
    # Treinamentos
    path("treinamentos/", lista_treinamentos, name="lista_treinamentos"),
    path("cadastrar-treinamento/", cadastrar_treinamento, name="cadastrar_treinamento"),
    path(
        "treinamentos/editar/<int:id>/", editar_treinamento, name="editar_treinamento"
    ),
    path("excluir/<int:id>/", excluir_treinamento, name="excluir_treinamento"),
    path(
        "treinamentos/imprimir_f003/<int:funcionario_id>/",
        imprimir_f003,
        name="imprimir_f003",
    ),
    path("gerar_relatorio_f003/", gerar_relatorio_f003, name="gerar_relatorio_f003"),
    path("relatorio/<int:funcionario_id>/pdf/", gerar_pdf, name="gerar_pdf"),
    path(
        "treinamentos/<int:treinamento_id>/visualizar/",
        visualizar_treinamento,
        name="visualizar_treinamento",
    ),
    path(
        "exportar-treinamentos/",
        exportar_treinamentos_csv,
        name="exportar_treinamentos",
    ),
    # Avaliação de Treinamentos
    path("avaliacoes/", lista_avaliacoes, name="lista_avaliacoes"),
    path("avaliacoes/cadastrar/", cadastrar_avaliacao, name="avaliacao_create"),
    path("avaliacoes/editar/<int:id>/", editar_avaliacao, name="editar_avaliacao"),
    path("avaliacoes/excluir/<int:id>/", excluir_avaliacao, name="excluir_avaliacao"),
    path(
        "avaliacoes/<int:id>/visualizar/",
        visualizar_avaliacao,
        name="visualizar_avaliacao",
    ),
    path(
        "get-treinamentos-funcionarios/<int:funcionario_id>/",
        get_treinamentos_por_funcionario,
        name="get_treinamentos_por_funcionario",
    ),
    path(
        "imprimir_treinamento/<int:treinamento_id>/",
        imprimir_treinamento,
        name="imprimir_treinamento",
    ),
    path(
        "levantamento-treinamento/",
        levantamento_treinamento,
        name="levantamento_treinamento",
    ),
    # Avaliação de Desempenho Anual
    path("avaliacoes-anual/", lista_avaliacao_anual, name="lista_avaliacao_anual"),
    path(
        "avaliacoes-anual/<int:id>/",
        visualizar_avaliacao_anual,
        name="visualizar_avaliacao_anual",
    ),
    path(
        "avaliacoes-anual/cadastrar/",
        cadastrar_avaliacao_anual,
        name="cadastrar_avaliacao_anual",
    ),
    path(
        "avaliacoes-anual/editar/<int:id>/",
        editar_avaliacao_anual,
        name="editar_avaliacao_anual",
    ),
    path(
        "avaliacoes-anual/excluir/<int:id>/",
        excluir_avaliacao_anual,
        name="excluir_avaliacao_anual",
    ),
    path(
        "avaliacoes-anual/imprimir/<int:avaliacao_id>/",
        imprimir_avaliacao,
        name="imprimir_avaliacao_anual",
    ),
    path(
        "avaliacoes-anual/imprimir-simplificado/<int:avaliacao_id>/",
        imprimir_simplificado,
        name="imprimir_simplificado",
    ),
    # Avaliação de Desempenho de Experiência
    path(
        "avaliacoes-experiencia/",
        lista_avaliacao_experiencia,
        name="lista_avaliacao_experiencia",
    ),
    path(
        "avaliacoes-experiencia/cadastrar/",
        cadastrar_avaliacao_experiencia,
        name="cadastrar_avaliacao_experiencia",
    ),
    path(
        "avaliacoes-experiencia/editar/<int:id>/",
        editar_avaliacao_experiencia,
        name="editar_avaliacao_experiencia",
    ),
    path(
        "avaliacoes-experiencia/excluir/<int:id>/",
        excluir_avaliacao_experiencia,
        name="excluir_avaliacao_experiencia",
    ),
    path(
        "avaliacoes-experiencia/<int:id>/",
        visualizar_avaliacao_experiencia,
        name="visualizar_avaliacao_experiencia",
    ),
    path(
        "avaliacao_experiencia/imprimir/<int:avaliacao_id>/",
        imprimir_avaliacao_experiencia,
        name="imprimir_avaliacao_experiencia",
    ),
    # Job Rotation
    path(
        "jobrotation/",
        lista_jobrotation_evaluation,
        name="lista_jobrotation_evaluation",
    ),
    path(
        "jobrotation/cadastrar/",
        cadastrar_jobrotation_evaluation,
        name="cadastrar_jobrotation_evaluation",
    ),
    path(
        "jobrotation/<int:id>/",
        visualizar_jobrotation_evaluation,
        name="visualizar_jobrotation_evaluation",
    ),
    path(
        "jobrotation/editar/<int:id>/",
        editar_jobrotation_evaluation,
        name="editar_jobrotation_evaluation",
    ),
    path(
        "jobrotation/<int:id>/excluir/", excluir_jobrotation, name="excluir_jobrotation"
    ),
    path(
        "jobrotation/imprimir/<int:id>/",
        imprimir_jobrotation_evaluation,
        name="imprimir_jobrotation_evaluation",
    ),
    # APIs auxiliares
    path(
        "get_funcionario_info/<int:id>/",
        get_funcionario_info,
        name="get_funcionario_info",
    ),
    path(
        "get-treinamentos/<int:funcionario_id>/",
        get_treinamentos,
        name="get_treinamentos",
    ),
    path(
        "get-treinamentos-funcionarios/<int:funcionario_id>/",
        get_treinamentos_por_funcionario,
        name="get_treinamentos_por_funcionario",
    ),
    path("api/competencias/", get_competencias, name="get_competencias"),
    path("get-cargo/<int:funcionario_id>/", get_cargo, name="get_cargo"),
    path(
        "api/funcionario/ficha/<int:id>/",
        get_funcionario_ficha,
        name="funcionario-ficha",
    ),
    # Lista de Presença
    path("lista-presenca/", lista_presenca, name="lista_presenca"),
    path(
        "lista-presenca/cadastrar/",
        cadastrar_lista_presenca,
        name="cadastrar_lista_presenca",
    ),
    path(
        "lista-presenca/editar/<int:id>/",
        editar_lista_presenca,
        name="editar_lista_presenca",
    ),
    path(
        "lista-presenca/excluir/<int:id>/",
        excluir_lista_presenca,
        name="excluir_lista_presenca",
    ),
    path(
        "listas-presenca/<int:lista_id>/visualizar/",
        visualizar_lista_presenca,
        name="visualizar_lista_presenca",
    ),
    path(
        "lista-presenca/imprimir/<int:lista_id>/",
        imprimir_lista_presenca,
        name="imprimir_lista_presenca",
    ),
    path(
        "lista-presenca/exportar/",
        exportar_listas_presenca,
        name="exportar_listas_presenca",
    ),
    # Comunicados
    path("comunicados/", lista_comunicados, name="lista_comunicados"),
    path("comunicados/cadastrar/", cadastrar_comunicado, name="cadastrar_comunicado"),
    path("comunicados/<int:id>/", visualizar_comunicado, name="visualizar_comunicado"),
    path("comunicados/editar/<int:id>/", editar_comunicado, name="editar_comunicado"),
    path(
        "comunicados/excluir/<int:id>/", excluir_comunicado, name="excluir_comunicado"
    ),
    path(
        "comunicados/imprimir/<int:id>/",
        imprimir_comunicado,
        name="imprimir_comunicado",
    ),
    path(
        "comunicados/imprimir_assinaturas/<int:id>/",
        imprimir_assinaturas,
        name="imprimir_assinaturas",
    ),
    # Integração de Funcionários
    path("integracao/", lista_integracoes, name="lista_integracoes"),
    path("integracao/cadastrar/", cadastrar_integracao, name="cadastrar_integracao"),
    path(
        "integracao/<int:integracao_id>/",
        visualizar_integracao,
        name="visualizar_integracao",
    ),
    path(
        "integracao/editar/<int:integracao_id>/",
        editar_integracao,
        name="editar_integracao",
    ),  # Adicione esta linha
    path(
        "integracao/imprimir/<int:integracao_id>/",
        imprimir_integracao,
        name="imprimir_integracao",
    ),
    path(
        "integracao/excluir/<int:integracao_id>/",
        excluir_integracao,
        name="excluir_integracao",
    ),
    # Calendario
    path("calendario/", calendario_view, name="calendario"),
    path("calendario/adicionar/", adicionar_evento, name="adicionar_evento"),
    path("calendario/editar/<int:evento_id>/", editar_evento, name="editar_evento"),
    path("calendario/excluir/<int:evento_id>/", excluir_evento, name="excluir_evento"),
    path("exportar_calendario/", exportar_calendario, name="exportar_calendario"),
    path("imprimir_calendario/", imprimir_calendario, name="imprimir_calendario"),
    path("calendario/eventos_json/", eventos_json, name="eventos_json"),
    # Matriz de Polivalência
    path("matriz/", lista_matriz_polivalencia, name="lista_matriz_polivalencia"),
    path(
        "matriz/cadastrar/",
        cadastrar_matriz_polivalencia,
        name="cadastrar_matriz_polivalencia",
    ),
    path(
        "matriz/<int:id>/editar/",
        editar_matriz_polivalencia,
        name="editar_matriz_polivalencia",
    ),
    path(
        "matriz/<int:id>/excluir/",
        excluir_matriz_polivalencia,
        name="excluir_matriz_polivalencia",
    ),
    path("matriz/<int:id>/notas/", gerenciar_notas, name="gerenciar_notas"),
    path("matriz/<int:id>/imprimir/", imprimir_matriz, name="imprimir_matriz"),
    # Atividades
    path("atividades/", lista_atividades, name="lista_atividades"),
    path("atividades/cadastrar/", cadastrar_atividade, name="cadastrar_atividade"),
    path("atividades/<int:id>/editar/", editar_atividade, name="editar_atividade"),
    path("atividades/<int:id>/excluir/", excluir_atividade, name="excluir_atividade"),
    # APIs para AJAX
    path(
        "get-atividades-por-departamento/",
        get_atividades_por_departamento,
        name="get_atividades_por_departamento",
    ),
    path(
        "get-atividades-e-funcionarios-por-departamento/",
        get_atividades_e_funcionarios_por_departamento,
        name="get_atividades_e_funcionarios_por_departamento",
    ),
    path(
        "api/funcionario/<int:funcionario_id>/", funcionario_api, name="funcionario_api"
    ),
    # Relatorios
    path(
        "relatorios/indicador_anual/",
        RelatorioIndicadorAnualView.as_view(),
        name="relatorio_indicador_anual",
    ),
    path(
        "relatorios/planilha-treinamentos/",
        RelatorioPlanilhaTreinamentosView.as_view(),
        name="relatorio_planilha_treinamentos",
    ),
    path(
        "relatorios/indicador/",
        RelatorioPlanilhaTreinamentosView.as_view(
            template_name="relatorios/indicador.html"
        ),
        name="relatorio_indicador",
    ),
    path(
        "relatorios/horas-treinamento/",
        RelatorioPlanilhaTreinamentosView.as_view(
            template_name="relatorios/relatorio_horas_treinamento.html"
        ),
        name="relatorio_horas_treinamento",
    ),
    path(
        "cronograma-treinamentos/",
        cronograma_treinamentos,
        name="cronograma_treinamentos",
    ),
    path(
        "cronograma-avaliacao-eficacia/",
        cronograma_avaliacao_eficacia,
        name="cronograma_avaliacao_eficacia",
    ),
    # Formularios    
    path(
    "formularios/solicitacao-bolsa/<int:funcionario_id>/",
    formulario_f033,
    name="formulario_f033",
    ),

    path(
        "formularios/avaliacao-capacitacao-pratica/carta/<int:funcionario_id>/",
        avaliacao_capacitacao,
        name="carta_avaliacao_capacitacao",
    ),
    path(
        "formularios/pesquisa-consciencia/",
        FormularioPesquisaConscienciaView.as_view(),
        name="formulario_pesquisa_consciencia",
    ),
    path(
        "formularios/carta-competencia/<int:funcionario_id>/",
        FormularioCartaCompetenciaView.as_view(),
        name="formulario_carta_competencia",
    ),
   
    path("organograma/", organograma_view, name="organograma"),
    path(
        "historico-cargo/<int:funcionario_id>/",
        listar_historico_cargo,
        name="listar_historico_cargo",
    ),
    path(
        "historico-cargo/<int:funcionario_id>/adicionar/",
        adicionar_historico_cargo,
        name="adicionar_historico_cargo",
    ),
    path(
        "historico-cargo/<int:historico_id>/excluir/",
        excluir_historico_cargo,
        name="excluir_historico_cargo",
    ),
    path("avaliacao-anual/", cadastrar_type_avaliacao, name="cadastrar_type_avaliacao"),
    path('funcionarios/imprimir-organograma/', imprimir_organograma, name='imprimir_organograma'),
    path("cargos/organograma/", organograma_cargos, name="organograma_cargos"),
    path('relatorios/aniversariantes/', relatorio_aniversariantes, name='relatorio_aniversariantes'),

]

# Adiciona URLs para servir arquivos de mídia durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
