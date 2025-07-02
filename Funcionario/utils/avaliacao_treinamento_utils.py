from django.contrib import messages

from Funcionario.forms import AvaliacaoTreinamentoForm
from Funcionario.models import Funcionario, ListaPresenca, Treinamento
from Funcionario.models import AvaliacaoTreinamento


def get_opcoes_avaliacao():
    """Retorna os conjuntos de opções para perguntas da avaliação."""
    return {
        "opcoes_conhecimento": AvaliacaoTreinamento.OPCOES_CONHECIMENTO,
        "opcoes_aplicacao": AvaliacaoTreinamento.OPCOES_APLICACAO,
        "opcoes_resultados": AvaliacaoTreinamento.OPCOES_RESULTADOS,
    }


def processar_formulario_avaliacao(request, instance=None):
    """
    Processa o formulário de avaliação, com preenchimento dinâmico de treinamentos.
    """
    funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")
    listas_presenca = ListaPresenca.objects.all()
    treinamentos = Treinamento.objects.all()

    if request.method == "POST":
        form = AvaliacaoTreinamentoForm(request.POST, request.FILES, instance=instance)
        funcionario_id = request.POST.get("funcionario")
        if funcionario_id:
            form.fields["treinamento"].queryset = Treinamento.objects.filter(funcionarios__id=funcionario_id)

        if form.is_valid():
            form.save()
            return form, funcionarios, listas_presenca, True

        messages.error(request, "Erro ao salvar a avaliação. Verifique os campos.")
        return form, funcionarios, listas_presenca, False

    form = AvaliacaoTreinamentoForm(instance=instance)
    if instance and instance.funcionario:
        form.fields["treinamento"].queryset = Treinamento.objects.filter(funcionarios=instance.funcionario)

    return form, funcionarios, listas_presenca, None
