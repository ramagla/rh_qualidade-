from datetime import date

import openpyxl
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.forms import modelform_factory
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from Funcionario.forms import ListaPresencaForm
from Funcionario.models import (
    AvaliacaoTreinamento,
    Funcionario,
    ListaPresenca,
    Treinamento,
)
from Funcionario.templatetags.conversores import horas_formatadas


# Função lista_presenca
@login_required
def lista_presenca(request):
    listas_presenca = ListaPresenca.objects.all().order_by(
        "-data_inicio"
    )  # Ordenar por assunto

    # Contadores para os cards
    total_listas = listas_presenca.count()
    listas_finalizadas = listas_presenca.filter(situacao="finalizado").count()
    listas_em_andamento = listas_presenca.filter(situacao="em_andamento").count()
    listas_indefinidas = listas_presenca.filter(situacao="indefinido").count()

    # Filtros
    instrutores = ListaPresenca.objects.values_list("instrutor", flat=True).distinct()
    instrutor_filtro = request.GET.get("instrutor", None)
    situacao_filtro = request.GET.get("situacao")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    if instrutor_filtro:
        listas_presenca = listas_presenca.filter(instrutor=instrutor_filtro)

    if situacao_filtro:
        listas_presenca = listas_presenca.filter(situacao=situacao_filtro)

    if data_inicio and data_fim:
        listas_presenca = listas_presenca.filter(
            data_inicio__gte=data_inicio, data_fim__lte=data_fim
        )

    # Paginação
    paginator = Paginator(listas_presenca, 10)  # 10 itens por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "lista_presenca/lista_presenca.html",
        {
            "listas_presenca": page_obj,
            "page_obj": page_obj,
            "listas_presenca": listas_presenca,
            "instrutores": instrutores,
            "situacao_opcoes": ListaPresenca.SITUACAO_CHOICES,
            "total_listas": total_listas,
            "listas_finalizadas": listas_finalizadas,
            "listas_em_andamento": listas_em_andamento,
            "listas_indefinidas": listas_indefinidas,
        },
    )


def processar_lista_presenca(lista_presenca):
    # Regras de criação
    if (
        lista_presenca.situacao == "finalizado"
        or (lista_presenca.situacao == "em_andamento" and lista_presenca.planejado == "sim")
    ):
        treinamento_existente = Treinamento.objects.filter(
            nome_curso=lista_presenca.assunto,
            data_inicio=lista_presenca.data_inicio,
            data_fim=lista_presenca.data_fim,
            descricao=lista_presenca.descricao,
            carga_horaria=lista_presenca.duracao,
        ).first()

        if not treinamento_existente:
            treinamento_existente = Treinamento.objects.create(
                tipo="interno",
                categoria="treinamento",
                nome_curso=lista_presenca.assunto,
                instituicao_ensino="Bras-Mol",
                status="planejado" if lista_presenca.situacao == "em_andamento" else "concluido",
                data_inicio=lista_presenca.data_inicio,
                data_fim=lista_presenca.data_fim,
                carga_horaria=lista_presenca.duracao,
                descricao=lista_presenca.descricao,
                situacao="aprovado",
                planejado=lista_presenca.planejado,
            )

        else:
            treinamento_existente.funcionarios.clear()

        for participante in lista_presenca.participantes.all():
            treinamento_existente.funcionarios.add(participante)

        if lista_presenca.necessita_avaliacao:
            for participante in lista_presenca.participantes.all():
                avaliacao, criada = AvaliacaoTreinamento.objects.get_or_create(
                    funcionario=participante,
                    treinamento=treinamento_existente,
                    defaults={
                        "data_avaliacao": lista_presenca.data_fim or date.today(),
                        "periodo_avaliacao": 60,
                        "pergunta_1": None,
                        "pergunta_2": None,
                        "pergunta_3": None,
                        "responsavel_1": participante.responsavel,
                        "descricao_melhorias": "Aguardando avaliação",
                        "avaliacao_geral": None,
                    },
                )
                if not criada:
                    avaliacao.data_avaliacao = lista_presenca.data_fim or date.today()
                    avaliacao.pergunta_1 = None
                    avaliacao.pergunta_2 = None
                    avaliacao.pergunta_3 = None
                    avaliacao.responsavel_1 = participante.responsavel
                    avaliacao.descricao_melhorias = "Aguardando avaliação"
                    avaliacao.avaliacao_geral = None
                    avaliacao.save()

@login_required
def cadastrar_lista_presenca(request):
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
        {
            "form": form,
            "todos_funcionarios": funcionarios,
            "treinamentos": treinamentos,
        },
    )

@login_required
def editar_lista_presenca(request, id):
    lista = get_object_or_404(ListaPresenca, id=id)
    treinamentos = Treinamento.objects.all()
    todos_funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")

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
        {
            "form": form,
            "todos_funcionarios": todos_funcionarios,
            "treinamentos": treinamentos,
            "lista": lista,
        },
    )


@login_required
def excluir_lista_presenca(request, id):
    lista = get_object_or_404(ListaPresenca, id=id)
    lista.delete()
    return redirect("lista_presenca")

from django.utils.timezone import now

@login_required
def visualizar_lista_presenca(request, lista_id):
    lista = get_object_or_404(ListaPresenca, id=lista_id)
    return render(
        request,
        "lista_presenca/visualizar_lista_presenca.html",
        {
            "lista": lista,
            "now": now()
        }
    )



# Função para imprimir lista de presença
@login_required
def imprimir_lista_presenca(request, lista_id):
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
            "numero_formulario": "F013 Rev.03",  # ✅ Adicionado aqui

        },
    )


# Função para exportar listas de presença


@login_required
def exportar_listas_presenca(request):
    listas_presenca = ListaPresenca.objects.all()

    instrutor_filtro = request.GET.get("instrutor")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    if instrutor_filtro:
        listas_presenca = listas_presenca.filter(instrutor=instrutor_filtro)

    if data_inicio and data_fim:
        listas_presenca = listas_presenca.filter(
            data_inicio__gte=data_inicio, data_fim__lte=data_fim
        )

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "Listas de Presença"

    worksheet.append(
        [
            "ID",
            "Assunto",
            "Data Início",
            "Data Fim",
            "Duração (Horas)",
            "Instrutor",
            "Necessita Avaliação",
            "Situação",
            "Participantes",
        ]
    )

    for lista in listas_presenca:
        participantes = ", ".join([p.nome for p in lista.participantes.all()])
        worksheet.append(
            [
                lista.id,
                lista.assunto,
                lista.data_inicio.strftime("%d/%m/%Y") if lista.data_inicio else "",
                lista.data_fim.strftime("%d/%m/%Y") if lista.data_fim else "",
                lista.duracao,
                lista.instrutor,
                "Sim" if lista.necessita_avaliacao else "Não",
                dict(ListaPresenca.SITUACAO_CHOICES).get(lista.situacao, "Indefinido"),
                participantes,
            ]
        )

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=Listas_de_Presenca.xlsx"
    workbook.save(response)
    return response
