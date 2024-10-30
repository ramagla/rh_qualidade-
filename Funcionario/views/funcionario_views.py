from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from Funcionario.models import Funcionario, Treinamento
from Funcionario.forms import FuncionarioForm
from django.utils import timezone

@login_required
def lista_funcionarios(request):
    funcionarios = Funcionario.objects.all()
    # Aplicação de filtros e preparação do contexto
    context = {
        'funcionarios': funcionarios,
        'locais_trabalho': Funcionario.objects.values_list('local_trabalho', flat=True).distinct(),
        'responsaveis': Funcionario.objects.values('responsavel').distinct(),
        'niveis_escolaridade': Funcionario.objects.values_list('escolaridade', flat=True).distinct(),
        'status_opcoes': ['Ativo', 'Inativo'],
    }
    return render(request, 'lista_funcionarios.html', context)

def visualizar_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    form = FuncionarioForm(instance=funcionario)
    for field in form.fields.values():
        field.widget.attrs['disabled'] = True
    return render(request, 'cadastrar_funcionario.html', {'form': form, 'visualizacao': True})

def cadastrar_funcionario(request):
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lista_funcionarios')
    else:
        form = FuncionarioForm()
    return render(request, 'cadastrar_funcionario.html', {'form': form})

def editar_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, request.FILES, instance=funcionario)
        if form.is_valid():
            form.save()
            messages.success(request, f'Funcionário {funcionario.nome} atualizado com sucesso!')
            return redirect('lista_funcionarios')
        else:
            messages.error(request, 'Erro ao atualizar o funcionário.')
    else:
        form = FuncionarioForm(instance=funcionario)
    return render(request, 'cadastrar_funcionario.html', {'form': form, 'funcionario': funcionario})

def excluir_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    if Treinamento.objects.filter(funcionario=funcionario).exists():
        messages.error(request, "Funcionário possui registros associados e não pode ser excluído.")
    else:
        funcionario.delete()
        messages.success(request, 'Funcionário excluído com sucesso.')
    return redirect('lista_funcionarios')
