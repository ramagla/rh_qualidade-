from datetime import timedelta
import calendar
from dateutil.relativedelta import relativedelta

from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.shortcuts import render
from django.utils.timezone import now

from metrologia.models.models_dispositivos import Dispositivo
from metrologia.models.models_tabelatecnica import TabelaTecnica


def _eom(d):
    return d.replace(day=calendar.monthrange(d.year, d.month)[1])


@login_required
@permission_required("metrologia.acesso_metrologia", raise_exception=True)
def home(request):
    today = now().date()
    start_month = today.replace(day=1)
    end_month = _eom(today)

    # -------- Filtros (offcanvas) --------
    status_filtro = request.GET.get("status")  # ativo/inativo/todos
    janela = request.GET.get("janela")         # 30/60/90 dias

    qs_base = TabelaTecnica.objects.all()

    if status_filtro in {"ativo", "inativo"}:
        qs_base = qs_base.filter(status=status_filtro)
    else:
        qs_base = qs_base.filter(status="ativo")  # padrão

    dias_alerta = int(janela) if (janela and janela.isdigit()) else 30

    # -------- Cálculo de próxima calibração e coleção para alerta --------
    candidatos = []
    total_ativos = 0
    vencidos = 0
    proximos = 0
    calibrados_mes = 0

    for eq in qs_base:
        # total ativos (após filtro)
        total_ativos += 1

        # calibrado este mês
        if eq.data_ultima_calibracao and start_month <= eq.data_ultima_calibracao <= end_month:
            calibrados_mes += 1

        # próxima calibração por regra do fim do mês
        if eq.data_ultima_calibracao and eq.frequencia_calibracao:
            prox = _eom(eq.data_ultima_calibracao + relativedelta(months=eq.frequencia_calibracao))
            eq.proxima_calibracao = prox

            if prox < today:
                vencidos += 1
            elif today <= prox <= today + timedelta(days=dias_alerta):
                proximos += 1
                candidatos.append(eq)

    # Ordena alertas (próximos dentro da janela)
    alertas_calibracao = sorted(candidatos, key=lambda x: x.proxima_calibracao)[:10]

    # Itens recentes
    equipamentos_recente = TabelaTecnica.objects.order_by("-updated_at")[:5]
    dispositivos_recente = Dispositivo.objects.order_by("-updated_at")[:5]

    context = {
        "nome_modulo": "Metrologia",
        "icone_modulo": "bi-rulers",

        # KPIs
        "kpi_total_ativos": total_ativos,
        "kpi_vencidos": vencidos,
        "kpi_proximos": proximos,
        "kpi_calibrados_mes": calibrados_mes,

        # Listas
        "alertas_calibracao": alertas_calibracao,
        "equipamentos_recente": equipamentos_recente,
        "dispositivos_recente": dispositivos_recente,

        # Suporte a template
        "today": today,
        "start_month": start_month,
        "end_month": end_month,

        # Echo filtros
        "status_filtro": status_filtro or "ativo",
        "dias_alerta": dias_alerta,
    }
    return render(request, "metrologia/home.html", context)
