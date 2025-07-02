# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now

# Locais
from Funcionario.forms import AvaliacaoExperienciaForm
from Funcionario.models import AvaliacaoExperiencia, Funcionario
from Funcionario.utils.avaliacao_experiencia_utils import calcular_orientacao


@login_required
def lista_avaliacao_experiencia(request):
    """
    Exibe a lista de avaliações de experiência com filtros opcionais.
    """
    avaliacoes = AvaliacaoExperiencia.objects.all()

    funcionario_id = request.GET.get("funcionario")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    if funcionario_id:
        avaliacoes = avaliacoes.filter(funcionario_id=funcionario_id)

    if data_inicio and data_fim:
        avaliacoes = avaliacoes.filter(data_avaliacao__range=[data_inicio, data_fim])

    funcionarios = Funcionario.objects.filter(
        id__in=avaliacoes.values_list("funcionario_id", flat=True)
    )

    paginator = Paginator(avaliacoes, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "avaliacoes": page_obj,
        "funcionarios": funcionarios,
        "total_avaliacoes": avaliacoes.count(),
        "efetivar": avaliacoes.filter(orientacao__icontains="Efetivar").count(),
        "treinamento": avaliacoes.filter(orientacao__icontains="Treinamento").count(),
        "desligar": avaliacoes.filter(orientacao__icontains="Desligar").count(),
        "page_obj": page_obj,
    }
    return render(request, "avaliacao_desempenho_experiencia/lista_avaliacao_experiencia.html", context)


@login_required
def cadastrar_avaliacao_experiencia(request):
    """
    Cadastra uma nova avaliação de experiência.
    """
    if request.method == "POST":
        form = AvaliacaoExperienciaForm(request.POST, request.FILES)
        if form.is_valid():
            avaliacao = form.save(commit=False)
            avaliacao.orientacao = request.POST.get("status")
            avaliacao.save()
            return redirect("lista_avaliacao_experiencia")
    else:
        form = AvaliacaoExperienciaForm()

    context = {
        "form": form,
        "funcionarios": Funcionario.objects.filter(status="Ativo").order_by("nome"),
        "edicao": False,
        "url_voltar": "lista_avaliacao_experiencia",
        "param_id": None,
    }
    return render(request, "avaliacao_desempenho_experiencia/form_avaliacao_experiencia.html", context)


@login_required
def editar_avaliacao_experiencia(request, id):
    """
    Edita uma avaliação de experiência existente.
    """
    avaliacao = get_object_or_404(AvaliacaoExperiencia, id=id)

    if request.method == "POST":
        form = AvaliacaoExperienciaForm(request.POST, request.FILES, instance=avaliacao)

        if request.POST.get("remover_anexo") == "1" and avaliacao.anexo:
            avaliacao.anexo.delete(save=False)
            avaliacao.anexo = None

        if form.is_valid():
            avaliacao.orientacao, avaliacao.status = calcular_orientacao(request.POST)
            form.save()
            messages.success(request, "Avaliação atualizada com sucesso!")
            return redirect("lista_avaliacao_experiencia")
        else:
            messages.error(request, "Erro ao atualizar a avaliação. Verifique os dados informados.")
    else:
        form = AvaliacaoExperienciaForm(instance=avaliacao)

    context = {
        "form": form,
        "avaliacao": avaliacao,
        "funcionarios": Funcionario.objects.filter(status="Ativo").order_by("nome"),
        "edicao": True,
        "url_voltar": "lista_avaliacao_experiencia",
        "param_id": None,
    }
    return render(request, "avaliacao_desempenho_experiencia/form_avaliacao_experiencia.html", context)


@login_required
def excluir_avaliacao_experiencia(request, id):
    """
    Exclui uma avaliação de experiência.
    """
    avaliacao = get_object_or_404(AvaliacaoExperiencia, id=id)
    if request.method == "POST":
        avaliacao.delete()
    return redirect("lista_avaliacao_experiencia")


@login_required
def visualizar_avaliacao_experiencia(request, id):
    """
    Visualiza os dados de uma avaliação de experiência.
    """
    avaliacao = get_object_or_404(AvaliacaoExperiencia, id=id)
    return render(
        request,
        "avaliacao_desempenho_experiencia/visualizar_avaliacao_experiencia.html",
        {"avaliacao": avaliacao, "now": now()},
    )

@login_required
def imprimir_avaliacao_experiencia(request, avaliacao_id):
    """
    Gera a visualização de impressão da avaliação de experiência.
    """
    avaliacao = get_object_or_404(AvaliacaoExperiencia, id=avaliacao_id)

    context = {
        "avaliacao": avaliacao,
        "opcoes_adaptacao_trabalho": {
            4: "Está plenamente identificado com as atividades do seu cargo e integrou-se perfeitamente às normas da Bras-Mol.",
            3: "Tem feito o possível para integrar-se no seu cargo e no próprio trabalho, tentando se adaptar às características da Bras-Mol.",
            2: "Precisa muito esforço para conseguir integrar-se ao seu cargo e aos requisitos administrativos da Bras-Mol.",
            1: "Mantém um comportamento oposto ao solicitado para seu cargo e demonstra ter sérias dificuldades de aceitação das características da Bras-Mol.",
        },
        "opcoes_interesse": {
            4: "Parece vivamente interessado por seu novo trabalho.",
            3: "Apresenta um entusiasmo adequado, tendo em vista o seu pouco tempo de Bras-Mol.",
            2: "Dá a impressão de ser um funcionário que não entende a necessidade de estímulo para poder interessar-se pelo seu trabalho.",
            1: "Em várias ocasiões, apresenta uma falta total de entusiasmo e vontade de trabalhar.",
        },
        "opcoes_relacionamento_social": {
            4: "Apresentou grande habilidade em conseguir amigos, mesmo com pouco tempo de Bras-Mol; todos já gostaram muito dele(a).",
            3: "Entrosou-se bem com os demais, foi aceito sem resistências.",
            2: "Está fazendo muito esforço para conseguir maior integração social com os colegas.",
            1: "Sente-se perdido entre os colegas, parece não ter sido aceito pelo grupo de trabalho.",
        },
        "opcoes_capacidade_aprendizagem": {
            4: "Parece especialmente habilitado para o cargo em que está, tem facilidade em aprender, permitindo-lhe executar sem falhas.",
            3: "Parece adequado para o cargo ao qual foi encaminhado, aprende suas tarefas sem grandes problemas.",
            2: "Está conseguindo compreender o que lhe foi ensinado à custa de grande esforço pessoal, necessitando repetir-se a mesma coisa várias vezes.",
            1: "É tão difícil de compreender o que o estão ensinando que parece não ter a mínima capacidade para o trabalho.",
        },
    }

    return render(
        request,
        "avaliacao_desempenho_experiencia/impressao_avaliacao_experiencia.html",
        context,
    )
