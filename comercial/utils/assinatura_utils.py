from django.utils import timezone


def preencher_assinatura(request, instancia):
    instancia.usuario = request.user
    instancia.assinatura_nome = request.user.get_full_name() or request.user.username
    instancia.assinatura_cn = request.user.email
    instancia.data_assinatura = timezone.now()
