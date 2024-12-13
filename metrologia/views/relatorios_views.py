from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def metrologia_relatorios(request):
    context = {
        'module': 'Relatórios',
        'content': 'Aqui você encontrará os Relatórios do módulo Metrologia.'
    }
    return render(request, 'metrologia/relatorios.html', context)
