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
