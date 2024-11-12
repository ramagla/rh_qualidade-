from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from Funcionario.models import Comunicado
from Funcionario.forms import ComunicadoForm

def lista_comunicados(request):
    comunicados = Comunicado.objects.all()  # Certifique-se de que todos os comunicados são recuperados corretamente
    return render(request, 'comunicados/lista_comunicados.html', {'comunicados': comunicados})

def imprimir_comunicado(request, id):
    comunicado = get_object_or_404(Comunicado, id=id)  # Alterado para buscar por 'id'
    return render(request, 'comunicados/imprimir_comunicado.html', {'comunicado': comunicado})

def cadastrar_comunicado(request):
    if request.method == 'POST':
        form = ComunicadoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Comunicado cadastrado com sucesso!")
            return redirect('lista_comunicados')
    else:
        form = ComunicadoForm()
    return render(request, 'comunicados/cadastrar_comunicado.html', {'form': form})

def visualizar_comunicado(request, id):  # Alterado para 'id'
    comunicado = get_object_or_404(Comunicado, id=id)  # Alterado para 'id'
    return render(request, 'comunicados/visualizar_comunicado.html', {'comunicado': comunicado})

def editar_comunicado(request, id):
    comunicado = get_object_or_404(Comunicado, id=id)
    
    if request.method == 'POST':
        form = ComunicadoForm(request.POST, instance=comunicado)
        if form.is_valid():
            form.save()
            return redirect('lista_comunicados')
    else:
        form = ComunicadoForm(instance=comunicado)  # Isso carrega os dados do banco
    
    return render(request, 'comunicados/editar_comunicado.html', {'form': form})

def excluir_comunicado(request, id):
    comunicado = get_object_or_404(Comunicado, id=id)
    if request.method == 'POST':
        comunicado.delete()
        messages.success(request, "Comunicado excluído com sucesso!")
        return redirect('lista_comunicados')  # Redireciona para a lista de comunicados após a exclusão
    return render(request, 'comunicados/excluir_comunicado.html', {'comunicado': comunicado})