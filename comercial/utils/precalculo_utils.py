from decimal import Decimal
from comercial.models.precalculo import PreCalculoMaterial
from tecnico.models.roteiro import InsumoEtapa

def atualizar_materiais_do_roteiro(precalc):
    item = getattr(precalc.analise_comercial_item, "item", None)
    roteiro = getattr(item, "roteiro", None)

    if not roteiro:
        return

    # Lista de códigos de matéria-prima no roteiro
    codigos_roteiro = set(
        InsumoEtapa.objects.filter(
            etapa__roteiro=roteiro,
            tipo_insumo="matéria_prima"
        )
        .select_related("materia_prima")
        .values_list("materia_prima__codigo", flat=True)
    )

    # Remove materiais que não estão mais no roteiro
    precalc.materiais.exclude(codigo__in=codigos_roteiro).delete()

    # Adiciona os novos códigos que ainda não existem
    codigos_existentes = set(precalc.materiais.values_list("codigo", flat=True))
    novos_codigos = codigos_roteiro - codigos_existentes

    for codigo in novos_codigos:
        PreCalculoMaterial.objects.create(
            precalculo=precalc,
            codigo=codigo,
            desenvolvido_mm=Decimal("0.0000000"),  # 🔐 obrigatório
            peso_liquido=Decimal("0.0000000"),
            peso_bruto=Decimal("0.0000000"),
        )

    # Garante no mínimo 3 linhas
    restantes = 3 - precalc.materiais.count()
    for _ in range(restantes):
        PreCalculoMaterial.objects.create(
            precalculo=precalc,
            codigo="",
            desenvolvido_mm=Decimal("0.0000000"),
            peso_liquido=Decimal("0.0000000"),
            peso_bruto=Decimal("0.0000000"),
        )
