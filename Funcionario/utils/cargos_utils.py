from collections import defaultdict
from ..models import Cargo
from django.db.models import Q, Count


def agrupar_cargos_por_nivel():
    """
    Agrupa cargos por nível hierárquico, incluindo o funcionário ativo (status=Ativo).
    """
    cargos_agrupados = defaultdict(list)

    for cargo in Cargo.objects.prefetch_related("cargo_atual_funcionarios").order_by("nivel", "nome"):
        funcionario_ativo = next(
            (f for f in cargo.cargo_atual_funcionarios.all() if f.status == "Ativo"),
            None
        )
        cargos_agrupados[cargo.nivel].append({
            "cargo": cargo,
            "funcionario_ativo": funcionario_ativo
        })

    return sorted(cargos_agrupados.items())


def obter_dados_cards(cargos_queryset):
    """
    Retorna dados estatísticos dos cards da tela de listagem.
    """
    total_cargos = cargos_queryset.count()
    departamento_mais_frequente = (
        cargos_queryset.values("departamento")
        .annotate(total=Count("departamento"))
        .order_by("-total")
        .first()
    )
    departamento_nome = departamento_mais_frequente["departamento"] if departamento_mais_frequente else "Nenhum"

    from ..models import Revisao
    ultima_revisao = (
        Revisao.objects.filter(cargo__in=cargos_queryset).order_by("-data_revisao").first()
    )
    data_ultima_revisao = ultima_revisao.data_revisao if ultima_revisao else "Sem revisão"

    cargos_sem_descricao = cargos_queryset.filter(
        Q(descricao_arquivo__isnull=True) | Q(descricao_arquivo="")
    ).count()

    return {
        "total_cargos": total_cargos,
        "departamento_mais_frequente": departamento_nome,
        "ultima_revisao": data_ultima_revisao,
        "cargos_sem_descricao": cargos_sem_descricao,
    }


def preencher_datas_formulario(cargo):
    """
    Retorna o dicionário de datas formatadas para pré-preencher o formulário.
    """
    return {
        "elaborador_data": cargo.elaborador_data.strftime("%Y-%m-%d") if cargo.elaborador_data else "",
        "aprovador_data": cargo.aprovador_data.strftime("%Y-%m-%d") if cargo.aprovador_data else "",
    }
