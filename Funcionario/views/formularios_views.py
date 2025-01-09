from django.views.generic import TemplateView
from django.shortcuts import render, redirect,get_object_or_404
from django.utils.timezone import now
from Funcionario.models import Settings, Funcionario
from django.contrib.auth.decorators import login_required


# Avaliação de Capacitação Prática
@login_required
def avaliacao_capacitacao(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    settings = Settings.objects.first()
    context = {
        'settings': settings,
        'funcionario': funcionario,
        'data_atual': now(),
    }
    return render(request, 'formularios/avaliacao_capacitacao.html', context)

# Pesquisa de Consciência
class FormularioPesquisaConscienciaView(TemplateView):
    template_name = 'formularios/pesquisa_consciencia.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        funcionarios = Funcionario.objects.filter(status='Ativo').order_by('nome')
        context['funcionarios'] = funcionarios
        context['titulo'] = "Pesquisa de Consciência"
        return context

class FormularioCartaCompetenciaView(TemplateView):
    template_name = 'formularios/carta_competencia.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtém o funcionário pelo ID ou retorna 404 se não existir
        funcionario_id = self.kwargs.get('funcionario_id')
        context['funcionario'] = get_object_or_404(Funcionario, id=funcionario_id)
        return context

@login_required
def filtro_funcionario(request):
    # Define o redirecionamento com base no parâmetro 'next_view'
    next_view = request.GET.get('next_view', 'carta_avaliacao_capacitacao')

    if request.method == 'POST':
        funcionario_id = request.POST.get('funcionario')
        return redirect(next_view, funcionario_id=funcionario_id)

    # Filtra funcionários ativos e ordena por nome
    funcionarios = Funcionario.objects.filter(status='Ativo').order_by('nome')
    return render(request, 'formularios/filtro_funcionario.html', {'funcionarios': funcionarios, 'next_view': next_view})
@login_required
def filtro_carta_competencia(request):
    if request.method == 'POST':
        # Recupera o ID do funcionário selecionado no formulário
        funcionario_id = request.POST.get('funcionario')
        return redirect('formulario_carta_competencia', funcionario_id=funcionario_id)

    # Filtra apenas os funcionários com status ativo
    funcionarios = Funcionario.objects.filter(status='Ativo').order_by('nome')
    return render(request, 'formularios/filtro_funcionario2.html', {'funcionarios': funcionarios})

