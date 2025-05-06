from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from Funcionario.forms import IntegracaoFuncionarioForm  # Formulário para Integração
from Funcionario.models import (  # Modelo IntegracaoFuncionario e Funcionario
    Funcionario,
    IntegracaoFuncionario,
)


# View para listar integrações com filtros
@login_required
def lista_integracoes(request):
    # Obter os filtros do GET
    funcionario_id = request.GET.get("funcionario")
    # O filtro do departamento vem como 'departamento'
    local_trabalho = request.GET.get("departamento")
    requer_treinamento = request.GET.get("requer_treinamento")
    grupo_whatsapp = request.GET.get("grupo_whatsapp")

    # Filtrar as integrações com base nos parâmetros
    integracoes = IntegracaoFuncionario.objects.all()
    if funcionario_id:
        integracoes = integracoes.filter(funcionario_id=funcionario_id)
    if local_trabalho:
        integracoes = integracoes.filter(funcionario__local_trabalho=local_trabalho)
    if requer_treinamento:
        integracoes = integracoes.filter(
            requer_treinamento=(requer_treinamento == "True")
        )
    if grupo_whatsapp:
        integracoes = integracoes.filter(grupo_whatsapp=(grupo_whatsapp == "True"))

    # Ordenar as integrações pelo nome do funcionário relacionado
    integracoes = integracoes.order_by("funcionario__nome")

    # Paginação (10 registros por página)
    paginator = Paginator(integracoes, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Filtrar apenas funcionários com integração cadastrada e ordenar por nome
    funcionarios_com_integracao = (
        Funcionario.objects.filter(integracaofuncionario__isnull=False)
        .distinct()
        .order_by("nome")
    )

    # Obter os valores únicos do campo `local_trabalho` para o filtro de departamento e ordená-los
    departamentos = (
        Funcionario.objects.filter(
            integracaofuncionario__isnull=False  # Filtrar funcionários que possuem integração
        )
        .values_list("local_trabalho", flat=True)
        .distinct()
    )
    departamentos = sorted(departamentos, key=lambda x: x.lower() if x else "")

    # Dados para os cards
    total_integracoes = integracoes.count()
    total_requer_treinamento = integracoes.filter(requer_treinamento=True).count()
    total_grupo_whatsapp = integracoes.filter(grupo_whatsapp=True).count()
    total_sem_pdf = integracoes.filter(
        Q(pdf_integracao__isnull=True) | Q(pdf_integracao="")
    ).count()

    # Não é necessário nenhum ajuste adicional aqui para o PDF, pois será renderizado diretamente no template.
    return render(
        request,
        "integracao/lista_integracoes.html",
        {
            "integracoes": page_obj,
            "page_obj": page_obj,  # Ordenado pelo nome do funcionário
            "funcionarios": funcionarios_com_integracao,  # Somente funcionários com integração
            "departamentos": departamentos,  # Passar os departamentos ordenados para o template
            "total_integracoes": total_integracoes,
            "total_requer_treinamento": total_requer_treinamento,
            "total_grupo_whatsapp": total_grupo_whatsapp,
            "total_sem_pdf": total_sem_pdf,
        },
    )


# View para visualizar uma integração específica
from django.utils.timezone import now  # Adicione no topo, se ainda não tiver

@login_required
def visualizar_integracao(request, integracao_id):
    integracao = get_object_or_404(IntegracaoFuncionario, id=integracao_id)
    return render(
        request,
        "integracao/visualizar_integracao.html",
        {
            "integracao": integracao,
            "now": now(),  # Passa a data e hora atual
        },
    )


# View para cadastrar uma nova integração


@login_required
def cadastrar_integracao(request):
    if request.method == "POST":
        form = IntegracaoFuncionarioForm(request.POST, request.FILES)
        if form.is_valid():
            integracao = form.save()
            messages.success(request, "Integração cadastrada com sucesso.")
            return redirect(reverse("lista_integracoes"))
    else:
        form = IntegracaoFuncionarioForm()
    return render(
        request,
        "integracao/form_integracao.html",
        {"form": form, "integracao": None},
    )



# View para excluir uma integração
@login_required
def excluir_integracao(request, integracao_id):
    integracao = get_object_or_404(IntegracaoFuncionario, id=integracao_id)
    if request.method == "POST":
        integracao.delete()
        messages.success(request, "Integração excluída com sucesso.")
    return redirect(reverse("lista_integracoes"))


@login_required
def editar_integracao(request, integracao_id):
    integracao = get_object_or_404(IntegracaoFuncionario, id=integracao_id)
    if request.method == "POST":
        form = IntegracaoFuncionarioForm(
            request.POST, request.FILES, instance=integracao
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Integração atualizada com sucesso.")
            return redirect(reverse("lista_integracoes"))
    else:
        form = IntegracaoFuncionarioForm(instance=integracao)
    return render(
        request,
        "integracao/form_integracao.html",
        {"form": form, "integracao": integracao},
    )



@login_required
def imprimir_integracao(request, integracao_id):
    try:
        integracao = IntegracaoFuncionario.objects.get(id=integracao_id)
    except IntegracaoFuncionario.DoesNotExist:
        raise Http404("Integração de Funcionário não encontrada.")

    return render(
        request,
        "integracao/imprimir_integracao.html",
        {"integracao": integracao},
    )
