import csv
from datetime import datetime
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Case, CharField, Value, When
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.utils import timezone
from xhtml2pdf import pisa

from Funcionario.forms import TreinamentoForm
from Funcionario.models import Funcionario, IntegracaoFuncionario, Treinamento


@login_required
def lista_treinamentos(request):
    tipo = request.GET.get("tipo")
    status = request.GET.get("status")
    # Obtém o ID do funcionário selecionado
    funcionario_id = request.GET.get("funcionario")
    # Alterado para evitar problema com ManyToMany
    ordenacao = request.GET.get("ordenacao", "nome_curso")

    # Atualização para ManyToMany
    treinamentos = Treinamento.objects.prefetch_related("funcionarios").all()

    if tipo:
        treinamentos = treinamentos.filter(tipo=tipo)
    if status:
        treinamentos = treinamentos.filter(status=status)
    if funcionario_id:
        treinamentos = treinamentos.filter(funcionarios__id=funcionario_id)

    # '-data_fim' faz a ordenação decrescente
    treinamentos = treinamentos.order_by("-data_fim")

    # Filtrar funcionários que estão na lista de treinamentos
    funcionarios = (
        Funcionario.objects.filter(
            id__in=treinamentos.values_list("funcionarios__id", flat=True)
        )
        .distinct()
        .order_by("nome")
    )

    # Paginação
    paginator = Paginator(treinamentos, 10)  # 10 itens por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Dados para os cards
    total_treinamentos = treinamentos.count()
    treinamentos_concluidos = treinamentos.filter(status="concluido").count()
    treinamentos_em_andamento = treinamentos.filter(status="cursando").count()
    treinamentos_requeridos = treinamentos.filter(status="requerido").count()

    context = {
        "treinamentos": page_obj,
        "page_obj": page_obj,
        "funcionarios": funcionarios,  # Apenas funcionários relacionados
        "tipos_treinamento": Treinamento.TIPO_TREINAMENTO_CHOICES,
        "ordenacao": ordenacao,
        "total_treinamentos": total_treinamentos,
        "treinamentos_concluidos": treinamentos_concluidos,
        "treinamentos_em_andamento": treinamentos_em_andamento,
        "treinamentos_requeridos": treinamentos_requeridos,
    }

    return render(request, "treinamentos/lista_treinamentos.html", context)


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from Funcionario.forms import TreinamentoForm
from Funcionario.models import Funcionario, AvaliacaoTreinamento, Treinamento
from datetime import date


@login_required
def cadastrar_treinamento(request):
    if request.method == "POST":
        form = TreinamentoForm(request.POST, request.FILES)
        if form.is_valid():
            treinamento = form.save()

            if treinamento.necessita_avaliacao and treinamento.status == "concluido":
                for participante in treinamento.funcionarios.all():
                    AvaliacaoTreinamento.objects.get_or_create(
                        funcionario=participante,
                        treinamento=treinamento,
                        defaults={
                            "data_avaliacao": treinamento.data_fim or date.today(),
                            "periodo_avaliacao": 60,
                            "pergunta_1": None,
                            "pergunta_2": None,
                            "pergunta_3": None,
                            "responsavel_1": participante.responsavel,
                            "descricao_melhorias": "Aguardando avaliação",
                            "avaliacao_geral": None,
                        }
                    )

            return redirect("lista_treinamentos")
        else:
            print(f"Erros: {form.errors}")
            print(f"Dados enviados: {request.POST}")
    else:
        form = TreinamentoForm()

    funcionarios_ativos = Funcionario.objects.filter(status="Ativo").order_by("nome")

    return render(
        request,
        "treinamentos/form_treinamento.html",
        {
            "form": form,
            "funcionarios": funcionarios_ativos,
        },
    )


@login_required
def editar_treinamento(request, id):
    treinamento = get_object_or_404(Treinamento, id=id)
    if request.method == "POST":
        form = TreinamentoForm(request.POST, request.FILES, instance=treinamento)
        if form.is_valid():
            treinamento = form.save()

            if treinamento.necessita_avaliacao and treinamento.status == "concluido":
                for participante in treinamento.funcionarios.all():
                    avaliacao, criada = AvaliacaoTreinamento.objects.get_or_create(
                        funcionario=participante,
                        treinamento=treinamento,
                        defaults={
                            "data_avaliacao": treinamento.data_fim or date.today(),
                            "periodo_avaliacao": 60,
                            "pergunta_1": None,
                            "pergunta_2": None,
                            "pergunta_3": None,
                            "responsavel_1": participante.responsavel,
                            "descricao_melhorias": "Aguardando avaliação",
                            "avaliacao_geral": None,
                        }
                    )
                    if not criada:
                        # Atualiza campos se a avaliação já existia
                        avaliacao.data_avaliacao = treinamento.data_fim or date.today()
                        avaliacao.pergunta_1 = None
                        avaliacao.pergunta_2 = None
                        avaliacao.pergunta_3 = None
                        avaliacao.responsavel_1 = participante.responsavel
                        avaliacao.descricao_melhorias = "Aguardando avaliação"
                        avaliacao.avaliacao_geral = None
                        avaliacao.save()

            return redirect("lista_treinamentos")
    else:
        form = TreinamentoForm(instance=treinamento)
        if form.instance.data_inicio:
            form.initial["data_inicio"] = form.instance.data_inicio.strftime("%Y-%m-%d")
        if form.instance.data_fim:
            form.initial["data_fim"] = form.instance.data_fim.strftime("%Y-%m-%d")

    return render(
        request,
        "treinamentos/form_treinamento.html",
        {
            "form": form,
            "funcionarios": Funcionario.objects.filter(status="Ativo").order_by("nome"),
        },
    )



@login_required
def excluir_treinamento(request, id):
    treinamento = get_object_or_404(Treinamento, id=id)
    if request.method == "POST":
        treinamento.delete()
        return redirect("lista_treinamentos")
    return render(
        request, "treinamentos/excluir_treinamento.html", {"treinamento": treinamento}
    )


@login_required
def visualizar_treinamento(request, treinamento_id):
    treinamento = get_object_or_404(Treinamento, id=treinamento_id)
    return render(
        request,
        "treinamentos/visualizar_treinamento.html",
        {
            "treinamento": treinamento,
            "now": timezone.now(),  # adiciona data/hora atual
        },
    )


from Funcionario.models import Documento, RevisaoDoc

@login_required
def imprimir_f003(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    treinamentos = Treinamento.objects.filter(funcionarios=funcionario)
    integracao = IntegracaoFuncionario.objects.filter(funcionario=funcionario).first()
    ultima_atualizacao = treinamentos.order_by("-data_fim").first().data_fim if treinamentos.exists() else None

    # 🔎 Busca a última revisão do formulário F003
    try:
        doc_f003 = Documento.objects.get(codigo="F003")
        revisao = doc_f003.revisoes.filter(status="ativo").order_by("-data_revisao").first()
        numero_formulario = f"{doc_f003.codigo} Rev.{revisao.numero_revisao}" if revisao else f"{doc_f003.codigo} Rev.00"
    except Documento.DoesNotExist:
        numero_formulario = "F003 Rev.04"

    return render(
        request,
        "treinamentos/relatorio_f003.html",
        {
            "funcionario": funcionario,
            "treinamentos": treinamentos,
            "current_date": timezone.now(),
            "ultima_atualizacao": ultima_atualizacao,
            "integracao": integracao,
            "numero_formulario": numero_formulario,  # ⬅️ usado no rodapé
        },
    )



@login_required
def gerar_pdf(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    treinamentos = Treinamento.objects.filter(funcionario=funcionario)

    template = get_template("relatorio_f003.html")
    html = template.render(
        {
            "funcionario": funcionario,
            "treinamentos": treinamentos,
            "ultima_atualizacao": funcionario.updated_at,
            "is_pdf": True,  # Adicionando esta variável para controle no template
        }
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="F003 - {funcionario.nome}.pdf"'
    )

    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), response)
    if pdf.err:
        return HttpResponse("Erro ao gerar o PDF", status=500)

    return response


@login_required
def gerar_relatorio_f003(request):
    if request.method == "POST":
        funcionario_id = request.POST.get("funcionario")

        # Busca o funcionário
        funcionario = get_object_or_404(Funcionario, id=funcionario_id)

        # Busca a integração associada ao funcionário
        integracao = IntegracaoFuncionario.objects.filter(
            funcionario=funcionario
        ).first()

        # Busca os treinamentos associados ao funcionário
        treinamentos = Treinamento.objects.filter(funcionario=funcionario)

        # Debug: Verifica os dados do funcionário, integração e treinamentos
        print(f"Funcionário: {funcionario}")
        print(f"Integracao encontrada: {integracao}")
        print(f"Treinamentos encontrados: {list(treinamentos)}")

        # Cria o contexto a ser enviado ao template
        context = {
            "funcionario": funcionario,
            "treinamentos": treinamentos,
            "integracao": integracao,  # Inclui a integração no contexto
        }

        # Debug: Exibe o contexto completo
        print(f"Contexto enviado ao template: {context}")

        return render(request, "relatorio_f003.html", context)


@login_required
def exportar_treinamentos_csv(request):
    treinamentos = Treinamento.objects.prefetch_related("funcionarios").all()

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="treinamentos.csv"'

    writer = csv.writer(response)
    writer.writerow(
        ["Funcionários", "Curso", "Tipo", "Status", "Data Conclusão", "Carga Horária"]
    )

    for treinamento in treinamentos:
        funcionarios = ", ".join(func.nome for func in treinamento.funcionarios.all())
        writer.writerow(
            [
                funcionarios,
                treinamento.nome_curso,
                treinamento.tipo,
                treinamento.status,
                treinamento.data_fim,
                treinamento.carga_horaria,
            ]
        )

    return response



@login_required
def levantamento_treinamento(request):
    filtro_departamento = request.GET.get("departamento", "")
    filtro_data_inicio = request.GET.get("data_inicio", "")
    filtro_data_fim = request.GET.get("data_fim", "")

    # Converte filtro_data_inicio para um objeto de data e extrai o ano
    ano_inicio = None
    if filtro_data_inicio:
        try:
            ano_inicio = datetime.strptime(filtro_data_inicio, "%Y-%m-%d").year
        except ValueError:
            ano_inicio = None

    # Filtros de funcionários
    funcionarios = Funcionario.objects.all()
    if filtro_departamento:
        funcionarios = funcionarios.filter(local_trabalho=filtro_departamento)

    # Treinamentos requeridos associados aos funcionários filtrados
    treinamentos = Treinamento.objects.filter(
        funcionarios__in=funcionarios,
        status="requerido"
    )
    if filtro_data_inicio:
        treinamentos = treinamentos.filter(data_inicio__gte=filtro_data_inicio)
    if filtro_data_fim:
        treinamentos = treinamentos.filter(data_fim__lte=filtro_data_fim)

    # Determina a chefia imediata
    chefia_imediata = (
        funcionarios.first().responsavel if funcionarios.exists() else None
    )

    # Anota a situação do treinamento e ordena por nome do funcionário
    treinamentos = (
        treinamentos
        .annotate(
            situacao_treinamento=Case(
                When(status="aprovado", then=Value("APROVADO")),
                When(status="reprovado", then=Value("REPROVADO")),
                default=Value("PENDENTE"),
                output_field=CharField(),
            )
        )
        .order_by("funcionarios__nome")
    )

    return render(
        request,
        "treinamentos/levantamento_treinamento.html",
        {
            "departamentos": Funcionario.objects.values_list(
                "local_trabalho", flat=True
            ).distinct(),
            "filtro_departamento": filtro_departamento,
            "filtro_data_inicio": filtro_data_inicio,
            "filtro_data_fim": filtro_data_fim,
            "ano_inicio": ano_inicio,
            "treinamentos": treinamentos,
            "chefia_imediata": chefia_imediata,
        },
    )
