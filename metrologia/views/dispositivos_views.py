from datetime import timedelta

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, DateField, ExpressionWrapper, F, Q, Value
from django.db.models.functions import Coalesce
from django.forms import inlineformset_factory, modelformset_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.timezone import now

from Funcionario.models import Funcionario
from metrologia.forms import ControleEntradaSaidaForm, CotaForm, DispositivoForm
from metrologia.models.models_dispositivos import (
    ControleEntradaSaida,
    Cota,
    Dispositivo,
)
from metrologia.models.models_tabelatecnica import TabelaTecnica
from django.contrib.auth.decorators import login_required, permission_required

import calendar
from dateutil.relativedelta import relativedelta

def _eom(d):
    return d.replace(day=calendar.monthrange(d.year, d.month)[1])

@login_required
@permission_required("metrologia.view_dispositivo", raise_exception=True)
def lista_dispositivos(request):
    today = now().date()
    range_start = today
    range_end = today + timedelta(days=31)

    # Base queryset
    qs = Dispositivo.objects.all()

    # 🔁 Filtros dinâmicos (no queryset, antes de montar a lista)
    local_armazenagem = request.GET.get("local_armazenagem")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    codigo = request.GET.get("codigo")
    cliente = request.GET.get("cliente")
    situacao = request.GET.get("situacao")

    if data_inicio and data_fim:
        qs = qs.filter(data_ultima_calibracao__range=[data_inicio, data_fim])

    if local_armazenagem:
        qs = qs.filter(local_armazenagem__icontains=local_armazenagem)

    if codigo:
        qs = qs.filter(codigo=codigo)

    if cliente:
        qs = qs.filter(cliente__icontains=cliente)

    if situacao:
        qs = qs.filter(controle_entrada_saida__situacao=situacao)

    # 🗓️ Calcula proxima_calibracao (EOM) e monta lista para paginação
    dispositivos = []
    for d in qs:
        if d.data_ultima_calibracao and d.frequencia_calibracao:
            prox = _eom(d.data_ultima_calibracao + relativedelta(months=d.frequencia_calibracao))
            setattr(d, "proxima_calibracao", prox)
        else:
            setattr(d, "proxima_calibracao", None)
        dispositivos.append(d)

    # 📊 Estatísticas dos cards (com a lista já filtrada)
    total_dispositivos = len(dispositivos)
    total_fora_prazo = len([d for d in dispositivos if d.proxima_calibracao and d.proxima_calibracao < today])
    total_proximo_prazo = len([d for d in dispositivos if d.proxima_calibracao and range_start <= d.proxima_calibracao <= range_end])

    filtro_prazo = request.GET.get("prazo")

    dentro, proximo, fora = [], [], []
    for d in dispositivos:
        if d.proxima_calibracao:
            if d.proxima_calibracao < today:
                fora.append(d)
            elif range_start <= d.proxima_calibracao <= range_end:
                proximo.append(d)
            else:
                dentro.append(d)
        else:
            # sem próxima calculada: trate como "dentro" para exibir (ajuste se preferir ocultar)
            dentro.append(d)

    if filtro_prazo == "fora":
        dispositivos_filtrados = fora
    elif filtro_prazo == "proximo":
        dispositivos_filtrados = proximo
    elif filtro_prazo == "dentro":
        dispositivos_filtrados = dentro
    else:
        dispositivos_filtrados = dentro + proximo + fora

    # 📄 Paginação sobre a lista filtrada por prazo
    paginator = Paginator(dispositivos_filtrados, 10)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)

    # 📋 Combos e contadores que dependem de QuerySet (use o qs filtrado)
    codigos_disponiveis = qs.values_list("codigo", flat=True).distinct().order_by("codigo")
    clientes_disponiveis = qs.values_list("cliente", flat=True).distinct().order_by("cliente")
    total_ok = qs.filter(controle_entrada_saida__situacao="OK").count()
    total_nok = qs.filter(controle_entrada_saida__situacao="NOK").count()
    locais_disponiveis = qs.values_list("local_armazenagem", flat=True).distinct().order_by("local_armazenagem")

    context = {
        "page_obj": page_obj,
        "codigos_disponiveis": codigos_disponiveis,
        "clientes_disponiveis": clientes_disponiveis,
        "total_dispositivos": total_dispositivos,
        "total_fora_prazo": total_fora_prazo,
        "total_proximo_prazo": total_proximo_prazo,
        "total_ok": total_ok,
        "total_nok": total_nok,
        "today": today,
        "locais_disponiveis": locais_disponiveis,
        "prazo_selecionado": filtro_prazo, 
    }
    return render(request, "dispositivos/lista_dispositivos.html", context)




def salvar_dispositivo_e_cotas(request, dispositivo_form, cota_formset, dispositivo):

    dispositivo = dispositivo_form.save()

    if cota_formset:
        cotas = cota_formset.save(commit=False)
        for cota in cotas:
            cota.dispositivo = dispositivo
            cota.save()

        for cota in cota_formset.deleted_objects:
            cota.delete()
    else:
        # Criação direta a partir de listas do POST
        cotas_numero = request.POST.getlist("cotas_numero[]")
        cotas_valor_minimo = request.POST.getlist("cotas_valor_minimo[]")
        cotas_valor_maximo = request.POST.getlist("cotas_valor_maximo[]")

        for numero, valor_min, valor_max in zip(
            cotas_numero, cotas_valor_minimo, cotas_valor_maximo
        ):
            Cota.objects.create(
                dispositivo=dispositivo,
                numero=numero,
                valor_minimo=valor_min,
                valor_maximo=valor_max,
            )

    return dispositivo

@login_required
@permission_required("metrologia.add_dispositivo", raise_exception=True)
def cadastrar_dispositivo(request):
    CotaFormSet = modelformset_factory(
        Cota,
        fields=("numero", "valor_minimo", "valor_maximo"),
        extra=0,
        can_delete=True,
    )

    if request.method == "POST":
        dispositivo_form = DispositivoForm(request.POST, request.FILES)
        cota_formset = CotaFormSet(request.POST, queryset=Cota.objects.none())

        if dispositivo_form.is_valid() and cota_formset.is_valid():
            salvar_dispositivo_e_cotas(request, dispositivo_form, cota_formset, None)
            return redirect("lista_dispositivos")

    else:
        dispositivo_form = DispositivoForm()
        cota_formset = CotaFormSet(queryset=Cota.objects.none())

    return render(
        request,
        "dispositivos/form_dispositivo.html",
        {
            "form": dispositivo_form,
            "cotas_forms": cota_formset,
            "edicao": False,
            "url_voltar": "lista_dispositivos",
        },
    )


@login_required
@permission_required("metrologia.change_dispositivo", raise_exception=True)
def editar_dispositivo(request, dispositivo_id):
    dispositivo = get_object_or_404(Dispositivo, id=dispositivo_id)

    CotaFormSet = modelformset_factory(
        Cota,
        fields=("numero", "valor_minimo", "valor_maximo"),
        extra=0,
        can_delete=True,
    )

    if request.method == "POST":
        dispositivo_form = DispositivoForm(request.POST, request.FILES, instance=dispositivo)
        cota_formset = CotaFormSet(request.POST, queryset=Cota.objects.filter(dispositivo=dispositivo))

        print("Form válido:", dispositivo_form.is_valid())
        print("Formset válido:", cota_formset.is_valid())
        print("Formset erros:", cota_formset.errors)
        print("Formset non_form_errors:", cota_formset.non_form_errors())

        if dispositivo_form.is_valid() and cota_formset.is_valid():
            salvar_dispositivo_e_cotas(request, dispositivo_form, cota_formset, dispositivo)
            return redirect("lista_dispositivos")

    else:
        dispositivo_form = DispositivoForm(instance=dispositivo)
        cota_formset = CotaFormSet(queryset=Cota.objects.filter(dispositivo=dispositivo))

    return render(
        request,
        "dispositivos/form_dispositivo.html",
        {
            "form": dispositivo_form,
            "cotas_forms": cota_formset,
            "edicao": True,
            "url_voltar": "lista_dispositivos",
        },
    )



@login_required
@permission_required("metrologia.delete_dispositivo", raise_exception=True)
def excluir_dispositivo(request, id):
    dispositivo = get_object_or_404(Dispositivo, id=id)

    if request.method == "POST":
        dispositivo.delete()
        messages.success(
            request, f"Dispositivo {dispositivo.codigo} foi excluído com sucesso!"
        )
        return redirect(reverse("lista_dispositivos"))

    # Para casos onde a view é acessada diretamente por GET
    messages.error(request, "A exclusão deve ser confirmada pelo modal.")
    return redirect(reverse("lista_dispositivos"))


from django.utils.timezone import now

@login_required
@permission_required("metrologia.view_dispositivo", raise_exception=True)
def visualizar_dispositivo(request, id):
    dispositivo = get_object_or_404(Dispositivo, id=id)
    cotas = Cota.objects.filter(dispositivo=dispositivo)
    
    return render(
        request,
        "dispositivos/visualizar_dispositivo.html",
        {
            "dispositivo": dispositivo,
            "cotas": cotas,
            "now": now(),  # para uso no rodapé
        },
    )


@login_required
@permission_required("metrologia.relatorio_equipamentos_calibrar", raise_exception=True)
def imprimir_dispositivo(request):
    """Imprime a lista de dispositivos."""
    dispositivos = TabelaTecnica.objects.all()
    return render(
        request,
        "dispositivos/imprimir_dispositivo.html",
        {"dispositivos": dispositivos},
    )

@login_required
@permission_required("metrologia.view_controleentradasaida", raise_exception=True)
def historico_movimentacoes(request, dispositivo_id):
    dispositivo = get_object_or_404(Dispositivo, id=dispositivo_id)
    movimentacoes = ControleEntradaSaida.objects.filter(
        dispositivo=dispositivo
    ).order_by("-data_movimentacao")

    return render(
        request,
        "dispositivos/historico_movimentacoes.html",
        {
            "dispositivo": dispositivo,
            "movimentacoes": movimentacoes,
        },
    )

@login_required
@permission_required("metrologia.add_controleentradasaida", raise_exception=True)
def cadastrar_movimentacao(request, dispositivo_id):
    dispositivo = get_object_or_404(Dispositivo, id=dispositivo_id)
    # Busca setores distintos, classificados em ordem alfabética
    setores = (
        Funcionario.objects.values_list("local_trabalho", flat=True)
        .distinct()
        .order_by("local_trabalho")
    )

    if request.method == "POST":
        form = ControleEntradaSaidaForm(request.POST)
        if form.is_valid():
            movimentacao = form.save(commit=False)
            movimentacao.dispositivo = dispositivo
            movimentacao.save()
            return redirect("historico_movimentacoes", dispositivo_id=dispositivo_id)
    else:
        form = ControleEntradaSaidaForm()

    return render(
        request,
        "dispositivos/cadastrar_movimentacao.html",
        {
            "dispositivo": dispositivo,
            "form": form,
            "setores": setores,
        },
    )

@login_required
@permission_required("metrologia.delete_controleentradasaida", raise_exception=True)
def excluir_movimentacao(request, id):
    movimentacao = get_object_or_404(ControleEntradaSaida, id=id)
    dispositivo_id = movimentacao.dispositivo.id
    if request.method == "POST":
        movimentacao.delete()
        return redirect("historico_movimentacoes", dispositivo_id=dispositivo_id)
    return render(
        request,
        "dispositivos/excluir_movimentacao.html",
        {"movimentacao": movimentacao},
    )
