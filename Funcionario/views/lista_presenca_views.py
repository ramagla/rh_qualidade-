from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from Funcionario.models import ListaPresenca, Funcionario, AvaliacaoTreinamento, Treinamento
from Funcionario.forms import ListaPresencaForm
from Funcionario.templatetags.conversores import horas_formatadas
from django.core.paginator import Paginator
from django.db import transaction


import openpyxl




# Função lista_presenca
def lista_presenca(request):
    listas_presenca = ListaPresenca.objects.all().order_by('-data_inicio')  # Substituído para data_inicio

    
    # Filtros
    instrutores = ListaPresenca.objects.values_list('instrutor', flat=True).distinct()
    instrutor_filtro = request.GET.get('instrutor')
    situacao_filtro = request.GET.get('situacao')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    if instrutor_filtro:
        listas_presenca = listas_presenca.filter(instrutor=instrutor_filtro)

    if situacao_filtro:
        listas_presenca = listas_presenca.filter(situacao=situacao_filtro)


    if data_inicio and data_fim:
        listas_presenca = listas_presenca.filter(data_inicio__gte=data_inicio, data_fim__lte=data_fim)

    # Paginação
    registros_por_pagina = int(request.GET.get('registros_por_pagina', 10))  # Valor padrão é 10
    paginator = Paginator(listas_presenca, registros_por_pagina)
    pagina = request.GET.get('pagina')
    listas_presenca = paginator.get_page(pagina)

    return render(request, 'lista_presenca/lista_presenca.html', {
        'listas_presenca': listas_presenca,
        'instrutores': instrutores,
        'registros_por_pagina': registros_por_pagina,
        'situacao_opcoes': ListaPresenca.SITUACAO_CHOICES,

        
    })


def cadastrar_lista_presenca(request):
    if request.method == 'POST':
        form = ListaPresencaForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                lista_presenca = form.save()
                if lista_presenca.situacao == 'finalizado':
                    for participante in lista_presenca.participantes.all():
                        Treinamento.objects.create(
                            funcionario=participante,
                            tipo='interno',
                            categoria='treinamento',
                            nome_curso=lista_presenca.assunto,
                            instituicao_ensino='Bras-Mol',
                            status='concluido',
                            data_inicio=lista_presenca.data_inicio,
                            data_fim=lista_presenca.data_fim,
                            carga_horaria=lista_presenca.duracao,
                            descricao=lista_presenca.descricao,
                            situacao='aprovado',
                        )
                return redirect('lista_presenca')
    else:
        form = ListaPresencaForm()

    funcionarios = Funcionario.objects.filter(status='Ativo')
    return render(request, 'lista_presenca/cadastrar_lista_presenca.html', {
        'form': form,
        'funcionarios': funcionarios,
    })


# Função editar_lista_presenca
def editar_lista_presenca(request, id):
    lista = get_object_or_404(ListaPresenca, id=id)

    if request.method == 'POST':
        form = ListaPresencaForm(request.POST, request.FILES, instance=lista)
        if form.is_valid():
            with transaction.atomic():
                lista = form.save()
                if lista.situacao == 'finalizado':
                    for participante in lista.participantes.all():
                        Treinamento.objects.create(
                            funcionario=participante,
                            tipo='interno',
                            categoria='treinamento',
                            nome_curso=lista.assunto,
                            instituicao_ensino='Bras-Mol',
                            status='concluido',
                            data_inicio=lista.data_inicio,
                            data_fim=lista.data_fim,
                            carga_horaria=lista.duracao,
                            descricao=lista.descricao,
                            situacao='aprovado',
                        )
                return redirect('lista_presenca')
    else:
        form = ListaPresencaForm(instance=lista)

    return render(request, 'lista_presenca/edit_lista_presenca.html', {
        'form': form,
    })


# Função para excluir lista de presença
def excluir_lista_presenca(request, id):
    lista = get_object_or_404(ListaPresenca, id=id)
    lista.delete()
    return redirect('lista_presenca')

# Função para visualizar uma lista de presença
def visualizar_lista_presenca(request, lista_id):
    lista = get_object_or_404(ListaPresenca, id=lista_id)
    return render(request, 'lista_presenca/visualizar_lista_presenca.html', {'lista': lista})

# Função para imprimir lista de presença
def imprimir_lista_presenca(request, lista_id):
    lista = get_object_or_404(ListaPresenca, id=lista_id)

    data_inicio = lista.data_inicio.strftime('%d/%m/%Y') if lista.data_inicio else ''
    data_fim = lista.data_fim.strftime('%d/%m/%Y') if lista.data_fim else ''

    return render(request, 'lista_presenca/imprimir_lista_presenca.html', {
        'lista': lista,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
    })

# Função para exportar listas de presença
def exportar_listas_presenca(request):
    listas_presenca = ListaPresenca.objects.all()

    instrutor_filtro = request.GET.get('instrutor')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    if instrutor_filtro:
        listas_presenca = listas_presenca.filter(instrutor=instrutor_filtro)

    if data_inicio and data_fim:
        listas_presenca = listas_presenca.filter(data_inicio__gte=data_inicio, data_fim__lte=data_fim)

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'Listas de Presença'

    worksheet.append([
        'ID', 'Assunto', 'Data Início', 'Data Fim', 'Duração (Horas)', 'Instrutor', 
        'Necessita Avaliação', 'Situação', 'Participantes'
    ])

    for lista in listas_presenca:
        participantes = ', '.join([p.nome for p in lista.participantes.all()])
        worksheet.append([
            lista.id,
            lista.assunto,
            lista.data_inicio.strftime('%d/%m/%Y') if lista.data_inicio else '',
            lista.data_fim.strftime('%d/%m/%Y') if lista.data_fim else '',
            lista.duracao,
            lista.instrutor,
            'Sim' if lista.necessita_avaliacao else 'Não',
            dict(ListaPresenca.SITUACAO_CHOICES).get(lista.situacao, 'Indefinido'),
            participantes
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Listas_de_Presenca.xlsx'
    workbook.save(response)
    return response