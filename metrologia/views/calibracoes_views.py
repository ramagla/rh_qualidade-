from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def metrologia_calibracoes(request):
    context = {
        'module': 'Calibrações',
        'content': 'Aqui estão as informações sobre Calibrações.'
    }
    return render(request, 'metrologia/calibracoes.html', context)
