from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.models import User, Group
from alerts.models import AlertaConfigurado

@login_required
@permission_required("alerts.view_alertaconfigurado", raise_exception=True)
def gerenciar_alertas(request):
    alertas = AlertaConfigurado.objects.all()
    return render(request, "alertas/gerenciar_alertas.html", {
        "titulo": "Gerenciar Alertas In-App",
        "alertas": alertas
    })

@login_required
@permission_required("alerts.change_alertaconfigurado", raise_exception=True)
def editar_alerta_configurado(request, alerta_id):
    alerta = get_object_or_404(AlertaConfigurado, id=alerta_id)

    if request.method == "POST":
        usuarios_ids = request.POST.getlist("usuarios")
        grupos_ids = request.POST.getlist("grupos")
        alerta.usuarios.set(usuarios_ids)
        alerta.grupos.set(grupos_ids)
        alerta.ativo = "ativo" in request.POST
        alerta.save()
        return redirect("alerts:gerenciar_alertas")  # ← Aqui está a correção

    usuarios = User.objects.all()
    grupos = Group.objects.all()
    return render(request, "alertas/editar_alerta.html", {
        "alerta": alerta,
        "usuarios": usuarios,
        "grupos": grupos,
    })