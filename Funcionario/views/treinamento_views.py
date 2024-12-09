from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from io import BytesIO
from xhtml2pdf import pisa
from Funcionario.models import Treinamento, Funcionario, IntegracaoFuncionario
from Funcionario.forms import TreinamentoForm
from django.utils import timezone
from django.core.paginator import Paginator
import csv



def lista_treinamentos(request):
    tipo = request.GET.get('tipo')
    status = request.GET.get('status')
    funcionario_id = request.GET.get('funcionario')  # Obtém o ID do funcionário selecionado
    ordenacao = request.GET.get('ordenacao', 'nome_curso')  # Alterado para evitar problema com ManyToMany

    # Atualização para ManyToMany
    treinamentos = Treinamento.objects.prefetch_related('funcionarios').all()

    if tipo:
        treinamentos = treinamentos.filter(tipo=tipo)
    if status:
        treinamentos = treinamentos.filter(status=status)
    if funcionario_id:
        treinamentos = treinamentos.filter(funcionarios__id=funcionario_id)


    # Filtrar funcionários que estão na lista de treinamentos
    funcionarios = Funcionario.objects.filter(
        id__in=treinamentos.values_list('funcionarios__id', flat=True)
    ).distinct()

    # Paginação
    paginator = Paginator(treinamentos, 10)  # 10 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Dados para os cards
    total_treinamentos = treinamentos.count()
    treinamentos_concluidos = treinamentos.filter(status='concluido').count()
    treinamentos_em_andamento = treinamentos.filter(status='cursando').count()
    treinamentos_requeridos = treinamentos.filter(status='requerido').count()

    context = {
        'treinamentos': page_obj,
        'page_obj': page_obj,
        'funcionarios': funcionarios,  # Apenas funcionários relacionados

        'tipos_treinamento': Treinamento.TIPO_TREINAMENTO_CHOICES,
        'ordenacao': ordenacao,
        'total_treinamentos': total_treinamentos,
        'treinamentos_concluidos': treinamentos_concluidos,
        'treinamentos_em_andamento': treinamentos_em_andamento,
        'treinamentos_requeridos': treinamentos_requeridos,
    }
    
    return render(request, 'treinamentos/lista_treinamentos.html', context)

def cadastrar_treinamento(request):
    if request.method == 'POST':
        form = TreinamentoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lista_treinamentos')
        else:
            print(f"Erros: {form.errors}")
            print(f"Dados enviados: {request.POST}")
    else:
        form = TreinamentoForm()
    return render(request, 'treinamentos/cadastrar_treinamento.html', {'form': form})

def editar_treinamento(request, id):
    treinamento = get_object_or_404(Treinamento, id=id)
    if request.method == "POST":
        form = TreinamentoForm(request.POST, request.FILES, instance=treinamento)
        if form.is_valid():
            form.save()
            return redirect('lista_treinamentos')
    else:
        form = TreinamentoForm(instance=treinamento)
    
    # Forçar o formato para garantir que seja compreendido pelo campo de data
    if form.instance.data_inicio:
        form.initial['data_inicio'] = form.instance.data_inicio.strftime('%Y-%m-%d')
    if form.instance.data_fim:
        form.initial['data_fim'] = form.instance.data_fim.strftime('%Y-%m-%d')

    return render(request, 'treinamentos/editar_treinamento.html', {'form': form})

def excluir_treinamento(request, id):
    treinamento = get_object_or_404(Treinamento, id=id)
    if request.method == "POST":
        treinamento.delete()
        return redirect('lista_treinamentos')
    return render(request, 'treinamentos/excluir_treinamento.html', {'treinamento': treinamento})


def visualizar_treinamento(request, treinamento_id):
    treinamento = get_object_or_404(Treinamento, id=treinamento_id)
    return render(request, 'treinamentos/visualizar_treinamento.html', {'treinamento': treinamento})


def imprimir_f003(request, funcionario_id):
    # Obtém o funcionário pelo ID
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)

    # Busca os treinamentos associados ao funcionário
    treinamentos = Treinamento.objects.filter(funcionarios=funcionario)

    # Busca a integração associada ao funcionário
    integracao = IntegracaoFuncionario.objects.filter(funcionario=funcionario).first()

    # Obtém a data da última atualização dos treinamentos
    ultima_atualizacao = treinamentos.order_by('-data_fim').first().data_fim if treinamentos.exists() else None

    # Debug para verificar os dados no terminal
    print(f"Funcionário: {funcionario}")
    print(f"Treinamentos: {list(treinamentos)}")
    print(f"Data de Integração: {integracao.data_integracao if integracao else 'Nenhuma integração encontrada'}")

    # Renderiza o template com os dados necessários
    return render(request, 'treinamentos/relatorio_f003.html', {
        'funcionario': funcionario,
        'treinamentos': treinamentos,
        'current_date': timezone.now(),
        'ultima_atualizacao': ultima_atualizacao,
        'integracao': integracao,  # Inclui a integração no contexto
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

def gerar_relatorio_f003(request):
    if request.method == 'POST':
        funcionario_id = request.POST.get('funcionario')
        
        # Busca o funcionário
        funcionario = get_object_or_404(Funcionario, id=funcionario_id)

        # Busca a integração associada ao funcionário
        integracao = IntegracaoFuncionario.objects.filter(funcionario=funcionario).first()

        # Busca os treinamentos associados ao funcionário
        treinamentos = Treinamento.objects.filter(funcionario=funcionario)

        # Debug: Verifica os dados do funcionário, integração e treinamentos
        print(f"Funcionário: {funcionario}")
        print(f"Integracao encontrada: {integracao}")
        print(f"Treinamentos encontrados: {list(treinamentos)}")

        # Cria o contexto a ser enviado ao template
        context = {
            'funcionario': funcionario,
            'treinamentos': treinamentos,
            'integracao': integracao,  # Inclui a integração no contexto
        }

        # Debug: Exibe o contexto completo
        print(f"Contexto enviado ao template: {context}")

        return render(request, 'relatorio_f003.html', context)

    
def exportar_treinamentos_csv(request):
    treinamentos = Treinamento.objects.prefetch_related('funcionarios').all()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="treinamentos.csv"'

    writer = csv.writer(response)
    writer.writerow(['Funcionários', 'Curso', 'Tipo', 'Status', 'Data Conclusão', 'Carga Horária'])

    for treinamento in treinamentos:
        funcionarios = ", ".join(func.nome for func in treinamento.funcionarios.all())
        writer.writerow([
            funcionarios,
            treinamento.nome_curso,
            treinamento.tipo,
            treinamento.status,
            treinamento.data_fim,
            treinamento.carga_horaria,
        ])

    return response



from django.db.models import Case, When, Value, CharField
from datetime import datetime


def levantamento_treinamento(request):
    filtro_departamento = request.GET.get('departamento', '')
    filtro_data_inicio = request.GET.get('data_inicio', '')
    filtro_data_fim = request.GET.get('data_fim', '')

    # Converte filtro_data_inicio para um objeto de data e extrai o ano
    ano_inicio = None
    if filtro_data_inicio:
        try:
            ano_inicio = datetime.strptime(filtro_data_inicio, '%Y-%m-%d').year
        except ValueError:
            ano_inicio = None  # Define como None se o formato for inválido

    # Filtros
    funcionarios = Funcionario.objects.all()
    if filtro_departamento:
        funcionarios = funcionarios.filter(local_trabalho=filtro_departamento)

    # Filtra os treinamentos associados aos funcionários filtrados
    treinamentos = Treinamento.objects.filter(
        funcionarios__in=funcionarios,
        status='requerido'   # Apenas treinamentos com o status "Requerido"
    )
    if filtro_data_inicio:
        treinamentos = treinamentos.filter(data_inicio__gte=filtro_data_inicio)
    if filtro_data_fim:
        treinamentos = treinamentos.filter(data_fim__lte=filtro_data_fim)

    # Determina a chefia imediata
    chefia_imediata = funcionarios.first().responsavel if funcionarios.exists() else None

    # Anotação para status da situação
    treinamentos = treinamentos.annotate(
        situacao_treinamento=Case(
            When(status='aprovado', then=Value('APROVADO')),
            When(status='reprovado', then=Value('REPROVADO')),
            default=Value('PENDENTE'),
            output_field=CharField(),
        )
    )

    # Renderiza o template
    return render(request, 'treinamentos/levantamento_treinamento.html', {
        'departamentos': Funcionario.objects.values_list('local_trabalho', flat=True).distinct(),
        'filtro_departamento': filtro_departamento,
        'filtro_data_inicio': filtro_data_inicio,
        'filtro_data_fim': filtro_data_fim,
        'ano_inicio': ano_inicio,  # Envia o ano para o template
        'treinamentos': treinamentos,
        'chefia_imediata': chefia_imediata,
    })
