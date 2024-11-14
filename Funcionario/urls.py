from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from Funcionario import views

# Import das views organizadas por funcionalidade
from .views.home_views import home,calendario_view,adicionar_evento,editar_evento,excluir_evento,exportar_calendario,imprimir_calendario
from .views.funcionario_views import (
    lista_funcionarios,
    cadastrar_funcionario,
    editar_funcionario,
    excluir_funcionario,
    visualizar_funcionario,
    ImprimirFichaView,
)
from .views.cargos_views import (
    lista_cargos,
    cadastrar_cargo,
    editar_cargo,
    excluir_cargo,   
    historico_revisoes,
)
from .views.treinamento_views import (
    lista_treinamentos,
    cadastrar_treinamento,
    editar_treinamento,
    excluir_treinamento,
    visualizar_treinamento,
    imprimir_f003,
    gerar_pdf,
    gerar_relatorio_f003,
)

from .views.avaliacao_treinamentos_views import (
    lista_avaliacoes,
    cadastrar_avaliacao,
    editar_avaliacao,
    excluir_avaliacao,    
    get_treinamentos_por_funcionario,
    lista_avaliacoes,
    imprimir_treinamento,
    visualizar_avaliacao
)

from Funcionario.views.avaliacao_anual_views import (
    lista_avaliacao_anual,
    cadastrar_avaliacao_anual,
    editar_avaliacao_anual,
    excluir_avaliacao_anual,
    imprimir_avaliacao,
    visualizar_avaliacao_anual,
    imprimir_simplificado
)
from Funcionario.views.avaliacao_experiencia_views import (
    lista_avaliacao_experiencia,
    cadastrar_avaliacao_experiencia,
    editar_avaliacao_experiencia,
    excluir_avaliacao_experiencia,
    visualizar_avaliacao_experiencia,
    imprimir_avaliacao_experiencia
)

from .views.job_rotation_views import (
    lista_jobrotation_evaluation,
    cadastrar_jobrotation_evaluation,
    visualizar_jobrotation_evaluation,
    editar_jobrotation_evaluation,
    excluir_jobrotation,
    imprimir_jobrotation_evaluation
)
from .views.api_views import get_funcionario_info, get_treinamentos, get_competencias, get_cargo,get_funcionario_ficha

from .views.lista_presenca_views import (
    lista_presenca,
    cadastrar_lista_presenca,
    editar_lista_presenca,
    excluir_lista_presenca,
    visualizar_lista_presenca,
    imprimir_lista_presenca
)

from .views.comunicados_views import (
    lista_comunicados,
    cadastrar_comunicado,
    visualizar_comunicado,
    editar_comunicado,
    excluir_comunicado,
    imprimir_comunicado,
    imprimir_assinaturas
)

from .views.integracao_views import (
    lista_integracoes,
    visualizar_integracao,
    cadastrar_integracao,
    excluir_integracao,
    editar_integracao,
    imprimir_integracao,
)



# Definição das `urlpatterns`
urlpatterns = [
    # Home
    path('', home, name='home'),
    path('home/', home, name='home'),
    
    # Funcionários
    path('funcionarios/', lista_funcionarios, name='lista_funcionarios'),
    path('funcionarios/<int:funcionario_id>/', visualizar_funcionario, name='visualizar_funcionario'),
    path('funcionarios/cadastrar/', cadastrar_funcionario, name='cadastrar_funcionario'),
    path('funcionarios/editar/<int:funcionario_id>/', editar_funcionario, name='editar_funcionario'),
    path('funcionarios/excluir/<int:funcionario_id>/', excluir_funcionario, name='excluir_funcionario'),

    # Imprimir ficha
    path('imprimir-ficha/', ImprimirFichaView.as_view(), name='imprimir_ficha'),
    path('imprimir-ficha/<int:funcionario_id>/', ImprimirFichaView.as_view(), name='imprimir_ficha'),


    
    # Cargos
    path('cargos/', lista_cargos, name='lista_cargos'),
    path('cargos/cadastrar/', cadastrar_cargo, name='cadastrar_cargo'),
    path('cargos/<int:cargo_id>/editar/', editar_cargo, name='editar_cargo'),
    path('cargos/<int:cargo_id>/excluir/', excluir_cargo, name='excluir_cargo'),
    path('cargos/<int:cargo_id>/historico-revisoes/', historico_revisoes, name='historico_revisoes'),
    path('revisoes/<int:revisao_id>/excluir/', views.excluir_revisao, name='excluir_revisao'),
    path('cargos/<int:cargo_id>/adicionar-revisao/', views.adicionar_revisao, name='adicionar_revisao'),

    # Treinamentos
    path('treinamentos/', lista_treinamentos, name='lista_treinamentos'),
    path('cadastrar-treinamento/', cadastrar_treinamento, name='cadastrar_treinamento'),
    path('treinamentos/editar/<int:id>/', editar_treinamento, name='editar_treinamento'),
    path('treinamentos/excluir/<int:id>/', excluir_treinamento, name='excluir_treinamento'),
    path('treinamentos/imprimir_f003/<int:funcionario_id>/', imprimir_f003, name='imprimir_f003'),
    path('gerar_relatorio_f003/', gerar_relatorio_f003, name='gerar_relatorio_f003'),
    path('relatorio/<int:funcionario_id>/pdf/', gerar_pdf, name='gerar_pdf'),
    path('treinamentos/<int:treinamento_id>/visualizar/', visualizar_treinamento, name='visualizar_treinamento'),

    # Avaliação de Treinamentos
    path('avaliacoes/', lista_avaliacoes, name='lista_avaliacoes'),
    path('avaliacoes/cadastrar/', cadastrar_avaliacao, name='avaliacao_create'),
    path('avaliacoes/editar/<int:id>/', editar_avaliacao, name='editar_avaliacao'),
    path('avaliacoes/excluir/<int:id>/', excluir_avaliacao, name='excluir_avaliacao'),
    path('avaliacoes/<int:id>/visualizar/', visualizar_avaliacao, name='visualizar_avaliacao'),
    path('get-treinamentos/<int:funcionario_id>/', get_treinamentos_por_funcionario, name='get_treinamentos_por_funcionario'),
    path('imprimir_treinamento/<int:treinamento_id>/', imprimir_treinamento, name='imprimir_treinamento'),



     # Avaliação de Desempenho Anual
    path('avaliacoes-anual/', lista_avaliacao_anual, name='lista_avaliacao_anual'),
    path('avaliacoes-anual/<int:id>/', visualizar_avaliacao_anual, name='visualizar_avaliacao_anual'),

    path('avaliacoes-anual/cadastrar/', cadastrar_avaliacao_anual, name='cadastrar_avaliacao_anual'),
    path('avaliacoes-anual/editar/<int:id>/', editar_avaliacao_anual, name='editar_avaliacao_anual'),
    path('avaliacoes-anual/excluir/<int:id>/', excluir_avaliacao_anual, name='excluir_avaliacao_anual'),
    path('avaliacoes-anual/imprimir/<int:avaliacao_id>/', imprimir_avaliacao, name='imprimir_avaliacao_anual'),
    path('avaliacoes-anual/imprimir-simplificado/<int:avaliacao_id>/', imprimir_simplificado, name='imprimir_simplificado'),



    # Avaliação de Desempenho de Experiência
    path('avaliacoes-experiencia/', lista_avaliacao_experiencia, name='lista_avaliacao_experiencia'),
    path('avaliacoes-experiencia/cadastrar/', cadastrar_avaliacao_experiencia, name='cadastrar_avaliacao_experiencia'),
    path('avaliacoes-experiencia/editar/<int:id>/', editar_avaliacao_experiencia, name='editar_avaliacao_experiencia'),
    path('avaliacoes-experiencia/excluir/<int:id>/', excluir_avaliacao_experiencia, name='excluir_avaliacao_experiencia'),
    path('avaliacoes-experiencia/<int:id>/', visualizar_avaliacao_experiencia, name='visualizar_avaliacao_experiencia'),
    path('avaliacao_experiencia/imprimir/<int:avaliacao_id>/', imprimir_avaliacao_experiencia, name='imprimir_avaliacao_experiencia'),



    # Job Rotation
    path('jobrotation/', lista_jobrotation_evaluation, name='lista_jobrotation_evaluation'),
    path('jobrotation/cadastrar/', cadastrar_jobrotation_evaluation, name='cadastrar_jobrotation_evaluation'),
    path('jobrotation/<int:id>/', visualizar_jobrotation_evaluation, name='visualizar_jobrotation_evaluation'),
    path('jobrotation/editar/<int:id>/', editar_jobrotation_evaluation, name='editar_jobrotation_evaluation'),
    path('jobrotation/<int:id>/excluir/', excluir_jobrotation, name='excluir_jobrotation'),
    path('jobrotation/imprimir/<int:id>/', imprimir_jobrotation_evaluation, name='imprimir_jobrotation_evaluation'),


    # APIs auxiliares
    path('get_funcionario_info/<int:id>/', get_funcionario_info, name='get_funcionario_info'),
    path('get_treinamentos/<int:funcionario_id>/', get_treinamentos, name='get_treinamentos'),
    path('api/competencias/', get_competencias, name='get_competencias'),
    path('get-cargo/<int:funcionario_id>/', get_cargo, name='get_cargo'),
    path('api/funcionario/ficha/<int:id>/', get_funcionario_ficha, name='funcionario-ficha'),


    # Lista de Presença
    path('lista-presenca/', lista_presenca, name='lista_presenca'),
    path('lista-presenca/cadastrar/', cadastrar_lista_presenca, name='cadastrar_lista_presenca'),
    path('lista-presenca/editar/<int:id>/', editar_lista_presenca, name='editar_lista_presenca'),
    path('lista-presenca/excluir/<int:id>/', excluir_lista_presenca, name='excluir_lista_presenca'),
    path('listas-presenca/<int:lista_id>/visualizar/', visualizar_lista_presenca, name='visualizar_lista_presenca'),
    path('lista-presenca/imprimir/<int:lista_id>/', imprimir_lista_presenca, name='imprimir_lista_presenca'),
  
  # Comunicados       
    path('comunicados/', lista_comunicados, name='lista_comunicados'),
    path('comunicados/cadastrar/', cadastrar_comunicado, name='cadastrar_comunicado'),
    path('comunicados/<int:id>/', visualizar_comunicado, name='visualizar_comunicado'),
    path('comunicados/editar/<int:id>/', editar_comunicado, name='editar_comunicado'),
    path('comunicados/excluir/<int:id>/', excluir_comunicado, name='excluir_comunicado'),
    path('comunicados/imprimir/<int:id>/', imprimir_comunicado, name='imprimir_comunicado'),
    path('comunicados/imprimir_assinaturas/<int:id>/', imprimir_assinaturas, name='imprimir_assinaturas'),


# Integração de Funcionários
    path('integracao/', lista_integracoes, name='lista_integracoes'),
    path('integracao/cadastrar/', cadastrar_integracao, name='cadastrar_integracao'),
    path('integracao/<int:integracao_id>/', visualizar_integracao, name='visualizar_integracao'),
    path('integracao/editar/<int:integracao_id>/', editar_integracao, name='editar_integracao'),  # Adicione esta linha
    path('integracao/imprimir/<int:integracao_id>/', imprimir_integracao, name='imprimir_integracao'),

    path('integracao/excluir/<int:integracao_id>/', excluir_integracao, name='excluir_integracao'),



# Calendario
    path('calendario/', calendario_view, name='calendario'),
    path('calendario/adicionar/', adicionar_evento, name='adicionar_evento'),
    path('calendario/editar/<int:evento_id>/', editar_evento, name='editar_evento'),
    path('calendario/excluir/<int:evento_id>/', excluir_evento, name='excluir_evento'),
    path('exportar_calendario/', exportar_calendario, name='exportar_calendario'),
    path('imprimir_calendario/', imprimir_calendario, name='imprimir_calendario'),



]

# Adiciona URLs para servir arquivos de mídia durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
