from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from Funcionario.models import Funcionario, Treinamento,AvaliacaoAnual, AvaliacaoExperiencia, HistoricoCargo
from Funcionario.forms import FuncionarioForm
from django.views.generic import View
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from django.db.models import Count 
from django.db.models import Q
from ..models.cargo import Cargo





@login_required
def lista_funcionarios(request):
    # Aplica o filtro padrão de status "Ativo"
    status = request.GET.get('status', 'Ativo')  # Valor padrão é "Ativo"
    funcionarios = Funcionario.objects.filter(status=status).order_by('nome')

    # Dados para os cards
    total_ativos = Funcionario.objects.filter(status="Ativo").count()
    total_inativos = Funcionario.objects.filter(status="Inativo").count()
    local_mais_comum = Funcionario.objects.values('local_trabalho').annotate(count=Count('id')).order_by('-count').first()
    total_pendentes = Funcionario.objects.filter(
        Q(curriculo__isnull=True) | Q(curriculo='')
    ).count()  # Verifica NULL e strings vazias

    # Lista de responsáveis disponíveis
    responsaveis = Funcionario.objects.filter(responsavel__isnull=False, status="Ativo").distinct()

    # Outros filtros
    nome = request.GET.get('nome')
    if nome:
        funcionarios = funcionarios.filter(nome__icontains=nome)

    local_trabalho = request.GET.get('local_trabalho')
    if local_trabalho:
        funcionarios = funcionarios.filter(local_trabalho=local_trabalho)

    responsavel = request.GET.get('responsavel')
    if responsavel:
        if responsavel == "None":
            funcionarios = funcionarios.filter(responsavel__isnull=True)
        else:
            funcionarios = funcionarios.filter(responsavel_id=responsavel)

    escolaridade = request.GET.get('escolaridade')
    if escolaridade:
        funcionarios = funcionarios.filter(escolaridade=escolaridade)

    # Paginação
    paginator = Paginator(funcionarios, 10)  # 10 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'locais_trabalho': Funcionario.objects.filter(status="Ativo").values_list('local_trabalho', flat=True).distinct(),
        'responsaveis': responsaveis,
        'niveis_escolaridade': Funcionario.objects.filter(status="Ativo").values_list('escolaridade', flat=True).distinct(),
        'status_opcoes': Funcionario.objects.values_list('status', flat=True).distinct(),
        'filtro_status': status,  # Inclui o status aplicado no contexto
        'total_ativos': total_ativos,
        'total_pendentes': total_pendentes,
        'local_mais_comum': local_mais_comum['local_trabalho'] if local_mais_comum else "N/A",
        'total_inativos': total_inativos,
        'funcionarios': funcionarios,  # Apenas funcionários filtrados
    }

    return render(request, 'funcionarios/lista_funcionarios.html', context)

@login_required
def visualizar_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)

    # Obter o cargo do responsável, caso exista
    cargo_responsavel = None
    if funcionario.responsavel:
        responsaveis = Funcionario.objects.filter(nome=funcionario.responsavel)
        if responsaveis.exists():
            cargo_responsavel = responsaveis.first().cargo_responsavel  # Obtenha o cargo do primeiro registro encontrado
        else:
            cargo_responsavel = 'Cargo não encontrado'  # Ou lidar de outra forma

    context = {
        'funcionario': funcionario,
        'cargo_responsavel': cargo_responsavel,
    }
    return render(request, 'funcionarios/visualizar_funcionario.html', context)




@login_required
def cadastrar_funcionario(request):
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, request.FILES)
        if form.is_valid():
            funcionario = form.save(commit=False)
            print(f"Responsável: {funcionario.responsavel}, Cargo do Responsável: {funcionario.cargo_responsavel}")
            funcionario.save()
            messages.success(request, 'Funcionário cadastrado com sucesso!')
            return redirect('lista_funcionarios')
        else:
            messages.error(request, 'Erro ao cadastrar o funcionário. Verifique os dados e tente novamente.')
    else:
        form = FuncionarioForm()
    return render(request, 'funcionarios/cadastrar_funcionario.html', {'form': form})

@login_required
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
@login_required
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
        # Obtém o funcionário e todas as avaliações associadas
        funcionario = get_object_or_404(Funcionario, id=funcionario_id)
        
        # Filtra as avaliações de experiência e anuais do funcionário
        avaliacoes_experiencia = AvaliacaoExperiencia.objects.filter(funcionario=funcionario)
        avaliacoes_anual = AvaliacaoAnual.objects.filter(funcionario=funcionario)
        
        # Define o status do prazo para cada avaliação de experiência
        today = timezone.now().date()
        
        for avaliacao in avaliacoes_experiencia:
            data_limite = avaliacao.data_avaliacao + timedelta(days=30)
            avaliacao.get_status_prazo = "Dentro do Prazo" if data_limite >= today else "Em Atraso"

        for avaliacao in avaliacoes_anual:
            data_limite = avaliacao.data_avaliacao + timedelta(days=365)
            avaliacao.get_status_prazo = "Dentro do Prazo" if data_limite >= today else "Em Atraso"
        
        context = {
            'funcionario': funcionario,
            'avaliacoes_experiencia': avaliacoes_experiencia,
            'avaliacoes_anual': avaliacoes_anual,
        }
        
        return render(request, 'funcionarios/template_de_impressao.html', context)

    def post(self, request, funcionario_id):
        # A lógica de imprimir deve ser tratada aqui, se necessário.
        # Para o momento, apenas redireciona para o método GET
        return self.get(request, funcionario_id)
    

@login_required
def gerar_organograma(funcionario):
    """
    Função recursiva para construir a hierarquia completa.
    Inclui a contagem de subordinados.
    """
    # Alterando para filtrar pelo id do responsável, em vez de pelo nome
    subordinados = Funcionario.objects.filter(responsavel_id=funcionario.id, status="Ativo")
    estrutura = []
    for subordinado in subordinados:
        estrutura.append({
            'nome': subordinado.nome,
            'cargo': subordinado.cargo_atual,
            'foto': subordinado.foto.url if subordinado.foto else None,
            'subordinados': gerar_organograma(subordinado),
            'quantidade_subordinados': subordinados.count()  # Contagem de subordinados
        })
    return estrutura


@login_required
def organograma_view(request):
    """
    View para exibir o organograma.
    Carrega todos os funcionários no topo da hierarquia (sem responsável).
    """
    top_funcionarios = Funcionario.objects.filter(responsavel__isnull=True, status="Ativo")

    organograma = []
    for funcionario in top_funcionarios:
        organograma.append({
            'nome': funcionario.nome,
            'cargo': funcionario.cargo_atual,
            'foto': funcionario.foto.url if funcionario.foto else None,
            'subordinados': gerar_organograma(funcionario)  # Gera a hierarquia completa
        })

    return render(request, 'funcionarios/organograma.html', {'organograma': organograma})


# Listar histórico de cargos
@login_required
def listar_historico_cargo(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    historicos = HistoricoCargo.objects.filter(funcionario=funcionario).order_by('-data_atualizacao')
    return render(request, 'funcionarios/historico_cargo.html', {'funcionario': funcionario, 'historicos': historicos})
@login_required
def adicionar_historico_cargo(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)

    if request.method == 'POST':
        cargo_id = request.POST.get('cargo')
        data_atualizacao = request.POST.get('data_atualizacao')  # Captura a data do formulário
        cargo = get_object_or_404(Cargo, id=cargo_id)

        HistoricoCargo.objects.create(
            funcionario=funcionario,
            cargo=cargo,
            data_atualizacao=data_atualizacao  # Usa a data fornecida pelo usuário
        )
        messages.success(request, "Histórico de cargo adicionado com sucesso.")
        return redirect('listar_historico_cargo', funcionario_id=funcionario.id)

    cargos = Cargo.objects.all()
    return render(request, 'funcionarios/adicionar_historico_cargo.html', {
        'funcionario': funcionario,
        'cargos': cargos
    })
@login_required
def excluir_historico_cargo(request, historico_id):
    # Obtém o objeto HistoricoCargo
    historico = get_object_or_404(HistoricoCargo, id=historico_id)

    if request.method == 'POST':
        # Exclui o histórico
        historico.delete()
        # Redireciona após a exclusão
        return redirect('listar_historico_cargo', funcionario_id=historico.funcionario.id)

    return redirect('listar_historico_cargo', funcionario_id=historico.funcionario.id)