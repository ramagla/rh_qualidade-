from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from Funcionario.forms import AvaliacaoTreinamentoForm
from Funcionario.models import (
    AvaliacaoTreinamento,
    Funcionario,
    ListaPresenca,
    Treinamento,
)




@login_required
def lista_avaliacoes(request):
    avaliacoes_treinamento = AvaliacaoTreinamento.objects.all().order_by(
        "funcionario__nome"
    )  # Ordena por nome do funcionário

    # Filtra por treinamento, se selecionado
    treinamento_id = request.GET.get("treinamento")
    if treinamento_id:
        avaliacoes_treinamento = avaliacoes_treinamento.filter(
            treinamento_id=treinamento_id
        )

    # Filtra por funcionário, se selecionado
    funcionario_id = request.GET.get("funcionario")
    if funcionario_id:
        avaliacoes_treinamento = avaliacoes_treinamento.filter(
            funcionario_id=funcionario_id
        )

    # Filtra por período de data, se ambos os campos forem preenchidos
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    if data_inicio and data_fim:
        avaliacoes_treinamento = avaliacoes_treinamento.filter(
            data_avaliacao__range=[data_inicio, data_fim]
        )

    # Contadores para os cards
    total_avaliacoes = avaliacoes_treinamento.count()
    muito_eficaz = avaliacoes_treinamento.filter(avaliacao_geral=5).count()
    eficaz = avaliacoes_treinamento.filter(avaliacao_geral=2).count()
    pouco_eficaz = avaliacoes_treinamento.filter(avaliacao_geral=1).count()

    # Paginação
    paginator = Paginator(avaliacoes_treinamento, 10)  # 10 itens por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Busca apenas funcionários e treinamentos com avaliações no conjunto filtrado
    funcionarios_ativos = Funcionario.objects.filter(
        id__in=avaliacoes_treinamento.values_list(
            "funcionario_id", flat=True
        ).distinct()
    )
    listas_presenca = Treinamento.objects.filter(
        id__in=AvaliacaoTreinamento.objects.values_list(
            "treinamento_id", flat=True
        ).distinct()
    )

    # Renderiza o template com os filtros aplicados
    return render(
        request,
        "avaliacao_treinamento/lista_avaliacao.html",
        {
            "avaliacoes_treinamento": page_obj,  # Paginação aplicada
            "funcionarios_ativos": funcionarios_ativos,
            "listas_presenca": listas_presenca,
            "total_avaliacoes": total_avaliacoes,
            "muito_eficaz": muito_eficaz,
            "eficaz": eficaz,
            "pouco_eficaz": pouco_eficaz,
            "page_obj": page_obj,  # Enviado para o template para controle do paginator
        },
    )


def get_opcoes_avaliacao():
    return {
        "opcoes_conhecimento": [
            (1, "Muito baixo"),
            (2, "Baixo"),
            (3, "Médio"),
            (4, "Bom"),
            (5, "Excelente"),
        ],
        "opcoes_aplicacao": [
            (1, "Muito baixo"),
            (2, "Baixo"),
            (3, "Médio"),
            (4, "Bom"),
            (5, "Excelente"),
        ],
        "opcoes_resultados": [
            (1, "Muito baixo"),
            (2, "Baixo"),
            (3, "Médio"),
            (4, "Bom"),
            (5, "Excelente"),
        ],
    }


def processar_formulario_avaliacao(request, instance=None):
    funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")
    listas_presenca = ListaPresenca.objects.all()
    treinamentos = Treinamento.objects.all()

    if request.method == "POST":
        form = AvaliacaoTreinamentoForm(request.POST, request.FILES, instance=instance)

        funcionario_id = request.POST.get("funcionario")
        if funcionario_id:
            form.fields["treinamento"].queryset = Treinamento.objects.filter(
                funcionarios__id=funcionario_id
            )

        if form.is_valid():
            form.save()
            return form, funcionarios, listas_presenca, True
        else:
            messages.error(request, "Erro ao salvar a avaliação. Verifique os campos.")
            return form, funcionarios, listas_presenca, False
    else:
        form = AvaliacaoTreinamentoForm(instance=instance)
        if instance and instance.funcionario:
            form.fields["treinamento"].queryset = Treinamento.objects.filter(
                funcionarios=instance.funcionario
            )
        return form, funcionarios, listas_presenca, None


@login_required
def cadastrar_avaliacao(request):
    form, funcionarios, listas_presenca, status = processar_formulario_avaliacao(request)

    if status is True:
        messages.success(request, "Avaliação cadastrada com sucesso!")
        return redirect("lista_avaliacoes")

    return render(
        request,
        "avaliacao_treinamento/form_avaliacao.html",
        {
            "form": form,
            "funcionarios": funcionarios,
            "listas_presenca": listas_presenca,
            **get_opcoes_avaliacao(),
        },
    )


@login_required
def editar_avaliacao(request, id):
    avaliacao = get_object_or_404(AvaliacaoTreinamento, id=id)
    form, funcionarios, listas_presenca, status = processar_formulario_avaliacao(request, instance=avaliacao)

    if status is True:
        messages.success(request, "Avaliação atualizada com sucesso!")
        return redirect("lista_avaliacoes")

    treinamentos = Treinamento.objects.filter(funcionarios=avaliacao.funcionario)

    return render(
        request,
        "avaliacao_treinamento/form_avaliacao.html",
        {
            "form": form,
            "avaliacao": avaliacao,
            "funcionarios": funcionarios,
            "treinamentos": treinamentos,
            "listas_presenca": listas_presenca,
            **get_opcoes_avaliacao(),
        },
    )


from django.utils import timezone

@login_required
def visualizar_avaliacao(request, id):
    avaliacao = get_object_or_404(AvaliacaoTreinamento, id=id)

    # Mapeamento das respostas para texto
    opcoes_conhecimento = {
        1: "Não possui conhecimento mínimo da metodologia para sua aplicação.",
        2: "Apresenta deficiências nos conceitos, o que compromete a aplicação.",
        3: "Possui noções básicas, mas necessita de acompanhamento e suporte na aplicação.",
        4: "Possui domínio necessário da metodologia e a utiliza adequadamente.",
        5: "Possui completo domínio e utiliza a metodologia com excelência.",
    }
    opcoes_aplicacao = {
        1: "Está muito abaixo do esperado.",
        2: "Aplicação está abaixo do esperado.",
        3: "Aplicação é razoável, mas não dentro do esperado.",
        4: "Aplicação está adequada e corresponde às expectativas.",
        5: "Aplicação excede as expectativas.",
    }
    opcoes_resultados = {
        1: "Nenhum resultado foi obtido efetivamente até o momento.",
        2: "As melhorias obtidas estão muito abaixo do esperado.",
        3: "As melhorias obtidas são consideráveis, mas não dentro do esperado.",
        4: "As melhorias obtidas são boas e estão dentro do esperado.",
        5: "As melhorias obtidas excederam as expectativas.",
    }

    grau_conhecimento = opcoes_conhecimento.get(avaliacao.pergunta_1, "Resposta não especificada")
    aplicacao_conceitos = opcoes_aplicacao.get(avaliacao.pergunta_2, "Resposta não especificada")
    resultados_obtidos = opcoes_resultados.get(avaliacao.pergunta_3, "Resposta não especificada")

    avaliacao_geral_map = {1: "Pouco Eficaz", 2: "Eficaz", 5: "Muito Eficaz"}
    avaliacao_geral = avaliacao_geral_map.get(avaliacao.avaliacao_geral, "Indeterminado")

    treinamento = avaliacao.treinamento if avaliacao.treinamento else None

    return render(
        request,
        "avaliacao_treinamento/visualizar_avaliacao.html",
        {
            "avaliacao": avaliacao,
            "grau_conhecimento": grau_conhecimento,
            "aplicacao_conceitos": aplicacao_conceitos,
            "resultados_obtidos": resultados_obtidos,
            "melhorias": avaliacao.descricao_melhorias,
            "avaliacao_geral": avaliacao_geral,
            "treinamento": treinamento,
            "now": timezone.now(),  # <- adicionado aqui
        },
    )

def get_treinamentos_por_funcionario(request, funcionario_id):
    treinamentos = ListaPresenca.objects.filter(participantes__id=funcionario_id)
    data = [
        {
            "id": treinamento.id,
            "treinamento": treinamento.treinamento,
            "data_realizacao": treinamento.data_realizacao.strftime("%Y-%m-%d"),
            "assunto": treinamento.assunto,
        }
        for treinamento in treinamentos
    ]
    return JsonResponse(data, safe=False)


@login_required
def imprimir_treinamento(request, treinamento_id):
    # Obtém a avaliação de treinamento ou retorna 404
    avaliacao = get_object_or_404(AvaliacaoTreinamento, id=treinamento_id)

    # Verifica se o funcionário relacionado existe
    funcionario = avaliacao.funcionario if avaliacao.funcionario else None

    # Define o contexto para o template
    context = {
        "avaliacao": avaliacao,
        "opcoes_conhecimento": AvaliacaoTreinamento.OPCOES_CONHECIMENTO,
        "opcoes_aplicacao": AvaliacaoTreinamento.OPCOES_APLICACAO,
        "opcoes_resultados": AvaliacaoTreinamento.OPCOES_RESULTADOS,
        "responsavel_funcionario": (
            funcionario.responsavel if funcionario else "Não definido"
        ),
    }

    # Renderiza o template de impressão
    return render(request, "avaliacao_treinamento/impressao_treinamento.html", context)


@login_required
def excluir_avaliacao(request, id):
    # Obtém a avaliação ou retorna 404
    avaliacao = get_object_or_404(AvaliacaoTreinamento, id=id)

    # Exclui a avaliação e redireciona para a lista
    avaliacao.delete()
    return redirect("lista_avaliacoes")
