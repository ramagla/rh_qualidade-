from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from .views import acesso_negado,alertas_emails,feriados,logs,permissoes_acesso






urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', include('Funcionario.urls')),  # Inclui as URLs da sua aplicação
    path('metrologia/', include('metrologia.urls')),  # Inclui as URLs do app Metrologia
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path('acesso_negado/', acesso_negado, name='acesso_negado'),
    path('permissoes-acesso/', permissoes_acesso, name='permissoes_acesso'),
    path('logs/', logs, name='logs'),
    path('alertas-email/', alertas_emails, name='alertas_emails'),
    path('feriados/', feriados, name='feriados'),






] 
