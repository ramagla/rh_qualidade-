from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import get_object_or_404, render

from Funcionario.views import banco_horas_views, funcionario_views
from Funcionario.views import organograma_views 
from Funcionario.views import avaliacao_anual_views
from Funcionario.views import avaliacao_experiencia_views
from Funcionario.views import avaliacao_treinamentos_views
from Funcionario.views import cargos_views
from Funcionario.views import comunicados_views
from Funcionario.views import formularios_views
from Funcionario.views import home_views
from Funcionario.views import integracao_views
from Funcionario.views import job_rotation_views
from Funcionario.views import lista_presenca_views
from Funcionario.views import matriz_views
from Funcionario.views import atividade_views
from Funcionario.views import relatorios_views
from Funcionario.views import treinamento_views
from Funcionario.views import api_views
from Funcionario.views import funcionario_views as funcionario_utils_views


# Definição das `urlpatterns`
urlpatterns = [
    path("", home_views.home, name="funcionarios_home"),
    path("home/", home_views.home, name="home"),
    path("marcar_lidos/", home_views.marcar_alertas_como_lidos, name="marcar_alertas_como_lidos"),
    path("api/treinamentos-cargo/<int:cargo_id>/", cargos_views.obter_treinamentos_por_cargo, name="obter_treinamentos_por_cargo"),

    path("banco-horas/", banco_horas_views.listar_banco_horas, name="listar_banco_horas"),
    path("banco-horas/cadastrar/", banco_horas_views.cadastrar_banco_horas, name="cadastrar_banco_horas"),
    path("banco-horas/editar/<int:pk>/", banco_horas_views.editar_banco_horas, name="editar_banco_horas"),
    path("banco-horas/visualizar/<int:pk>/", banco_horas_views.visualizar_banco_horas, name="visualizar_banco_horas"),
    path("banco-horas/excluir/<int:pk>/", banco_horas_views.excluir_banco_horas, name="excluir_banco_horas"),
    path("banco-horas/ocorrencias/<int:funcionario_id>/", banco_horas_views.buscar_ocorrencias_portaria, name="buscar_ocorrencias_portaria"),

    path("funcionarios/", funcionario_views.lista_funcionarios, name="lista_funcionarios"),
    path("funcionarios/cadastrar/", funcionario_views.cadastrar_funcionario, name="cadastrar_funcionario"),
    path("funcionarios/editar/<int:funcionario_id>/", funcionario_views.editar_funcionario, name="editar_funcionario"),
    path("funcionarios/<int:funcionario_id>/", funcionario_views.visualizar_funcionario, name="visualizar_funcionario"),
    path("funcionarios/excluir/<int:funcionario_id>/", funcionario_views.excluir_funcionario, name="excluir_funcionario"),
    path("funcionarios/imprimir-organograma/", organograma_views.imprimir_organograma, name="imprimir_organograma"),
    path("organograma/", organograma_views.organograma_view, name="organograma"),
    path("historico-cargo/<int:funcionario_id>/", funcionario_views.listar_historico_cargo, name="listar_historico_cargo"),
    path("historico-cargo/<int:funcionario_id>/adicionar/", funcionario_views.adicionar_historico_cargo, name="adicionar_historico_cargo"),
    path("historico-cargo/<int:historico_id>/excluir/", funcionario_views.excluir_historico_cargo, name="excluir_historico_cargo"),

    path("imprimir-ficha/", funcionario_views.ImprimirFichaView.as_view(), name="imprimir_ficha"),
    path("imprimir-ficha/<int:funcionario_id>/", funcionario_views.ImprimirFichaView.as_view(), name="imprimir_ficha"),

    path("cargos/", cargos_views.lista_cargos, name="lista_cargos"),
    path("cargos/cadastrar/", cargos_views.cadastrar_cargo, name="cadastrar_cargo"),
    path("cargos/editar/<int:cargo_id>/", cargos_views.editar_cargo, name="editar_cargo"),
    path("cargos/excluir/<int:cargo_id>/", cargos_views.excluir_cargo, name="excluir_cargo"),
    path("cargos/<int:cargo_id>/historico-revisoes/", cargos_views.historico_revisoes, name="historico_revisoes"),
    path("cargos/<int:cargo_id>/adicionar-revisao/", cargos_views.adicionar_revisao, name="adicionar_revisao"),
    path("revisoes/<int:revisao_id>/excluir/", cargos_views.excluir_revisao, name="excluir_revisao"),
    path("cargos/organograma/", cargos_views.organograma_cargos, name="organograma_cargos"),
    path("imprimir_cargo/<int:cargo_id>/", cargos_views.imprimir_cargo, name="imprimir_cargo"),

    path("treinamentos/", treinamento_views.lista_treinamentos, name="lista_treinamentos"),
    path("treinamentos/cadastrar/", treinamento_views.cadastrar_treinamento, name="cadastrar_treinamento"),
    path("treinamentos/editar/<int:id>/", treinamento_views.editar_treinamento, name="editar_treinamento"),
    path("treinamentos/excluir/<int:id>/", treinamento_views.excluir_treinamento, name="excluir_treinamento"),
    path("treinamentos/imprimir_f003/<int:funcionario_id>/", treinamento_views.imprimir_f003, name="imprimir_f003"),
    path("treinamentos/exportar/", treinamento_views.exportar_treinamentos_csv, name="exportar_treinamentos"),
    path("treinamentos/<int:treinamento_id>/visualizar/", treinamento_views.visualizar_treinamento, name="visualizar_treinamento"),
    path("treinamentos/relatorio-f003/", treinamento_views.gerar_relatorio_f003, name="gerar_relatorio_f003"),
    path("treinamentos/relatorio/<int:funcionario_id>/pdf/", treinamento_views.gerar_pdf, name="gerar_pdf"),
    path("treinamentos/levantamento/", treinamento_views.levantamento_treinamento, name="levantamento_treinamento"),

    path("avaliacoes/", avaliacao_treinamentos_views.lista_avaliacoes, name="lista_avaliacoes"),
    path("avaliacoes/cadastrar/", avaliacao_treinamentos_views.cadastrar_avaliacao, name="avaliacao_create"),
    path("avaliacoes/editar/<int:id>/", avaliacao_treinamentos_views.editar_avaliacao, name="editar_avaliacao"),
    path("avaliacoes/excluir/<int:id>/", avaliacao_treinamentos_views.excluir_avaliacao, name="excluir_avaliacao"),
    path("avaliacoes/<int:id>/", avaliacao_treinamentos_views.visualizar_avaliacao, name="visualizar_avaliacao"),
    path("avaliacoes/imprimir/<int:treinamento_id>/", avaliacao_treinamentos_views.imprimir_treinamento, name="imprimir_treinamento"),
    path("avaliacoes/get-treinamentos/<int:funcionario_id>/", avaliacao_treinamentos_views.get_treinamentos_por_funcionario, name="get_treinamentos_por_funcionario"),

    path("avaliacoes-anual/", avaliacao_anual_views.lista_avaliacao_anual, name="lista_avaliacao_anual"),
    path("avaliacoes-anual/cadastrar/", avaliacao_anual_views.cadastrar_avaliacao_anual, name="cadastrar_avaliacao_anual"),
    path("avaliacoes-anual/type/", avaliacao_anual_views.cadastrar_type_avaliacao, name="cadastrar_type_avaliacao"),
    path("avaliacoes-anual/editar/<int:id>/", avaliacao_anual_views.editar_avaliacao_anual, name="editar_avaliacao_anual"),
    path("avaliacoes-anual/excluir/<int:id>/", avaliacao_anual_views.excluir_avaliacao_anual, name="excluir_avaliacao_anual"),
    path("avaliacoes-anual/<int:id>/", avaliacao_anual_views.visualizar_avaliacao_anual, name="visualizar_avaliacao_anual"),
    path("avaliacoes-anual/imprimir/<int:avaliacao_id>/", avaliacao_anual_views.imprimir_avaliacao, name="imprimir_avaliacao_anual"),
    path("avaliacoes-anual/imprimir-simplificado/<int:avaliacao_id>/", avaliacao_anual_views.imprimir_simplificado, name="imprimir_simplificado"),

    path("avaliacoes-experiencia/", avaliacao_experiencia_views.lista_avaliacao_experiencia, name="lista_avaliacao_experiencia"),
    path("avaliacoes-experiencia/cadastrar/", avaliacao_experiencia_views.cadastrar_avaliacao_experiencia, name="cadastrar_avaliacao_experiencia"),
    path("avaliacoes-experiencia/editar/<int:id>/", avaliacao_experiencia_views.editar_avaliacao_experiencia, name="editar_avaliacao_experiencia"),
    path("avaliacoes-experiencia/excluir/<int:id>/", avaliacao_experiencia_views.excluir_avaliacao_experiencia, name="excluir_avaliacao_experiencia"),
    path("avaliacoes-experiencia/<int:id>/", avaliacao_experiencia_views.visualizar_avaliacao_experiencia, name="visualizar_avaliacao_experiencia"),
    path("avaliacoes-experiencia/imprimir/<int:avaliacao_id>/", avaliacao_experiencia_views.imprimir_avaliacao_experiencia, name="imprimir_avaliacao_experiencia"),

    path("comunicados/", comunicados_views.lista_comunicados, name="lista_comunicados"),
    path("comunicados/cadastrar/", comunicados_views.cadastrar_comunicado, name="cadastrar_comunicado"),
    path("comunicados/visualizar/<int:id>/", comunicados_views.visualizar_comunicado, name="visualizar_comunicado"),
    path("comunicados/editar/<int:id>/", comunicados_views.editar_comunicado, name="editar_comunicado"),
    path("comunicados/excluir/<int:id>/", comunicados_views.excluir_comunicado, name="excluir_comunicado"),
    path("comunicados/imprimir/<int:id>/", comunicados_views.imprimir_comunicado, name="imprimir_comunicado"),
    path("comunicados/imprimir_assinaturas/<int:id>/", comunicados_views.imprimir_assinaturas, name="imprimir_assinaturas"),

    path("integracao/", integracao_views.lista_integracoes, name="lista_integracoes"),
    path("integracao/cadastrar/", integracao_views.cadastrar_integracao, name="cadastrar_integracao"),
    path("integracao/visualizar/<int:integracao_id>/", integracao_views.visualizar_integracao, name="visualizar_integracao"),
    path("integracao/editar/<int:integracao_id>/", integracao_views.editar_integracao, name="editar_integracao"),
    path("integracao/excluir/<int:integracao_id>/", integracao_views.excluir_integracao, name="excluir_integracao"),
    path("integracao/imprimir/<int:integracao_id>/", integracao_views.imprimir_integracao, name="imprimir_integracao"),

    # APIs auxiliares
    path("api/funcionario/<int:funcionario_id>/", api_views.funcionario_api, name="funcionario_api"),
    path("api/get-cargo/<int:funcionario_id>/", api_views.get_cargo, name="get_cargo"),
    path("api/competencias/", api_views.get_competencias, name="get_competencias"),
    path("api/get-ficha/<int:id>/", api_views.get_funcionario_ficha, name="funcionario_ficha"),
    path("api/get-info/<int:id>/", api_views.get_funcionario_info, name="get_funcionario_info"),
    path("api/get-treinamentos/<int:funcionario_id>/", api_views.get_treinamentos, name="get_treinamentos"),
    path("api/get-treinamentos-funcionario/<int:funcionario_id>/", api_views.get_treinamentos_por_funcionario, name="get_treinamentos_por_funcionario"),


    path("lista-presenca/", lista_presenca_views.lista_presenca, name="lista_presenca"),
    path("lista-presenca/cadastrar/", lista_presenca_views.cadastrar_lista_presenca, name="cadastrar_lista_presenca"),
    path("lista-presenca/editar/<int:id>/", lista_presenca_views.editar_lista_presenca, name="editar_lista_presenca"),
    path("lista-presenca/excluir/<int:id>/", lista_presenca_views.excluir_lista_presenca, name="excluir_lista_presenca"),
    path("listas-presenca/<int:lista_id>/visualizar/", lista_presenca_views.visualizar_lista_presenca, name="visualizar_lista_presenca"),
    path("lista-presenca/imprimir/<int:lista_id>/", lista_presenca_views.imprimir_lista_presenca, name="imprimir_lista_presenca"),
    path("lista-presenca/exportar/", lista_presenca_views.exportar_listas_presenca, name="exportar_listas_presenca"),

    path("calendario/", home_views.calendario_view, name="calendario"),
    path("calendario/adicionar/", home_views.adicionar_evento, name="adicionar_evento"),
    path("calendario/editar/<int:evento_id>/", home_views.editar_evento, name="editar_evento"),
    path("calendario/excluir/<int:evento_id>/", home_views.excluir_evento, name="excluir_evento"),
    path("calendario/eventos_json/", home_views.eventos_json, name="eventos_json"),
    path("exportar_calendario/", home_views.exportar_calendario, name="exportar_calendario"),
    path("imprimir_calendario/", home_views.imprimir_calendario, name="imprimir_calendario"),
    path("cipa/imprimir/", home_views.imprimir_cipa_view, name="imprimir_cipa"),
    path("brigada/imprimir/", home_views.imprimir_brigada_view, name="imprimir_brigada"),

    # Job Rotation
    path("jobrotation/", job_rotation_views.lista_jobrotation_evaluation, name="lista_jobrotation_evaluation"),
    path("jobrotation/cadastrar/", job_rotation_views.cadastrar_jobrotation_evaluation, name="cadastrar_jobrotation_evaluation"),
    path("jobrotation/<int:id>/", job_rotation_views.visualizar_jobrotation_evaluation, name="visualizar_jobrotation_evaluation"),
    path("jobrotation/editar/<int:id>/", job_rotation_views.editar_jobrotation_evaluation, name="editar_jobrotation_evaluation"),
    path("jobrotation/<int:id>/excluir/", job_rotation_views.excluir_jobrotation, name="excluir_jobrotation"),
    path("jobrotation/imprimir/<int:id>/", job_rotation_views.imprimir_jobrotation_evaluation, name="imprimir_jobrotation_evaluation"),
    
    
    # Matriz de Polivalência
    path("matriz/", matriz_views.lista_matriz_polivalencia, name="lista_matriz_polivalencia"),
    path("matriz/cadastrar/", matriz_views.cadastrar_matriz_polivalencia, name="cadastrar_matriz_polivalencia"),
    path("matriz/editar/<int:id>/", matriz_views.editar_matriz_polivalencia, name="editar_matriz_polivalencia"),
    path("matriz/excluir/<int:id>/", matriz_views.excluir_matriz_polivalencia, name="excluir_matriz_polivalencia"),
    path("matriz/<int:id>/imprimir/", matriz_views.imprimir_matriz, name="imprimir_matriz"),


    # ATIVIDADES DA MATRIZ
    path("atividades/", atividade_views.lista_atividades, name="lista_atividades"),
    path("atividades/cadastrar/", atividade_views.cadastrar_atividade, name="cadastrar_atividade"),
    path("atividades/editar/<int:id>/", atividade_views.editar_atividade, name="editar_atividade"),
    path("atividades/excluir/<int:id>/", atividade_views.excluir_atividade, name="excluir_atividade"),
    path("atividades/<int:id>/", atividade_views.visualizar_atividade, name="visualizar_atividade"),
    path("atividades/<int:id>/notas/", atividade_views.gerenciar_notas, name="gerenciar_notas"),
    path("atividades/importar/", atividade_views.importar_atividades, name="importar_atividades"),
    path("atividades/get-por-departamento/", atividade_views.get_atividades_por_departamento, name="get_atividades_por_departamento"),
    path("atividades/get-atividades-e-funcionarios/", atividade_views.get_atividades_e_funcionarios_por_departamento, name="get_atividades_e_funcionarios_por_departamento"),

    path("relatorios/indicador_anual/", relatorios_views.RelatorioIndicadorAnualView.as_view(), name="relatorio_indicador_anual"),
    path("relatorios/planilha-treinamentos/", relatorios_views.RelatorioPlanilhaTreinamentosView.as_view(), name="relatorio_planilha_treinamentos"),
    path("relatorios/indicador/", relatorios_views.RelatorioPlanilhaTreinamentosView.as_view(template_name="relatorios/indicador.html"), name="relatorio_indicador"),
    path("relatorios/horas-treinamento/", relatorios_views.RelatorioPlanilhaTreinamentosView.as_view(template_name="relatorios/relatorio_horas_treinamento.html"), name="relatorio_horas_treinamento"),
    path("relatorios/aniversariantes/", relatorios_views.relatorio_aniversariantes, name="relatorio_aniversariantes"),
    path("relatorios/banco-horas/", relatorios_views.relatorio_banco_horas, name="relatorio_banco_horas"),

    path("cronograma-treinamentos/", relatorios_views.cronograma_treinamentos, name="cronograma_treinamentos"),
    path("cronograma-avaliacao-eficacia/", relatorios_views.cronograma_avaliacao_eficacia, name="cronograma_avaliacao_eficacia"),

    path("formularios/solicitacao-bolsa/<int:funcionario_id>/", formularios_views.formulario_f033, name="formulario_f033"),
    path("formularios/avaliacao-capacitacao-pratica/carta/<int:funcionario_id>/", formularios_views.avaliacao_capacitacao, name="carta_avaliacao_capacitacao"),
    path("formularios/folha-ponto/<int:funcionario_id>/", formularios_views.formulario_folha_ponto, name="formulario_folha_ponto"),
    path("formularios/pesquisa-consciencia/", formularios_views.FormularioPesquisaConscienciaView.as_view(), name="formulario_pesquisa_consciencia"),
    path("formularios/carta-competencia/<int:funcionario_id>/",formularios_views.FormularioCartaCompetenciaView.as_view(), name="formulario_carta_competencia"),
    path("formularios/saida-antecipada/<int:funcionario_id>/", formularios_views.formulario_saida_antecipada, name="formulario_saida_antecipada"),
    path("funcionarios/filtro-generico/", formularios_views.filtro_funcionario_generico, name="filtro_funcionario_generico"),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)