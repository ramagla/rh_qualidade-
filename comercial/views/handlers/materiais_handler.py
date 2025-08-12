from django.forms import inlineformset_factory
from decimal import Decimal
from comercial.forms.precalculos_form import PreCalculoMaterialForm
from comercial.models.precalculo import PreCalculo, PreCalculoMaterial
from comercial.utils.email_cotacao_utils import disparar_email_cotacao_material
from tecnico.models.roteiro import InsumoEtapa


def processar_aba_materiais(request, precalc, materiais_respondidos, form_precalculo=None):
    salvo = False

    # GET: apenas se não houver materiais, cria com base no roteiro
    if request.method == "GET" and hasattr(precalc, "analise_comercial_item") and not precalc.materiais.exists():
        try:
            roteiro = getattr(precalc.analise_comercial_item, "roteiro_selecionado", None)
            if roteiro:
                MP_ALIASES = {"materia_prima", "matéria_prima", "mp", "MP", "MATERIA_PRIMA"}
                SE_ALIASES = {
                    "insumos", "servico_externo", "serviço_externo", "servico", "serviço",
                    "se", "SE", "SERVICO_EXTERNO", "SERVIÇO_EXTERNO", "INSUMOS"
                }

                print(f"[MP][PC={precalc.id}] Repovoamento — Roteiro={getattr(roteiro, 'id', None)}")
                tipos_all = list(
                    InsumoEtapa.objects.filter(etapa__roteiro=roteiro)
                    .values_list("tipo_insumo", flat=True).distinct()
                )
                print(f"[MP][PC={precalc.id}] Tipos no roteiro: {tipos_all}")

                # Apenas MPs reais (com vínculo e NÃO pertencentes aos aliases de serviço)
                insumos_materia_prima = (
                    InsumoEtapa.objects
                    .filter(etapa__roteiro=roteiro)
                    .filter(tipo_insumo__in=MP_ALIASES)
                    .exclude(tipo_insumo__in=SE_ALIASES)
                    .filter(materia_prima__isnull=False)
                    .select_related("materia_prima", "etapa")
                )
                print(f"[MP][PC={precalc.id}] Selecionados como MP: {insumos_materia_prima.count()}")

                # Remove todos os materiais se forem diferentes do roteiro
                materiais_atuais = list(precalc.materiais.values_list("codigo", flat=True))
                codigos_do_roteiro = [i.materia_prima.codigo for i in insumos_materia_prima if i.materia_prima]
                if set(materiais_atuais) != set(codigos_do_roteiro):
                    removed = PreCalculoMaterial.objects.filter(precalculo=precalc).delete()
                    print(f"[MP][PC={precalc.id}] Materiais limpos: {removed}")

                # Cria 3 cópias por insumo (sem duplicar código)
                criados = 0
                for insumo in insumos_materia_prima:
                    mp = insumo.materia_prima
                    if not mp:
                        continue
                    if PreCalculoMaterial.objects.filter(precalculo=precalc, codigo=mp.codigo).exists():
                        continue
                    for _ in range(3):
                        PreCalculoMaterial.objects.create(
                            precalculo=precalc,
                            roteiro=roteiro,
                            codigo=mp.codigo,
                            nome_materia_prima=mp.codigo,
                            descricao=getattr(mp, "descricao", ""),
                            tipo_material=getattr(mp, "tipo_material", ""),
                            desenvolvido_mm=insumo.desenvolvido or Decimal("0"),
                            peso_liquido=insumo.peso_liquido or Decimal("0"),
                            peso_bruto=insumo.peso_bruto or Decimal("0"),
                        )
                        criados += 1
                        print(f"[MP][PC={precalc.id}] Criado material para insumo {insumo.id} (cod={mp.codigo})")

                precalc.refresh_from_db()
                print(f"[MP][PC={precalc.id}] Criados: {criados} | Total agora: {precalc.materiais.count()}")

        except Exception as e:
            print(f"⚠️ [MP][PC={precalc.id}] Erro: {e}")

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

            enviados = set()
            if not materiais_respondidos:
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
