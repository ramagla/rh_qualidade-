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
