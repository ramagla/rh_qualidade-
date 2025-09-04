import os
import re
from datetime import timedelta

import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from qualidade_fornecimento.forms.inspecao10_form import Inspecao10Form
from qualidade_fornecimento.models.fornecedor import FornecedorQualificado
from qualidade_fornecimento.models.inspecao10 import (
    DevolucaoServicoExterno,
    Inspecao10,
)
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo


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


@login_required
@permission_required('qualidade_fornecimento.importar_excel_inspecao10', raise_exception=True)
def importar_inspecao10_excel(request):
    """
    Importa inspeções do Excel para Inspecao10.
    Colunas esperadas:
      Data, Hora - Início, Hora - Fim, Fornecedor, Nº OP,
      Código Bras-Mol, Quantidade Total, Quantidade Não OK,
      Disposição, Observações, Responsável.
    """
    if request.method == "POST" and request.FILES.get("arquivo_excel"):
        df = pd.read_excel(request.FILES["arquivo_excel"])
        df.columns = df.columns.str.strip()

        erros = []
        importados = 0

        for idx, row in df.iterrows():
            linha = idx + 2  # para mensagens
            try:
                # validações mínimas
                if pd.isna(row["Data"]): raise ValueError("Data vazia.")
                if pd.isna(row["Hora - Início"]) or pd.isna(row["Hora - Fim"]):
                    raise ValueError("Hora início/fim vazia.")
                if pd.isna(row["Fornecedor"]): raise ValueError("Fornecedor vazio.")
                if pd.isna(row["Nº OP"]): raise ValueError("Nº OP vazio.")

                # conversões
                data = pd.to_datetime(row["Data"], dayfirst=True).date()
                hora_inicio = pd.to_datetime(str(row["Hora - Início"])).time()
                hora_fim    = pd.to_datetime(str(row["Hora - Fim"])).time()

                # NORMALIZAÇÃO E BUSCA DE FORNECEDOR
                raw_for = str(row["Fornecedor"]).strip()
                base_for = re.sub(r'\s*\(.*\)', '', raw_for).strip().upper()
                fornecedor = FornecedorQualificado.objects.filter(
                    nome__icontains=base_for
                ).first()
                if not fornecedor:
                    raise ValueError(f"Fornecedor '{raw_for}' não encontrado.")

                # NORMALIZAÇÃO E BUSCA DE CÓDIGO BRAS-MOL (fallback suave)
                cod_raw = str(row.get("Código Bras-Mol", "")).strip().upper()
                materia = None
                if cod_raw:
                    materia = MateriaPrimaCatalogo.objects.filter(
                        codigo__iexact=cod_raw
                    ).first()
                    if not materia:
                        erros.append(f"Linha {linha}: Código Bras-Mol '{cod_raw}' não encontrado; importando sem código.")
                        materia = None

                # Quantidades
                qt_tot = int(row["Quantidade Total"]) if not pd.isna(row["Quantidade Total"]) else 0
                qt_nok = int(row["Quantidade Não OK"]) if not pd.isna(row["Quantidade Não OK"]) else 0

                # Responsável
                usr_raw = str(row.get("Responsável", "")).strip().lower()
                responsavel = User.objects.filter(username__iexact=usr_raw).first() or request.user

                # Disposição
                disp_raw = str(row.get("Disposição", "Sucatear")).strip()
                opcoes = dict(Inspecao10.DISPOSICAO_CHOICES)
                disposicao = disp_raw if disp_raw in opcoes else "Sucatear"

                # criação
                Inspecao10.objects.create(
                    numero_op=str(row["Nº OP"]).strip(),
                    codigo_brasmol=materia,
                    data=data,
                    fornecedor=fornecedor,
                    hora_inicio=hora_inicio,
                    hora_fim=hora_fim,
                    quantidade_total=qt_tot,
                    quantidade_nok=qt_nok,
                    disposicao=disposicao,
                    observacoes=str(row.get("Observações", "")).strip(),
                    responsavel=responsavel,
                )
                importados += 1

            except Exception as e:
                erros.append(f"Linha {linha}: {e}")

        # salvar log de erros, se houver
        if erros:
            caminho = os.path.join(
                "C:/Projetos/RH-Qualidade/rh_qualidade/qualidade_fornecimento/views",
                "erros_importacao_inspecao10.txt"
            )
            with open(caminho, "w", encoding="utf-8") as f:
                f.write("\n".join(erros))
            messages.warning(request, f"{len(erros)} alertas/erros gerados. Veja 'erros_importacao_inspecao10.txt'.")

        messages.success(request, f"{importados} inspeções importadas com sucesso.")
        return redirect("listar_inspecoes10")

    return render(request, "f223/importar_excel.html")



@login_required
@permission_required("qualidade_fornecimento.view_inspecao10", raise_exception=True)
def verificar_estoque_devolucao(request):
    # Apenas serviços SEM data_envio definida (não enviados ainda)
    estoque = (
        DevolucaoServicoExterno.objects
        .filter(servico__data_envio__isnull=True)
        .values(
            "inspecao__numero_op",
            "inspecao__codigo_brasmol__codigo",
            "inspecao__fornecedor__nome"
        )
        .annotate(total=Sum("quantidade"))
        .order_by("inspecao__numero_op", "inspecao__codigo_brasmol__codigo")
    )

    return render(request, "f223/verificar_estoque_devolucao.html", {"estoque": estoque})
