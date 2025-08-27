from django.forms import inlineformset_factory
from django.forms.models import BaseInlineFormSet
from decimal import Decimal
from comercial.forms.precalculos_form import PreCalculoServicoExternoForm
from comercial.models.precalculo import PreCalculo, PreCalculoServicoExterno
from comercial.utils.email_cotacao_utils import disparar_emails_cotacao_servicos
from tecnico.models.roteiro import InsumoEtapa
from django.forms import HiddenInput

class ServicoInlineFormSet(BaseInlineFormSet):
    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)

        # Campos de compras não são obrigatórios
        for fld in ("lote_minimo", "entrega_dias", "fornecedor", "icms", "preco_kg"):
            if fld in form.fields:
                form.fields[fld].required = False

        # 🛠️ INSUMO: não obrigatório + preservar valor existente
        if "insumo" in form.fields:
            inst = form.instance
            insumo_id = getattr(inst, "insumo_id", None)

            # Não travar a validação por ausência de insumo no POST
            form.fields["insumo"].required = False

            if insumo_id:
                # Quando houver, restringe ao próprio insumo e esconde
                form.fields["insumo"].queryset = InsumoEtapa.objects.filter(pk=insumo_id)
                form.fields["insumo"].initial = insumo_id
                form.fields["insumo"].empty_label = None
                form.fields["insumo"].widget = HiddenInput()
            else:
                # Sem insumo na instância: mantém campo oculto/ignorado
                # (segue não obrigatório; o clean() do form preserva se vier a existir)
                form.fields["insumo"].queryset = InsumoEtapa.objects.none()
                form.fields["insumo"].widget = HiddenInput()

        return form


def processar_aba_servicos(request, precalc, submitted=False, servicos_respondidos=False, form_precalculo=None):
    print(f"[SERVICOS][ENTER][PC={precalc.id}] method={request.method}")
    salvo = False

    if request.method == "GET" and hasattr(precalc, "analise_comercial_item") and not precalc.servicos.exists():
        roteiro = getattr(precalc.analise_comercial_item, "roteiro_selecionado", None)
        print(f"[SERVICOS][GET][PC={precalc.id}] roteiro_id={getattr(roteiro,'id',None)}")
        if roteiro:
            insumos_filtrados = (
                InsumoEtapa.objects
                .filter(etapa__roteiro=roteiro, tipo_insumo="insumos")
                .select_related("materia_prima", "etapa")
            )
            print(f"[SERVICOS][GET][PC={precalc.id}] insumos_servico_count={insumos_filtrados.count()}")

            removed = PreCalculoServicoExterno.objects.filter(precalculo=precalc).delete()
            print(f"[SERVICOS][GET][PC={precalc.id}] removidos={removed}")

            criados = 0
            for insumo in insumos_filtrados:
                label = getattr(insumo, "descricao", "") or getattr(insumo, "nome", "") or ""
                mp = getattr(insumo, "materia_prima", None)
                for _ in range(3):
                    obj = PreCalculoServicoExterno.objects.create(
                        precalculo=precalc,
                        insumo=insumo,
                        desenvolvido_mm=getattr(insumo, "desenvolvido", 0) or 0,
                        peso_liquido=getattr(insumo, "peso_liquido", 0) or 0,
                        peso_bruto=getattr(insumo, "peso_bruto", 0) or 0,
                        preco_kg=None,
                        icms=None,
                        nome_insumo=label,
                        codigo_materia_prima=getattr(mp, "codigo", ""),
                        descricao_materia_prima=getattr(mp, "descricao", ""),
                        unidade=getattr(mp, "unidade", ""),
                        status="aguardando",
                        compras_solicitado_em=None,
                    )
                    criados += 1
                    print(f"[SERVICOS][GET][PC={precalc.id}] criado_id={obj.id} insumo_id={insumo.id} label='{label}'")

            precalc.refresh_from_db()
            total = precalc.servicos.count()
            print(f"[SERVICOS][GET][PC={precalc.id}] criados={criados} total_pos={total}")

    data = None
    if request.method == "POST":
        print(f"[SERVICOS][POST][PC={precalc.id}] keys_count={len(request.POST.keys())}")
        print(f"[SERVICOS][POST][PC={precalc.id}] keys_sample={list(request.POST.keys())[:30]}")
        data = request.POST.copy()

        total = int(data.get("sev-TOTAL_FORMS", 0))
        print(f"[SERVICOS][POST][PC={precalc.id}] sev-TOTAL_FORMS={total}")

        status_field = PreCalculoServicoExterno._meta.get_field("status")
        default_status = status_field.get_default() or status_field.choices[0][0]
        print(f"[SERVICOS][POST][PC={precalc.id}] default_status='{default_status}'")

        for i in range(total):
            for fld in ("lote_minimo", "desenvolvido_mm", "peso_liquido", "peso_bruto", "preco_kg", "icms", "peso_liquido_total"):
                key = f"sev-{i}-{fld}"
                val = data.get(key)
                if val:
                    try:
                        s = val.replace(",", ".")
                        dp = PreCalculoServicoExterno._meta.get_field(fld).decimal_places
                        quant = Decimal(1).scaleb(-dp)
                        num = Decimal(s).quantize(quant)
                        data[key] = str(num)
                    except Exception as e:
                        data[key] = s
                        print(f"[SERVICOS][POST][PC={precalc.id}] normalizacao_falhou key={key} val='{val}' err='{e}'")
            sk = f"sev-{i}-status"
            if not data.get(sk):
                data[sk] = default_status

    SevSet = inlineformset_factory(
        PreCalculo,
        PreCalculoServicoExterno,
        form=PreCalculoServicoExternoForm,
        formset=ServicoInlineFormSet,
        extra=0,
        can_delete=True,
    )
    fs_sev = SevSet(data if request.method == "POST" else None, instance=precalc, prefix="sev")
    print(f"[SERVICOS][FS][PC={precalc.id}] is_bound={fs_sev.is_bound} total_forms={fs_sev.total_form_count()}")

    try:
        mf_valid = fs_sev.management_form.is_valid()
        print(f"[SERVICOS][FS][PC={precalc.id}] mgmt_valid={mf_valid} mgmt_errors={fs_sev.management_form.errors}")
    except Exception as e:
        print(f"[SERVICOS][FS][PC={precalc.id}] mgmt_check_error='{e}'")

    # (mantém os prints acima) + imprime o queryset aceito do campo 'insumo'
    for i, form in enumerate(fs_sev.forms):
        inst = form.instance
        print(
            f"[SERVICOS][FSFORM][PC={precalc.id}] i={i} pk={getattr(inst,'pk',None)} "
            f"insumo_id={getattr(inst,'insumo_id',None)} "
            f"preco_kg={getattr(inst,'preco_kg',None)} "
            f"compras_solicitado_em={getattr(inst,'compras_solicitado_em',None)}"
        )
        if "insumo" in form.fields:
            qs_ids = list(form.fields["insumo"].queryset.values_list("pk", flat=True))
            posted = None
            if request.method == "POST":
                posted = request.POST.get(f"sev-{i}-insumo")
            print(f"[SERVICOS][CHOICES][PC={precalc.id}] i={i} qs_ids={qs_ids} posted={posted}")


    for form in fs_sev.forms:
        instancia = form.instance
        if instancia and instancia.insumo_id:
            form.fields["desenvolvido_mm"].initial = instancia.desenvolvido_mm
            form.fields["peso_liquido"].initial = instancia.peso_liquido
            form.fields["peso_bruto"].initial = instancia.peso_bruto

    if request.method == "POST" and "form_servicos_submitted" in request.POST:
        print(f"[SERVICOS][POST][PC={precalc.id}] submetido com {len(request.POST.keys())} campos")
        print(f"[SERVICOS][POST][PC={precalc.id}] keys_sample={list(request.POST.keys())[:25]}")

        valid = fs_sev.is_valid()
        print(f"[SERVICOS][CHK][PC={precalc.id}] fs_sev.is_valid()={valid}")

        if not valid:
            print(f"[SERVICOS][ERR][PC={precalc.id}] fs_errors={fs_sev.errors}")
            print(f"[SERVICOS][ERR][PC={precalc.id}] fs_non_form_errors={fs_sev.non_form_errors()}")

        if valid:
            fs_sev.save()
            print(f"[SERVICOS][SAVE][PC={precalc.id}] formset_salvo=True")
            amostra = list(precalc.servicos.values("id","lote_minimo","entrega_dias","fornecedor_id","icms","preco_kg")[:5])
            print(f"[SERVICOS][SAVE][PC={precalc.id}] amostra={amostra}")


            if form_precalculo and form_precalculo.is_valid():
                obs = form_precalculo.cleaned_data.get("observacoes_servicos")
                if obs is not None:
                    precalc.observacoes_servicos = obs
                    precalc.save(update_fields=["observacoes_servicos"])
                    print(f"[SERVICOS][SAVE][PC={precalc.id}] obs_servicos_atualizada=True")

            precalc.servicos.update(selecionado=False)
            print(f"[SERVICOS][SEL][PC={precalc.id}] zerou_selecionados=True")

            escolhidos = []
            for key in request.POST:
                if key.startswith("selecionado_insumo_"):
                    prefixo = request.POST[key]
                    escolhidos.append(prefixo)
                    for sev_form in fs_sev:
                        if sev_form.prefix == prefixo and not sev_form.cleaned_data.get("DELETE", False):
                            obj = sev_form.save(commit=False)
                            obj.selecionado = True
                            obj.save()
                            print(f"[SERVICOS][SEL][PC={precalc.id}] marcado_selecionado prefixo={prefixo} id={obj.id}")

            print(f"[SERVICOS][SEL][PC={precalc.id}] escolhidos={escolhidos}")
            fs_sev.save()
            print(f"[SERVICOS][SAVE][PC={precalc.id}] formset_salvo_pos_selecao=True")

            amostra = list(
                precalc.servicos.values("id", "insumo_id", "preco_kg", "compras_solicitado_em")[:20]
            )
            print(f"[SERVICOS][DBG][PC={precalc.id}] amostra={amostra}")

            try:
                print(f"[SERVICOS][CALL][PC={precalc.id}] disparar_emails_cotacao_servicos")
                enviados = disparar_emails_cotacao_servicos(request, precalc)
                print(f"[SERVICOS][RET][PC={precalc.id}] enviados_por_insumo={enviados}")
                if any(x["preco_kg"] in (None, 0) for x in amostra) and enviados == 0:
                    print(f"[SERVICOS][WARN][PC={precalc.id}] havia_pendentes_e_retornou_zero")
            except Exception as e:
                import traceback
                print(f"[SERVICOS][EXC][PC={precalc.id}] util_erro='{e}'")
                print(traceback.format_exc())

            salvo = True
        else:
            print(f"[SERVICOS][ABORT][PC={precalc.id}] formset_invalido")

    return salvo, form_precalculo, fs_sev