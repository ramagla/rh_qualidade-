# Terceiros
import openpyxl

# Django
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now

# Internos
from Funcionario.forms import ListaPresencaForm
from Funcionario.models import Funcionario, ListaPresenca, Treinamento
from Funcionario.utils.lista_presenca_utils import processar_lista_presenca


@login_required
def lista_presenca(request):
    """Renderiza a listagem de listas de presença com filtros e paginação."""
    listas_presenca = ListaPresenca.objects.all().order_by("-data_inicio")

    participantes = Funcionario.objects.filter(
        id__in=listas_presenca.values_list("participantes__id", flat=True)
    ).distinct().order_by("nome")

    total_listas = listas_presenca.count()
    listas_finalizadas = listas_presenca.filter(situacao="finalizado").count()
    listas_em_andamento = listas_presenca.filter(situacao="em_andamento").count()
    listas_indefinidas = listas_presenca.filter(situacao="indefinido").count()

    instrutores = ListaPresenca.objects.values_list("instrutor", flat=True).distinct().order_by("instrutor")
    instrutor_filtro = request.GET.get("instrutor")
    situacao_filtro = request.GET.get("situacao")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    participante_filtro = request.GET.get("participante")

    if instrutor_filtro:
        listas_presenca = listas_presenca.filter(instrutor=instrutor_filtro)
    if situacao_filtro:
        listas_presenca = listas_presenca.filter(situacao=situacao_filtro)
    if data_inicio and data_fim:
        listas_presenca = listas_presenca.filter(data_inicio__gte=data_inicio, data_fim__lte=data_fim)
    if participante_filtro:
        listas_presenca = listas_presenca.filter(participantes__id=participante_filtro)

    paginator = Paginator(listas_presenca, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "lista_presenca/lista_presenca.html",
        {
            "listas_presenca": page_obj,
            "page_obj": page_obj,
            "instrutores": instrutores,
            "participantes": participantes,
            "situacao_opcoes": ListaPresenca.SITUACAO_CHOICES,
            "total_listas": total_listas,
            "listas_finalizadas": listas_finalizadas,
            "listas_em_andamento": listas_em_andamento,
            "listas_indefinidas": listas_indefinidas,
        },
    )


@login_required
def cadastrar_lista_presenca(request):
    """Cadastra nova lista de presença."""
    treinamentos = Treinamento.objects.filter(categoria="treinamento")
    funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")

    if request.method == "POST":
        form = ListaPresencaForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                lista_presenca = form.save()
                processar_lista_presenca(lista_presenca)
                return redirect("lista_presenca")
    else:
        form = ListaPresencaForm()

    return render(
        request,
        "lista_presenca/form_lista_presenca.html",
        {"form": form, "todos_funcionarios": funcionarios, "treinamentos": treinamentos},
    )


@login_required
def editar_lista_presenca(request, id):
    """Edita uma lista de presença existente."""
    lista = get_object_or_404(ListaPresenca, id=id)
    treinamentos = Treinamento.objects.all()
    funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")

    if request.method == "POST":
        form = ListaPresencaForm(request.POST, request.FILES, instance=lista)
        if form.is_valid():
            with transaction.atomic():
                lista = form.save()
                lista.participantes.set(request.POST.getlist("participantes"))
                processar_lista_presenca(lista)
                return redirect("lista_presenca")
    else:
        form = ListaPresencaForm(instance=lista)

    return render(
        request,
        "lista_presenca/form_lista_presenca.html",
        {"form": form, "todos_funcionarios": funcionarios, "treinamentos": treinamentos, "lista": lista},
    )


@login_required
def excluir_lista_presenca(request, id):
    """Exclui uma lista de presença."""
    lista = get_object_or_404(ListaPresenca, id=id)
    lista.delete()
    return redirect("lista_presenca")


@login_required
def visualizar_lista_presenca(request, lista_id):
    """Visualiza uma lista de presença."""
    lista = get_object_or_404(ListaPresenca, id=lista_id)
    return render(request, "lista_presenca/visualizar_lista_presenca.html", {"lista": lista, "now": now()})


@login_required
def imprimir_lista_presenca(request, lista_id):
    """Exibe versão de impressão da lista de presença."""
    lista = get_object_or_404(ListaPresenca, id=lista_id)
    data_inicio = lista.data_inicio.strftime("%d/%m/%Y") if lista.data_inicio else ""
    data_fim = lista.data_fim.strftime("%d/%m/%Y") if lista.data_fim else ""

    return render(
        request,
        "lista_presenca/imprimir_lista_presenca.html",
        {
            "lista": lista,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "numero_formulario": "F013 Rev.03",
        },
    )


@login_required
def exportar_listas_presenca(request):
    """Exporta as listas de presença para Excel."""
    listas_presenca = ListaPresenca.objects.all()
    instrutor_filtro = request.GET.get("instrutor")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    if instrutor_filtro:
        listas_presenca = listas_presenca.filter(instrutor=instrutor_filtro)
    if data_inicio and data_fim:
        listas_presenca = listas_presenca.filter(data_inicio__gte=data_inicio, data_fim__lte=data_fim)

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "Listas de Presença"

    worksheet.append(
        ["ID", "Assunto", "Data Início", "Data Fim", "Duração (Horas)", "Instrutor", "Necessita Avaliação", "Situação", "Participantes"]
    )

    for lista in listas_presenca:
        participantes = ", ".join([p.nome for p in lista.participantes.all()])
        worksheet.append([
            lista.id,
            lista.assunto,
            lista.data_inicio.strftime("%d/%m/%Y") if lista.data_inicio else "",
            lista.data_fim.strftime("%d/%m/%Y") if lista.data_fim else "",
            lista.duracao,
            lista.instrutor,
            "Sim" if lista.necessita_avaliacao else "Não",
            dict(ListaPresenca.SITUACAO_CHOICES).get(lista.situacao, "Indefinido"),
            participantes,
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=Listas_de_Presenca.xlsx"
    workbook.save(response)
    return response
