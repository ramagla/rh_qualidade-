from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from Funcionario.models import ListaPresenca, Funcionario, AvaliacaoTreinamento, Treinamento
from Funcionario.forms import ListaPresencaForm
from Funcionario.templatetags.conversores import horas_formatadas
from django.core.paginator import Paginator
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse



import openpyxl




# Função lista_presenca
@login_required
def lista_presenca(request):
    listas_presenca = ListaPresenca.objects.all().order_by('-data_inicio')  # Ordenar por assunto


    
    # Contadores para os cards
    total_listas = listas_presenca.count()
    listas_finalizadas = listas_presenca.filter(situacao='finalizado').count()
    listas_em_andamento = listas_presenca.filter(situacao='em_andamento').count()
    listas_indefinidas = listas_presenca.filter(situacao='indefinido').count()

    # Filtros
    instrutores = ListaPresenca.objects.values_list('instrutor', flat=True).distinct()
    instrutor_filtro = request.GET.get('instrutor', None) 
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
    paginator = Paginator(listas_presenca, 10)  # 10 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    return render(request, 'lista_presenca/lista_presenca.html', {
        'listas_presenca': page_obj,
        'page_obj': page_obj,
        'listas_presenca': listas_presenca,
        'instrutores': instrutores,        
        'situacao_opcoes': ListaPresenca.SITUACAO_CHOICES,
         'total_listas': total_listas,
        'listas_finalizadas': listas_finalizadas,
        'listas_em_andamento': listas_em_andamento,
        'listas_indefinidas': listas_indefinidas,      

        
    })

@login_required
def cadastrar_lista_presenca(request):
    # Obtém treinamentos da categoria 'treinamento'
    treinamentos = Treinamento.objects.filter(categoria='treinamento')

    # Obtém funcionários ativos para exibição no dropdown de filtro
    todos_funcionarios = Funcionario.objects.filter(status='Ativo').order_by('nome')

    # Obtém locais de trabalho distintos para o dropdown de filtro
    locais_trabalho = Funcionario.objects.values_list('local_trabalho', flat=True).distinct().order_by('local_trabalho')

    # Inicia a lista de funcionários com todos os ativos
    funcionarios = todos_funcionarios

    # Aplicação de filtros via GET
    filtro_nome = request.GET.get('filtro_nome')
    filtro_local_trabalho = request.GET.get('filtro_local_trabalho')

    if filtro_nome:
        funcionarios = funcionarios.filter(id=filtro_nome)
    if filtro_local_trabalho:
        funcionarios = funcionarios.filter(local_trabalho=filtro_local_trabalho)

    # Paginação para melhorar a exibição de funcionários
    paginator = Paginator(funcionarios, 20)  # Exibe 20 funcionários por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        form = ListaPresencaForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                lista_presenca = form.save()

                # Inicializa `treinamento_existente` para evitar erro de referência
                treinamento_existente = None  

                # Se a lista de presença estiver finalizada, cria um treinamento correspondente
                if lista_presenca.situacao == 'finalizado':
                    treinamento_existente = Treinamento.objects.filter(
                        nome_curso=lista_presenca.assunto,
                        data_inicio=lista_presenca.data_inicio,
                        data_fim=lista_presenca.data_fim,
                        descricao=lista_presenca.descricao,
                        carga_horaria=lista_presenca.duracao,
                    ).first()

                    if not treinamento_existente:
                        # Cria um novo treinamento caso não exista
                        treinamento_existente = Treinamento.objects.create(
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
                            planejado='sim',
                        )

                    # Associa os participantes ao treinamento criado
                    for participante in lista_presenca.participantes.all():
                        treinamento_existente.funcionarios.add(participante)

                # Criando avaliações de eficácia apenas se necessário e se o treinamento existir
                if lista_presenca.necessita_avaliacao and treinamento_existente:
                    for participante in lista_presenca.participantes.all():
                        AvaliacaoTreinamento.objects.create(
                            funcionario=participante,
                            treinamento=treinamento_existente,
                            data_avaliacao=lista_presenca.data_inicio or date.today(),
                            pergunta_1=1,
                            pergunta_2=1,
                            pergunta_3=1,
                            periodo_avaliacao=60,  
                            responsavel_1=participante.responsavel,  
                            descricao_melhorias="Aguardando avaliação",
                            avaliacao_geral=1
                        )

                return redirect('lista_presenca')
    else:
        form = ListaPresencaForm()

    return render(request, 'lista_presenca/cadastrar_lista_presenca.html', {
        'form': form,
        'todos_funcionarios': todos_funcionarios,  # Lista para dropdown de funcionários
        'treinamentos': treinamentos,  # Treinamentos disponíveis
        'locais_trabalho': locais_trabalho,  # Locais de trabalho para filtro
        'page_obj': page_obj,  # Lista paginada de funcionários
        'filtro_nome': filtro_nome,  # Manter valores dos filtros no template
        'filtro_local_trabalho': filtro_local_trabalho,  # Manter valores dos filtros
    })




@login_required
def editar_lista_presenca(request, id):
    lista = get_object_or_404(ListaPresenca, id=id)
    treinamentos = Treinamento.objects.all()
    
    # Obtém funcionários ativos para exibição no dropdown de filtro
    todos_funcionarios = Funcionario.objects.filter(status='Ativo').order_by('nome')
    
    # Obtém locais de trabalho distintos para o dropdown de filtro
    locais_trabalho = Funcionario.objects.values_list('local_trabalho', flat=True).distinct().order_by('local_trabalho')

    # Inicia a lista de funcionários com todos os ativos
    funcionarios = todos_funcionarios

    # Aplicação de filtros via GET
    filtro_nome = request.GET.get('filtro_nome')
    filtro_local_trabalho = request.GET.get('filtro_local_trabalho')

    if filtro_nome and filtro_nome.isdigit():  # Garante que seja um número válido
        funcionarios = funcionarios.filter(id=int(filtro_nome))

    if filtro_local_trabalho:
        funcionarios = funcionarios.filter(local_trabalho__icontains=filtro_local_trabalho)  # Permite busca parcial

    # Paginação para melhorar a exibição de funcionários
    paginator = Paginator(funcionarios, 20)  # Exibe 20 funcionários por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        form = ListaPresencaForm(request.POST, request.FILES, instance=lista)
        if form.is_valid():
            with transaction.atomic():
                lista = form.save()
                lista.participantes.set(request.POST.getlist('participantes'))  # Define os funcionários selecionados


                treinamento_existente = None  # Definir a variável antes do uso

                if lista.situacao == 'finalizado':
                    treinamento_existente = Treinamento.objects.filter(
                        nome_curso=lista.assunto,
                        data_inicio=lista.data_inicio,
                        data_fim=lista.data_fim,
                        descricao=lista.descricao,
                        carga_horaria=lista.duracao,
                    ).first()

                    if not treinamento_existente:
                        treinamento_existente = Treinamento.objects.create(
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
                            planejado='sim', 
                        )

                    treinamento_existente.funcionarios.clear()
                    for participante in lista.participantes.all():
                        treinamento_existente.funcionarios.add(participante)

                if lista.necessita_avaliacao and treinamento_existente:
                    for participante in lista.participantes.all():
                        avaliacao_existente = AvaliacaoTreinamento.objects.filter(
                            funcionario=participante,
                            treinamento=treinamento_existente,
                        ).first()

                        if not avaliacao_existente:
                            AvaliacaoTreinamento.objects.create(
                                funcionario=participante,
                                treinamento=treinamento_existente,
                                data_avaliacao=lista.data_inicio or date.today(),
                                pergunta_1=1,
                                pergunta_2=1,
                                pergunta_3=1,
                                periodo_avaliacao=60,
                                responsavel_1=participante.responsavel,
                                descricao_melhorias="Aguardando avaliação",
                                avaliacao_geral=1
                            )
                        else:
                            avaliacao_existente.data_avaliacao = lista.data_inicio or date.today()
                            avaliacao_existente.pergunta_1 = 1
                            avaliacao_existente.pergunta_2 = 1
                            avaliacao_existente.pergunta_3 = 1
                            avaliacao_existente.responsavel_1 = participante.responsavel
                            avaliacao_existente.descricao_melhorias = "Aguardando avaliação"
                            avaliacao_existente.avaliacao_geral = 1
                            avaliacao_existente.save()

                return redirect('lista_presenca')
    else:      
        form = ListaPresencaForm(instance=lista)

    return render(request, 'lista_presenca/edit_lista_presenca.html', {
        'form': form,
        'todos_funcionarios': todos_funcionarios,  # Lista para dropdown de funcionários
        'treinamentos': treinamentos,  # Treinamentos disponíveis
        'locais_trabalho': locais_trabalho,  # Locais de trabalho para filtro
        'page_obj': page_obj,  # Lista paginada de funcionários
        'filtro_nome': filtro_nome,  # Manter valores dos filtros no template
        'filtro_local_trabalho': filtro_local_trabalho,  # Manter valores dos filtros
        'lista': lista,  # Passa a lista de presença para verificar os participantes já adicionados
    })



# Função para excluir lista de presença
@login_required
def excluir_lista_presenca(request, id):
    lista = get_object_or_404(ListaPresenca, id=id)
    lista.delete()
    return redirect('lista_presenca')

from django.forms import modelform_factory
@login_required
def visualizar_lista_presenca(request, lista_id):
    lista = get_object_or_404(ListaPresenca, id=lista_id)
    # Criar um formulário baseado no modelo sem campos editáveis
    ListaPresencaForm = modelform_factory(ListaPresenca, fields='__all__')
    form = ListaPresencaForm(instance=lista)
    return render(request, 'lista_presenca/visualizar_lista_presenca.html', {'form': form})


# Função para imprimir lista de presença
@login_required
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
@login_required
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