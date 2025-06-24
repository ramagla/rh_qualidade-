from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Sum  # ✅ CORRETO
from django.core.paginator import Paginator

from qualidade_fornecimento.models.inspecao10 import Inspecao10
from qualidade_fornecimento.forms.inspecao10_form import Inspecao10Form


@login_required
@permission_required("qualidade_fornecimento.view_inspecao10", raise_exception=True)
def listar_inspecoes10(request):
    queryset = Inspecao10.objects.select_related("fornecedor", "responsavel").all()

    # 🔎 Novos filtros
    fornecedor = request.GET.get("fornecedor")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    numero_op = request.GET.get("numero_op")
    codigo_brasmol = request.GET.get("codigo_brasmol")

    if fornecedor:
        queryset = queryset.filter(fornecedor__nome__icontains=fornecedor)
    if data_inicio:
        queryset = queryset.filter(data__gte=data_inicio)
    if data_fim:
        queryset = queryset.filter(data__lte=data_fim)
    if numero_op:
        queryset = queryset.filter(numero_op__icontains=numero_op)
    if codigo_brasmol:
        queryset = queryset.filter(codigo_brasmol__icontains=codigo_brasmol)

    # 📊 Indicadores
    total_inspecoes = queryset.count()
    total_falhas = queryset.filter(status="FALHA DE BANHO").count()
    total_ok = total_inspecoes - total_falhas

    total_horas_delta = queryset.aggregate(total=Sum("tempo_gasto"))["total"] or timedelta()
    horas = total_horas_delta.total_seconds() // 3600
    minutos = (total_horas_delta.total_seconds() % 3600) // 60
    total_horas = f"{int(horas)}h {int(minutos)}min"

    # 📄 Paginação
    paginator = Paginator(queryset.order_by("-data", "-id"), 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    contexto = {
        "page_obj": page_obj,
        "total_inspecoes": total_inspecoes,
        "total_aprovadas": total_ok,
        "total_reprovadas": total_falhas,
        "total_horas": total_horas,
        "request": request,
        "fornecedores": FornecedorQualificado.objects.order_by("nome")
    }

    return render(request, "f223/lista_f223.html", contexto)


@login_required
@permission_required("qualidade_fornecimento.add_inspecao10", raise_exception=True)
def cadastrar_inspecao10(request):
    form = Inspecao10Form(request.POST or None)

    if form.is_valid():
        obj = form.save(commit=False)
        obj.responsavel = request.user  # registra quem cadastrou
        obj.save()
        messages.success(request, "Inspeção cadastrada com sucesso.")
        return redirect("listar_inspecoes10")

    return render(request, "f223/form_inspecao.html", {
        "form": form,
        "modo": "Cadastro"
    })

@login_required
@permission_required("qualidade_fornecimento.change_inspecao10", raise_exception=True)
def editar_inspecao10(request, id):
    obj = get_object_or_404(Inspecao10, id=id)
    form = Inspecao10Form(request.POST or None, instance=obj)

    if form.is_valid():
        form.save()
        messages.success(request, "Inspeção atualizada com sucesso.")
        return redirect("listar_inspecoes10")

    return render(request, "f223/form_inspecao.html", {
        "form": form,
        "modo": "Edição"
    })

from django.contrib import messages

@login_required
@permission_required("qualidade_fornecimento.delete_inspecao10", raise_exception=True)
def excluir_inspecao10(request, id):
    obj = get_object_or_404(Inspecao10, id=id)
    
    if request.method == "POST":
        obj.delete()
        messages.success(request, f"Inspeção de {obj.fornecedor} excluída com sucesso.")
    
    return redirect("listar_inspecoes10")




from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
import pandas as pd
from datetime import datetime
from qualidade_fornecimento.models.inspecao10 import Inspecao10
from qualidade_fornecimento.models.fornecedor import FornecedorQualificado

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
import pandas as pd
from datetime import datetime
from qualidade_fornecimento.models.inspecao10 import Inspecao10
from qualidade_fornecimento.models.fornecedor import FornecedorQualificado

import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
import pandas as pd
from datetime import datetime
from qualidade_fornecimento.models.inspecao10 import Inspecao10
from qualidade_fornecimento.models.fornecedor import FornecedorQualificado

@login_required
@permission_required('qualidade_fornecimento.importar_excel_inspecao10', raise_exception=True)
def importar_inspecao10_excel(request):
    if request.method == "POST" and request.FILES.get("arquivo_excel"):
        excel_file = request.FILES["arquivo_excel"]
        try:
            df = pd.read_excel(excel_file)
            df.columns = df.columns.str.strip()  # limpa espaços nos nomes das colunas

            erros = []
            importados = 0

            for index, row in df.iterrows():
                try:
                    if pd.isna(row["Data"]):
                        raise ValueError("Data está vazia.")
                    if pd.isna(row["Hora - Início"]) or pd.isna(row["Hora - Fim"]):
                        raise ValueError("Hora de início ou fim está vazia.")
                    if pd.isna(row["Fornecedor"]):
                        raise ValueError("Fornecedor está vazio.")
                    if pd.isna(row["Nº OP"]):
                        raise ValueError("Nº OP está vazio.")

                    data = pd.to_datetime(row["Data"], dayfirst=True).date()
                    hora_inicio = pd.to_datetime(str(row["Hora - Início"])).time()
                    hora_fim = pd.to_datetime(str(row["Hora - Fim"])).time()

                    fornecedor_nome = str(row["Fornecedor"]).strip()
                    fornecedor = FornecedorQualificado.objects.filter(nome__iexact=fornecedor_nome).first()
                    if not fornecedor:
                        raise ValueError(f"Fornecedor '{fornecedor_nome}' não encontrado.")

                    responsavel_raw = row.get("Responsável", "")
                    responsavel_username = str(responsavel_raw).strip().lower()
                    responsavel = User.objects.filter(username__iexact=responsavel_username).first() or request.user

                    Inspecao10.objects.create(
                        numero_op=str(row["Nº OP"]),
                        codigo_brasmol=str(row.get("Código Bras-Mol", "SEM_CODIGO")),
                        data=data,
                        fornecedor=fornecedor,
                        hora_inicio=hora_inicio,
                        hora_fim=hora_fim,
                        quantidade_total=int(row["Quantidade Total"]),
                        quantidade_nok=int(row["Quantidade Não OK"]),
                        observacoes=str(row.get("Observações", "")).strip(),
                        responsavel=responsavel,
                    )
                    importados += 1

                except Exception as e:
                    erro_msg = f"Linha {index + 2}: {e}"  # +2 por causa do cabeçalho e índice base 0
                    erros.append(erro_msg)

            # Salva os erros em um arquivo
            if erros:
                caminho_arquivo = os.path.join(
                    "C:/Projetos/RH-Qualidade/rh_qualidade/qualidade_fornecimento/views",
                    "erros_importacao_inspecao10.txt"
                )
                with open(caminho_arquivo, "w", encoding="utf-8") as f:
                    for erro in erros:
                        f.write(erro + "\n")

                messages.warning(request, f"{len(erros)} erros encontrados. Verifique o arquivo 'erros_importacao_inspecao10.txt'")
                messages.info(request, f"{importados} inspeções importadas com sucesso.")
            else:
                messages.success(request, f"{importados} inspeções importadas com sucesso!")

            return redirect("listar_inspecoes10")

        except Exception as e:
            messages.error(request, f"Erro ao processar o arquivo: {str(e)}")

    return render(request, "f223/importar_excel.html")
