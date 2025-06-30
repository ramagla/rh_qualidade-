# Arquivo: Funcionario/views/atividade_views.py

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
import pandas as pd
from django.db.models import Count

from Funcionario.forms.matriz_polivalencia_forms import AtividadeForm, NotaForm
from Funcionario.models.funcionario import Funcionario
from Funcionario.models.matriz_polivalencia import Atividade, Nota
from Funcionario.models.departamentos import Departamentos


@login_required
def lista_atividades(request):
    departamento = request.GET.get("departamento")
    nome = request.GET.get("nome")

    atividades = Atividade.objects.all()
    if departamento:
        atividades = atividades.filter(departamentos=departamento)
    if nome:
        atividades = atividades.filter(nome__icontains=nome)
    atividades = atividades.order_by("nome")

    paginator = Paginator(atividades, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    atividades_por_departamento = (
        Atividade.objects.values("departamentos__id", "departamentos__nome")
        .annotate(total=Count("id"))
        .order_by("departamentos__nome")
    )

    context = {
        "page_obj": page_obj,
        "nomes_atividades": Atividade.objects.values_list("nome", flat=True).distinct(),
        "departamentos": Departamentos.objects.filter(ativo=True).order_by("nome"),
        "total_atividades": atividades.count(),
        "atividades_por_departamento": atividades_por_departamento,
    }
    return render(request, "matriz_polivalencia/lista_atividades.html", context)


@login_required
def cadastrar_atividade(request):
    funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")
    departamentos = Departamentos.objects.all()

    if request.method == "POST":
        form = AtividadeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Atividade cadastrada com sucesso!")
            return redirect("lista_atividades")
    else:
        form = AtividadeForm()

    return render(request, "matriz_polivalencia/form_atividade.html", {
        "form": form,
        "funcionarios": funcionarios,
        "departamentos": departamentos,
    })


@login_required
def editar_atividade(request, id):
    atividade = get_object_or_404(Atividade, id=id)
    departamentos = Departamentos.objects.all()

    if request.method == "POST":
        form = AtividadeForm(request.POST, instance=atividade)
        if form.is_valid():
            form.save()
            messages.success(request, "Atividade atualizada com sucesso.")
            return redirect("lista_atividades")
    else:
        form = AtividadeForm(instance=atividade)

    return render(request, "matriz_polivalencia/form_atividade.html", {
        "form": form,
        "atividade": atividade,
        "departamentos": departamentos,
    })


@login_required
def excluir_atividade(request, id):
    atividade = get_object_or_404(Atividade, id=id)
    if request.method == "POST":
        atividade.delete()
        messages.success(request, "Atividade excluída com sucesso.")
        return redirect("lista_atividades")
    return render(request, "matriz_polivalencia/excluir_atividade.html", {"atividade": atividade})


@login_required
def visualizar_atividade(request, id):
    atividade = get_object_or_404(Atividade, id=id)
    return render(request, "matriz_polivalencia/visualizar_atividade.html", {"atividade": atividade})


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
            return redirect("visualizar_matriz_polivalencia", id=atividade.departamento_id)
    else:
        form = NotaForm()

    return render(request, "matriz_polivalencia/gerenciar_notas.html", {
        "form": form,
        "notas": atividade.notas.all(),
        "atividade": atividade,
    })


@login_required
@permission_required("Funcionario.add_atividade", raise_exception=True)
def importar_atividades(request):
    if request.method == "POST":
        arquivo = request.FILES.get("arquivo")
        if not arquivo:
            messages.error(request, "Nenhum arquivo foi enviado.")
            return redirect("importar_atividades")

        try:
            df = pd.read_excel(arquivo)
            colunas = ["Nome da Atividade", "Departamentos (separados por vírgula)"]
            if not all(col in df.columns for col in colunas):
                messages.error(request, "Colunas obrigatórias ausentes no arquivo.")
                return redirect("importar_atividades")

            total_criadas, total_existentes = 0, 0
            for _, row in df.iterrows():
                nome = str(row[colunas[0]]).strip()
                departamentos = str(row[colunas[1]]).split(",")

                if not nome:
                    continue

                atividade, criada = Atividade.objects.get_or_create(nome=nome)
                if criada:
                    total_criadas += 1
                else:
                    total_existentes += 1

                atividade.departamentos.clear()
                for nome_dep in departamentos:
                    dep = nome_dep.strip()
                    if not dep:
                        continue
                    try:
                        departamento = Departamentos.objects.get(nome__iexact=dep)
                        atividade.departamentos.add(departamento)
                    except Departamentos.DoesNotExist:
                        messages.warning(request, f"Departamento '{dep}' não encontrado. Ignorado.")

            messages.success(
                request,
                f"Importação concluída: {total_criadas} criadas, {total_existentes} já existiam."
            )
            return redirect("lista_atividades")

        except Exception as e:
            messages.error(request, f"Erro ao processar o arquivo: {e}")
            return redirect("importar_atividades")

    return render(request, "matriz_polivalencia/importar_atividades.html")


@login_required
def get_atividades_por_departamento(request):
    """Retorna atividades vinculadas ao departamento (JSON)."""
    departamento_id = request.GET.get("departamento_id")
    atividades = Atividade.objects.filter(departamentos__id=departamento_id).order_by("nome")
    atividades_data = [{"id": a.id, "nome": a.nome} for a in atividades]
    return JsonResponse({"atividades": atividades_data})


def get_atividades_e_funcionarios_por_departamento(request):
    """Retorna atividades e funcionários com notas vinculados ao departamento."""
    departamento_id = request.GET.get("departamento_id")
    if not departamento_id:
        return JsonResponse({"erro": "Departamento não especificado."}, status=400)

    atividades = Atividade.objects.filter(departamentos=departamento_id).values("id", "nome")
    funcionarios = Funcionario.objects.filter(notas__atividade__departamentos=departamento_id).distinct().values("id", "nome")

    return JsonResponse({
        "atividades": list(atividades),
        "funcionarios": list(funcionarios)
    })
