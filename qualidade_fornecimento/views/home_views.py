from datetime import datetime, date, timedelta
from django.shortcuts import render
from django.utils import timezone
from qualidade_fornecimento.models.f045 import RelatorioF045
from qualidade_fornecimento.models.inspecao_servico_externo import InspecaoServicoExterno
from qualidade_fornecimento.models.controle_servico_externo import ControleServicoExterno
from qualidade_fornecimento.models.materiaPrima import RelacaoMateriaPrima
from qualidade_fornecimento.utils import gerar_grafico_velocimetro

def dashboard_qualidade_view(request):
    total_f045 = RelatorioF045.objects.count()
    total_servico = ControleServicoExterno.objects.count()
    total_f045_assinados = RelatorioF045.objects.filter(data_assinatura__isnull=False).count()

    # Dados semestrais
    ano_atual = datetime.today().year
    semestre = 1 if datetime.today().month <= 6 else 2
    inicio = date(ano_atual, 1, 1) if semestre == 1 else date(ano_atual, 7, 1)
    fim = date(ano_atual, 6, 30) if semestre == 1 else date(ano_atual, 12, 31)

    dados_mp = RelacaoMateriaPrima.objects.filter(data_entrada__range=[inicio, fim])
    reprovados = dados_mp.filter(status__in=["Reprovado", "Aprovado Condicionalmente"]).count()
    atrasos = [d.atraso_em_dias for d in dados_mp if d.atraso_em_dias is not None]
    total = max(1, dados_mp.count())

    iqf = round((1 - (reprovados / total)) * 100, 1)
    ip = round((1 - (sum(atrasos) / len(atrasos) / 100)) * 100, 1) if atrasos else 100

    # Simulação de IQG apenas para gráfico
    pontuacao_simulada = 90 / 100
    iqf_pond = (iqf / 100) * 0.5
    ip_pond = (ip / 100) * 0.3
    iqs = pontuacao_simulada * 0.2
    iqg_medio = round((iqf_pond + ip_pond + iqs) * 100, 1)

    # 🔽 FILTROS RÁPIDOS
    periodo = request.GET.get("periodo")
    status = request.GET.get("status")

    relatorios = RelatorioF045.objects.all()

    if periodo:
        try:
            dias = int(periodo)
            data_limite = timezone.now() - timedelta(days=dias)
            relatorios = relatorios.filter(assinado_em__gte=data_limite)
        except ValueError:
            pass

    if status:
        relatorios = relatorios.filter(status_geral=status)

    ultimos_relatorios = relatorios.order_by("-id")[:50]

    ultimas_inspecoes = (
        InspecaoServicoExterno.objects.select_related("servico", "servico__fornecedor")
        .order_by("-id")[:10]
    )

    grafico_velocimetro = gerar_grafico_velocimetro(iqg_medio)

    return render(request, "qualidade_fornecimento/home.html", {
        "kpi_f045_total": total_f045,
        "kpi_servico_total": total_servico,
        "kpi_f045_assinados": total_f045_assinados,
        "kpi_iqg": iqg_medio,
        "kpi_iqf": iqf,
        "kpi_ip": ip,
        "grafico_velocimetro": grafico_velocimetro,
        "ultimos_relatorios": ultimos_relatorios,
        "ultimas_inspecoes": ultimas_inspecoes,
    })
