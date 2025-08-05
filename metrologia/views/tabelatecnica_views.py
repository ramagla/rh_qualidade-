from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import DateField, DurationField, ExpressionWrapper, F, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now

from Funcionario.models import Funcionario

from ..forms import TabelaTecnicaForm
from ..models.models_tabelatecnica import TabelaTecnica

from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import DateField, DurationField, ExpressionWrapper, F, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now

from Funcionario.models import Funcionario
from ..forms import TabelaTecnicaForm
from ..models.models_tabelatecnica import TabelaTecnica


@login_required
@permission_required("metrologia.view_tabelatecnica", raise_exception=True)
def lista_tabelatecnica(request):
    today = now().date()
    range_start = today
    range_end = today + timedelta(days=31)

    # 🔍 Apenas instrumentos ATIVOS para estatísticas dos cards
    ativos = TabelaTecnica.objects.filter(status="ativo").annotate(
        proxima_calibracao=ExpressionWrapper(
            Coalesce(F("data_ultima_calibracao"), Value(today)) +
            ExpressionWrapper(
                Coalesce(F("frequencia_calibracao"), Value(1)) * Value(30),
                output_field=DurationField()
            ),
            output_field=DateField()
        )
    )

    # 📊 Estatísticas para os cards
    total_tabelas = ativos.count()
    total_fora_prazo = ativos.filter(proxima_calibracao__lt=today).count()
    total_proximo_prazo = ativos.filter(
        proxima_calibracao__gte=range_start,
        proxima_calibracao__lte=range_end
    ).count()

    # 🧾 Lista geral com anotação, sem filtro fixo de status
    tabelas = TabelaTecnica.objects.annotate(
        proxima_calibracao=ExpressionWrapper(
            Coalesce(F("data_ultima_calibracao"), Value(today)) +
            ExpressionWrapper(
                Coalesce(F("frequencia_calibracao"), Value(1)) * Value(30),
                output_field=DurationField()
            ),
            output_field=DateField()
        )
    )

    # 🔁 Filtros dinâmicos
    codigo = request.GET.get("codigo")
    if codigo:
        tabelas = tabelas.filter(codigo=codigo)

    nome_equipamento = request.GET.get("nome_equipamento")
    if nome_equipamento:
        tabelas = tabelas.filter(nome_equipamento__icontains=nome_equipamento)

    unidade_medida = request.GET.get("unidade_medida")
    if unidade_medida:
        tabelas = tabelas.filter(unidade_medida=unidade_medida)

    status = request.GET.get("status", "ativo")
    tabelas = tabelas.filter(status=status)

    responsavel = request.GET.get("responsavel")
    if responsavel:
        tabelas = tabelas.filter(responsavel_id=responsavel)

    proprietario = request.GET.get("proprietario")
    if proprietario:
        tabelas = tabelas.filter(proprietario__icontains=proprietario)

    fabricante = request.GET.get("fabricante")
    if fabricante:
        tabelas = tabelas.filter(fabricante__icontains=fabricante)

    responsaveis = Funcionario.objects.filter(
        id__in=tabelas.values_list("responsavel_id", flat=True)
    ).distinct().only("id", "nome")

    unidades_medida_choices = dict(TabelaTecnica.UNIDADE_MEDIDA_CHOICES)

    paginator = Paginator(tabelas, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "equipamentos": tabelas.values_list("nome_equipamento", flat=True).distinct().order_by("nome_equipamento"),
        "unidades_medida": unidades_medida_choices,
        "codigos": tabelas.values_list("codigo", flat=True).distinct().order_by("codigo"),
        "responsaveis": responsaveis,
        "proprietarios": tabelas.values_list("proprietario", flat=True).distinct().order_by("proprietario"),
        "fabricantes": tabelas.values_list("fabricante", flat=True).distinct().order_by("fabricante"),
        "status_selecionado": status,
        "total_tabelas": total_tabelas,
        "total_fora_prazo": total_fora_prazo,
        "total_proximo_prazo": total_proximo_prazo,
        "today": today,
    }

    return render(request, "tabelatecnica/lista_tabelatecnica.html", context)


@login_required
@permission_required("metrologia.add_tabelatecnica", raise_exception=True)
def cadastrar_tabelatecnica(request):
    if request.method == "POST":
        form = TabelaTecnicaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Tabela Técnica cadastrada com sucesso!")
            return redirect("lista_tabelatecnica")
        else:
            messages.error(request, "Erro ao cadastrar a Tabela Técnica.")
    else:
        form = TabelaTecnicaForm()

    context = {
        "form": form,
        "edicao": False,
        "url_voltar": "lista_tabelatecnica"
    }
    return render(request, "tabelatecnica/form_tabelatecnica.html", context)


@login_required
@permission_required("metrologia.change_tabelatecnica", raise_exception=True)
def editar_tabelatecnica(request, id):
    tabela = get_object_or_404(TabelaTecnica, id=id)

    if request.method == "POST":
        form = TabelaTecnicaForm(request.POST, request.FILES, instance=tabela)
        if form.is_valid():
            form.save()
            messages.success(request, "Tabela Técnica editada com sucesso!")
            return redirect("lista_tabelatecnica")
    else:
        form = TabelaTecnicaForm(instance=tabela)

    context = {
    "form": form,
    "edicao": True,
    "url_voltar": "lista_tabelatecnica"  # sem param_id
}

    return render(request, "tabelatecnica/form_tabelatecnica.html", context)


from django.utils import timezone

@login_required
@permission_required("metrologia.view_tabelatecnica", raise_exception=True)
def visualizar_tabelatecnica(request, id):
    tabelatecnica = get_object_or_404(TabelaTecnica, id=id)
    context = {
        "tabelatecnica": tabelatecnica,
        "now": timezone.now(),  # ⏰ Data e hora atual
    }
    return render(request, "tabelatecnica/visualizar_tabelatecnica.html", context)

@login_required
@permission_required("metrologia.delete_tabelatecnica", raise_exception=True)
def excluir_tabelatecnica(request, id):
    tabela = get_object_or_404(TabelaTecnica, id=id)
    tabela.delete()
    messages.success(request, "Tabela Técnica excluída com sucesso.")
    return redirect("lista_tabelatecnica")

@login_required
@permission_required("metrologia.imprimir_tabelatecnica", raise_exception=True)
def imprimir_tabelatecnica(request):
    # Filtra equipamentos com status 'Ativo', ignorando maiúsculas/minúsculas
    tabelas = TabelaTecnica.objects.filter(status__iexact="Ativo").order_by("codigo")

    context = {
        "tabelas": tabelas,
    }
    return render(request, "tabelatecnica/imprimir_tabelatecnica.html", context)


def enviar_alertas_calibracao():
    today = now().date()
    range_end = today + timedelta(days=30)

    # Equipamentos com calibração vencida
    equipamentos_vencidos = TabelaTecnica.objects.annotate(
        proxima_calibracao=ExpressionWrapper(
            Coalesce(F("data_ultima_calibracao"), Value(today))
            + ExpressionWrapper(
                Coalesce(F("frequencia_calibracao"), Value(1)) * Value(30),
                output_field=DurationField(),
            ),
            output_field=DateField(),
        )
    ).filter(proxima_calibracao__lt=today)

    # Equipamentos próximos do vencimento
    equipamentos_proximos = TabelaTecnica.objects.annotate(
        proxima_calibracao=ExpressionWrapper(
            Coalesce(F("data_ultima_calibracao"), Value(today))
            + ExpressionWrapper(
                Coalesce(F("frequencia_calibracao"), Value(1)) * Value(30),
                output_field=DurationField(),
            ),
            output_field=DateField(),
        )
    ).filter(proxima_calibracao__gte=today, proxima_calibracao__lte=range_end)

    # E-mail de alerta para equipamentos vencidos
    if equipamentos_vencidos.exists():
        mensagem_vencidos = "\n".join(
            f"{eq.codigo} - {eq.nome_equipamento} (Próxima Calibração: {eq.proxima_calibracao})"
            for eq in equipamentos_vencidos
        )
        send_mail(
            "Alerta: Equipamentos com Calibração Vencida",
            f"Os seguintes equipamentos estão com calibração vencida:\n\n{mensagem_vencidos}",
            "no-reply@brasmol.com",  # Remetente
            ["metrologia@brasmol.com"],  # Destinatários
            fail_silently=False,
        )

    # E-mail de alerta para equipamentos próximos do vencimento
    if equipamentos_proximos.exists():
        mensagem_proximos = "\n".join(
            f"{eq.codigo} - {eq.nome_equipamento} (Próxima Calibração: {eq.proxima_calibracao})"
            for eq in equipamentos_proximos
        )
        send_mail(
            "Alerta: Equipamentos Próximos do Vencimento",
            f"Os seguintes equipamentos estão próximos do vencimento da calibração:\n\n{mensagem_proximos}",
            "no-reply@brasmol.com",  # Remetente
            ["metrologia@brasmol.com"],  # Destinatários
            fail_silently=False,
        )
