from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from Funcionario.models import Funcionario, Treinamento,AvaliacaoDesempenho
from Funcionario.forms import FuncionarioForm
from django.views.generic import View
from django.utils import timezone
from datetime import timedelta




@login_required
def lista_funcionarios(request):
    funcionarios = Funcionario.objects.all()

    local_trabalho = request.GET.get('local_trabalho')
    if local_trabalho:
        funcionarios = funcionarios.filter(local_trabalho=local_trabalho)

    responsavel = request.GET.get('responsavel')
    if responsavel:
        funcionarios = funcionarios.filter(responsavel=responsavel)

    escolaridade = request.GET.get('escolaridade')
    if escolaridade:
        funcionarios = funcionarios.filter(escolaridade=escolaridade)

    status = request.GET.get('status')
    if status:
        funcionarios = funcionarios.filter(status=status)

    context = {
        'funcionarios': funcionarios,
        'locais_trabalho': Funcionario.objects.values_list('local_trabalho', flat=True).distinct(),
        'responsaveis': Funcionario.objects.values('responsavel').distinct(),
        'niveis_escolaridade': Funcionario.objects.values_list('escolaridade', flat=True).distinct(),
        'status_opcoes': Funcionario.objects.values_list('status', flat=True).distinct(),
    }

    return render(request, 'funcionarios/lista_funcionarios.html', context)

def visualizar_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)

    # Aqui você deve obter o cargo do responsável, caso exista
    cargo_responsavel = None
    if funcionario.responsavel:
        try:
            responsavel_funcionario = Funcionario.objects.get(nome=funcionario.responsavel)
            cargo_responsavel = responsavel_funcionario.cargo_responsavel  # Obtenha o cargo
        except Funcionario.DoesNotExist:
            cargo_responsavel = 'Cargo não encontrado'  # Ou lidar de outra forma

    context = {
        'funcionario': funcionario,
        'cargo_responsavel': cargo_responsavel,  # Adicione o cargo ao contexto
    }
    return render(request, 'funcionarios/visualizar_funcionario.html', context)




def cadastrar_funcionario(request):
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Funcionário cadastrado com sucesso!')
            return redirect('lista_funcionarios')
        else:
            messages.error(request, 'Erro ao cadastrar o funcionário. Verifique os dados e tente novamente.')
    else:
        form = FuncionarioForm()
    return render(request, 'funcionarios/cadastrar_funcionario.html', {'form': form})


def editar_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)

    # Inicialize as variáveis
    cargo_responsavel = None
    responsavel_nome = funcionario.responsavel  # Nome do responsável

    # Verifique se o responsável foi fornecido
    if responsavel_nome:
        try:
            # Busque o funcionário responsável pelo nome
            responsavel_funcionario = Funcionario.objects.get(nome=responsavel_nome)
            cargo_responsavel = responsavel_funcionario.cargo_responsavel  # Acesse o cargo do responsável
        except Funcionario.DoesNotExist:
            cargo_responsavel = 'Cargo não encontrado'  # Ou lidar de outra forma

    # Criação do formulário para edição
    form = FuncionarioForm(request.POST or None, request.FILES or None, instance=funcionario)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Funcionário editado com sucesso!')
        return redirect('lista_funcionarios')

    # Certifique-se de que 'responsaveis' está sendo passado no contexto
    responsaveis = Funcionario.objects.exclude(id=funcionario_id)  # Excluir o próprio funcionário da lista

    context = {
        'form': form,
        'funcionario': funcionario,
        'cargo_responsavel': cargo_responsavel,
        'responsaveis': responsaveis  # Adicione isso ao contexto
    }

    return render(request, 'funcionarios/editar_funcionario.html', context)

def excluir_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    if Treinamento.objects.filter(funcionario=funcionario).exists():
        messages.error(request, "Funcionário possui registros associados e não pode ser excluído.")
    else:
        funcionario.delete()
        messages.success(request, 'Funcionário excluído com sucesso.')
    return redirect('lista_funcionarios')


class ImprimirFichaView(View):
    def get(self, request, funcionario_id):
        # Obtém o funcionário e todas as avaliações de desempenho associadas
        funcionario = get_object_or_404(Funcionario, id=funcionario_id)
        avaliacoes_desempenho = AvaliacaoDesempenho.objects.filter(funcionario=funcionario)

        # Define o status do prazo para cada avaliação
        today = timezone.now().date()
        for avaliacao in avaliacoes_desempenho:
            dias_prazo = 30 if avaliacao.tipo == 'EXPERIENCIA' else 365
            data_limite = avaliacao.data_avaliacao + timedelta(days=dias_prazo)
            avaliacao.get_status_prazo = "Dentro do Prazo" if data_limite >= today else "Em Atraso"

        context = {
            'funcionario': funcionario,
            'avaliacoes_desempenho': avaliacoes_desempenho,
        }
        return render(request, 'funcionarios/template_de_impressao.html', context)

    def post(self, request, funcionario_id):
        # A lógica de imprimir deve ser tratada aqui, se necessário.
        # Para o momento, apenas redireciona para o método 
        return self.get(request, funcionario_id)