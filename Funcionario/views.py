from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from xhtml2pdf import pisa
from weasyprint import HTML

from django.contrib.auth.decorators import login_required
from .models import Cargo, Revisao, Funcionario,Treinamento
from .forms import FuncionarioForm, CargoForm, RevisaoForm,TreinamentoForm
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
        'treinamentos': treinamentos,
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
