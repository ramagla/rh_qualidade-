# Funcionario/services/indicadores.py
from collections import defaultdict
from django.db import transaction
from django.db.models import Q, Count

from Funcionario.models import (
    Treinamento,
    Funcionario,
    FechamentoIndicadorTreinamento,
)

# Helper: devolve tuplas (inicio_mes, fim_mes) por trimestre
TRIMESTRES = {
    1: (1, 3),
    2: (4, 6),
    3: (7, 9),
    4: (10, 12),
}

STATUS_OK = {"concluido", "concluído", "CONCLUIDO", "CONCLUÍDO"}


def _dividir_horas_por_trimestre(data_inicio, data_fim, total_horas):
    """
    Se você já tem essa função no projeto, pode reutilizá-la.
    Aqui vai uma versão simplificada proporcional por mês.
    """
    from datetime import date

    if not data_fim:
        data_fim = data_inicio

    dias = max((data_fim - data_inicio).days + 1, 1)
    horas_por_dia = total_horas / dias

    acumulado = defaultdict(float)
    dia = data_inicio
    while dia <= data_fim:
        if dia.month in (1, 2, 3):
            t = 1
        elif dia.month in (4, 5, 6):
            t = 2
        elif dia.month in (7, 8, 9):
            t = 3
        else:
            t = 4
        acumulado[t] += horas_por_dia
        dia = date.fromordinal(dia.toordinal() + 1)

    # arredonda com 2 casas
    return {t: round(h, 2) for t, h in acumulado.items()}


def _media_trimestre(ano: int, trimestre: int) -> float:
    """
    Calcula a média (horas por funcionário) do trimestre informado.
    """
    inicio_mes, fim_mes = TRIMESTRES[trimestre]

    # Treinamentos no período, status tolerante
    treinamentos = Treinamento.objects.filter(
        data_inicio__year=ano,
        data_inicio__month__gte=inicio_mes,
        data_inicio__month__lte=fim_mes,
        status__in=STATUS_OK,
    )

    total_horas_trimestre = 0.0
    for tmt in treinamentos:
        # carga_horaria em "8h" ou numérica
        carga_raw = tmt.carga_horaria or "0"
        try:
            carga = float(str(carga_raw).lower().replace("h", "").strip() or 0)
        except ValueError:
            carga = 0.0

        participantes = Funcionario.objects.filter(
            treinamentos__nome_curso=tmt.nome_curso,
            treinamentos__data_inicio=tmt.data_inicio,
        ).distinct().count()

        total = carga * max(participantes, 0)
        distribuicao = _dividir_horas_por_trimestre(tmt.data_inicio, tmt.data_fim, total)
        total_horas_trimestre += distribuicao.get(trimestre, 0.0)

    total_funcionarios = Funcionario.objects.filter(status="Ativo").count() or 1
    media = round(total_horas_trimestre / total_funcionarios, 2)
    return media


@transaction.atomic
def recalcular_fechamento_trimestre(ano: int, trimestre: int, usuario=None) -> dict:
    """
    Recalcula SOMENTE o trimestre informado.
    - Atualiza/Cria FechamentoIndicadorTreinamento(ano, trimestre)
    - Zera os demais campos valor_tX nesse registro para evitar ambiguidade
    - Recalcula a média anual com base nos 4 fechamentos disponíveis
    Retorna dict com medias.
    """
    media_t = _media_trimestre(ano, trimestre)

    # Atualiza o fechamento do trimestre escolhido limpando outros campos
    defaults = {"media": None}
    for k in (1, 2, 3, 4):
        defaults[f"valor_t{k}"] = media_t if k == trimestre else None

    reg, _created = FechamentoIndicadorTreinamento.objects.update_or_create(
        ano=ano, trimestre=trimestre, defaults=defaults
    )

    # Carrega valores dos 4 trimestres (0.0 quando ausentes)
    valores = {}
    for t in (1, 2, 3, 4):
        r = FechamentoIndicadorTreinamento.objects.filter(ano=ano, trimestre=t).first()
        if not r:
            valores[t] = 0.0
            continue
        v = getattr(r, f"valor_t{t}", None)
        if v is None or v == 0:
            # fallback: se legado, olhe outros campos
            v_alt = next((getattr(r, f"valor_t{x}") for x in (1, 2, 3, 4) if getattr(r, f"valor_t{x}") not in (None, 0)), 0)
            valores[t] = float(v_alt or 0)
        else:
            valores[t] = float(v)

    media_anual = round(sum(valores.values()) / 4.0, 2)

    # Atualiza a média anual em todos os registros do ano (conveniência)
    FechamentoIndicadorTreinamento.objects.filter(ano=ano).update(media=media_anual)

    return {
        "media_trimestre": media_t,
        "media_anual": media_anual,
        "valores": valores,
    }
