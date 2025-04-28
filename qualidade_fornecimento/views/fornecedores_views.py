# qualidade_fornecimento/views/fornecedores_views.py
from datetime import timedelta

import openpyxl  # ou pandas, conforme sua preferência
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from qualidade_fornecimento.forms import FornecedorForm
from qualidade_fornecimento.models import FornecedorQualificado


def lista_fornecedores(request):
    fornecedores_qs = FornecedorQualificado.objects.all().order_by("-atualizado_em")

    # Captura os filtros enviados via GET
    data_inicial = request.GET.get("data_inicial")
    data_final = request.GET.get("data_final")
    produto = request.GET.get("produto")
    certificacao = request.GET.get("certificacao")
    status_filter = request.GET.get("status")

    if data_inicial:
        fornecedores_qs = fornecedores_qs.filter(data_homologacao__gte=data_inicial)
    if data_final:
        fornecedores_qs = fornecedores_qs.filter(data_homologacao__lte=data_final)
    if produto:
        fornecedores_qs = fornecedores_qs.filter(produto_servico=produto)
    if certificacao:
        fornecedores_qs = fornecedores_qs.filter(tipo_certificacao=certificacao)
    if status_filter:
        fornecedores_qs = fornecedores_qs.filter(status=status_filter)

    # Extração dos valores distintos para os filtros
    filter_produtos = sorted(
        set(fornecedores_qs.values_list("produto_servico", flat=True))
    )
    filter_certificacoes = sorted(
        set(fornecedores_qs.values_list("tipo_certificacao", flat=True))
    )
    filter_status = sorted(set(fornecedores_qs.values_list("status", flat=True)))

    # Paginação: 10 itens por página
    paginator = Paginator(fornecedores_qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Dados para os cards
    total_fornecedores = fornecedores_qs.count()
    total_vencidas = fornecedores_qs.filter(
        vencimento_certificacao__lt=timezone.now().date()
    ).count()
    total_alto_risco = fornecedores_qs.filter(risco="Alto").count()

    current_date = timezone.now().date()
    current_date_plus_30 = current_date + timedelta(days=30)
    total_proximas = fornecedores_qs.filter(
        vencimento_certificacao__gte=current_date,
        vencimento_certificacao__lte=current_date_plus_30,
    ).count()

    context = {
        "fornecedores_paginados": page_obj,
        "total_fornecedores": total_fornecedores,
        "total_vencidas": total_vencidas,
        "total_alto_risco": total_alto_risco,
        "total_proximas": total_proximas,
        "current_date": current_date,
        "current_date_plus_30": current_date_plus_30,
        "filter_produtos": filter_produtos,
        "filter_certificacoes": filter_certificacoes,
        "filter_status": filter_status,
    }

    return render(request, "fornecedores/lista_fornecedores.html", context)


import logging

from django.contrib import messages

logger = logging.getLogger(__name__)


@login_required
def cadastrar_fornecedor(request):
    if request.method == "POST":
        form = FornecedorForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Fornecedor cadastrado com sucesso!")
                return redirect("lista_fornecedores")
            except Exception as e:
                logger.error("Erro ao salvar o fornecedor: %s", e, exc_info=True)
                messages.error(request, f"Erro ao salvar o fornecedor: {e}")
        else:
            error_messages = []
            for field, errors in form.errors.items():
                error_messages.append(f"{field}: {', '.join(errors)}")
            messages.error(
                request, "Erro ao cadastrar o fornecedor. " + " | ".join(error_messages)
            )
    else:
        form = FornecedorForm()

    return render(
        request, "fornecedores/form_fornecedor.html", {"form": form, "modo": "Cadastro"}
    )


@login_required
def editar_fornecedor(request, id):
    fornecedor = get_object_or_404(FornecedorQualificado, id=id)
    if request.method == "POST":
        form = FornecedorForm(request.POST, request.FILES, instance=fornecedor)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Fornecedor atualizado com sucesso!")
                return redirect("lista_fornecedores")
            except Exception as e:
                logger.error("Erro ao salvar o fornecedor: %s", e, exc_info=True)
                messages.error(request, f"Erro ao salvar o fornecedor: {e}")
        else:
            error_messages = []
            for field, errors in form.errors.items():
                error_messages.append(f"{field}: {', '.join(errors)}")
            messages.error(
                request, "Erro ao atualizar o fornecedor. " + " | ".join(error_messages)
            )
    else:
        form = FornecedorForm(instance=fornecedor)

    return render(
        request, "fornecedores/form_fornecedor.html", {"form": form, "modo": "Edição"}
    )


@login_required
def excluir_fornecedor(request, id):
    fornecedor = get_object_or_404(FornecedorQualificado, id=id)
    if request.method == "POST":
        fornecedor.delete()
        messages.success(request, "Fornecedor excluído com sucesso!")
        return redirect("lista_fornecedores")
    return render(
        request, "fornecedores/excluir_fornecedor.html", {"fornecedor": fornecedor}
    )


@login_required
def visualizar_fornecedor(request, id):
    fornecedor = get_object_or_404(FornecedorQualificado, id=id)
    context = {"fornecedor": fornecedor, "now": timezone.now()}
    return render(request, "fornecedores/visualizar_fornecedor_pdf.html", context)


@login_required
def importar_excel_fornecedores(request):
    if request.method == "POST":
        excel_file = request.FILES.get("excel_file")
        if excel_file:
            try:
                workbook = openpyxl.load_workbook(excel_file)
                sheet = workbook.active
                row_count = sheet.max_row
                logger.info(
                    "Total de linhas no Excel (incluindo cabeçalho): %s", row_count
                )

                # Itera sobre as linhas, ignorando o cabeçalho
                for index, row in enumerate(
                    sheet.iter_rows(min_row=2, values_only=True), start=2
                ):
                    # Verifica se a linha não está vazia
                    if not any(row):
                        logger.info("Linha %s vazia, pulando", index)
                        continue
                    # Exemplo de extração de valores:
                    nome = row[0]
                    produto_servico = row[1]
                    data_homologacao = row[2]
                    tipo_certificacao = row[3]
                    vencimento_certificacao = row[4]
                    risco = row[5]
                    data_avaliacao_risco = row[6]
                    tipo_formulario = row[7]
                    data_auditoria = row[8]
                    nota_auditoria = row[9]
                    especialista_nome = row[10]
                    especialista_contato = row[11]

                    logger.info("Linha %s: %s, %s", index, nome, produto_servico)

                    # Aqui você pode criar o objeto. Exemplo simples:
                    fornecedor, created = FornecedorQualificado.objects.get_or_create(
                        nome=nome,
                        defaults={
                            "produto_servico": produto_servico,
                            "data_homologacao": data_homologacao,
                            "tipo_certificacao": tipo_certificacao,
                            "vencimento_certificacao": vencimento_certificacao,
                            "risco": risco,
                            "data_avaliacao_risco": data_avaliacao_risco,
                            "tipo_formulario": tipo_formulario,
                            "data_auditoria": data_auditoria,
                            "nota_auditoria": nota_auditoria,
                            "especialista_nome": especialista_nome,
                            "especialista_contato": especialista_contato,
                        },
                    )
                    if not created:
                        # Se o fornecedor já existe, você pode atualizar os campos se desejar
                        fornecedor.produto_servico = produto_servico
                        fornecedor.data_homologacao = data_homologacao
                        fornecedor.tipo_certificacao = tipo_certificacao
                        fornecedor.vencimento_certificacao = vencimento_certificacao
                        fornecedor.risco = risco
                        fornecedor.data_avaliacao_risco = data_avaliacao_risco
                        fornecedor.tipo_formulario = tipo_formulario
                        fornecedor.data_auditoria = data_auditoria
                        fornecedor.nota_auditoria = nota_auditoria
                        fornecedor.especialista_nome = especialista_nome
                        fornecedor.especialista_contato = especialista_contato
                        fornecedor.save()
                messages.success(request, "Dados importados com sucesso!")
                return redirect("lista_fornecedores")
            except Exception as e:
                logger.error("Erro ao importar dados: %s", e, exc_info=True)
                messages.error(request, f"Erro ao importar dados: {e}")
        else:
            messages.error(request, "Selecione um arquivo Excel para importar.")
    return render(request, "fornecedores/importar_excel.html")
