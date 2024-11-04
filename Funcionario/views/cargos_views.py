from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from ..models import Funcionario, Cargo, Revisao
from ..forms import CargoForm, RevisaoForm




def lista_cargos(request):
    cargos = Cargo.objects.all()

    # Aplicar filtro de departamento
    departamento = request.GET.get('departamento')
    if departamento:
        cargos = cargos.filter(departamento=departamento)

    # Aplicar filtro de cargo
    cargo_nome = request.GET.get('cargo')
    if cargo_nome:
        cargos = cargos.filter(nome=cargo_nome)

    # Adicionar a última revisão para cada cargo
    for cargo in cargos:
        cargo.ultima_revisao = cargo.revisoes.order_by('-data_revisao').first()

    # Obter todos os departamentos e cargos para o formulário de filtro
    todos_departamentos = Cargo.objects.values_list('departamento', flat=True).distinct()
    todos_cargos = Cargo.objects.all()

    return render(request, 'cargos/lista_cargos.html', {
        'cargos': cargos,
        'departamentos': todos_departamentos,
        'todos_cargos': todos_cargos,
    })


def cadastrar_cargo(request):
    if request.method == 'POST':
        form = CargoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lista_cargos')
    else:
        form = CargoForm()
    return render(request, 'cargos/cadastrar_cargo.html', {'form': form})

def excluir_cargo(request, cargo_id):
    cargo = get_object_or_404(Cargo, id=cargo_id)
    cargo.delete()
    messages.success(request, "Cargo excluído com sucesso!")
    return redirect('lista_cargos')

def historico_revisoes(request, cargo_id):
    cargo = get_object_or_404(Cargo, id=cargo_id)
    revisoes = cargo.revisoes.all()
    return render(request, 'cargos/historico_revisoes.html', {'cargo': cargo, 'revisoes': revisoes})

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
    return render(request, 'cargos/adicionar_revisao.html', {'form': form, 'cargo': cargo})

def excluir_revisao(request, revisao_id):
    revisao = get_object_or_404(Revisao, id=revisao_id)
    cargo_id = revisao.cargo.id  # Salva o ID do cargo antes da exclusão
    revisao.delete()
    messages.success(request, 'Revisão excluída com sucesso.')
    return redirect('historico_revisoes', cargo_id=cargo_id)

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


def editar_cargo(request, cargo_id):
    cargo = get_object_or_404(Cargo, id=cargo_id)
    if request.method == 'POST':
        form = CargoForm(request.POST, request.FILES, instance=cargo)
        if form.is_valid():
            form.save()
            return redirect('lista_cargos')  # Redireciona para a lista de cargos após a edição
    else:
        form = CargoForm(instance=cargo)
    return render(request, 'cargos/editar_cargo.html', {'form': form})

