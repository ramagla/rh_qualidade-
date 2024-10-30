# lista_presenca_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from Funcionario.models import Funcionario, ListaPresenca
from Funcionario.forms import ListaPresencaForm


# Função lista_presenca
def lista_presenca(request):
    listas_presenca = ListaPresenca.objects.all()
    
    # Obter todos os instrutores únicos do modelo ListaPresenca
    instrutores = ListaPresenca.objects.values_list('instrutor', flat=True).distinct()

    # Filtro por Instrutor
    instrutor_filtro = request.GET.get('instrutor')
    if instrutor_filtro:
        listas_presenca = listas_presenca.filter(instrutor=instrutor_filtro)

    # Filtro por Período
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    if data_inicio and data_fim:
        listas_presenca = listas_presenca.filter(data_realizacao__range=[data_inicio, data_fim])

    return render(request, 'lista_presenca.html', {
        'listas_presenca': listas_presenca,
        'instrutores': instrutores,  # Passa os instrutores para o template
    })


def cadastrar_lista_presenca(request):
    if request.method == 'POST':
        form = ListaPresencaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lista_presenca')  # Certifique-se de que a URL 'lista_presenca' está definida corretamente
        else:
            # Exibe os erros do formulário no console
            print(form.errors)
    else:
        form = ListaPresencaForm()

    locais_trabalho = Funcionario.objects.values('local_trabalho').distinct()
    funcionarios = Funcionario.objects.select_related('cargo_atual')

    context = {
        'form': form,
        'locais_trabalho': locais_trabalho,
        'funcionarios': funcionarios
    }

    return render(request, 'cadastrar_lista_presenca.html', context)


def editar_lista_presenca(request, id):
    lista = get_object_or_404(ListaPresenca, id=id)

    if request.method == 'POST':
        form = ListaPresencaForm(request.POST, request.FILES, instance=lista)
        if form.is_valid():
            # Cálculo da duração quando o formulário é salvo
            horario_inicio = form.cleaned_data.get('horario_inicio')
            horario_fim = form.cleaned_data.get('horario_fim')

            if horario_inicio and horario_fim:
                # Combine time with a fixed date (e.g., today) to create a datetime object
                today = datetime.today()
                inicio = datetime.combine(today, horario_inicio)
                fim = datetime.combine(today, horario_fim)

                # Calculate duration in hours
                duration = (fim - inicio).total_seconds() / 3600  # diferença em horas
                lista.duracao = duration  # ou você pode atribuir isso diretamente ao campo no form

            lista.save()  # Salvar a lista com a nova duração
            return redirect('lista_presenca')

    else:
        form = ListaPresencaForm(instance=lista)

    locais_trabalho = Funcionario.objects.values('local_trabalho').distinct()
    funcionarios = Funcionario.objects.all()

    return render(request, 'cadastrar_lista_presenca.html', {
        'form': form,
        'locais_trabalho': locais_trabalho,
        'funcionarios': funcionarios,
    })


def excluir_lista_presenca(request, id):
    lista = get_object_or_404(ListaPresenca, id=id)
    lista.delete()  # Remove a lista de presença do banco de dados
    return redirect('lista_presenca')  # Redireciona para a lista de presenças


def visualizar_lista_presenca(request, lista_id):
    lista = get_object_or_404(ListaPresenca, id=lista_id)
    return render(request, 'visualizar_lista_presenca.html', {'lista': lista})
