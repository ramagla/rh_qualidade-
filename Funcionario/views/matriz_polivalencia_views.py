# Configurar o backend antes de importar pyplot
import matplotlib
import matplotlib.pyplot as plt
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from ..forms.matriz_polivalencia_forms import (
    AtividadeForm,
    MatrizPolivalenciaForm,
    NotaForm,
)
from ..models.funcionario import Funcionario
from ..models.matriz_polivalencia import Atividade, MatrizPolivalencia, Nota

matplotlib.use("Agg")  # Backend para renderização sem GUI


@login_required
def lista_matriz_polivalencia(request):
    departamento = request.GET.get("departamento")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    # Filtrando as matrizes
    matrizes = MatrizPolivalencia.objects.all()

    # Filtrando matrizes por departamento
    if departamento:
        matrizes = matrizes.filter(departamento=departamento)

    # Filtro de datas
    if data_inicio:
        matrizes = matrizes.filter(atualizado_em__gte=data_inicio)

    if data_fim:
        matrizes = matrizes.filter(atualizado_em__lte=data_fim)

    # Recuperando os departamentos disponíveis
    departamentos = MatrizPolivalencia.objects.values_list(
        "departamento", flat=True
    ).distinct()

    # Paginação
    paginator = Paginator(matrizes, 10)  # 10 itens por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "matriz_polivalencia/matriz_polivalencia_lista.html",
        {"matrizes": page_obj, "page_obj": page_obj, "departamentos": departamentos},
    )


def gerar_grafico_icone(nota):
    icones = {
        0: "icons/barra_0.png",
        1: "icons/barra_1.png",
        2: "icons/barra_2.png",
        3: "icons/barra_3.png",
        4: "icons/barra_4.png",
    }
    return icones.get(nota, "icons/barra_1.png")


def imprimir_matriz(request, id):
    print(">>> TIPO DE REQUEST:", type(request))

    matriz = get_object_or_404(MatrizPolivalencia, id=id)
    atividades = matriz.atividades.all()  # <- ajustado para .all()
    notas = Nota.objects.filter(atividade__in=atividades)

    # Pega apenas os funcionários que possuem nota associada à matriz
    colaborador_ids = notas.values_list("funcionario_id", flat=True).distinct()
    colaboradores = Funcionario.objects.filter(id__in=colaborador_ids)

    # Dicionário de notas
    notas_por_funcionario = {
        colaborador.id: {
            atividade.id: {"pontuacao": None, "suplente": False, "grafico": None}
            for atividade in atividades
        }
        for colaborador in colaboradores
    }

    for nota in notas:
        notas_por_funcionario[nota.funcionario.id][nota.atividade.id] = {
            "pontuacao": nota.pontuacao,
            "suplente": nota.suplente,
            "grafico": gerar_grafico_icone(nota.pontuacao),
        }

    notas_lista = [
        {
            "colaborador_id": colab_id,
            "atividade_id": ativ_id,
            "pontuacao": valores["pontuacao"],
            "suplente": valores["suplente"],
            "grafico": valores["grafico"],
        }
        for colab_id, atividades in notas_por_funcionario.items()
        for ativ_id, valores in atividades.items()
    ]

    colaboradores_com_suplente = [
        {
            "id": colaborador.id,
            "nome": colaborador.nome,
            "suplente": any(
                nota["suplente"]
                for nota in notas_por_funcionario[colaborador.id].values()
            ),
        }
        for colaborador in colaboradores
    ]

    return render(
        request,
        "matriz_polivalencia/imprimir_matriz.html",
        {
            "matriz": matriz,
            "atividades": atividades,
            "colaboradores": colaboradores_com_suplente,
            "notas_lista": notas_lista,
        },
    )



@login_required
def cadastrar_matriz_polivalencia(request):
    funcionarios = Funcionario.objects.filter(status="Ativo").order_by(
        "nome"
    )  # Funcionários ativos ordenados
    atividades = Atividade.objects.all()  # Todas as atividades
    departamentos = Atividade.objects.values_list(
        "departamento", flat=True
    ).distinct()  # Departamentos únicos

    if request.method == "POST":
        form = MatrizPolivalenciaForm(request.POST)
        if form.is_valid():
            matriz = form.save()

            # Processa as notas e suplentes dos funcionários
            for funcionario in funcionarios:
                for atividade in atividades:
                    nota_key = f"nota_{funcionario.id}_{atividade.id}"
                    suplente_key = f"suplente_{funcionario.id}"
                    nota_value = request.POST.get(nota_key)

                    # Converter nota para número inteiro e validar
                    nota_value = (
                        int(nota_value)
                        if nota_value is not None and nota_value.isdigit()
                        else None
                    )
                    suplente_value = request.POST.get(suplente_key, "off") == "on"

                    if (
                        nota_value is not None
                    ):  # Verifica se a nota foi fornecida, incluindo 0
                        Nota.objects.update_or_create(
                            funcionario=funcionario,
                            atividade=atividade,
                            defaults={
                                "pontuacao": nota_value,
                                "suplente": suplente_value,
                            },
                        )

            messages.success(request, "Matriz de Polivalência cadastrada com sucesso!")
            return redirect("lista_matriz_polivalencia")
        else:
            messages.error(
                request,
                "Erro ao cadastrar a Matriz de Polivalência. Verifique os dados.",
            )
    else:
        form = MatrizPolivalenciaForm()

    return render(
        request,
        "matriz_polivalencia/form_matriz.html",
        {
            "form": form,
            "funcionarios": list(funcionarios.values("id", "nome")),
            "atividades": atividades,
            "departamentos": departamentos,
            "campos_responsaveis": ['elaboracao', 'coordenacao', 'validacao'],
        },
    )



# Editar uma matriz de polivalência
@login_required
def editar_matriz_polivalencia(request, id):
    # Pré-carregar as relações para otimizar o acesso aos dados relacionados
    matriz = get_object_or_404(
        MatrizPolivalencia.objects.select_related(
            "elaboracao", "coordenacao", "validacao"
        ),
        id=id,
    )

    # Departamento fixo associado ao cadastro da matriz
    departamento_selecionado = matriz.departamento

    # Filtrar atividades relacionadas ao departamento selecionado
    atividades = Atividade.objects.filter(departamento=departamento_selecionado)

    # Pega os funcionários que possuem nota relacionada com as atividades da matriz
    atividade_ids = atividades.values_list("id", flat=True)
    funcionarios = Funcionario.objects.filter(
        notas__atividade_id__in=atividade_ids
    ).distinct().order_by("nome")

    # Obter todos os departamentos disponíveis para o select
    departamentos = Atividade.objects.values_list("departamento", flat=True).distinct()

    # Construir o dicionário de notas com suplente
    notas_por_funcionario = {
        funcionario.id: {
            atividade.id: {"pontuacao": None, "suplente": False}
            for atividade in atividades
        }
        for funcionario in funcionarios
    }

    # Preencher com os valores das notas existentes
    for nota in Nota.objects.filter(
        funcionario__in=funcionarios, atividade__in=atividades
    ):
        notas_por_funcionario[nota.funcionario.id][nota.atividade.id] = {
            "pontuacao": nota.pontuacao,
            "suplente": nota.suplente,
        }

    if request.method == "POST":
        form = MatrizPolivalenciaForm(request.POST, instance=matriz)
        if form.is_valid():
            matriz = form.save(commit=False)
            matriz.departamento = departamento_selecionado  # preservar o departamento original
            matriz.save()

            # Atualizar notas dos colaboradores
            for funcionario in funcionarios:
                for atividade in atividades:
                    nota_key = f"nota_{funcionario.id}_{atividade.id}"
                    suplente_key = f"suplente_{funcionario.id}"
                    nota_value = request.POST.get(nota_key)
                    suplente_value = request.POST.get(suplente_key, "off") == "on"

                    if nota_value:
                        Nota.objects.update_or_create(
                            funcionario=funcionario,
                            atividade=atividade,
                            defaults={
                                "pontuacao": nota_value,
                                "suplente": suplente_value,
                            },
                        )

            messages.success(request, "Matriz de Polivalência atualizada com sucesso.")
            return redirect("lista_matriz_polivalencia")
        else:
            messages.error(request, "Erro ao atualizar a Matriz de Polivalência.")
    else:
        form = MatrizPolivalenciaForm(instance=matriz)

    # Converter as notas para lista de dicionários (JSON)
    notas_lista = [
        {
            "funcionario_id": func_id,
            "atividade_id": ativ_id,
            "pontuacao": valores["pontuacao"],
            "suplente": valores["suplente"],
        }
        for func_id, atividades_dict in notas_por_funcionario.items()
        for ativ_id, valores in atividades_dict.items()
    ]

    return render(
        request,
        "matriz_polivalencia/form_matriz.html",
        {
            "form": form,
            "matriz": matriz,
            "funcionarios": list(funcionarios.values("id", "nome")),
            "atividades": atividades,
            "departamentos": departamentos,
            "notas_lista": notas_lista,
            "departamento_selecionado": departamento_selecionado,
            "campos_responsaveis": ['elaboracao', 'coordenacao', 'validacao'],
        },
    )



# Excluir uma matriz de polivalência
@login_required
def excluir_matriz_polivalencia(request, id):
    matriz = get_object_or_404(MatrizPolivalencia, id=id)
    if request.method == "POST":
        matriz.delete()  # O método sobrescrito cuidará de excluir as notas relacionadas
        messages.success(
            request,
            "Matriz de Polivalência e suas notas relacionadas foram excluídas com sucesso.",
        )
        return redirect("lista_matriz_polivalencia")
    return render(request, "matriz_polivalencia/excluir.html", {"matriz": matriz})


def lista_atividades(request):
    # Pega os filtros do GET
    departamento = request.GET.get("departamento", "")
    nome = request.GET.get("nome", "")

    # Filtrando as atividades
    atividades = Atividade.objects.all()

    if departamento:
        atividades = atividades.filter(departamento=departamento)

    if nome:
        atividades = atividades.filter(nome__icontains=nome)

    # Adicionando uma ordenação para evitar o erro de "UnorderedObjectListWarning"
    atividades = atividades.order_by("nome")  # Ou qualquer outro campo desejado

    # Paginação
    paginator = Paginator(atividades, 10)  # 10 itens por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Dados para os cards e acordions
    total_atividades = atividades.count()

    # Quantidade de atividades por departamento
    atividades_por_departamento = (
        Atividade.objects.values("departamento")
        .annotate(total=Count("departamento"))
        .order_by("departamento")
    )

    return render(
        request,
        "matriz_polivalencia/lista_atividades.html",
        {
            "page_obj": page_obj,  # Objeto de paginação
            # Listagem de nomes para filtro
            "nomes_atividades": Atividade.objects.values_list(
                "nome", flat=True
            ).distinct(),
            # Listagem de departamentos para filtro
            "departamentos": Atividade.objects.values_list(
                "departamento", flat=True
            ).distinct(),
            "total_atividades": total_atividades,  # Total de atividades
            "atividades_por_departamento": atividades_por_departamento,  # Atividades por departamento
        },
    )


@login_required
def cadastrar_atividade(request):
    # Obter todos os departamentos únicos
    departamentos = Funcionario.objects.values("local_trabalho").distinct()

    # Obter todos os funcionários ativos
    funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")

    if request.method == "POST":
        form = AtividadeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Atividade cadastrada com sucesso!")
            return redirect("lista_atividades")
    else:
        form = AtividadeForm()

    return render(
        request,
        "matriz_polivalencia/form_atividade.html",
        {
            "form": form,
            "funcionarios": funcionarios,  # Passa os funcionários para o template
            "departamentos": departamentos,  # Passa os departamentos únicos para o template
        },
    )


# Gerenciar notas (adicionar/editar/excluir)


@login_required
def gerenciar_notas(request, id):
    atividade = get_object_or_404(Atividade, id=id)
    if request.method == "POST":
        form = NotaForm(request.POST)
        if form.is_valid():
            nota = form.save(commit=False)
            nota.atividade = atividade
            nota.save()
            messages.success(request, "Nota adicionada/atualizada com sucesso.")
            return redirect("visualizar_matriz_polivalencia", id=atividade.departamento)
    else:
        form = NotaForm()
    notas = atividade.notas.all()
    return render(
        request,
        "matriz_polivalencia/gerenciar_notas.html",
        {
            "form": form,
            "notas": notas,
            "atividade": atividade,
        },
    )


@login_required
def visualizar_atividade(request, id):
    atividade = get_object_or_404(Atividade, id=id)
    return render(
        request,
        "matriz_polivalencia/visualizar_atividade.html",
        {"atividade": atividade},
    )


@login_required
def editar_atividade(request, id):
    atividade = get_object_or_404(Atividade, id=id)
    departamentos = Funcionario.objects.values(
        "local_trabalho"
    ).distinct()  # Lista de departamentos únicos

    if request.method == "POST":
        form = AtividadeForm(request.POST, instance=atividade)
        if form.is_valid():
            form.save()
            messages.success(request, "Atividade atualizada com sucesso.")
            return redirect("lista_atividades")
    else:
        form = AtividadeForm(instance=atividade)

    return render(
        request,
        "matriz_polivalencia/form_atividade.html",
        {
            "form": form,
            "atividade": atividade,
            "departamentos": departamentos,  # Passa os departamentos como contexto
        },
    )


@login_required
def excluir_atividade(request, id):
    atividade = get_object_or_404(Atividade, id=id)
    if request.method == "POST":
        atividade.delete()
        messages.success(request, "Atividade excluída com sucesso.")
        return redirect("lista_atividades")  # Redireciona para a lista de atividades
    return render(
        request, "matriz_polivalencia/excluir_atividade.html", {"atividade": atividade}
    )


@login_required
def get_atividades_por_departamento(request):
    departamento = request.GET.get("departamento")  # Obtém o departamento selecionado
    # Filtra atividades pelo departamento
    atividades = Atividade.objects.filter(departamento=departamento)
    atividade_list = [
        {"id": atividade.id, "nome": atividade.nome} for atividade in atividades
    ]
    return JsonResponse({"atividades": atividade_list})


@login_required
def get_atividades_e_funcionarios_por_departamento(request):
    departamento = request.GET.get("departamento")

    if departamento:
        # Buscar atividades relacionadas ao departamento
        atividades = Atividade.objects.filter(departamento=departamento).values("id", "nome")

        # Agrupar funcionários ativos por local_trabalho
        funcionarios = Funcionario.objects.filter(status="Ativo").order_by("local_trabalho", "nome")
        colaboradores_por_departamento = {}

        for f in funcionarios:
            setor = f.local_trabalho or "Sem Setor"
            if setor not in colaboradores_por_departamento:
                colaboradores_por_departamento[setor] = []
            colaboradores_por_departamento[setor].append({
                "id": f.id,
                "nome": f.nome
            })

        return JsonResponse({
            "atividades": list(atividades),
            "colaboradores_por_departamento": colaboradores_por_departamento
        })

    return JsonResponse({"error": "Departamento não encontrado"}, status=400)
