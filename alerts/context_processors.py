from alerts.models import AlertaUsuario

def alertas_do_usuario(request):
    if not request.user.is_authenticated:
        return {}
    qs = AlertaUsuario.objects.filter(usuario=request.user, lido=False, excluido=False).order_by("-criado_em")
    alertas_modal = qs.filter(exige_confirmacao=True)[:5]
    return {
        "ultimos_alertas": qs[:10],
        "alertas_nao_lidos": qs.count(),
        "alertas_modal": alertas_modal,  # NOVO
    }

