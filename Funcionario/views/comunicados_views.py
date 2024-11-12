from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from Funcionario.models import Comunicado, Funcionario
from Funcionario.forms import ComunicadoForm

def lista_comunicados(request):
    # Recupera todos os comunicados
    comunicados = Comunicado.objects.all()

    # Obtenção dos filtros
    tipo = request.GET.get('tipo', '')
    departamento = request.GET.get('departamento', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')

    # Filtros com condicional
    if tipo:
        comunicados = comunicados.filter(tipo=tipo)
    if departamento:
        comunicados = comunicados.filter(departamento_responsavel__icontains=departamento)
    if data_inicio and data_fim:
        comunicados = comunicados.filter(data__range=[data_inicio, data_fim])
    elif data_inicio:
        comunicados = comunicados.filter(data__gte=data_inicio)
    elif data_fim:
        comunicados = comunicados.filter(data__lte=data_fim)

    # Contexto do template com os filtros aplicados
    context = {
        'comunicados': comunicados,
        'tipo': tipo,
        'departamento': departamento,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
    }

    return render(request, 'comunicados/lista_comunicados.html', context)
    
def imprimir_comunicado(request, id):
    comunicado = get_object_or_404(Comunicado, id=id)  # Alterado para buscar por 'id'
    return render(request, 'comunicados/imprimir_comunicado.html', {'comunicado': comunicado})

def cadastrar_comunicado(request):
    if request.method == 'POST':
        form = ComunicadoForm(request.POST, request.FILES)  # Inclua request.FILES aqui
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
        form = ComunicadoForm(request.POST, request.FILES, instance=comunicado)  # Inclua request.FILES aqui
        if form.is_valid():
            form.save()
            return redirect('lista_comunicados')
    else:
        form = ComunicadoForm(instance=comunicado)  # Carrega os dados existentes do banco

    return render(request, 'comunicados/editar_comunicado.html', {'form': form})


def excluir_comunicado(request, id):
    comunicado = get_object_or_404(Comunicado, id=id)
    if request.method == 'POST':
        comunicado.delete()
        messages.success(request, "Comunicado excluído com sucesso!")
        return redirect('lista_comunicados')  # Redireciona para a lista de comunicados após a exclusão
    return render(request, 'comunicados/excluir_comunicado.html', {'comunicado': comunicado})



def imprimir_assinaturas(request, id):
    comunicado = get_object_or_404(Comunicado, id=id)
    funcionarios_ativos = Funcionario.objects.filter(status='Ativo').order_by('nome')
    return render(request, 'comunicados/imprimir_assinaturas.html', {
        'comunicado': comunicado,
        'funcionarios_ativos': funcionarios_ativos
    })