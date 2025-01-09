# metrologia/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from django.utils.timezone import now
from metrologia.models.models_tabelatecnica import TabelaTecnica
from metrologia.models.models_dispositivos import Dispositivo
from django.db.models import F, ExpressionWrapper, DateField


@login_required
def home(request):
    today = now().date()

    # Equipamentos com calibração vencida ou próxima do vencimento
    alertas_calibracao = TabelaTecnica.objects.annotate(
        proxima_calibracao=ExpressionWrapper(
            F('data_ultima_calibracao') + timedelta(days=30) * F('frequencia_calibracao'),
            output_field=DateField()
        )
    ).filter(
        proxima_calibracao__lte=today + timedelta(days=30)
    ).order_by('proxima_calibracao')[:10]

    # Equipamentos recentemente alterados
    equipamentos_recente = TabelaTecnica.objects.order_by('-updated_at')[:5]

    # Dispositivos recentemente alterados
    dispositivos_recente = Dispositivo.objects.order_by('-updated_at')[:5]

    context = {
        'nome_modulo': 'Metrologia',
        'icone_modulo': 'bi-rulers',
        'alertas_calibracao': alertas_calibracao,
        'equipamentos_recente': equipamentos_recente,
        'dispositivos_recente': dispositivos_recente,
    }
    return render(request, 'metrologia/home.html', context)