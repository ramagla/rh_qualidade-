from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views



urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', include('Funcionario.urls')),  # Inclui as URLs da sua aplicação
    path('metrologia/', include('metrologia.urls')),  # Inclui as URLs do app Metrologia
    path("ckeditor5/", include("django_ckeditor_5.urls")),

] 
