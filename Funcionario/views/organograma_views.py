# Bibliotecas padrão
from collections import defaultdict
from copy import deepcopy

# Django
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# App Interno
from Funcionario.models import Funcionario
from Funcionario.utils.funcionario_utils import gerar_organograma_dict, gerar_cargos_para_impressao


@login_required
def organograma_view(request):
    """Renderiza o organograma com base nos subordinados do usuário."""
    if request.user.is_superuser:
        top_funcionarios = Funcionario.objects.filter(responsavel__isnull=True, status="Ativo")
    else:
        funcionario = Funcionario.objects.filter(nome=request.user.get_full_name()).first()
        top_funcionarios = (
            Funcionario.objects.filter(responsavel=funcionario, status="Ativo")
            if funcionario else
            Funcionario.objects.filter(responsavel__isnull=True, status="Ativo")
        )

    organograma = [
        {
            "nome": f.nome,
            "cargo": f.cargo_atual,
            "foto": f.foto.url if f.foto else None,
            "subordinados": gerar_organograma_dict(f),
        }
        for f in top_funcionarios
    ]
    return render(request, "funcionarios/organograma/organograma.html", {"organograma": organograma})


@login_required
def imprimir_organograma(request):
    """Gera o organograma impresso por cargos com hierarquia."""
    organograma = gerar_cargos_para_impressao()
    contexto = {
        "organograma": organograma,
        "revisao": "06",
        "data": "04/03/2025",
        "elaborador": "Anderson Goveia",
        "aprovador": "Lilian Fernandes"
    }
    return render(request, "funcionarios/organograma/organograma_imprimir.html", contexto)
