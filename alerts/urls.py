from django.urls import path
from alerts.views import alertas_configurados


app_name = "alerts"

urlpatterns = [
    path("gerenciar/", alertas_configurados.gerenciar_alertas, name="gerenciar_alertas"),
    path("gerenciar/<int:alerta_id>/editar/", alertas_configurados.editar_alerta_configurado, name="editar_alerta_configurado"),
]
