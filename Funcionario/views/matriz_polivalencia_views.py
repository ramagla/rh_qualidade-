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
from Funcionario.models.choices_departamento import DEPARTAMENTOS_EMPRESA


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

    departamentos = DEPARTAMENTOS_EMPRESA


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
    matriz = get_object_or_404(MatrizPolivalencia, id=id)
    atividades = matriz.atividades.all()
    notas = Nota.objects.filter(atividade__in=atividades)

    colaborador_ids = notas.values_list("funcionario_id", flat=True).distinct()
    colaboradores = Funcionario.objects.filter(id__in=colaborador_ids)

    def gerar_grafico_icone(nota):
        icones = {
            0: "icons/barra_0.png",
            1: "icons/barra_1.png",
            2: "icons/barra_2.png",
            3: "icons/barra_3.png",
            4: "icons/barra_4.png",
        }
        return icones.get(nota, "icons/barra_0.png")

    def descricao_nivel(nota):
        return {
            0: "Não Treinado",
            1: "Tarefas básicas com acompanhamento",
            2: "Tarefas chave com acompanhamento",
            3: "Qualificado sem acompanhamento",
            4: "Qualificador",
        }.get(nota, "")

    notas_por_funcionario = {
        colaborador.id: {
            atividade.id: {"pontuacao": None, "perfil": "", "grafico": "", "descricao": "", "nivel": ""}
            for atividade in atividades
        }
        for colaborador in colaboradores
    }

    for nota in notas:
        p = nota.pontuacao
        notas_por_funcionario[nota.funcionario.id][nota.atividade.id] = {
            "pontuacao": p,
            "perfil": nota.perfil,
            "grafico": gerar_grafico_icone(p) if p is not None else "icons/barra_0.png",
            "descricao": descricao_nivel(p),
            "nivel": p,
        }

    notas_lista = [
        {
            "colaborador_id": colab_id,
            "atividade_id": ativ_id,
            "pontuacao": valores["pontuacao"],
            "perfil": valores["perfil"],
            "grafico": valores["grafico"],
            "descricao": valores["descricao"],
            "nivel": valores["nivel"],
        }
        for colab_id, atividades in notas_por_funcionario.items()
        for ativ_id, valores in atividades.items()
        if valores["pontuacao"] is not None
    ]

    colaboradores_com_perfil = [
        {
            "id": colaborador.id,
            "nome": colaborador.nome,
            "perfil": next(
                (nota["perfil"] for nota in notas_por_funcionario[colaborador.id].values() if nota["perfil"]),
                ""
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
            "colaboradores": colaboradores_com_perfil,
            "notas_lista": notas_lista,
        },
    )





def salvar_notas_funcionarios(request, funcionarios, atividades, usar_perfil=False, usar_suplente=False, excluir_ids=None):
    """
    Salva ou atualiza notas dos funcionários para as atividades.
    Ignora funcionários cujo ID esteja na lista `excluir_ids`.
    """
    excluir_ids = excluir_ids or []

    for funcionario in funcionarios:
        if funcionario.id in excluir_ids:
            continue  # pula os funcionários removidos

        for atividade in atividades:
            nota_key = f"nota_{funcionario.id}_{atividade.id}"
            nota_value = request.POST.get(nota_key)

            if not nota_value or not nota_value.isdigit():
                continue

            dados_nota = {"pontuacao": int(nota_value)}

            if usar_perfil:
                perfil_key = f"perfil_{funcionario.id}"
                dados_nota["perfil"] = request.POST.get(perfil_key, "")

            if usar_suplente:
                suplente_key = f"suplente_{funcionario.id}"
                dados_nota["suplente"] = request.POST.get(suplente_key, "off") == "on"

            Nota.objects.update_or_create(
                funcionario=funcionario,
                atividade=atividade,
                defaults=dados_nota
            )



@login_required
def save_matriz_polivalencia(request, form, atividades, funcionarios, is_edit=False, excluir_ids=None):
    if form.is_valid():
        matriz = form.save(commit=False)
        if is_edit:
            matriz.departamento = form.cleaned_data.get("departamento") or matriz.departamento
        matriz.save()
        salvar_notas_funcionarios(
            request,
            funcionarios,
            atividades,
            usar_perfil=True,
            excluir_ids=excluir_ids  # repassa lista de funcionários removidos
        )
        return matriz, True
    return None, False



@login_required
def cadastrar_matriz_polivalencia(request):
    todos_funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")
    departamentos = DEPARTAMENTOS_EMPRESA
    atividades = Atividade.objects.none()
    funcionarios_tabela = list(todos_funcionarios.values("id", "nome"))

    if request.method == "POST":
        form = MatrizPolivalenciaForm(request.POST)
        departamento = request.POST.get("departamento")
        atividades = Atividade.objects.filter(departamento=departamento)

        matriz, sucesso = save_matriz_polivalencia(request, form, atividades, todos_funcionarios)
        if sucesso:
            messages.success(request, "Matriz de Polivalência cadastrada com sucesso!")
            if "salvar_adicionar_nova" in request.POST:
                return redirect("cadastrar_matriz_polivalencia")
            return redirect("lista_matriz_polivalencia")
        else:
            messages.error(request, "Erro ao cadastrar a Matriz de Polivalência. Verifique os dados.")
    else:
        form = MatrizPolivalenciaForm()

    return render(
        request,
        "matriz_polivalencia/form_matriz.html",
        {
            "form": form,
            "funcionarios_tabela": funcionarios_tabela,
            "funcionarios_disponiveis": funcionarios_tabela,
            "atividades": atividades,
            "departamentos": departamentos,
            "campos_responsaveis": ["elaboracao", "coordenacao", "validacao"],
            "url_voltar": "lista_matriz_polivalencia",
        },
    )



@login_required
def editar_matriz_polivalencia(request, id):
    matriz = get_object_or_404(
        MatrizPolivalencia.objects.select_related("elaboracao", "coordenacao", "validacao"),
        id=id,
    )

    departamentos = DEPARTAMENTOS_EMPRESA
    atividades = Atividade.objects.filter(departamento=matriz.departamento)
    atividade_ids = atividades.values_list("id", flat=True)

    funcionarios_com_nota = Funcionario.objects.filter(
        notas__atividade_id__in=atividade_ids
    ).distinct().order_by("nome")

    todos_funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")

    # Dicionário com notas por funcionário e atividade
    notas_por_funcionario = {
        funcionario.id: {
            atividade.id: {"pontuacao": None, "perfil": ""}
            for atividade in atividades
        }
        for funcionario in funcionarios_com_nota
    }

    for nota in Nota.objects.filter(funcionario__in=funcionarios_com_nota, atividade__in=atividades):
        notas_por_funcionario[nota.funcionario.id][nota.atividade.id] = {
            "pontuacao": nota.pontuacao,
            "perfil": nota.perfil,
        }

    if request.method == "POST":
        form = MatrizPolivalenciaForm(request.POST, instance=matriz)

        # 🔻 Recupera os IDs de colaboradores removidos
        colaboradores_removidos = request.POST.get("colaboradores_removidos", "")
        ids_removidos = [int(id.strip()) for id in colaboradores_removidos.split(",") if id.strip().isdigit()]

        # 🔻 Base apenas dos IDs que estavam na tabela antes da edição
        ids_enviados = set()
        for key in request.POST.keys():
            if key.startswith("nota_") or key.startswith("perfil_"):
                parts = key.split("_")
                if len(parts) >= 2 and parts[1].isdigit():
                    ids_enviados.add(int(parts[1]))

        # 🔻 Considera somente os IDs que foram mantidos na tabela (não removidos)
        ids_mantidos = [fid for fid in ids_enviados if fid not in ids_removidos]

        # 🔻 Busca os objetos Funcionario correspondentes aos mantidos
        funcionarios_restantes = Funcionario.objects.filter(id__in=ids_mantidos)

        nova_matriz, sucesso = save_matriz_polivalencia(
            request,
            form,
            atividades,
            funcionarios_restantes,
            is_edit=True,
            excluir_ids=ids_removidos
        )

        if sucesso:
            Nota.objects.filter(funcionario_id__in=ids_removidos, atividade__in=atividades).delete()

            messages.success(request, "Matriz de Polivalência atualizada com sucesso.")
            return redirect("lista_matriz_polivalencia")
        else:
            messages.error(request, "Erro ao atualizar a Matriz de Polivalência.")
    else:
        form = MatrizPolivalenciaForm(instance=matriz)

    notas_lista = [
        {
            "funcionario_id": func_id,
            "atividade_id": ativ_id,
            "pontuacao": valores["pontuacao"],
            "perfil": valores["perfil"],
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
            "funcionarios_tabela": list(Funcionario.objects.filter(id__in=notas_por_funcionario.keys()).values("id", "nome")),
            "funcionarios_disponiveis": list(Funcionario.objects.filter(status="Ativo").values("id", "nome")),
            "atividades": atividades,
            "departamentos": departamentos,
            "notas_lista": notas_lista,
            "departamento_selecionado": matriz.departamento,
            "campos_responsaveis": ["elaboracao", "coordenacao", "validacao"],
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
           "departamentos": DEPARTAMENTOS_EMPRESA,
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
