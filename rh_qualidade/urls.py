from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path


from .views import acesso_negado, alertas_emails, feriados, logs, permissoes_acesso

from Funcionario.views.home_views import login_view

urlpatterns = [
    path("admin/", admin.site.urls),

    # Aqui o ajuste!
    path("login/", login_view, name="login"),

    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("Funcionario.urls")),
    path("metrologia/", include("metrologia.urls")),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path("acesso_negado/", acesso_negado, name="acesso_negado"),
    path("permissoes-acesso/<int:usuario_id>/", permissoes_acesso, name="permissoes_acesso"),
    path("permissoes-acesso/", permissoes_acesso, name="permissoes_acesso_lista"),
    path("logs/", logs, name="logs"),
    path("alertas-email/", alertas_emails, name="alertas_emails"),
    path("feriados/", feriados, name="feriados"),
]
