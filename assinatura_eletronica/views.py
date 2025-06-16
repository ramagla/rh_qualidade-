from django.http import JsonResponse, Http404
from django.shortcuts import render
from .models import AssinaturaEletronica

def validar_assinatura(request, hash_assinatura):
    try:
        assinatura = AssinaturaEletronica.objects.get(hash=hash_assinatura)
    except AssinaturaEletronica.DoesNotExist:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({"valido": False})
        raise Http404("Assinatura não encontrada")

    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            "valido": True,
            "usuario": assinatura.usuario.username,
            "data_assinatura": assinatura.data_assinatura.isoformat(),
            "origem": f"{assinatura.origem_model} #{assinatura.origem_id}",
            "hash": assinatura.hash
        })

    return render(request, 'validar.html', {'assinatura': assinatura})


