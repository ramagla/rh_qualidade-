from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from xhtml2pdf import pisa
from weasyprint import HTML
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from .models import Cargo, Revisao, Funcionario,Treinamento, ListaPresenca,AvaliacaoTreinamento,AvaliacaoDesempenho
from .forms import FuncionarioForm, CargoForm, RevisaoForm,TreinamentoForm, ListaPresencaForm,AvaliacaoTreinamentoForm,AvaliacaoForm,AvaliacaoAnualForm,AvaliacaoExperienciaForm
from django.http import JsonResponse, HttpResponse
from django.utils import timezone


@login_required
def home(request):
    return render(request, 'home.html')

# Função para listar funcionários
def lista_funcionarios(request):
    funcionarios = Funcionario.objects.all()

    # Aplicar filtro por Local de Trabalho
    local_trabalho = request.GET.get('local_trabalho')
    if local_trabalho:
        funcionarios = funcionarios.filter(local_trabalho=local_trabalho)
    
    # Aplicar filtro por Responsável
    responsavel_id = request.GET.get('responsavel')
    if responsavel_id:
        funcionarios = funcionarios.filter(responsavel=responsavel_id)
    
    # Aplicar filtro por Escolaridade
    escolaridade = request.GET.get('escolaridade')
    if escolaridade:
        funcionarios = funcionarios.filter(escolaridade=escolaridade)

    # Obter todos os locais de trabalho, responsáveis e níveis de escolaridade para o formulário de filtro
    locais_trabalho = Funcionario.objects.values_list('local_trabalho', flat=True).distinct()
    responsaveis = Funcionario.objects.filter(responsavel__isnull=False).distinct()
    niveis_escolaridade = Funcionario.objects.values_list('escolaridade', flat=True).distinct()

    return render(request, 'lista_funcionarios.html', {
        'funcionarios': funcionarios,
        'locais_trabalho': locais_trabalho,
        'responsaveis': responsaveis,
        'niveis_escolaridade': niveis_escolaridade,
    })

# Função para cadastrar funcionário
def cadastrar_funcionario(request):
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, request.FILES)  # Aceita arquivos enviados
        if form.is_valid():
            form.save()
            return redirect('lista_funcionarios')
    else:
        form = FuncionarioForm()

    return render(request, 'cadastrar_funcionario.html', {'form': form})

# Função para editar funcionário
def editar_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    
    if request.method == 'POST':
        # Inclui o request.FILES para processar o upload de arquivos
        form = FuncionarioForm(request.POST, request.FILES, instance=funcionario)
        if form.is_valid():
            form.save()
            return redirect('lista_funcionarios')
    else:
        # Criar um dicionário com os dados formatados
        initial_data = {
            'nome': funcionario.nome,
            'data_admissao': funcionario.data_admissao.strftime('%d/%m/%Y'),  # Formato Brasileiro
            'cargo_inicial': funcionario.cargo_inicial,
            'cargo_atual': funcionario.cargo_atual,
            'numero_registro': funcionario.numero_registro,
            'local_trabalho': funcionario.local_trabalho,
            'data_integracao': funcionario.data_integracao.strftime('%d/%m/%Y'),  # Formato Brasileiro
            'escolaridade': funcionario.escolaridade,
            'responsavel': funcionario.responsavel,
            'foto': funcionario.foto,  # Incluir a foto existente no formulário
            'curriculo': funcionario.curriculo  # Incluir o currículo existente no formulário
        }
        form = FuncionarioForm(initial=initial_data, instance=funcionario)

    return render(request, 'cadastrar_funcionario.html', {'form': form, 'funcionario': funcionario})


# Função para excluir funcionário
def excluir_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    funcionario.delete()
    return redirect('lista_funcionarios')

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

    return render(request, 'lista_cargos.html', {
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

def editar_cargo(request, cargo_id):
    cargo = get_object_or_404(Cargo, id=cargo_id)
    if request.method == 'POST':
        form = CargoForm(request.POST, request.FILES, instance=cargo)
        if form.is_valid():
            form.save()
            return redirect('lista_cargos')  # Redireciona para a lista de cargos após a edição
    else:
        form = CargoForm(instance=cargo)
    return render(request, 'editar_cargo.html', {'form': form})


def cadastrar_treinamento(request):
    if request.method == 'POST':
        form = TreinamentoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lista_treinamentos')  # Redirecionar para a lista de treinamentos após o cadastro
    else:
        form = TreinamentoForm()
    return render(request, 'cadastrar_treinamento.html', {'form': form})

def lista_treinamentos(request):
    # Ordena os treinamentos pela data de término (data_fim) da mais recente para a mais antiga
    treinamentos = Treinamento.objects.all().order_by('-data_fim')

    # Filtros
    funcionario_id = request.GET.get('funcionario')
    tipo_treinamento = request.GET.get('tipo')
    status = request.GET.get('status')
    categoria = request.GET.get('categoria')

    if funcionario_id:
        treinamentos = treinamentos.filter(funcionario__id=funcionario_id)
    
    if tipo_treinamento:
        treinamentos = treinamentos.filter(tipo=tipo_treinamento)
    
    if status:
        treinamentos = treinamentos.filter(status=status)
    
    if categoria:
        treinamentos = treinamentos.filter(categoria=categoria)

    # Lista de funcionários, categorias e tipos para os filtros
    funcionarios = Funcionario.objects.all()
    categorias = Treinamento.CATEGORIA_CHOICES
    tipos_treinamento = Treinamento.TIPO_TREINAMENTO_CHOICES

    context = {
        'treinamentos': Treinamento.objects.all(),
        'funcionarios': funcionarios,
        'categorias': [cat[0] for cat in categorias],
        'tipos_treinamento': [tipo[0] for tipo in tipos_treinamento],
    }

    return render(request, 'lista_treinamentos.html', context)


def editar_treinamento(request, id):
    treinamento = get_object_or_404(Treinamento, id=id)
    
    if request.method == "POST":
        form = TreinamentoForm(request.POST, request.FILES, instance=treinamento)
        if form.is_valid():
            form.save()
            return redirect('lista_treinamentos')
    else:
        form = TreinamentoForm(instance=treinamento)
        # Formatar as datas no formato 'yyyy-MM-dd' para exibição no formulário
        if treinamento.data_inicio:
            form.fields['data_inicio'].initial = treinamento.data_inicio.strftime('%Y-%m-%d')
        if treinamento.data_fim:
            form.fields['data_fim'].initial = treinamento.data_fim.strftime('%Y-%m-%d')

    return render(request, 'editar_treinamento.html', {'form': form})


def excluir_treinamento(request, id):
    treinamento = get_object_or_404(Treinamento, id=id)
    if request.method == "POST":
        treinamento.delete()
        return redirect('lista_treinamentos')

    return render(request, 'excluir_treinamento.html', {'treinamento': treinamento})


def gerar_relatorio_f003(request):
    if request.method == 'POST':
        funcionario_id = request.POST.get('funcionario')
        funcionario = get_object_or_404(Funcionario, id=funcionario_id)
        treinamentos = Treinamento.objects.filter(funcionario=funcionario)

        # Lógica para preencher o relatório com as informações do funcionário e treinamentos
        # Aqui você pode configurar para renderizar um PDF ou exibir uma visualização prévia na tela.

        context = {
            'funcionario': funcionario,
            'treinamentos': treinamentos,
        }
        return render(request, 'relatorio_f003.html', context)
    
def imprimir_f003(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    treinamentos = Treinamento.objects.filter(funcionario=funcionario)

    # Obtendo a data da última atualização
    ultima_atualizacao = treinamentos.order_by('-data_fim').first().data_fim if treinamentos.exists() else None

    return render(request, 'relatorio_f003.html', {
        'funcionario': funcionario,
        'treinamentos': treinamentos,
        'current_date': timezone.now(),
        'ultima_atualizacao': ultima_atualizacao,
    })

    # Renderiza uma página com os dados do funcionário e seus treinamentos
    return render(request, 'imprimir_f003.html', {
        'funcionario': funcionario,
        'treinamentos': treinamentos
        
    })

def gerar_pdf(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    treinamentos = Treinamento.objects.filter(funcionario=funcionario)

    template = get_template('relatorio_f003.html')
    html = template.render({
        'funcionario': funcionario,
        'treinamentos': treinamentos,
        'ultima_atualizacao': funcionario.updated_at,
        'is_pdf': True  # Adicionando esta variável para controle no template
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="F003 - {funcionario.nome}.pdf"'

    pdf = pisa.pisaDocument(BytesIO(html.encode('UTF-8')), response)
    if pdf.err:
        return HttpResponse('Erro ao gerar o PDF', status=500)

    return response

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



def avaliar_treinamento(request):
    if request.method == 'POST':
        form = AvaliacaoTreinamentoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_avaliacoes')  # Redirecionar para a lista de avaliações
    else:
        form = AvaliacaoTreinamentoForm()
    
    return render(request, 'avaliar_treinamento.html', {'form': form})

def get_conhecimento_label(i):
    labels = {
        1: "Baixo",
        2: "Médio-Baixo",
        3: "Médio",
        4: "Médio-Alto",
        5: "Alto"
    }
    return labels.get(i, "Indefinido")

def get_aplicacao_label(i):
    labels = {
        1: "Baixo",
        2: "Médio-Baixo",
        3: "Médio",
        4: "Médio-Alto",
        5: "Alto"
    }
    return labels.get(i, "Indefinido")

def get_resultados_label(i):
    labels = {
        1: "Insatisfatório",
        2: "Regular",
        3: "Bom",
        4: "Muito Bom",
        5: "Excelente"
    }
    return labels.get(i, "Indefinido")



def lista_avaliacoes(request):
    # Carregar todas as avaliações de treinamento e desempenho
    avaliacoes_treinamento = AvaliacaoTreinamento.objects.all()
    avaliacoes_desempenho = AvaliacaoDesempenho.objects.all()

    # Aplicar filtros de funcionário e datas
    funcionario_id = request.GET.get('funcionario')
    if funcionario_id:
        avaliacoes_treinamento = avaliacoes_treinamento.filter(funcionario_id=funcionario_id)
        avaliacoes_desempenho = avaliacoes_desempenho.filter(funcionario_id=funcionario_id)

    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    if data_inicio and data_fim:
        avaliacoes_treinamento = avaliacoes_treinamento.filter(data_avaliacao__range=[data_inicio, data_fim])
        avaliacoes_desempenho = avaliacoes_desempenho.filter(data_avaliacao__range=[data_inicio, data_fim])

    # Aplicar filtro por tipo de avaliação
    tipo = request.GET.get('tipo')
    if tipo:
        avaliacoes_desempenho = avaliacoes_desempenho.filter(tipo=tipo)

    # Processar status de avaliação e prazo para avaliações de treinamento
    for avaliacao in avaliacoes_treinamento:
        if avaliacao.avaliacao_geral <= 2:
            avaliacao.status_avaliacao = "Pouco Eficaz"
        elif 3 <= avaliacao.avaliacao_geral <= 4:
            avaliacao.status_avaliacao = "Eficaz"
        else:
            avaliacao.status_avaliacao = "Muito Eficaz"
        
        # Prazo de Avaliação
        prazo_avaliacao = avaliacao.data_avaliacao + timezone.timedelta(days=avaliacao.periodo_avaliacao)
        avaliacao.status_prazo = "Dentro do Prazo" if timezone.now().date() <= prazo_avaliacao else "Fora do Prazo"
    
    # Processar o tipo para avaliações de desempenho
    for avaliacao in avaliacoes_desempenho:
        if avaliacao.tipo == 'ANUAL':
            avaliacao.tipo_descricao = "Anual"
        elif avaliacao.tipo == 'EXPERIENCIA':
            avaliacao.tipo_descricao = "Experiência"
        else:
            avaliacao.tipo_descricao = "Indefinido"
    
    context = {
        'avaliacoes_treinamento': avaliacoes_treinamento,
        'avaliacoes_desempenho': avaliacoes_desempenho,
        'treinamentos': Treinamento.objects.all(),
        'funcionarios': Funcionario.objects.all(),
        'listas_presenca': ListaPresenca.objects.all(),
    }

    return render(request, 'lista_avaliacao.html', context)


# Funções para pegar os labels das opções
def get_conhecimento_label(value):
    labels = {
        1: 'Não possui conhecimento mínimo da metodologia para sua aplicação.',
        2: 'Apresenta deficiências nos conceitos, o que compromete a aplicação.',
        3: 'Possui noções básicas, mas necessita de acompanhamento e suporte na aplicação.',
        4: 'Possui domínio necessário da metodologia e a utiliza adequadamente.',
        5: 'Possui completo domínio e utiliza a metodologia com excelência.',
    }
    return labels.get(value, '')

def get_aplicacao_label(value):
    labels = {
        1: 'Está muito abaixo do esperado.',
        2: 'Aplicação está abaixo do esperado.',
        3: 'Aplicação é razoável, mas não dentro do esperado.',
        4: 'Aplicação está adequada e corresponde às expectativas.',
        5: 'Aplicação excede as expectativas.',
    }
    return labels.get(value, '')

def get_resultados_label(value):
    labels = {
        1: 'Nenhum resultado foi obtido efetivamente até o momento.',
        2: 'As melhorias obtidas estão muito abaixo do esperado.',
        3: 'As melhorias obtidas são consideráveis, mas não dentro do esperado.',
        4: 'As melhorias obtidas são boas e estão dentro do esperado.',
        5: 'As melhorias obtidas excederam as expectativas.',
    }
    return labels.get(value, '')

# Função de cadastro da avaliação
def cadastrar_avaliacao(request):
    funcionarios = Funcionario.objects.all()
    listas_presenca = ListaPresenca.objects.all()

    opcoes_conhecimento = AvaliacaoTreinamento.OPCOES_CONHECIMENTO
    opcoes_aplicacao = AvaliacaoTreinamento.OPCOES_APLICACAO
    opcoes_resultados = AvaliacaoTreinamento.OPCOES_RESULTADOS

    if request.method == 'POST':
        # Processar os dados do formulário
        funcionario_id = request.POST.get('funcionario')
        lista_presenca_id = request.POST.get('treinamento')
        data_avaliacao = request.POST.get('data_avaliacao')
        periodo_avaliacao = request.POST.get('periodo_avaliacao')
        conhecimento = request.POST.get('conhecimento')
        aplicacao = request.POST.get('aplicacao')
        resultados = request.POST.get('resultados')
        responsavel_1 = request.POST.get('responsavel1')
        cargo_1 = request.POST.get('cargo1')
        responsavel_2 = request.POST.get('responsavel2')
        cargo_2 = request.POST.get('cargo2')
        responsavel_3 = request.POST.get('responsavel3')
        cargo_3 = request.POST.get('cargo3')
        descricao_melhorias = request.POST.get('melhorias')

        funcionario = get_object_or_404(Funcionario, id=funcionario_id)
        lista_presenca = get_object_or_404(ListaPresenca, id=lista_presenca_id)

        # Cálculo da avaliação geral
        total_pontos = int(conhecimento) + int(aplicacao) + int(resultados)
        if 3 <= total_pontos <= 7:
            avaliacao_geral = 1  # Pouco eficaz
        elif 8 <= total_pontos <= 11:
            avaliacao_geral = 3  # Eficaz
        else:
            avaliacao_geral = 5  # Muito eficaz

        # Criação da nova avaliação com dados completos
        AvaliacaoTreinamento.objects.create(
            funcionario=funcionario,
            treinamento=lista_presenca,
            data_avaliacao=data_avaliacao,
            periodo_avaliacao=periodo_avaliacao,
            pergunta_1=conhecimento,
            pergunta_2=aplicacao,
            pergunta_3=resultados,
            responsavel_1_nome=responsavel_1,
            responsavel_1_cargo=cargo_1,
            responsavel_2_nome=responsavel_2,
            responsavel_2_cargo=cargo_2,
            responsavel_3_nome=responsavel_3,
            responsavel_3_cargo=cargo_3,
            descricao_melhorias=descricao_melhorias,
            avaliacao_geral=avaliacao_geral
        )

        # Redireciona para a página de lista
        return redirect('lista_avaliacoes')

    context = {
        'funcionarios': funcionarios,
        'listas_presenca': listas_presenca,
        'opcoes_conhecimento': opcoes_conhecimento,
        'opcoes_aplicacao': opcoes_aplicacao,
        'opcoes_resultados': opcoes_resultados,
    }
    return render(request, 'cadastrar_avaliacao.html', context)





def editar_avaliacao(request, id):
    avaliacao = get_object_or_404(AvaliacaoTreinamento, id=id)
    
    if request.method == 'POST':
        form = AvaliacaoTreinamentoForm(request.POST, instance=avaliacao)
        if form.is_valid():
            form.save()
            return redirect('lista_avaliacoes')  # Redirecione para a lista de avaliações após a edição
    else:
        form = AvaliacaoTreinamentoForm(instance=avaliacao)
    
    return render(request, 'editar_avaliacao.html', {'form': form, 'avaliacao': avaliacao})

def excluir_avaliacao(request, id):
    avaliacao = get_object_or_404(AvaliacaoTreinamento, id=id)
    if request.method == "POST":
        avaliacao.delete()
        return redirect('lista_avaliacoes')  # Redireciona para a lista de avaliações após excluir
    return redirect('lista_avaliacoes')  # Redireciona caso não seja POST


def get_cargo(request, funcionario_id):
    try:
        funcionario = Funcionario.objects.get(id=funcionario_id)
        data = {
            'cargo': funcionario.cargo_atual.nome if funcionario.cargo_atual else 'Cargo não encontrado',
            'departamento': funcionario.local_trabalho or 'Departamento não encontrado',
            'responsavel': funcionario.responsavel or 'Responsável não encontrado'
        }
        return JsonResponse(data)
    except Funcionario.DoesNotExist:
        return JsonResponse({
            'cargo': 'Não encontrado', 
            'departamento': 'Não encontrado',
            'responsavel': 'Não encontrado'
        }, status=404)


def lista_avaliacao_desempenho(request):
    # Recupera todas as avaliações, tanto do tipo 'ANUAL' quanto 'EXPERIENCIA'
    avaliacoes = AvaliacaoDesempenho.objects.all()  # Isso recupera todas as avaliações

    # Se você precisar filtrar por funcionário ou data, adicione lógica aqui
    funcionario_id = request.GET.get('funcionario')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    if funcionario_id:
        avaliacoes = avaliacoes.filter(funcionario_id=funcionario_id)
    if data_inicio and data_fim:
        avaliacoes = avaliacoes.filter(data_avaliacao__range=[data_inicio, data_fim])

    return render(request, 'lista_avaliacao_desempenho.html', {
        'avaliacoes': avaliacoes,
        'funcionarios': Funcionario.objects.all(),  # Para o filtro
    })


def cadastrar_avaliacao_experiencia(request):
    funcionarios = Funcionario.objects.all()  # Busca todos os funcionários

    if request.method == 'POST':
        form = AvaliacaoExperienciaForm(request.POST)
        if form.is_valid():
            form.save()  # Salva a avaliação
            return redirect('lista_avaliacao_desempenho')  # Redireciona para a lista após salvar
        else:
            print(form.errors)  # Adicione esta linha para verificar erros no console

    else:
        form = AvaliacaoExperienciaForm()

    return render(request, 'cadastrar_avaliacao_experiencia.html', {'form': form, 'funcionarios': funcionarios})

def cadastrar_avaliacao_anual(request):
    if request.method == 'POST':
        form = AvaliacaoAnualForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_avaliacao_desempenho')  # Redireciona para a lista após salvar
    else:
        form = AvaliacaoAnualForm()

    funcionarios = Funcionario.objects.all()  # Pegar todos os funcionários

    return render(request, 'cadastrar_avaliacao_anual.html', {
        'form': form,
        'funcionarios': funcionarios
    })


def editar_avaliacao_desempenho(request, id):
    avaliacao = get_object_or_404(AvaliacaoDesempenho, id=id)
    
    if request.method == 'POST':
        form = AvaliacaoForm(request.POST, instance=avaliacao)
        if form.is_valid():
            form.save()
            return redirect('lista_avaliacao_desempenho')  # Redireciona para a lista após edição
    else:
        form = AvaliacaoForm(instance=avaliacao)
    
    return render(request, 'editar_avaliacao_desempenho.html', {'form': form, 'avaliacao': avaliacao})

def excluir_avaliacao_desempenho(request, id):
    avaliacao = get_object_or_404(AvaliacaoDesempenho, id=id)
    if request.method == "POST":
        avaliacao.delete()
        return redirect('lista_avaliacao_desempenho')  # Redireciona para a lista após a exclusão
    return redirect('lista_avaliacao_desempenho')

