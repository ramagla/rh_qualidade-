from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from collections import defaultdict

from ..forms import CargoForm, RevisaoForm
from ..models import Cargo, Funcionario, Revisao
from Funcionario.models.departamentos import Departamentos

@login_required
def organograma_cargos(request):
    cargos_agrupados = defaultdict(list)

    for cargo in Cargo.objects.prefetch_related("cargo_atual_funcionarios").order_by("nivel", "nome"):
        funcionario_ativo = next(
            (f for f in cargo.cargo_atual_funcionarios.all() if f.status == "Ativo"),
            None
        )
        cargos_agrupados[cargo.nivel].append({
            "cargo": cargo,
            "funcionario_ativo": funcionario_ativo
        })

    niveis_ordenados = sorted(cargos_agrupados.items())

    return render(request, "cargos/organograma_cargos.html", {
        "niveis_ordenados": niveis_ordenados
    })
@login_required
def lista_cargos(request):
    # Recupera todos os cargos ordenados por número da DC
    cargos = Cargo.objects.all().order_by("nome")

    # Aplicar filtro de departamento
    departamento = request.GET.get("departamento")
    if departamento:
        cargos = cargos.filter(departamento=departamento)

    # Aplicar filtro de nome do cargo
    cargo_nome = request.GET.get("cargo")
    if cargo_nome:
        cargos = cargos.filter(nome=cargo_nome)

    # Adicionar a última revisão para cada cargo
    for cargo in cargos:
        cargo.ultima_revisao = cargo.revisoes.order_by("-data_revisao").first()

    
    todos_cargos = Cargo.objects.all().distinct("nome").order_by("nome")

    # Dados para os cards
    total_cargos = cargos.count()
    departamento_mais_frequente = (
        cargos.values("departamento")
        .annotate(total=Count("departamento"))
        .order_by("-total")
        .first()
    )
    departamento_mais_frequente = (
        departamento_mais_frequente["departamento"]
        if departamento_mais_frequente
        else "Nenhum"
    )

    ultima_revisao = (
        Revisao.objects.filter(cargo__in=cargos).order_by("-data_revisao").first()
    )
    ultima_revisao = ultima_revisao.data_revisao if ultima_revisao else "Sem revisão"

    cargos_sem_descricao = cargos.filter(
        Q(descricao_arquivo__isnull=True) | Q(descricao_arquivo="")
    ).count()

    # Paginação
    paginator = Paginator(cargos, 10)  # Define 10 cargos por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Contexto para o template
    return render(
        request,
        "cargos/lista_cargos.html",
        {
            "cargos": page_obj,
            "page_obj": page_obj,
            "departamentos": Departamentos.objects.all(),
            "todos_cargos": todos_cargos,
            "total_cargos": total_cargos,
            "departamento_mais_frequente": departamento_mais_frequente,
            "ultima_revisao": ultima_revisao,
            "cargos_sem_descricao": cargos_sem_descricao,
        },
    )


@login_required
def cadastrar_cargo(request):
    if request.method == "POST":
        form = CargoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("lista_cargos")
    else:
        form = CargoForm()
    return render(request, "cargos/form_cargo.html", {"form": form, "cargo": None})


def excluir_cargo(request, cargo_id):
    cargo = get_object_or_404(Cargo, id=cargo_id)
    cargo.delete()
    messages.success(request, "Cargo excluído com sucesso!")
    return redirect("lista_cargos")


def historico_revisoes(request, cargo_id):
    cargo = get_object_or_404(Cargo, id=cargo_id)
    revisoes = cargo.revisoes.all()
    return render(
        request,
        "cargos/historico_revisoes.html",
        {"cargo": cargo, "revisoes": revisoes},
    )


def adicionar_revisao(request, cargo_id):
    cargo = get_object_or_404(Cargo, id=cargo_id)

    if request.method == "POST":
        form = RevisaoForm(request.POST)
        if form.is_valid():
            revisao = form.save(commit=False)
            revisao.cargo = cargo
            revisao.save()
            return redirect("historico_revisoes", cargo_id=cargo_id)
    else:
        form = RevisaoForm()

    # ✅ variável resolvida no backend para uso direto no template
    titulo_pagina = f"Adicionar Revisão para {cargo.nome}"

    return render(
        request,
        "cargos/adicionar_revisao.html",
        {
            "form": form,
            "cargo": cargo,
            "titulo_pagina": titulo_pagina,
            "param_id": cargo.id,  # ✅ Adicione esta linha
        },
    )



def excluir_revisao(request, revisao_id):
    revisao = get_object_or_404(Revisao, id=revisao_id)
    cargo_id = revisao.cargo.id  # Salva o ID do cargo antes da exclusão
    revisao.delete()
    messages.success(request, "Revisão excluída com sucesso.")
    return redirect("historico_revisoes", cargo_id=cargo_id)


def obter_cargos(request, funcionario_id):
    try:
        funcionario = Funcionario.objects.get(pk=funcionario_id)
        cargos = {
            "cargo_inicial": funcionario.cargo_inicial,
            "cargo_atual": funcionario.cargo_atual,
        }
        return JsonResponse(cargos)
    except Funcionario.DoesNotExist:
        return JsonResponse({"error": "Funcionário não encontrado"}, status=404)


@login_required
def buscar_cargos(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    data = {
        "cargo_inicial": funcionario.cargo_inicial.nome,
        "cargo_atual": funcionario.cargo_atual.nome,
    }
    return JsonResponse(data)


@login_required
def editar_cargo(request, cargo_id):
    cargo = get_object_or_404(Cargo, pk=cargo_id)

    if request.method == "POST":
        form = CargoForm(request.POST, request.FILES, instance=cargo)
        if form.is_valid():
            form.save()
            return redirect("lista_cargos")
    else:
        # Garantir que as datas estão no formato correto
        form = CargoForm(
            instance=cargo,
            initial={
                "elaborador_data": (
                    cargo.elaborador_data.strftime("%Y-%m-%d")
                    if cargo.elaborador_data
                    else ""
                ),
                "aprovador_data": (
                    cargo.aprovador_data.strftime("%Y-%m-%d")
                    if cargo.aprovador_data
                    else ""
                ),
            },
        )

    return render(request, "cargos/form_cargo.html", {"form": form, "cargo": None})


def imprimir_cargo(request, cargo_id):
    cargo = get_object_or_404(Cargo, pk=cargo_id)
    revisoes = cargo.revisoes.all().order_by(
        "-data_revisao"
    )  # Ordenar pela data mais recente
    return render(
        request, "cargos/imprimir_cargo.html", {"cargo": cargo, "revisoes": revisoes}
    )
