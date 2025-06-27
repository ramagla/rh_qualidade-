from datetime import timedelta

from django.db.models import DateField, ExpressionWrapper, F, IntegerField, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now

from Funcionario.models import Funcionario
from metrologia.models.models_tabelatecnica import TabelaTecnica


def lista_equipamentos_a_calibrar(request):
    today = now().date()
    range_end = today + timedelta(days=30)

    # Adiciona a anotação para calcular a próxima calibração com o uso de relativedelta
    tabelas = TabelaTecnica.objects.annotate(
        proxima_calibracao=ExpressionWrapper(
            Coalesce(F("data_ultima_calibracao"), Value(today))
            + ExpressionWrapper(
                Coalesce(
                    F("frequencia_calibracao"), Value(1), output_field=IntegerField()
                )
                * Value(30),
                output_field=DateField(),
            ),
            output_field=DateField(),
        )
    )

    # Equipamentos com calibração vencida
    equipamentos_vencidos = tabelas.filter(proxima_calibracao__lt=today).order_by(
        "proxima_calibracao"
    )

    # Equipamentos próximos do vencimento
    equipamentos_proximos = tabelas.filter(
        proxima_calibracao__gte=today, proxima_calibracao__lte=range_end
    ).order_by("proxima_calibracao")

    context = {
        "equipamentos_vencidos": equipamentos_vencidos,
        "equipamentos_proximos": equipamentos_proximos,
    }
    return render(request, "relatorios/equipamentos_a_calibrar.html", context)


def listar_equipamentos_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)

    if request.method == "POST":
        equipamentos_selecionados = request.POST.getlist("equipamentos_selecionados")
        equipamentos = TabelaTecnica.objects.filter(id__in=equipamentos_selecionados)
    else:
        equipamentos = TabelaTecnica.objects.filter(responsavel=funcionario)

    context = {
        "funcionario": funcionario,
        "equipamentos": equipamentos,
        "data_atual": now().date(),
    }
    return render(request, "relatorios/listar_equipamentos_funcionario.html", context)




def listar_funcionarios_ativos(request):
    funcionarios = Funcionario.objects.filter(status="Ativo").values("id", "nome")
    return JsonResponse(list(funcionarios), safe=False)


def equipamentos_por_funcionario(request):
    funcionario_id = request.GET.get("funcionario_id") or request.POST.get("funcionario_id")
    funcionario = None
    equipamentos = []

    if funcionario_id:
        funcionario = get_object_or_404(Funcionario, id=funcionario_id)
        equipamentos = TabelaTecnica.objects.filter(responsavel=funcionario)

    context = {
        "funcionario": funcionario,
        "equipamentos": equipamentos,
    }
    return render(request, "relatorios/selecionar_funcionario.html", context)


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from Funcionario.models import Funcionario
from metrologia.models.models_tabelatecnica import TabelaTecnica
from django.utils.timezone import now

@login_required
def equipamentos_para_calibracao(request):
    equipamentos = TabelaTecnica.objects.all().order_by("codigo")
    funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")

    context = {
        "equipamentos": equipamentos,
        "funcionarios": funcionarios,
        "data_atual": now().date(),
    }
    return render(request, "relatorios/selecionar_equipamentos_f062.html", context)


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from Funcionario.models import Funcionario
from metrologia.models.models_tabelatecnica import TabelaTecnica
from django.utils.timezone import now

from datetime import datetime

@login_required
def gerar_f062(request):
    if request.method == "POST":
        equipamentos_selecionados = request.POST.getlist("equipamentos_selecionados")
        solicitado_por_id = request.POST.get("solicitado_por")
        aprovado_por_id = request.POST.get("aprovado_por")
        prazo_realizacao_str = request.POST.get("prazo_realizacao")
        descricao_servico = request.POST.get("descricao_servico")

        equipamentos = TabelaTecnica.objects.filter(id__in=equipamentos_selecionados)
        solicitado_por = get_object_or_404(Funcionario, id=solicitado_por_id)
        aprovado_por = get_object_or_404(Funcionario, id=aprovado_por_id)

        # Converter prazo_realizacao para date
        prazo_realizacao = None
        if prazo_realizacao_str:
            prazo_realizacao = datetime.strptime(prazo_realizacao_str, "%Y-%m-%d").date()

        context = {
            "equipamentos": equipamentos,
            "solicitado_por": solicitado_por,
            "aprovado_por": aprovado_por,
            "prazo_realizacao": prazo_realizacao,
            "descricao_servico": descricao_servico,
            "data_atual": now().date(),
        }

        return render(request, "relatorios/f062_form.html", context)

    else:
        return redirect("equipamentos_para_calibracao")




