from django.http import JsonResponse
from tecnico.models.roteiro import RoteiroProducao
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo

def ajax_codigo_materia_prima_por_roteiro(request):
    roteiro_id = request.GET.get("roteiro_id")
    try:
        roteiro = RoteiroProducao.objects.get(id=roteiro_id)
        etapa = roteiro.etapas.first()
        if etapa:
            primeiro_insumo = etapa.insumos.filter(tipo_insumo="matéria_prima").first()
            if primeiro_insumo and primeiro_insumo.materia_prima:
                return JsonResponse({"sucesso": True, "codigo": primeiro_insumo.materia_prima.codigo})
    except Exception as e:
        # opcional: logar erro se necessário
        pass
    return JsonResponse({"sucesso": False, "codigo": ""})
