from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from .views import (
    acesso_negado,
    alertas_emails,
    feriados,
    logs,
    permissoes_acesso,
    permissoes_por_grupo,
    chat_gpt_query,  # ➤ Importa a view que você criou
)

from Funcionario.views.home_views import login_view

urlpatterns = [
    path("admin/", admin.site.urls),

    # Login e Logout
    path("login/", login_view, name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Módulos do sistema
    path("", include("Funcionario.urls")),
    path("metrologia/", include("metrologia.urls")),
    path("qualidade/", include("qualidade_fornecimento.urls")),

    path("ckeditor5/", include("django_ckeditor_5.urls")),

    # Páginas internas e permissões
    path("acesso_negado/", acesso_negado, name="acesso_negado"),
    path("permissoes-acesso/", permissoes_acesso, name="permissoes_acesso_lista"),
    path("permissoes-grupo/<int:grupo_id>/", permissoes_por_grupo, name="permissoes_por_grupo"),
    path("permissoes-grupo/", permissoes_por_grupo, name="permissoes_por_grupo_lista"),


    path("alertas/", include("alerts.urls")),
    path("logs/", logs, name="logs"),
    path("alertas-email/", alertas_emails, name="alertas_emails"),
    path("feriados/", feriados, name="feriados"),

    # ➤ Endpoint do ChatGPT (aqui está o que você pediu)
    path("chat-gpt/", chat_gpt_query, name="chat_gpt_query"),
]
