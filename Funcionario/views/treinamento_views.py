# Bibliotecas padrão
import csv
from datetime import datetime
from io import BytesIO

# Django
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.utils import timezone
from xhtml2pdf import pisa

# App Interno
from Funcionario.forms import TreinamentoForm
from Funcionario.models import (
    Documento,
    Funcionario,
    IntegracaoFuncionario,
    Treinamento,
)
from Funcionario.utils.treinamento_utils import criar_ou_atualizar_avaliacao, obter_dados_relatorio_f003, obter_treinamentos_requeridos
from Funcionario.models import Departamentos


@login_required
def lista_treinamentos(request):
    tipo = request.GET.get("tipo")
    status = request.GET.get("status")
    funcionario_id = request.GET.get("funcionario")

    treinamentos = Treinamento.objects.prefetch_related("funcionarios").all()
    if tipo:
        treinamentos = treinamentos.filter(tipo=tipo)
    if status:
        treinamentos = treinamentos.filter(status=status)
    if funcionario_id:
        treinamentos = treinamentos.filter(funcionarios__id=funcionario_id)

    treinamentos = treinamentos.order_by("-data_fim")
    funcionarios = Funcionario.objects.filter(
        id__in=treinamentos.values_list("funcionarios__id", flat=True)
    ).distinct().order_by("nome")

    paginator = Paginator(treinamentos, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "treinamentos": page_obj,
        "page_obj": page_obj,
        "funcionarios": funcionarios,
        "tipos_treinamento": Treinamento.TIPO_TREINAMENTO_CHOICES,
        "ordenacao": request.GET.get("ordenacao", "nome_curso"),
        "total_treinamentos": treinamentos.count(),
        "treinamentos_concluidos": treinamentos.filter(status="concluido").count(),
        "treinamentos_em_andamento": treinamentos.filter(status="cursando").count(),
        "treinamentos_requeridos": treinamentos.filter(status="requerido").count(),
    }

    return render(request, "treinamentos/lista_treinamentos.html", context)


@login_required
def cadastrar_treinamento(request):
    if request.method == "POST":
        form = TreinamentoForm(request.POST, request.FILES)
        if form.is_valid():
            treinamento = form.save()
            criar_ou_atualizar_avaliacao(treinamento)
            return redirect("lista_treinamentos")
    else:
        form = TreinamentoForm()

    funcionarios_ativos = Funcionario.objects.filter(status="Ativo").order_by("nome")
    return render(request, "treinamentos/form_treinamento.html", {
        "form": form,
        "funcionarios": funcionarios_ativos,
    })


@login_required
def editar_treinamento(request, id):
    treinamento = get_object_or_404(Treinamento, id=id)

    if request.method == "POST":
        form = TreinamentoForm(request.POST, request.FILES, instance=treinamento)
        if form.is_valid():
            treinamento = form.save()
            criar_ou_atualizar_avaliacao(treinamento)
            return redirect("lista_treinamentos")
    else:
        form = TreinamentoForm(instance=treinamento)

    return render(request, "treinamentos/form_treinamento.html", {
        "form": form,
        "funcionarios": Funcionario.objects.filter(status="Ativo").order_by("nome"),
    })


@login_required
def excluir_treinamento(request, id):
    treinamento = get_object_or_404(Treinamento, id=id)
    if request.method == "POST":
        treinamento.delete()
        return redirect("lista_treinamentos")
    return render(request, "treinamentos/excluir_treinamento.html", {
        "treinamento": treinamento
    })


@login_required
def visualizar_treinamento(request, treinamento_id):
    treinamento = get_object_or_404(Treinamento, id=treinamento_id)
    return render(request, "treinamentos/visualizar_treinamento.html", {
        "treinamento": treinamento,
        "now": timezone.now(),
    })


@login_required
def imprimir_f003(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    treinamentos = Treinamento.objects.filter(funcionarios=funcionario)
    integracao = IntegracaoFuncionario.objects.filter(funcionario=funcionario).first()
    ultima_atualizacao = treinamentos.order_by("-data_fim").first().data_fim if treinamentos.exists() else None

    try:
        doc_f003 = Documento.objects.get(codigo="F003")
        revisao = doc_f003.revisoes.filter(status="ativo").order_by("-data_revisao").first()
        numero_formulario = f"{doc_f003.codigo} Rev.{revisao.numero_revisao}" if revisao else f"{doc_f003.codigo} Rev.00"
    except Documento.DoesNotExist:
        numero_formulario = "F003 Rev.04"

    return render(request, "treinamentos/relatorio_f003.html", {
        "funcionario": funcionario,
        "treinamentos": treinamentos,
        "current_date": timezone.now(),
        "ultima_atualizacao": ultima_atualizacao,
        "integracao": integracao,
        "numero_formulario": numero_formulario,
    })


@login_required
def gerar_pdf(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    treinamentos = Treinamento.objects.filter(funcionarios=funcionario)

    template = get_template("relatorio_f003.html")
    html = template.render({
        "funcionario": funcionario,
        "treinamentos": treinamentos,
        "ultima_atualizacao": funcionario.updated_at,
        "is_pdf": True,
    })

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="F003 - {funcionario.nome}.pdf"'

    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), response)
    if pdf.err:
        return HttpResponse("Erro ao gerar o PDF", status=500)

    return response


@login_required
def exportar_treinamentos_csv(request):
    treinamentos = Treinamento.objects.prefetch_related("funcionarios").all()

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="treinamentos.csv"'

    writer = csv.writer(response)
    writer.writerow(["Funcionários", "Curso", "Tipo", "Status", "Data Conclusão", "Carga Horária"])

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


@login_required
def levantamento_treinamento(request):
    filtro_departamento = request.GET.get("departamento", "")
    filtro_data_inicio = request.GET.get("data_inicio", "")
    filtro_data_fim = request.GET.get("data_fim", "")

    ano_inicio = None
    if filtro_data_inicio:
        try:
            ano_inicio = datetime.strptime(filtro_data_inicio, "%Y-%m-%d").year
        except ValueError:
            ano_inicio = None

    treinamentos, chefia_imediata = obter_treinamentos_requeridos(
        filtro_departamento,
        filtro_data_inicio,
        filtro_data_fim
    )

    context = {
        "departamentos": Departamentos.objects.filter(ativo=True).order_by("nome"),
        "filtro_departamento": filtro_departamento,
        "filtro_data_inicio": filtro_data_inicio,
        "filtro_data_fim": filtro_data_fim,
        "ano_inicio": ano_inicio,
        "treinamentos": treinamentos,
        "chefia_imediata": chefia_imediata,
    }

    return render(request, "treinamentos/levantamento_treinamento.html", context)


@login_required
def gerar_relatorio_f003(request):
    if request.method == "POST":
        funcionario_id = request.POST.get("funcionario")
        funcionario, treinamentos, integracao = obter_dados_relatorio_f003(funcionario_id)

        context = {
            "funcionario": funcionario,
            "treinamentos": treinamentos,
            "integracao": integracao,
        }

        return render(request, "relatorio_f003.html", context)
