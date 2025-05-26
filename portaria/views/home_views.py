from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from datetime import date
from portaria.models import (
    EntradaVisitante,
    LigacaoPortaria,
    RegistroConsumoAgua,
    OcorrenciaPortaria,
)

@login_required
@permission_required("portaria.acesso_portaria", raise_exception=True)
def portaria_home(request):
    visitantes_ativos = EntradaVisitante.objects.filter(hora_saida__isnull=True, pessoa__tipo="visitante").count()
    entregadores_ativos = EntradaVisitante.objects.filter(hora_saida__isnull=True, pessoa__tipo="entregador").count()
    recados_pendentes = LigacaoPortaria.objects.filter(recado_enviado=False).count()

    consumo_hoje = RegistroConsumoAgua.objects.filter(data=date.today()).first()
    consumo_agua_hoje = (consumo_hoje.leitura_final - consumo_hoje.leitura_inicial) if consumo_hoje else 0

    ultimas_ocorrencias = OcorrenciaPortaria.objects.order_by("-data_inicio", "-hora_inicio")[:5]

    context = {
        "visitantes_ativos": visitantes_ativos,
        "entregadores_ativos": entregadores_ativos,
        "recados_pendentes": recados_pendentes,
        "consumo_agua_hoje": consumo_agua_hoje,
        "ultimas_ocorrencias": ultimas_ocorrencias,
    }
    return render(request, "portaria_home.html", context)
