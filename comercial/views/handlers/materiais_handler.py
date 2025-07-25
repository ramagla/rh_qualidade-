from django.forms import inlineformset_factory
from decimal import Decimal
from comercial.forms.precalculos_form import PreCalculoMaterialForm
from comercial.models.precalculo import PreCalculo, PreCalculoMaterial
from comercial.utils.email_cotacao_utils import disparar_email_cotacao_material
from tecnico.models.roteiro import InsumoEtapa


def processar_aba_materiais(request, precalc, materiais_respondidos, form_precalculo=None):
    salvo = False
    insumos_materia_prima = []

    # GET: apenas se não houver materiais, cria com base no roteiro
    if request.method == "GET" and hasattr(precalc, "analise_comercial_item") and not precalc.materiais.exists():
        try:
            roteiro = getattr(precalc.analise_comercial_item, "roteiro_selecionado", None)
            if roteiro:
                insumos_materia_prima = (
                    InsumoEtapa.objects.filter(
                        etapa__roteiro=roteiro,
                        tipo_insumo="matéria_prima"
                    )
                    .select_related("materia_prima", "etapa")
                )

                # Remove materiais antigos que não estão mais relacionados
                materiais_invalidos = PreCalculoMaterial.objects.filter(precalculo=precalc).exclude(
                    codigo__in=[i.materia_prima.codigo for i in insumos_materia_prima if i.materia_prima]
                )
                if materiais_invalidos.exists():
                    materiais_invalidos.delete()

                # Cria novos registros (3 cópias por insumo)
                novos_insumos = [
                    i for i in insumos_materia_prima
                    if not precalc.materiais.filter(codigo=i.materia_prima.codigo).exists()
                ]
                for insumo in novos_insumos:
                    mp = insumo.materia_prima
                    if mp:
                        for _ in range(3):
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
                precalc.refresh_from_db()

        except Exception as e:
            print("⚠️ Erro ao processar insumos de matéria-prima:", e)

    # Normaliza os dados para POST
    data = None
    if request.method == "POST":
        data = request.POST.copy()
        total = int(data.get("mat-TOTAL_FORMS", 0))

        for i in range(total):
            key = f"mat-{i}-peso_bruto_total"
            val = data.get(key)
            if val:
                try:
                    s = val.replace(".", "").replace(",", ".")
                    num = Decimal(s)
                    data[key] = str(num)
                except Exception:
                    data[key] = s

    MatSet = inlineformset_factory(
        PreCalculo,
        PreCalculoMaterial,
        form=PreCalculoMaterialForm,
        extra=0,
        can_delete=True,
    )
    fs_mat = MatSet(data if request.method == "POST" else None, instance=precalc, prefix="mat")

    # POST: salvar + email
    if request.method == "POST" and "form_materiais_submitted" in request.POST:
        if fs_mat.is_valid():
            fs_mat.save()

            if form_precalculo and form_precalculo.is_valid():
                campo_obs = "observacoes_materiais"
                valor = form_precalculo.cleaned_data.get(campo_obs)
                setattr(precalc, campo_obs, valor)
                precalc.save(update_fields=[campo_obs])


            # Marca apenas o selecionado
            for mat in precalc.materiais.all():
                mat.selecionado = False
                mat.save(update_fields=["selecionado"])

            for key in request.POST:
                if key.startswith("material_selecionado"):
                    prefixo = request.POST[key]
                    for mat_form in fs_mat:
                        if mat_form.prefix == prefixo and not mat_form.cleaned_data.get("DELETE", False):
                            mat = mat_form.save(commit=False)
                            mat.selecionado = True
                            mat.save()

            fs_mat.save()

            # E-mail de cotação
            if not materiais_respondidos:
                enviados = set()
                for mat in precalc.materiais.all():
                    if mat.codigo and not mat.preco_kg and mat.codigo not in enviados:
                        disparar_email_cotacao_material(request, mat)
                        enviados.add(mat.codigo)

            salvo = True
        else:
            print("❌ Erros no formset de materiais:")
            for form in fs_mat:
                print(form.errors)

    return salvo, form_precalculo, fs_mat
