from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Cargo, Revisao, Funcionario
from .forms import FuncionarioForm, CargoForm, RevisaoForm
from django.http import JsonResponse

@login_required
def home(request):
    return render(request, 'home.html')

# Função para listar funcionários
def lista_funcionarios(request):
    funcionarios = Funcionario.objects.all()
    return render(request, 'lista_funcionarios.html', {'funcionarios': funcionarios})

# Função para cadastrar funcionário
def cadastrar_funcionario(request):
    form = FuncionarioForm()
    funcionarios = Funcionario.objects.all()
    if request.method == 'POST':
        form = FuncionarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_funcionarios')  # Alterado para redirecionar à lista de funcionários

    return render(request, 'cadastrar_funcionario.html', {'form': form, 'funcionarios': funcionarios})

# Função para editar funcionário
def editar_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, instance=funcionario)
        if form.is_valid():
            form.save()
            return redirect('lista_funcionarios')
    else:
        form = FuncionarioForm(instance=funcionario)
    return render(request, 'cadastrar_funcionario.html', {'form': form})

# Função para excluir funcionário
def excluir_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    funcionario.delete()
    return redirect('lista_funcionarios')

def lista_cargos(request):
    cargos = Cargo.objects.all()
    return render(request, 'lista_cargos.html', {'cargos': cargos})

def cadastrar_cargo(request):
    if request.method == 'POST':
        form = CargoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lista_cargos')
    else:
        form = CargoForm()
    return render(request, 'cadastrar_cargo.html', {'form': form})

def historico_revisoes(request, cargo_id):
    cargo = get_object_or_404(Cargo, id=cargo_id)
    revisoes = cargo.revisoes.all()
    return render(request, 'historico_revisoes.html', {'cargo': cargo, 'revisoes': revisoes})

def adicionar_revisao(request, cargo_id):
    cargo = get_object_or_404(Cargo, id=cargo_id)
    if request.method == 'POST':
        form = RevisaoForm(request.POST)
        if form.is_valid():
            revisao = form.save(commit=False)
            revisao.cargo = cargo
            revisao.save()
            return redirect('historico_revisoes', cargo_id=cargo_id)
    else:
        form = RevisaoForm()
    return render(request, 'adicionar_revisao.html', {'form': form, 'cargo': cargo})

def obter_cargos(request, funcionario_id):
    try:
        funcionario = Funcionario.objects.get(pk=funcionario_id)
        cargos = {
            'cargo_inicial': funcionario.cargo_inicial,
            'cargo_atual': funcionario.cargo_atual
        }
        return JsonResponse(cargos)
    except Funcionario.DoesNotExist:
        return JsonResponse({'error': 'Funcionário não encontrado'}, status=404)

    
def buscar_cargos(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    data = {
        'cargo_inicial': funcionario.cargo_inicial.nome,
        'cargo_atual': funcionario.cargo_atual.nome
    }
    return JsonResponse(data)

def sucesso_view(request):
    return render(request, 'sucesso.html')