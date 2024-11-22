from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from Funcionario.models import ListaPresenca, Funcionario, AvaliacaoTreinamento
from Funcionario.forms import ListaPresencaForm
from Funcionario.templatetags.conversores import horas_formatadas
from django.core.paginator import Paginator

import openpyxl




# Função lista_presenca
def lista_presenca(request):
    listas_presenca = ListaPresenca.objects.all().order_by('-data_realizacao')  # Ordenação decrescente pela data

    # Filtros
    instrutores = ListaPresenca.objects.values_list('instrutor', flat=True).distinct()
    instrutor_filtro = request.GET.get('instrutor')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    if instrutor_filtro:
        listas_presenca = listas_presenca.filter(instrutor=instrutor_filtro)

    if data_inicio and data_fim:
        listas_presenca = listas_presenca.filter(data_realizacao__range=[data_inicio, data_fim])

    # Paginação
    registros_por_pagina = int(request.GET.get('registros_por_pagina', 10))  # Valor padrão é 10
    paginator = Paginator(listas_presenca, registros_por_pagina)
    pagina = request.GET.get('pagina')
    listas_presenca = paginator.get_page(pagina)

    return render(request, 'lista_presenca/lista_presenca.html', {
        'listas_presenca': listas_presenca,
        'instrutores': instrutores,
        'registros_por_pagina': registros_por_pagina
    })


def cadastrar_lista_presenca(request):
    if request.method == 'POST':
        form = ListaPresencaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lista_presenca')
        else:
            print(form.errors)
    else:
        form = ListaPresencaForm()

    # Mantém locais de trabalho e treinamentos como estão
    locais_trabalho = Funcionario.objects.values('local_trabalho').distinct()
    
    # Filtra apenas funcionários com status "Ativo"
    funcionarios = Funcionario.objects.filter(status="Ativo").select_related('cargo_atual')
    
    # Carrega os treinamentos com suas relações
    treinamentos = AvaliacaoTreinamento.objects.select_related('treinamento').all()

    context = {
        'form': form,
        'locais_trabalho': locais_trabalho,
        'funcionarios': funcionarios,
        'treinamentos': treinamentos
    }

    return render(request, 'lista_presenca/cadastrar_lista_presenca.html', context)





def editar_lista_presenca(request, id):
    lista = get_object_or_404(ListaPresenca, id=id)

    if request.method == 'POST':
        form = ListaPresencaForm(request.POST, request.FILES, instance=lista)
        if form.is_valid():
            # Cálculo da duração quando o formulário é salvo
            horario_inicio = form.cleaned_data.get('horario_inicio')
            horario_fim = form.cleaned_data.get('horario_fim')
            if horario_inicio and horario_fim:
                today = datetime.today().date()
                inicio = datetime.combine(today, horario_inicio)
                fim = datetime.combine(today, horario_fim)
                duration = (fim - inicio).total_seconds() / 3600
                lista.duracao = round(duration, 2)  # Converte para ponto decimal com duas casas
            
            # Garante que a duração seja um número decimal
            lista.duracao = float(str(lista.duracao).replace(',', '.'))
            lista.save()
            return redirect('lista_presenca')
    else:
        # Converte a data para o formato ISO 8601 (yyyy-MM-dd)
        if lista.data_realizacao:
            lista.data_realizacao = lista.data_realizacao.strftime('%Y-%m-%d')
        
        # Certifica-se de que a duração está em formato de ponto decimal
        if lista.duracao:
            lista.duracao = round(float(lista.duracao), 2)
            
        form = ListaPresencaForm(instance=lista)

    locais_trabalho = Funcionario.objects.values('local_trabalho').distinct()
    funcionarios = Funcionario.objects.all()
    treinamentos = AvaliacaoTreinamento.objects.select_related('treinamento').all()

    return render(request, 'lista_presenca/edit_lista_presenca.html', {
        'form': form,
        'locais_trabalho': locais_trabalho,
        'funcionarios': funcionarios,
        'treinamentos': treinamentos,
    })




def excluir_lista_presenca(request, id):
    lista = get_object_or_404(ListaPresenca, id=id)
    lista.delete()  # Remove a lista de presença do banco de dados
    return redirect('lista_presenca')  # Redireciona para a lista de presenças


def visualizar_lista_presenca(request, lista_id):
    lista = get_object_or_404(ListaPresenca, id=lista_id)
    return render(request, 'lista_presenca/visualizar_lista_presenca.html', {'lista': lista})

def imprimir_lista_presenca(request, lista_id):
    lista = get_object_or_404(ListaPresenca, id=lista_id)

    # Formata a data de realização
    data_realizacao = lista.data_realizacao.strftime('%d/%m/%Y') if lista.data_realizacao else ''

    return render(request, 'lista_presenca/imprimir_lista_presenca.html', {
        'lista': lista,
        'data_realizacao': data_realizacao,
    })

def exportar_listas_presenca(request):
    listas_presenca = ListaPresenca.objects.all()

    # Filtros
    instrutor_filtro = request.GET.get('instrutor')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    if instrutor_filtro:
        listas_presenca = listas_presenca.filter(instrutor=instrutor_filtro)

    if data_inicio and data_fim:
        listas_presenca = listas_presenca.filter(data_realizacao__range=[data_inicio, data_fim])

    # Criar o arquivo Excel
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'Listas de Presença'

    # Cabeçalhos
    worksheet.append([
        'ID', 'Assunto', 'Data', 'Duração (Horas)', 'Instrutor', 'Necessita Avaliação', 'Participantes'
    ])

    # Adicionar os dados
    for lista in listas_presenca:
        participantes = ', '.join([p.nome for p in lista.participantes.all()])
        worksheet.append([
            lista.id,
            lista.assunto,
            lista.data_realizacao.strftime('%d/%m/%Y') if lista.data_realizacao else '',
            lista.duracao,
            lista.instrutor,
            'Sim' if lista.necessita_avaliacao else 'Não',
            participantes
        ])

    # Configurar a resposta para download
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Listas_de_Presenca.xlsx'

    workbook.save(response)
    return response