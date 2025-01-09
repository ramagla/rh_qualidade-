from django.urls import path
from .views.home_views import home
from . import views
from .views import calibracoes_views, relatorios_views, configuracoes_views

from django.conf import settings
from django.conf.urls.static import static

from .views.tabelatecnica_views import (
    lista_tabelatecnica,
    cadastrar_tabelatecnica,
    editar_tabelatecnica,
    excluir_tabelatecnica,
    visualizar_tabelatecnica,
    imprimir_tabelatecnica
)

from .views.relatorios_views import listar_equipamentos_funcionario, listar_funcionarios_ativos,equipamentos_por_funcionario

from .views.calibracoes_views import (
    lista_calibracoes,
    cadastrar_calibracao,
    editar_calibracao,
    excluir_calibracao,
    metrologia_calibracoes,
    obter_exatidao_requerida
)

from .views.cronogramas_views import (
    cronograma_equipamentos,
    cronograma_dispositivos
)

from .views.dispositivos_views import (
    lista_dispositivos,
    cadastrar_dispositivo,
    editar_dispositivo,
    excluir_dispositivo,
    visualizar_dispositivo,
    imprimir_dispositivo,
    excluir_movimentacao,
    historico_movimentacoes,
    cadastrar_movimentacao
)

from .views.calibracoes_dispositivos_views import (
    lista_calibracoes_dispositivos,
    cadastrar_calibracao_dispositivo,
    editar_calibracao_dispositivo,
    excluir_calibracao_dispositivo,
    get_dispositivo_info,
    imprimir_calibracao_dispositivo, 
)


urlpatterns = [
    path('', home, name='metrologia_home'),
    path('get_dispositivo_info/<int:dispositivo_id>/', get_dispositivo_info, name='get_dispositivo_info'),


    # URLs de Tabela Técnica
    path('tabelatecnica/', lista_tabelatecnica, name='lista_tabelatecnica'),
    path('tabelatecnica/cadastrar/', cadastrar_tabelatecnica, name='cadastrar_tabelatecnica'),
    path('tabelatecnica/<int:id>/editar/', editar_tabelatecnica, name='editar_tabelatecnica'),
    path('tabelatecnica/<int:id>/excluir/', excluir_tabelatecnica, name='excluir_tabelatecnica'),
    path('tabelatecnica/<int:id>/', visualizar_tabelatecnica, name='visualizar_tabelatecnica'),
    path('tabelatecnica/imprimir/', imprimir_tabelatecnica, name='imprimir_tabelatecnica'),

    # URLs de Calibrações
    path('calibracoes/instrumentos/', lista_calibracoes, name='calibracoes_instrumentos'),
    path('calibracoes/cadastrar/', cadastrar_calibracao, name='cadastrar_calibracao'),
    path('calibracoes/<int:pk>/editar/', editar_calibracao, name='editar_calibracao'),
    path('calibracoes/<int:id>/excluir/', excluir_calibracao, name='excluir_calibracao'),
    path('calibracoes/', metrologia_calibracoes, name='metrologia_calibracoes'),
 
    path('dispositivos/', lista_dispositivos, name='lista_dispositivos'),
    path('dispositivos/cadastrar/', cadastrar_dispositivo, name='cadastrar_dispositivo'),
    path('dispositivos/<int:dispositivo_id>/editar/', editar_dispositivo, name='editar_dispositivo'),
    path('dispositivos/<int:id>/excluir/', excluir_dispositivo, name='excluir_dispositivo'),
    path('dispositivos/<int:id>/', visualizar_dispositivo, name='visualizar_dispositivo'),
    path('dispositivos/imprimir/', imprimir_dispositivo, name='imprimir_dispositivo'),
    path('dispositivos/<int:dispositivo_id>/movimentacoes/', historico_movimentacoes, name='historico_movimentacoes'),
    path('dispositivos/<int:dispositivo_id>/movimentacoes/cadastrar/', cadastrar_movimentacao, name='cadastrar_movimentacao'),
    path('movimentacoes/<int:id>/excluir/', excluir_movimentacao, name='excluir_movimentacao'),

    # URLs de Calibrações de Dispositivos
    path('calibracoes/dispositivos/', lista_calibracoes_dispositivos, name='lista_calibracoes_dispositivos'),
    path('calibracoes/dispositivos/cadastrar/', cadastrar_calibracao_dispositivo, name='cadastrar_calibracao_dispositivo'),
    path('calibracoes/dispositivos/<int:pk>/editar/', editar_calibracao_dispositivo, name='editar_calibracao_dispositivo'),
    path('calibracoes/dispositivos/<int:id>/excluir/', excluir_calibracao_dispositivo, name='excluir_calibracao_dispositivo'),
    path('calibracoes/dispositivos/<int:dispositivo_id>/imprimir/', imprimir_calibracao_dispositivo, name='imprimir_calibracao_dispositivo'),  # Nova URL


    


    # path('calibracoes/dispositivos/', metrologia_calibracoes, name='calibracoes_dispositivos'),

    # URLs de Cronogramas
    path('cronograma/equipamentos/', cronograma_equipamentos, name='cronograma_calibracao'),
    path('cronograma/dispositivos/', cronograma_dispositivos, name='cronograma_dispositivos'),

    # Outras URLs
    path('relatorios/equipamentos-a-calibrar/', relatorios_views.lista_equipamentos_a_calibrar, name='relatorio_equipamentos_calibrar'),
    path('equipamentos/funcionario/<int:funcionario_id>/', listar_equipamentos_funcionario, name='listar_equipamentos_funcionario'),
    path('listar-funcionarios-ativos/', listar_funcionarios_ativos, name='listar_funcionarios_ativos'),
    path('equipamentos-por-funcionario/', equipamentos_por_funcionario, name='equipamentos_por_funcionario'),



    path('configuracoes/', configuracoes_views.metrologia_configuracoes, name='metrologia_configuracoes'),
    path('api/exatidao-requerida/<int:equipamento_id>/', obter_exatidao_requerida, name='obter_exatidao_requerida'),

] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

