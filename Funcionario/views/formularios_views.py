from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now
from django.views.generic import TemplateView

from Funcionario.models import Funcionario, Settings


@login_required
def formulario_f033(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    context = {
        "funcionario": funcionario,
        "data_atual": now(),
    }
    return render(request, "formularios/f033_formulario.html", context)



# Avaliação de Capacitação Prática
@login_required
def avaliacao_capacitacao(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    settings = Settings.objects.first()
    context = {
        "settings": settings,
        "funcionario": funcionario,
        "data_atual": now(),
    }
    return render(request, "formularios/avaliacao_capacitacao.html", context)


# Pesquisa de Consciência


class FormularioPesquisaConscienciaView(TemplateView):
    template_name = "formularios/pesquisa_consciencia.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")
        paginator = Paginator(funcionarios, 10)  # Altere a quantidade por página se necessário
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["page_obj"] = page_obj  # 👈 ESSENCIAL!
        context["titulo"] = "Pesquisa de Consciência"
        return context


from django.core.paginator import Paginator

class FormularioCartaCompetenciaView(TemplateView):
    template_name = "formularios/carta_competencia.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        funcionario_id = self.kwargs.get("funcionario_id")
        context["funcionario"] = get_object_or_404(Funcionario, id=funcionario_id)
        return context




@login_required
def filtro_funcionario_generico(request):
    next_view = request.GET.get("next_view") or request.POST.get("next_view")
    texto_botao = request.GET.get("texto_botao", "Gerar Formulário")
    titulo = request.GET.get("titulo", "Seleção de Funcionário")
    icone = request.GET.get("icone", "bi bi-person-lines-fill")
    emoji = request.GET.get("emoji", "👤")

    # ⚠️ CORREÇÃO: trata "None" string como nulo
    if next_view in [None, "", "None"]:
        messages.error(request, "Parâmetro 'next_view' inválido ou ausente.")
        return redirect("home")

    if request.method == "POST":
        funcionario_id = request.POST.get("funcionario")
        return redirect(next_view, funcionario_id=funcionario_id)

    funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")
    return render(request, "formularios/filtro_generico_wrapper.html", {
        "funcionarios": funcionarios,
        "next_view": next_view,
        "texto_botao": texto_botao,
        "titulo": titulo,
        "icone": icone,
        "emoji": emoji,
    })










@login_required
def formulario_saida_antecipada(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    return render(request, "formularios/saida_antecipada.html", {
        "funcionario": funcionario
    })

