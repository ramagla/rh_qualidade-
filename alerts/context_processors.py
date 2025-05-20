from alerts.models import AlertaUsuario

def alertas_do_usuario(request):
    if not request.user.is_authenticated:
        return {}

    alertas = AlertaUsuario.objects.filter(usuario=request.user, lido=False, excluido=False).order_by("-criado_em")
    return {
        "ultimos_alertas": alertas[:10],
        "alertas_nao_lidos": alertas.count(),
    }
