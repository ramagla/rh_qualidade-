from django.http import JsonResponse
from Funcionario.models import Funcionario, Treinamento

def get_funcionario_info(request, id):
    try:
        funcionario = Funcionario.objects.get(id=id)
        data = {
            'nome': funcionario.nome,
            'local_trabalho': funcionario.local_trabalho,
            'cargo_atual': funcionario.cargo_atual.nome if funcionario.cargo_atual else '',
        }
        return JsonResponse(data)
    except Funcionario.DoesNotExist:
        return JsonResponse({'error': 'Funcionário não encontrado'}, status=404)

def get_treinamentos(request, funcionario_id):
    treinamentos = Treinamento.objects.filter(funcionario_id=funcionario_id).values('tipo', 'nome_curso', 'categoria')
    return JsonResponse(list(treinamentos), safe=False)
