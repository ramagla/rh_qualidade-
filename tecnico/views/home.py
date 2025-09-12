# tecnico/views/home.py — PARA
from datetime import datetime
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count
from django.shortcuts import render

from tecnico.models.roteiro import RoteiroProducao, EtapaRoteiro
from tecnico.models.maquina import Maquina
from comercial.models import CentroDeCusto  # setores

@login_required
@permission_required("tecnico.acesso_tecnico", raise_exception=True)
def home_tecnico(request):
    # --- Filtros (GET) ---
    periodo = request.GET.get("periodo")  # YYYY-MM
    setor_id = request.GET.get("setor")
    status   = request.GET.get("status")  # 'aprovado' | 'pendente' | ''

    qs = RoteiroProducao.objects.select_related("item").all()

    if periodo:
        try:
            ano, mes = map(int, periodo.split("-"))
            qs = qs.filter(atualizado_em__year=ano, atualizado_em__month=mes)
        except Exception:
            pass

    if setor_id:
        qs = qs.filter(etapas__setor_id=setor_id)

    if status == "aprovado":
        qs = qs.filter(aprovado=True)
    elif status == "pendente":
        qs = qs.filter(aprovado=False)

    qs = qs.distinct()

    # --- KPIs ---
    total_roteiros   = qs.count()
    total_aprovados  = qs.filter(aprovado=True).count()
    revisao_alta     = qs.filter(revisao__gt=3).count()
    ultima_obj       = qs.order_by("-atualizado_em").first()
    ultima_data      = ultima_obj.atualizado_em if ultima_obj else None
    total_maquinas   = Maquina.objects.count()
    total_etapas     = EtapaRoteiro.objects.count()
    perc_aprovados   = round((total_aprovados / total_roteiros) * 100, 1) if total_roteiros else 0

    # --- Listas ---
    ultimos_roteiros = list(qs.order_by("-atualizado_em")[:10])

    # Top setores por etapas (com percentual p/ barra)
    base_setores = (
        EtapaRoteiro.objects.filter(roteiro__in=qs)
        .values("setor__nome")
        .annotate(qtd=Count("id"))
        .order_by("-qtd")
    )
    total_top = sum(r["qtd"] for r in base_setores) or 1
    top_setores = [
        {"setor__nome": r["setor__nome"], "qtd": r["qtd"], "pct": round((r["qtd"] / total_top) * 100, 1)}
        for r in base_setores[:5]
    ]

    setores = list(CentroDeCusto.objects.order_by("nome").values("id", "nome"))

    return render(
        request,
        "dasboard_tecnico.html",
        {
            "total_roteiros": total_roteiros,
            "total_aprovados": total_aprovados,
            "revisao_alta": revisao_alta,
            "ultima_data": ultima_data,
            "total_maquinas": total_maquinas,
            "total_etapas": total_etapas,
            "perc_aprovados": perc_aprovados,
            "ultimos_roteiros": ultimos_roteiros,
            "top_setores": top_setores,
            "setores": setores,
        },
    )
