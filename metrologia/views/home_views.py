# metrologia/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    context = {
        'nome_modulo': 'Metrologia',
        'icone_modulo': 'bi-rulers',
    }
    return render(request, 'metrologia/home.html', context)
