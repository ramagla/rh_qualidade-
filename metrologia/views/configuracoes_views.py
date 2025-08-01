from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def metrologia_configuracoes(request):
    context = {
        "module": "Configurações",
        "content": "Aqui você pode gerenciar as Configurações do módulo Metrologia.",
    }
    return render(request, "metrologia/configuracoes.html", context)
