from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from io import BytesIO
from xhtml2pdf import pisa
from Funcionario.models import Treinamento, Funcionario
from Funcionario.forms import TreinamentoForm
from django.utils import timezone

def lista_treinamentos(request):
    tipo = request.GET.get('tipo')
    status = request.GET.get('status')
    
    treinamentos = Treinamento.objects.all().order_by('-data_fim')
    
    if tipo:
        treinamentos = treinamentos.filter(tipo=tipo)
    if status:
        treinamentos = treinamentos.filter(status=status)
    
    context = {
        'treinamentos': treinamentos,
        'funcionarios': Funcionario.objects.all(),
        'tipos_treinamento': Treinamento.TIPO_TREINAMENTO_CHOICES,
    }
    return render(request, 'treinamentos/lista_treinamentos.html', context)

def cadastrar_treinamento(request):
    if request.method == 'POST':
        form = TreinamentoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lista_treinamentos')
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
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    treinamentos = Treinamento.objects.filter(funcionario=funcionario)

    # Obtendo a data da última atualização
    ultima_atualizacao = treinamentos.order_by('-data_fim').first().data_fim if treinamentos.exists() else None

    return render(request, 'treinamentos/relatorio_f003.html', {
        'funcionario': funcionario,
        'treinamentos': treinamentos,
        'current_date': timezone.now(),
        'ultima_atualizacao': ultima_atualizacao,
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
        funcionario = get_object_or_404(Funcionario, id=funcionario_id)
        treinamentos = Treinamento.objects.filter(funcionario=funcionario)

        # Lógica para preencher o relatório com as informações do funcionário e treinamentos
        # Aqui você pode configurar para renderizar um PDF ou exibir uma visualização prévia na tela.

        context = {
            'funcionario': funcionario,
            'treinamentos': treinamentos,
        }
        return render(request, 'relatorio_f003.html', context)