from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from assinatura_eletronica.views import  validar_assinatura

from .views import (
    acesso_negado,
    alertas_emails,
    feriados,
    logs,
    permissoes_acesso,
    home_geral,
    chat_gpt_query,
    copiar_permissoes
)
from .documentos_views import (
    lista_documentos, cadastrar_documento, editar_documento,
    excluir_documento, historico_documentos, adicionar_documento,
    excluir_revisao2, get_ultima_revisao_nao_lida, marcar_revisao_lida
)
from Funcionario.views.home_views import login_view
from rh_qualidade.views import home_geral
from rh_qualidade import atualizacao_views
from rh_qualidade.views import usuarios_ativos

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Home geral do sistema (todos os usuários veem)
    path("", home_geral, name="home_geral"),
    path("portaria/", include("portaria.urls")),

    path(
            "senha/esqueci/",
            auth_views.PasswordResetView.as_view(
                template_name="registration/password_reset_form.html",
                email_template_name="registration/password_reset_email.html",  # texto puro
                html_email_template_name="registration/password_reset_email.html",  # HTML estilizado
            ),
            name="password_reset"
        ),

    path("senha/enviado/", auth_views.PasswordResetDoneView.as_view(
        template_name="registration/password_reset_done.html"), name="password_reset_done"),
    path("senha/nova/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="registration/password_reset_confirm.html"), name="password_reset_confirm"),
    path("senha/finalizado/", auth_views.PasswordResetCompleteView.as_view(
        template_name="registration/password_reset_complete.html"), name="password_reset_complete"),

    # Login e Logout
    path("login/", login_view, name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Módulos por prefixo
    path("metrologia/", include("metrologia.urls")),
    path("qualidade/", include("qualidade_fornecimento.urls")),
    path("rh/", include("Funcionario.urls")),  # Acesso ao RH via /rh/

    # Plugins e ferramentas
    path("ckeditor5/", include("django_ckeditor_5.urls")),

    # Páginas internas
    path("acesso_negado/", acesso_negado, name="acesso_negado"),
    path("permissoes-acesso/", permissoes_acesso, name="permissoes_acesso_lista"),
    path("permissoes/copiar/", copiar_permissoes, name="copiar_permissoes"),

    path("alertas/", include("alerts.urls")),
    path("logs/", logs, name="logs"),
    path("alertas-email/", alertas_emails, name="alertas_emails"),
    path("feriados/", feriados, name="feriados"),

    # Integração com ChatGPT
    path("chat-gpt/", chat_gpt_query, name="chat_gpt_query"),

    #Documentos
    path("documentos/", lista_documentos, name="lista_documentos"),
    path("documentos/cadastrar/", cadastrar_documento, name="cadastrar_documento"),
    path("documentos/<int:documento_id>/editar/", editar_documento, name="editar_documento"),
    path("documentos/<int:documento_id>/excluir/", excluir_documento, name="excluir_documento"),
    path("documentos/<int:documento_id>/historico-documentos/", historico_documentos, name="historico_documentos"),
    path("documentos/<int:documento_id>/adicionar-documento/", adicionar_documento, name="adicionar_documento"),
    path("revisoes2/<int:revisao_id>/excluir/", excluir_revisao2, name="excluir_revisao2"),

    path("ajax/ultima-revisao-nao-lida/", get_ultima_revisao_nao_lida, name="get_ultima_revisao_nao_lida"),
    path("revisoes/marcar_lida/", marcar_revisao_lida, name="marcar_revisao_lida"),

    path("atualizacoes/", atualizacao_views.lista_atualizacoes, name="lista_atualizacoes"),
    path("atualizacoes/cadastrar/", atualizacao_views.cadastrar_atualizacao, name="cadastrar_atualizacao"),
    path("atualizacoes/editar/<int:id>/", atualizacao_views.editar_atualizacao, name="editar_atualizacao"),
    path("atualizacoes/excluir/<int:id>/", atualizacao_views.excluir_atualizacao, name="excluir_atualizacao"),
    path('atualizacoes/marcar_lida/', atualizacao_views.marcar_atualizacao_lida, name='marcar_atualizacao_lida'),
    path("ajax/ultima-atualizacao/", atualizacao_views.get_ultima_atualizacao, name="get_ultima_atualizacao"),
    path('usuarios-ativos/', usuarios_ativos, name='usuarios_ativos'),
    path("comercial/", include("comercial.urls")),
    path("assinatura/validar/<str:hash_assinatura>/", validar_assinatura, name="validar_assinatura"),



]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

