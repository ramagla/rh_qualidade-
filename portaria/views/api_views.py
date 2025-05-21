# portaria/views/api_views.py
from django.http import JsonResponse
from portaria.models import PessoaPortaria, VeiculoPortaria

def api_veiculos_da_pessoa(request, pessoa_id):
    veiculos = VeiculoPortaria.objects.filter(pessoa_id=pessoa_id)
    data = {
        "veiculos": [
            {"id": v.id, "placa": v.placa, "tipo": v.tipo}
            for v in veiculos
        ]
    }
    return JsonResponse(data)

