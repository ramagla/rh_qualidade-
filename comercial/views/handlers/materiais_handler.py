from django.forms import inlineformset_factory
from decimal import Decimal
from comercial.forms.precalculos_form import PreCalculoForm, PreCalculoMaterialForm
from comercial.models.precalculo import PreCalculo, PreCalculoMaterial
from comercial.utils.email_cotacao_utils import disparar_email_cotacao_material
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo
from tecnico.models.roteiro import InsumoEtapa

def processar_aba_materiais(request, precalc, materiais_respondidos, form_precalculo=None):
    salvo = False

    # Preenche automaticamente os insumos se ainda não houverem registros
    if request.method == "GET" and not precalc.materiais.exists():
        item = getattr(precalc.analise_comercial_item, "item", None)
        roteiro = getattr(item, "roteiro", None)

        if roteiro:
            insumos_materia_prima = InsumoEtapa.objects.filter(
                etapa__roteiro=roteiro,
                tipo_insumo="matéria_prima"
            ).select_related("materia_prima")[:3]

            for insumo in insumos_materia_prima:
                mp = insumo.materia_prima
                if mp:
                    PreCalculoMaterial.objects.create(
                        precalculo=precalc,
                        roteiro=roteiro,
                        codigo=mp.codigo,
                        nome_materia_prima=mp.codigo,
                        descricao=getattr(mp, 'descricao', ''),
                        tipo_material=getattr(mp, 'tipo_material', ''),
                        desenvolvido_mm=Decimal("0.0000000"),
                        peso_liquido=Decimal("0.0000000"),
                        peso_bruto=Decimal("0.0000000"),
                    )

        restantes = 3 - precalc.materiais.count()
        for _ in range(restantes):
            PreCalculoMaterial.objects.create(
                precalculo=precalc,
                codigo="",
                desenvolvido_mm=Decimal("0.0000000"),
                peso_liquido=Decimal("0.0000000"),
                peso_bruto=Decimal("0.0000000"),
            )

    qs_materiais = PreCalculoMaterial.objects.filter(precalculo=precalc)
    print("🔎 Materiais carregados do banco:")
    for m in qs_materiais:
        print(f" - {m.codigo} | Peso Bruto: {m.peso_bruto} | Peso Total: {m.peso_bruto_total}")

    MatSet = inlineformset_factory(
        PreCalculo,
        PreCalculoMaterial,
        form=PreCalculoMaterialForm,
        extra=0,
        can_delete=True,
    )

    fs_mat = MatSet(instance=precalc, queryset=qs_materiais, prefix="mat")  # Para GET

    if request.method == "POST":
        data = request.POST.copy()
        total = int(data.get("mat-TOTAL_FORMS", 0))

        for i in range(total):
            campo = f"mat-{i}-peso_bruto_total"
            valor = data.get(campo)
            if valor:
                try:
                    valor = valor.replace(".", "").replace(",", ".")
                    data[campo] = str(Decimal(valor))
                except Exception as e:
                    print(f"⚠️ Erro ao converter {campo} = '{valor}': {e}")
                    data[campo] = ""

        assert form_precalculo is not None, "form_precalculo não foi passado corretamente"

        fs_mat = MatSet(data=data, instance=precalc, queryset=qs_materiais, prefix="mat")

        # ⚠️ Verifica se houve envio da aba mesmo com valor ''
        if "form_materiais_submitted" in request.POST:
            if fs_mat.is_valid():
                selecionado = request.POST.get("material_selecionado")
                codigos_disparados = set()

                for mat_form in fs_mat:
                    if mat_form.cleaned_data and not mat_form.cleaned_data.get("DELETE", False):
                        mat = mat_form.save(commit=False)

                        if not mat.descricao:
                            mat.descricao = mat_form.cleaned_data.get("descricao") or mat.nome_materia_prima or ""
                        if not mat.tipo_material:
                            mat.tipo_material = mat_form.cleaned_data.get("tipo_material") or mat.tipo_material or ""

                        mat.selecionado = (mat_form.prefix == selecionado)

                        qtde_estimada = getattr(precalc.analise_comercial_item, "qtde_estimada", 0)
                        if mat.peso_bruto and qtde_estimada:
                            mat.peso_bruto_total = Decimal(mat.peso_bruto) * Decimal(qtde_estimada)

                        try:
                            mp = MateriaPrimaCatalogo.objects.get(codigo=mat.codigo)
                            if not mat.descricao:
                                mat.descricao = mp.descricao
                            if not mat.tipo_material:
                                mat.tipo_material = mp.tipo_material
                        except MateriaPrimaCatalogo.DoesNotExist:
                            pass

                        mat.save()

                        if (
                            not materiais_respondidos and
                            mat.codigo and not mat.preco_kg and
                            mat.codigo not in codigos_disparados
                        ):
                            disparar_email_cotacao_material(request, mat)
                            codigos_disparados.add(mat.codigo)

                fs_mat.save()

               
                salvo = True
            else:
                print("❌ ERROS DO FORMSET DE MATERIAIS:")
                for form in fs_mat:
                    print(form.errors)
                print("non_form_errors:", fs_mat.non_form_errors())

    return salvo, form_precalculo, fs_mat
