from django.forms import inlineformset_factory
from django.utils import timezone
from decimal import Decimal

from comercial.forms.precalculos_form import PreCalculoMaterialForm, PreCalculoForm
from comercial.models.precalculo import PreCalculo, PreCalculoMaterial
from comercial.utils.email_cotacao_utils import disparar_email_cotacao_material

from tecnico.models.roteiro import InsumoEtapa

def processar_aba_materiais(request, precalc, materiais_respondidos):
    if request.method == "GET" and not precalc.materiais.exists():
        item = getattr(precalc.analise_comercial_item, "item", None)
        roteiro = getattr(item, "roteiro", None)

        if roteiro:
            # Coleta os insumos tipo 'matéria_prima'
            insumos_materia_prima = InsumoEtapa.objects.filter(
                etapa__roteiro=roteiro,
                tipo_insumo="matéria_prima"
            ).select_related("materia_prima")[:3]  # garante no máximo 3

            for insumo in insumos_materia_prima:
                mp = insumo.materia_prima
                PreCalculoMaterial.objects.create(
                    precalculo=precalc,
                    codigo=mp.codigo,
                    desenvolvido_mm=0,
                    peso_liquido=0,
                    peso_bruto=0,
                    roteiro=roteiro,
                    # Se desejar: adicione nome_materia_prima, descricao, unidade etc.
                )

        # Se ainda tiver menos de 3 linhas, completa com em branco
        restantes = 3 - precalc.materiais.count()
        for _ in range(restantes):
            PreCalculoMaterial.objects.create(
                precalculo=precalc,
                codigo="",
                desenvolvido_mm=0,
                peso_liquido=0,
                peso_bruto=0,
            )

    MatSet = inlineformset_factory(
        PreCalculo,
        PreCalculoMaterial,
        form=PreCalculoMaterialForm,
        extra=0,
        can_delete=True,
    )

    form_precalculo = PreCalculoForm(
        request.POST if request.method == "POST" else None,
        instance=precalc
    )
    fs_mat = MatSet(
        request.POST if request.method == "POST" else None,
        instance=precalc,
        prefix='mat'
    )

    salvo = False

    if request.method == "POST" and "form_materiais_submitted" in request.POST:
        if form_precalculo.is_valid() and fs_mat.is_valid():
            form_precalculo.save()

            selecionado = request.POST.get("material_selecionado")
            codigos_disparados = set()

            for mat_form in fs_mat:
                if mat_form.cleaned_data and not mat_form.cleaned_data.get("DELETE", False):
                    mat = mat_form.save(commit=False)
                    mat.selecionado = (mat_form.prefix == selecionado)
                    mat.save()

                    if (
                        not materiais_respondidos
                        and mat.codigo
                        and not mat.preco_kg
                        and mat.codigo not in codigos_disparados
                    ):
                        disparar_email_cotacao_material(request, mat)
                        codigos_disparados.add(mat.codigo)

            fs_mat.save()
            salvo = True

    return salvo, form_precalculo, fs_mat
