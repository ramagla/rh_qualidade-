from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from datetime import datetime
from tecnico.models.roteiro import RoteiroProducao, EtapaRoteiro
from tecnico.models.maquina import Maquina

@login_required
@permission_required("tecnico.acesso_tecnico", raise_exception=True)
def home_tecnico(request):
    total_roteiros = RoteiroProducao.objects.count()
    total_aprovados = RoteiroProducao.objects.filter(aprovado=True).count()
    revisao_alta = RoteiroProducao.objects.filter(revisao__gt=3).count()
    ultima_atualizacao = RoteiroProducao.objects.order_by("-atualizado_em").first()
    total_maquinas = Maquina.objects.count()
    total_etapas = EtapaRoteiro.objects.count()

    return render(request, "dasboard_tecnico.html", {
        "total_roteiros": total_roteiros,
        "total_aprovados": total_aprovados,
        "revisao_alta": revisao_alta,
        "ultima_data": ultima_atualizacao.atualizado_em if ultima_atualizacao else None,
        "total_maquinas": total_maquinas,
        "total_etapas": total_etapas,
    })
