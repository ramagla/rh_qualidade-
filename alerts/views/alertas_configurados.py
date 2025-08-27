from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.models import User, Group
from alerts.models import AlertaConfigurado
from alerts.models import AlertaUsuario
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone

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
        alerta.exigir_confirmacao_modal = "exigir_confirmacao_modal" in request.POST  # NOVO
        alerta.observacoes = request.POST.get("observacoes") or ""
        alerta.save()
        return redirect("alerts:gerenciar_alertas")  # ← Aqui está a correção

    usuarios = User.objects.all()
    grupos = Group.objects.all()
    return render(request, "alertas/editar_alerta.html", {
        "alerta": alerta,
        "usuarios": usuarios,
        "grupos": grupos,
    })


@csrf_exempt
@require_POST
@login_required
def confirmar_alerta_usuario(request, alerta_id):
    alerta = get_object_or_404(AlertaUsuario, pk=alerta_id, usuario=request.user, excluido=False)
    alerta.confirmar()
    return JsonResponse({"status": "ok"})

@csrf_exempt
@login_required
def excluir_alerta_usuario(request, alerta_id):
    if request.method == "POST":
        try:
            alerta = AlertaUsuario.objects.get(pk=alerta_id, usuario=request.user)
            alerta.excluido = True
            alerta.save()
            return JsonResponse({"status": "ok"})
        except AlertaUsuario.DoesNotExist:
            return JsonResponse({"status": "erro", "mensagem": "Alerta não encontrado"}, status=404)
    return JsonResponse({"status": "erro", "mensagem": "Método inválido"}, status=405)
