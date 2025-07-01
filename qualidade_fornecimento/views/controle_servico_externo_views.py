# qualidade_fornecimento/views/controle_servico_externo_views.py

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from qualidade_fornecimento.forms.controle_servico_externo_form import (
    ControleServicoExternoForm,
    RetornoDiarioFormSet,
)
from qualidade_fornecimento.models.controle_servico_externo import (
    ControleServicoExterno,
)


@login_required
def cadastrar_controle_servico_externo(request):
    if request.method == "POST":
        form = ControleServicoExternoForm(request.POST)
        formset = RetornoDiarioFormSet(request.POST, prefix="retornos")

        if form.is_valid() and formset.is_valid():
            servico = form.save(commit=False)
            servico.save()

            formset.instance = servico
            formset.save()

            servico.total = servico.calcular_total()
            servico.status2 = servico.calcular_status2()
            servico.atraso_em_dias = servico.calcular_atraso_em_dias()
            servico.ip = servico.calcular_ip()
            servico.save()

            return redirect("listar_controle_servico_externo")

    else:
        form = ControleServicoExternoForm()
        formset = RetornoDiarioFormSet(prefix="retornos")

    # Pega o status da inspeção relacionada, se existir
    status_inspecao = None
    if "servico_id" in request.GET:
        try:
            servico = ControleServicoExterno.objects.get(pk=request.GET["servico_id"])
            if hasattr(servico, "inspecao"):
                status_inspecao = servico.inspecao.status_geral()
        except ControleServicoExterno.DoesNotExist:
            status_inspecao = None

    return render(
        request,
        "controle_servico_externo/form_controle_servico_externo.html",
        {"form": form, "formset": formset, "status_inspecao": status_inspecao},
    )


@login_required
def editar_controle_servico_externo(request, id):
    servico = get_object_or_404(ControleServicoExterno, id=id)

    if request.method == "POST":
        form = ControleServicoExternoForm(request.POST, instance=servico)
        formset = RetornoDiarioFormSet(request.POST, instance=servico, prefix="retornos")

        if form.is_valid() and formset.is_valid():
            servico = form.save(commit=False)
            servico.save()

            # ✅ Salva todo o formset (inclui exclusões)
            formset.save()

            # Atualiza campos automáticos
            servico.total = servico.calcular_total()
            servico.status2 = servico.calcular_status2()
            servico.atraso_em_dias = servico.calcular_atraso_em_dias()
            servico.ip = servico.calcular_ip()
            servico.save()

            return redirect("listar_controle_servico_externo")

    else:
        form = ControleServicoExternoForm(instance=servico)
        formset = RetornoDiarioFormSet(instance=servico, prefix="retornos")

    # 🔧 Preenche status_inspecao (usado no JS para calcular IQF)
    status_inspecao = servico.inspecao.status_geral() if hasattr(servico, "inspecao") else None

    return render(
        request,
        "controle_servico_externo/form_controle_servico_externo.html",
        {
            "form": form,
            "formset": formset,
            "editar": True,
            "status_inspecao": status_inspecao,
        },
    )



@login_required
def listar_controle_servico_externo(request):
    qs = ControleServicoExterno.objects.all().order_by("-data_envio")

    # Filtros
    pedido = request.GET.get("pedido")
    codigo_bm = request.GET.get("codigo_bm")
    fornecedor = request.GET.get("fornecedor")
    status2 = request.GET.get("status2")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    if pedido:
        qs = qs.filter(pedido=pedido)

    if codigo_bm:
        qs = qs.filter(codigo_bm__codigo=codigo_bm)

    if fornecedor:
        qs = qs.filter(fornecedor__nome=fornecedor)

    if status2:
        qs = qs.filter(status2=status2)

    if data_inicio:
        qs = qs.filter(data_envio__gte=data_inicio)

    if data_fim:
        qs = qs.filter(data_envio__lte=data_fim)

    # Paginação
    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Totais
    total_enviados = qs.count()
    total_ok = qs.filter(status2="OK").count()
    total_pendentes = qs.filter(status2="Atenção Saldo").count()
    total_atrasados = qs.filter(atraso_em_dias__gt=0).count()

    # Serviços disponíveis para inspeção
    servicos_disponiveis = ControleServicoExterno.objects.all().order_by("-data_envio")

    # Dados para os filtros
    pedidos = ControleServicoExterno.objects.values_list("pedido", flat=True).distinct().order_by("pedido")
    codigos_bm = ControleServicoExterno.objects.values_list("codigo_bm__codigo", flat=True).distinct().order_by("codigo_bm__codigo")
    fornecedores = ControleServicoExterno.objects.values_list("fornecedor__nome", flat=True).distinct().order_by("fornecedor__nome")

    context = {
    "servicos_paginados": page_obj,
    "total_enviados": total_enviados,
    "total_ok": total_ok,
    "total_pendentes": total_pendentes,
    "total_atrasados": total_atrasados,
    "servicos_disponiveis": servicos_disponiveis,
    "pedidos": pedidos,
    "codigos_bm": codigos_bm,
    "fornecedores": fornecedores,
}

    # 🧼 Limpa a sessão de sucesso da inspeção (evita modal duplicada após refresh)
    inspecao_id = request.session.pop("inspecao_pending", None)
    if inspecao_id:
        context["inspecao_pending"] = inspecao_id

    return render(request, "controle_servico_externo/lista_controle_servico_externo.html", context)


@login_required
def excluir_controle_servico_externo(request, id):
    servico = get_object_or_404(ControleServicoExterno, id=id)

    if request.method == "POST":
        servico.delete()
        return redirect("listar_controle_servico_externo")

    return render(
        request,
        "controle_servico_externo/controle_servico_externo_confirm_delete.html",
        {"servico": servico},
    )


from django.http import JsonResponse

from qualidade_fornecimento.models import FornecedorQualificado


@login_required
def api_leadtime(request, pk):
    try:
        fornecedor = FornecedorQualificado.objects.get(pk=pk)
        lead = fornecedor.lead_time if fornecedor.lead_time is not None else 0
        return JsonResponse({"lead_time": lead})
    except FornecedorQualificado.DoesNotExist:
        return JsonResponse({"lead_time": 0}, status=404)


@login_required
def visualizar_controle_servico_externo(request, id):
    servico = get_object_or_404(ControleServicoExterno, id=id)
    return render(
        request,
        "controle_servico_externo/visualizar_controle_servico_externo.html",
        {"servico": servico}
    )

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import datetime
import json

from qualidade_fornecimento.models import ControleServicoExterno, RetornoDiario

@csrf_exempt
@login_required
def registrar_entrega_servico_externo(request, servico_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            data_entrega = data.get("data")
            quantidade = data.get("quantidade")

            if not data_entrega or not quantidade:
                return JsonResponse({"success": False, "error": "Dados incompletos."})

            data_entrega = datetime.strptime(data_entrega, "%Y-%m-%d").date()
            quantidade = float(quantidade)

            servico = ControleServicoExterno.objects.get(id=servico_id)

            # Cria a nova entrega
            retorno = RetornoDiario.objects.create(
                servico=servico,
                data=data_entrega,
                quantidade=quantidade
            )

            # Atualiza o servico
            servico.total = servico.calcular_total()
            servico.status2 = servico.calcular_status2()
            servico.atraso_em_dias = servico.calcular_atraso_em_dias()
            servico.ip = servico.calcular_ip()
            servico.save()

            return JsonResponse({
                    "success": True,
                    "nova_entrega_data": retorno.data.strftime("%d/%m/%Y"),
                    "nova_entrega_quantidade": f"{retorno.quantidade:.2f}",
                    "novo_status": servico.status2
                })


        except ControleServicoExterno.DoesNotExist:
            print(f"Erro: Serviço com ID {servico_id} não encontrado.")
            return JsonResponse({"success": False, "error": "Serviço não encontrado."})

        except Exception as e:
            print("Erro ao registrar entrega:", e)
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Método não permitido."})



import os
import pandas as pd
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render
from qualidade_fornecimento.models import (
    ControleServicoExterno,
    FornecedorQualificado,
    MateriaPrimaCatalogo,
    RetornoDiario,
)

@login_required
@permission_required('qualidade_fornecimento.importar_excel_servico_externo', raise_exception=True)
def importar_excel_servico_externo(request):
    if request.method == "POST" and request.FILES.get("arquivo_excel"):
        df = pd.read_excel(request.FILES["arquivo_excel"])
        df.columns = df.columns.str.strip()

        erros = []
        importados = 0

        for idx, row in df.iterrows():
            linha = idx + 2
            try:
                # Pedido pode estar vazio e não deve ter .0
                pedido_raw = row.get("Pedido")
                if pd.notna(pedido_raw):
                    try:
                        pedido = str(int(pedido_raw))
                    except Exception:
                        pedido = str(pedido_raw).strip()
                else:
                    pedido = None

                if pd.isna(row["Fornecedor"]):
                    raise ValueError("Fornecedor vazio.")
                if pd.isna(row["Código BM"]):
                    raise ValueError("Código BM vazio.")
                if pd.isna(row["Quantidade Enviada"]):
                    raise ValueError("Quantidade Enviada vazia.")

                op = int(row["OP"]) if not pd.isna(row.get("OP")) else None
                nota_fiscal = str(row.get("Nota Fiscal", "")).strip()
                qtd_enviada = float(row["Quantidade Enviada"])
                observacao = str(row.get("Observação", "")).strip()

                data_envio = pd.to_datetime(row.get("Data Envio"), dayfirst=True).date() if not pd.isna(row.get("Data Envio")) else None
                data_negociada = pd.to_datetime(row.get("Data Negociada"), dayfirst=True).date() if not pd.isna(row.get("Data Negociada")) else None

                # Fornecedor
                fornecedor_nome = str(row["Fornecedor"]).strip()
                fornecedor = FornecedorQualificado.objects.filter(nome__icontains=fornecedor_nome).first()
                if not fornecedor:
                    raise ValueError(f"Fornecedor '{fornecedor_nome}' não encontrado.")

                # Código BM
                codigo_bm_str = str(row["Código BM"]).strip()
                codigo_bm = MateriaPrimaCatalogo.objects.filter(codigo__iexact=codigo_bm_str).first()
                if not codigo_bm:
                    raise ValueError(f"Código BM '{codigo_bm_str}' não encontrado.")

                # Lead time
                lead_time = fornecedor.lead_time if fornecedor.lead_time is not None else None

                # Última data de retorno
                datas_retorno = []
                for col_data in df.columns:
                    if "Retorno" in col_data and "Data" in col_data:
                        data_val = row.get(col_data)
                        if not pd.isna(data_val):
                            datas_retorno.append(pd.to_datetime(data_val, dayfirst=True).date())
                data_retorno = max(datas_retorno) if datas_retorno else None

                # Cria o serviço com status fixo OK
                servico = ControleServicoExterno.objects.create(
                    pedido=pedido,
                    op=op,
                    nota_fiscal=nota_fiscal,
                    fornecedor=fornecedor,
                    codigo_bm=codigo_bm,
                    quantidade_enviada=qtd_enviada,
                    data_envio=data_envio,
                    data_retorno=data_retorno,
                    data_negociada=data_negociada,
                    lead_time=lead_time,
                    observacao=observacao,
                    status2="OK"
                )

                # Importa retornos
                for col_data in df.columns:
                    if "Retorno" in col_data and "Data" in col_data:
                        numero = col_data.split(" ")[1]
                        col_qtd = f"Retorno {numero} - Qtd"
                        data_val = row.get(col_data)
                        qtd_val = row.get(col_qtd)

                        if not pd.isna(data_val) and not pd.isna(qtd_val):
                            data_entrega = pd.to_datetime(data_val, dayfirst=True).date()
                            quantidade = float(qtd_val)

                            RetornoDiario.objects.create(
                                servico=servico,
                                data=data_entrega,
                                quantidade=quantidade
                            )

                importados += 1

            except Exception as e:
                erros.append(f"Linha {linha}: {e}")

        if erros:
            caminho = os.path.join(
                "C:/Projetos/RH-Qualidade/rh_qualidade/qualidade_fornecimento/views",
                "erros_importacao_servico_externo.txt"
            )
            with open(caminho, "w", encoding="utf-8") as f:
                f.write("\n".join(erros))
            messages.warning(request, f"{len(erros)} erros encontrados. Veja 'erros_importacao_servico_externo.txt'.")

        messages.success(request, f"{importados} registros importados com sucesso.")
        return redirect("listar_controle_servico_externo")

    return render(request, "controle_servico_externo/importar_excel_servico.html")
