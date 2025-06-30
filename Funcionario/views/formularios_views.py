# Bibliotecas padrão
from calendar import monthrange

# Django - Funcionalidades principais
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now
from django.views.generic import TemplateView

# App Interno - Modelos e utils
from Funcionario.models import Funcionario, Settings
from Funcionario.utils.formularios_utils import (
    obter_nome_mes,
    obter_valores_mes_ano,
    obter_funcionarios_ativos_ordenados
)


@login_required
def formulario_f033(request, funcionario_id):
    """Renderiza o formulário F033 para um funcionário."""
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    context = {"funcionario": funcionario, "data_atual": now()}
    return render(request, "formularios/f033_formulario.html", context)


@login_required
def avaliacao_capacitacao(request, funcionario_id):
    """Renderiza o formulário de Avaliação de Capacitação Prática."""
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    settings = Settings.objects.first()
    context = {
        "funcionario": funcionario,
        "settings": settings,
        "data_atual": now(),
    }
    return render(request, "formularios/avaliacao_capacitacao.html", context)


class FormularioPesquisaConscienciaView(TemplateView):
    """Renderiza a listagem de funcionários para pesquisa de consciência."""
    template_name = "formularios/pesquisa_consciencia.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        funcionarios = obter_funcionarios_ativos_ordenados()
        paginator = Paginator(funcionarios, 10)
        page_number = self.request.GET.get("page")
        context["page_obj"] = paginator.get_page(page_number)
        context["titulo"] = "Pesquisa de Consciência"
        return context


class FormularioCartaCompetenciaView(TemplateView):
    """Renderiza a carta de competência para um funcionário."""
    template_name = "formularios/carta_competencia.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        funcionario_id = self.kwargs.get("funcionario_id")
        context["funcionario"] = get_object_or_404(Funcionario, id=funcionario_id)
        return context


@login_required
def filtro_funcionario_generico(request):
    """Filtro genérico para seleção de funcionário."""
    next_view = request.GET.get("next_view") or request.POST.get("next_view")
    texto_botao = request.GET.get("texto_botao", "Gerar Formulário")
    titulo = request.GET.get("titulo", "Seleção de Funcionário")
    icone = request.GET.get("icone", "bi bi-person-lines-fill")
    emoji = request.GET.get("emoji", "👤")

    if next_view in [None, "", "None"]:
        messages.error(request, "Parâmetro 'next_view' inválido ou ausente.")
        return redirect("home")

    if request.method == "POST":
        funcionario_id = request.POST.get("funcionario")
        return redirect(next_view, funcionario_id=funcionario_id)

    funcionarios = obter_funcionarios_ativos_ordenados()
    context = {
        "funcionarios": funcionarios,
        "next_view": next_view,
        "texto_botao": texto_botao,
        "titulo": titulo,
        "icone": icone,
        "emoji": emoji,
    }
    return render(request, "formularios/filtro_generico_wrapper.html", context)


@login_required
def formulario_saida_antecipada(request, funcionario_id):
    """Renderiza o formulário de saída antecipada."""
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    return render(request, "formularios/saida_antecipada.html", {"funcionario": funcionario})


@permission_required("Funcionario.emitir_ficha_epi", raise_exception=True)
def imprimir_ficha_epi(request, funcionario_id):
    """Renderiza a ficha de EPI para um funcionário."""
    funcionario = get_object_or_404(Funcionario, pk=funcionario_id, status="Ativo")
    context = {"funcionarios": [funcionario], "now": now()}
    return render(request, "formularios/relatorio_ficha_epi.html", context)


@login_required
def formulario_folha_ponto(request, funcionario_id):
    """Renderiza a folha ponto de um funcionário para o mês/ano especificado."""
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    settings = Settings.objects.first()

    mes, ano = obter_valores_mes_ano(request)
    dias_do_mes = range(1, monthrange(ano, mes)[1] + 1)
    nome_mes = obter_nome_mes(mes, ano)

    context = {
        "funcionario": funcionario,
        "settings": settings,
        "mes": mes,
        "ano": ano,
        "dias_do_mes": dias_do_mes,
        "nome_mes": nome_mes,
    }
    return render(request, "formularios/folha_ponto.html", context)
