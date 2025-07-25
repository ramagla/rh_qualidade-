from django.http import JsonResponse
from tecnico.models.roteiro import RoteiroProducao
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo

def ajax_codigo_materia_prima_por_roteiro(request):
    from tecnico.models.roteiro import RoteiroProducao
    from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo

    roteiro_id = request.GET.get("roteiro_id")
    item_id = request.GET.get("item_id")

    if item_id:
        roteiros = RoteiroProducao.objects.filter(item_id=item_id)
        lista = [{"id": r.id, "texto": str(r)} for r in roteiros]

        codigo_materia_prima = ""
        for r in roteiros:
            etapa = r.etapas.first()
            if etapa:
                insumo = etapa.insumos.filter(tipo_insumo="matéria_prima").first()
                if insumo and insumo.materia_prima:
                    codigo_materia_prima = insumo.materia_prima.codigo
                    break

        return JsonResponse({
            "sucesso": True,
            "roteiros": lista,
            "codigo": codigo_materia_prima
        })

    if roteiro_id:
        try:
            roteiro = RoteiroProducao.objects.get(id=roteiro_id)
            etapa = roteiro.etapas.first()
            if etapa:
                primeiro_insumo = etapa.insumos.filter(tipo_insumo="matéria_prima").first()
                if primeiro_insumo and primeiro_insumo.materia_prima:
                    return JsonResponse({"sucesso": True, "codigo": primeiro_insumo.materia_prima.codigo})
        except Exception:
            pass

    return JsonResponse({"sucesso": False, "codigo": "", "roteiros": []})


from django.http import JsonResponse
from comercial.models import Ferramenta

def ajax_valor_ferramenta(request):
    ferramenta_id = request.GET.get("id")
    try:
        ferramenta = Ferramenta.objects.get(id=ferramenta_id)
        return JsonResponse({"valor_total": float(ferramenta.valor_total)})
    except Ferramenta.DoesNotExist:
        return JsonResponse({"valor_total": None})
from django.http import JsonResponse
from comercial.models import PreCalculo





from django.http import JsonResponse
from comercial.models import PreCalculo

def dados_precalculo(request, pk):
    try:
        precalc = PreCalculo.objects.select_related(
            "cotacao__cliente", "analise_comercial_item__item"
        ).get(pk=pk)

        cliente = precalc.cotacao.cliente
        item = precalc.analise_comercial_item.item if hasattr(precalc, "analise_comercial_item") and precalc.analise_comercial_item else None

        return JsonResponse({
            "item": item.id if item else None,
            "cliente": cliente.id if cliente else None,
            "comprador": cliente.nome_contato or "",  # <-- CORRETO AGORA
            "codigo_desenho": item.codigo_desenho if item and hasattr(item, "codigo_desenho") else "",
            "revisao": item.revisao if item and hasattr(item, "revisao") else "",
            "data_revisao": item.data_revisao.isoformat() if item and item.data_revisao else "",
            "metodologia_aprovacao": getattr(precalc.analise_comercial_item, "metodologia", ""),
            "automotivo_oem": item.automotivo_oem if item and hasattr(item, "automotivo_oem") else False,
            "requisito_especifico": item.requisito_especifico if item and hasattr(item, "requisito_especifico") else False,
            "item_seguranca": item.item_seguranca if item and hasattr(item, "item_seguranca") else False,
        })
    except PreCalculo.DoesNotExist:
        return JsonResponse({}, status=404)


from tecnico.models.roteiro import RoteiroProducao
from django.http import JsonResponse

from django.http import JsonResponse
from tecnico.models.roteiro import RoteiroProducao
from comercial.models.item import Item
from django.views.decorators.http import require_GET

@require_GET
def ajax_roteiros_por_item(request):
    item_id = request.GET.get("item_id")
    roteiros = RoteiroProducao.objects.filter(item_id=item_id).order_by("tipo_roteiro")

    data = {
        "roteiros": [
            {
                "id": r.id,
                "label": f"{r.item.codigo} {r.get_tipo_roteiro_display()} ({r.etapas.count()} Etapas)"
            }
            for r in roteiros
        ]
    }

    return JsonResponse(data)
