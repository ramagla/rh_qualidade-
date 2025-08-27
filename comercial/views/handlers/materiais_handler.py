from decimal import Decimal, InvalidOperation
from django.forms import inlineformset_factory
from django.db.models import Q
from comercial.forms.precalculos_form import PreCalculoMaterialForm
from comercial.models.precalculo import PreCalculo, PreCalculoMaterial
from comercial.utils.email_cotacao_utils import disparar_email_cotacao_material
from tecnico.models.roteiro import InsumoEtapa


def processar_aba_materiais(request, precalc, materiais_respondidos, form_precalculo=None):
    print(f"[MP][ENTER][PC={precalc.id}] method={request.method}", flush=True)
    salvo = False

    # ——————————————————————————————————————————————————————
    # GET: repovoar a partir do roteiro se ainda não houver linhas
    # ——————————————————————————————————————————————————————
    if request.method == "GET" and hasattr(precalc, "analise_comercial_item") and not precalc.materiais.exists():
        try:
            roteiro = getattr(precalc.analise_comercial_item, "roteiro_selecionado", None)
            print(f"[MP][GET][PC={precalc.id}] roteiro_id={getattr(roteiro,'id',None)}", flush=True)
            if roteiro:
                MP_ALIASES = {"materia_prima", "matéria_prima", "mp", "MP", "MATERIA_PRIMA"}
                SE_ALIASES = {
                    "insumos", "servico_externo", "serviço_externo", "servico", "serviço",
                    "se", "SE", "SERVICO_EXTERNO", "SERVIÇO_EXTERNO", "INSUMOS"
                }

                tipos_all = list(
                    InsumoEtapa.objects.filter(etapa__roteiro=roteiro)
                    .values_list("tipo_insumo", flat=True).distinct()
                )
                print(f"[MP][GET][PC={precalc.id}] tipos_no_roteiro={tipos_all}", flush=True)

                insumos_materia_prima = (
                    InsumoEtapa.objects
                    .filter(etapa__roteiro=roteiro)
                    .filter(tipo_insumo__in=MP_ALIASES)
                    .exclude(tipo_insumo__in=SE_ALIASES)
                    .filter(materia_prima__isnull=False)
                    .select_related("materia_prima", "etapa")
                )
                print(f"[MP][GET][PC={precalc.id}] MPs_selecionadas={insumos_materia_prima.count()}", flush=True)

                materiais_atuais = list(precalc.materiais.values_list("codigo", flat=True))
                codigos_do_roteiro = [
                    i.materia_prima.codigo for i in insumos_materia_prima if i.materia_prima
                ]
                if set(materiais_atuais) != set(codigos_do_roteiro):
                    removed = PreCalculoMaterial.objects.filter(precalculo=precalc).delete()
                    print(f"[MP][GET][PC={precalc.id}] materiais_removidos={removed}", flush=True)

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
                        print(f"[MP][GET][PC={precalc.id}] criado_para_insumo={insumo.id} cod={mp.codigo}", flush=True)

                precalc.refresh_from_db()
                print(f"[MP][GET][PC={precalc.id}] criados={criados} total_atual={precalc.materiais.count()}", flush=True)

        except Exception as e:
            print(f"[MP][GET][PC={precalc.id}] excecao='{e}'", flush=True)

    # ——————————————————————————————————————————————————————
    # POST: normalização agressiva (vírgula/ponto) + logs do payload
    # ——————————————————————————————————————————————————————
    data = None
    if request.method == "POST":
        print(f"[MP][POST][PC={precalc.id}] keys_count={len(request.POST.keys())}", flush=True)
        print(f"[MP][POST][PC={precalc.id}] keys_sample={list(request.POST.keys())[:30]}", flush=True)

        data = request.POST.copy()
        total = int(data.get("mat-TOTAL_FORMS", 0) or 0)
        print(f"[MP][POST][PC={precalc.id}] mat-TOTAL_FORMS={total}", flush=True)

        decimais = (
            "lote_minimo", "icms", "preco_kg",
            "desenvolvido_mm", "peso_liquido", "peso_bruto", "peso_bruto_total",
        )
        for i in range(total):
            for fld in decimais:
                key = f"mat-{i}-{fld}"
                val = data.get(key)
                if val not in (None, ""):
                    try:
                        # Campos de compras podem vir com milhar + vírgula
                        if fld in ("lote_minimo", "icms", "preco_kg"):
                            s = str(val).replace(".", "").replace(",", ".")
                        else:
                            s = str(val).replace(",", ".")
                        Decimal(s)  # valida
                        data[key] = s
                    except Exception as e:
                        print(f"[MP][POST][PC={precalc.id}] normalizacao_falhou key={key} val='{val}' err='{e}'", flush=True)

        # Inteiro (aceita '10,0')
        for i in range(total):
            k = f"mat-{i}-entrega_dias"
            v = data.get(k)
            if v and isinstance(v, str):
                data[k] = v.strip().replace(".", "").replace(",", ".")

    MatSet = inlineformset_factory(
        PreCalculo, PreCalculoMaterial,
        form=PreCalculoMaterialForm,
        extra=0, can_delete=True,
    )
    fs_mat = MatSet(data if request.method == "POST" else None, instance=precalc, prefix="mat")
    print(f"[MP][FS][PC={precalc.id}] is_bound={fs_mat.is_bound} total_forms={fs_mat.total_form_count()}", flush=True)

    try:
        mg_ok = fs_mat.management_form.is_valid()
        print(f"[MP][FS][PC={precalc.id}] mgmt_valid={mg_ok} mgmt_errors={fs_mat.management_form.errors}", flush=True)
    except Exception as e:
        print(f"[MP][FS][PC={precalc.id}] mgmt_check_error='{e}'", flush=True)

    for i, form in enumerate(fs_mat.forms):
        inst = form.instance
        print(
            f"[MP][FSFORM][PC={precalc.id}] i={i} pk={getattr(inst,'pk',None)} "
            f"codigo={getattr(inst,'codigo',None)} preco_kg={getattr(inst,'preco_kg',None)} "
            f"fornecedor_id={getattr(inst,'fornecedor_id',None)}",
            flush=True
        )

    # ——————————————————————————————————————————————————————
    # POST: validar/salvar + observações + seleção + e-mails
    # ——————————————————————————————————————————————————————
    if request.method == "POST" and "form_materiais_submitted" in request.POST:
        print(f"[MP][CHK][PC={precalc.id}] form_materiais_submitted=True", flush=True)
        valid = fs_mat.is_valid()
        print(f"[MP][CHK][PC={precalc.id}] fs_mat.is_valid()={valid}", flush=True)

        if not valid:
            print(f"[MP][ERR][PC={precalc.id}] fs_errors={fs_mat.errors}", flush=True)
            print(f"[MP][ERR][PC={precalc.id}] fs_non_form_errors={fs_mat.non_form_errors()}", flush=True)

        if valid:
            fs_mat.save()
            print(f"[MP][SAVE][PC={precalc.id}] formset_salvo=True", flush=True)

            # Observações (campo do form principal)
            if form_precalculo and form_precalculo.is_valid():
                obs = form_precalculo.cleaned_data.get("observacoes_materiais")
                if obs is not None:
                    precalc.observacoes_materiais = obs
                    precalc.save(update_fields=["observacoes_materiais"])
                    print(f"[MP][SAVE][PC={precalc.id}] obs_materiais_atualizada=True", flush=True)

            # Seleção (zera e marca o escolhido)
            precalc.materiais.update(selecionado=False)
            # Suporta tanto radio único quanto múltiplos names:
            escolhido = request.POST.get("material_selecionado")
            if not escolhido:
                for k, v in request.POST.items():
                    if k.startswith("material_selecionado"):
                        escolhido = v
                        break

            if escolhido:
                for mf in fs_mat:
                    if mf.prefix == escolhido and not mf.cleaned_data.get("DELETE", False):
                        obj = mf.save(commit=False)
                        obj.selecionado = True
                        obj.save()
                        print(f"[MP][SEL][PC={precalc.id}] marcado_selecionado prefix={escolhido} id={obj.id}", flush=True)

            # Disparo de e-mails (somente se ainda não respondidos)
            enviados = set()
            if not materiais_respondidos:
                for mat in precalc.materiais.all():
                    if mat.codigo and (not mat.preco_kg or mat.preco_kg == 0) and mat.codigo not in enviados:
                        try:
                            disparar_email_cotacao_material(request, mat)
                            enviados.add(mat.codigo)
                        except Exception as e:
                            print(f"[MP][MAIL][PC={precalc.id}] erro_envio codigo={mat.codigo} err='{e}'", flush=True)
                print(f"[MP][MAIL][PC={precalc.id}] enviados_para_codigos={sorted(list(enviados))}", flush=True)

            salvo = True
        else:
            print(f"[MP][ABORT][PC={precalc.id}] formset_invalido", flush=True)

    return salvo, form_precalculo, fs_mat
