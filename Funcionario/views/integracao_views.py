from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from Funcionario.models import IntegracaoFuncionario, Funcionario  # Modelo IntegracaoFuncionario e Funcionario
from Funcionario.forms import IntegracaoFuncionarioForm  # Formulário para Integração
from django.urls import reverse
from django.db.models import Q
from django.http import Http404

# View para listar integrações com filtros
def lista_integracoes(request):
    # Obter os filtros do GET
    funcionario_id = request.GET.get('funcionario')
    local_trabalho = request.GET.get('departamento')
    requer_treinamento = request.GET.get('requer_treinamento')
    grupo_whatsapp = request.GET.get('grupo_whatsapp')
    
    # Filtrar as integrações com base nos parâmetros
    integracoes = IntegracaoFuncionario.objects.all()
    if funcionario_id:
        integracoes = integracoes.filter(funcionario_id=funcionario_id)
    if local_trabalho:
        integracoes = integracoes.filter(funcionario__local_trabalho=local_trabalho)
    if requer_treinamento:
        integracoes = integracoes.filter(requer_treinamento=(requer_treinamento == 'True'))
    if grupo_whatsapp:
        integracoes = integracoes.filter(grupo_whatsapp=(grupo_whatsapp == 'True'))

    # Filtrar apenas funcionários com integração cadastrada
    funcionarios_com_integracao = Funcionario.objects.filter(integracaofuncionario__isnull=False).distinct()

    # Obter locais de trabalho para o filtro
    locais_trabalho = Funcionario.objects.values_list('local_trabalho', flat=True).distinct()

    return render(request, 'funcionarios/integracao/lista_integracoes.html', {
        'integracoes': integracoes,
        'funcionarios': funcionarios_com_integracao,  # Somente funcionários com integração
        'locais_trabalho': locais_trabalho,
    })

# View para visualizar uma integração específica
def visualizar_integracao(request, integracao_id):
    integracao = get_object_or_404(IntegracaoFuncionario, id=integracao_id)
    return render(request, 'funcionarios/integracao/visualizar_integracao.html', {'integracao': integracao})

# View para cadastrar uma nova integração
def cadastrar_integracao(request):
    if request.method == 'POST':
        form = IntegracaoFuncionarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Integração cadastrada com sucesso.')
            return redirect(reverse('lista_integracoes'))
    else:
        form = IntegracaoFuncionarioForm()
    return render(request, 'funcionarios/integracao/cadastrar_integracao.html', {'form': form})

# View para excluir uma integração
def excluir_integracao(request, integracao_id):
    integracao = get_object_or_404(IntegracaoFuncionario, id=integracao_id)
    if request.method == 'POST':
        integracao.delete()
        messages.success(request, 'Integração excluída com sucesso.')
    return redirect(reverse('lista_integracoes'))

def editar_integracao(request, integracao_id):
    integracao = get_object_or_404(IntegracaoFuncionario, id=integracao_id)
    if request.method == 'POST':
        form = IntegracaoFuncionarioForm(request.POST, instance=integracao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Integração atualizada com sucesso.')
            return redirect(reverse('lista_integracoes'))
    else:
        form = IntegracaoFuncionarioForm(instance=integracao)
    return render(request, 'funcionarios/integracao/editar_integracao.html', {'form': form, 'integracao': integracao})

def imprimir_integracao(request, integracao_id):
    try:
        integracao = IntegracaoFuncionario.objects.get(id=integracao_id)
    except IntegracaoFuncionario.DoesNotExist:
        raise Http404("Integração de Funcionário não encontrada.")
    
    return render(request, 'funcionarios/integracao/imprimir_integracao.html', {'integracao': integracao})