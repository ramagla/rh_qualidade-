from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from .views import (
    acesso_negado,
    alertas_emails,
    feriados,
    logs,
    permissoes_acesso,
    home_geral,
    chat_gpt_query,
)

from Funcionario.views.home_views import login_view
from rh_qualidade.views import home_geral

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Home geral do sistema (todos os usuários veem)
    path("", home_geral, name="home_geral"),

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
    path("alertas/", include("alerts.urls")),
    path("logs/", logs, name="logs"),
    path("alertas-email/", alertas_emails, name="alertas_emails"),
    path("feriados/", feriados, name="feriados"),

    # Integração com ChatGPT
    path("chat-gpt/", chat_gpt_query, name="chat_gpt_query"),
]


