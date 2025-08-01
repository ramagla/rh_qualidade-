from django.http import JsonResponse
from metrologia.models import TabelaTecnica, Dispositivo

def get_equipamento_info(request, id):
    equipamento = TabelaTecnica.objects.filter(id=id).first()
    if equipamento:
        return JsonResponse({
            "descricao": equipamento.nome_equipamento,
            "modelo": equipamento.modelo,
            "capacidade": f"{equipamento.capacidade_minima} - {equipamento.capacidade_maxima} / {equipamento.resolucao}",
            "data_calibracao": equipamento.data_ultima_calibracao,
        })
    return JsonResponse({}, status=404)

def get_dispositivo_info(request, id):
    dispositivo = Dispositivo.objects.filter(id=id).first()
    if dispositivo:
        return JsonResponse({
            "descricao": dispositivo.descricao,
            "modelo": "",
            "capacidade": "",
            "data_calibracao": dispositivo.data_ultima_calibracao,
        })
    return JsonResponse({}, status=404)
