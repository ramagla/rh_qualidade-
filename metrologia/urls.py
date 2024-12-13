from django.urls import path
from .views.home_views import home
from . import views
from .views import calibracoes_views, relatorios_views, configuracoes_views

from .views.tabelatecnica_views import (
    lista_tabelatecnica,
    cadastrar_tabelatecnica,
    editar_tabelatecnica,
    excluir_tabelatecnica,
    visualizar_tabelatecnica,
    imprimir_tabelatecnica
)



urlpatterns = [
    path('', home, name='metrologia_home'),
   

    path('tabelatecnica/', lista_tabelatecnica, name='lista_tabelatecnica'),
    path('tabelatecnica/cadastrar/', cadastrar_tabelatecnica, name='cadastrar_tabelatecnica'),
    path('tabelatecnica/<int:id>/editar/', editar_tabelatecnica, name='editar_tabelatecnica'),
    path('tabelatecnica/<int:id>/excluir/', excluir_tabelatecnica, name='excluir_tabelatecnica'),
    path('tabelatecnica/<int:id>/', visualizar_tabelatecnica, name='visualizar_tabelatecnica'),
    path('tabelatecnica/imprimir/', imprimir_tabelatecnica, name='imprimir_tabelatecnica'),






    path('calibracoes/', calibracoes_views.metrologia_calibracoes, name='metrologia_calibracoes'),
    path('relatorios/', relatorios_views.metrologia_relatorios, name='metrologia_relatorios'),
    path('configuracoes/', configuracoes_views.metrologia_configuracoes, name='metrologia_configuracoes'),
    
]
