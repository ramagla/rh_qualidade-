from django.forms import inlineformset_factory
from django.forms.models import BaseInlineFormSet
from decimal import Decimal
from comercial.forms.precalculos_form import PreCalculoServicoExternoForm
from comercial.models.precalculo import PreCalculo, PreCalculoServicoExterno
from comercial.utils.email_cotacao_utils import disparar_emails_cotacao_servicos
from tecnico.models.roteiro import InsumoEtapa
from django.db.models import Q 
from django.utils import timezone

class ServicoInlineFormSet(BaseInlineFormSet):
    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)
        for fld in ("lote_minimo", "entrega_dias", "fornecedor", "icms", "preco_kg"):
            if fld in form.fields:
                form.fields[fld].required = False
        return form


def processar_aba_servicos(request, precalc, submitted=False, servicos_respondidos=False, form_precalculo=None):
    salvo = False

    # 🔍 GET: Carrega os insumos de SERVIÇO do roteiro técnico
    if request.method == "GET" and hasattr(precalc, "analise_comercial_item") and not precalc.servicos.exists():
        roteiro = getattr(precalc.analise_comercial_item, "roteiro_selecionado", None)
        if roteiro:
            SE_ALIASES = {
                "insumos", "servico_externo", "serviço_externo", "servico", "serviço",
                "se", "SE", "SERVICO_EXTERNO", "SERVIÇO_EXTERNO", "INSUMOS"
            }
            MP_ALIASES = {"materia_prima", "matéria_prima", "mp", "MP", "MATERIA_PRIMA"}

            print(f"[SE][PC={precalc.id}] Repovoamento — Roteiro={getattr(roteiro, 'id', None)}")
            tipos_all = list(
                InsumoEtapa.objects.filter(etapa__roteiro=roteiro)
                .values_list("tipo_insumo", flat=True).distinct()
            )
            print(f"[SE][PC={precalc.id}] Tipos no roteiro: {tipos_all}")

            # Seleciona explicitamente SOMENTE insumos de serviço (excluindo aliases de MP)
            insumos_filtrados = (
                InsumoEtapa.objects
                .filter(etapa__roteiro=roteiro, tipo_insumo__in=SE_ALIASES)
                .exclude(tipo_insumo__in=MP_ALIASES)
                .select_related("materia_prima", "etapa")
            )
            print(f"[SE][PC={precalc.id}] Selecionados como Serviço: {insumos_filtrados.count()}")

            # Remove serviços anteriores
            removed = PreCalculoServicoExterno.objects.filter(precalculo=precalc).delete()
            print(f"[SE][PC={precalc.id}] Serviços limpos: {removed}")

            # Cria 3 cópias por insumo
            criados = 0
            for insumo in insumos_filtrados:
                label = getattr(insumo, "descricao", "") or getattr(insumo, "nome", "") or ""
                mp = getattr(insumo, "materia_prima", None)
                for _ in range(3):
                    PreCalculoServicoExterno.objects.create(
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
                    print(f"[SE][PC={precalc.id}] Criado serviço para insumo {insumo.id} (label='{label}')")

            precalc.refresh_from_db()
            print(f"[SE][PC={precalc.id}] Criados: {criados} | Total agora: {precalc.servicos.count()}")

    # 🧾 POST: Processa os dados do formulário
    data = None
    if request.method == "POST":
        data = request.POST.copy()
        total = int(data.get("sev-TOTAL_FORMS", 0))

        # Normaliza decimais e status
        status_field = PreCalculoServicoExterno._meta.get_field("status")
        default_status = status_field.get_default() or status_field.choices[0][0]

        for i in range(total):
            for fld in ("desenvolvido_mm", "peso_liquido", "peso_bruto", "preco_kg", "icms", "peso_liquido_total"):
                key = f"sev-{i}-{fld}"
                val = data.get(key)
                if val:
                    try:
                        s = val.replace(",", ".")
                        dp = PreCalculoServicoExterno._meta.get_field(fld).decimal_places
                        quant = Decimal(1).scaleb(-dp)
                        num = Decimal(s).quantize(quant)
                        data[key] = str(num)
                    except Exception:
                        data[key] = s
            sk = f"sev-{i}-status"
            if not data.get(sk):
                data[sk] = default_status

    # 🧱 Formset dos serviços
    SevSet = inlineformset_factory(
        PreCalculo,
        PreCalculoServicoExterno,
        form=PreCalculoServicoExternoForm,
        formset=ServicoInlineFormSet,
        extra=0,
        can_delete=True,
    )
    fs_sev = SevSet(data if request.method == "POST" else None, instance=precalc, prefix="sev")

    print(f"\n[SE][PC={precalc.id}] Formset (Pré-Renderização) - Serviços Externos | total_forms={fs_sev.total_form_count()}")
    for i, form in enumerate(fs_sev.forms):
        inst = form.instance
        print(
            f"Form {i} | pk={getattr(inst,'pk',None)} | insumo_id={getattr(inst,'insumo_id',None)} | "
            f"desenvolvido_mm={getattr(inst,'desenvolvido_mm',None)} | "
            f"peso_liquido={getattr(inst,'peso_liquido',None)} | peso_bruto={getattr(inst,'peso_bruto',None)}"
        )

    # Carrega os valores técnicos nos campos
    for form in fs_sev.forms:
        instancia = form.instance
        if instancia and instancia.insumo_id:
            form.fields["desenvolvido_mm"].initial = instancia.desenvolvido_mm
            form.fields["peso_liquido"].initial = instancia.peso_liquido
            form.fields["peso_bruto"].initial = instancia.peso_bruto

    # 📨 Salvar e enviar cotações, se aplicável
    if request.method == "POST" and "form_servicos_submitted" in request.POST:
        if fs_sev.is_valid():
            fs_sev.save()

            if form_precalculo and form_precalculo.is_valid():
                obs = form_precalculo.cleaned_data.get("observacoes_servicos")
                if obs is not None:
                    precalc.observacoes_servicos = obs
                    precalc.save(update_fields=["observacoes_servicos"])

            precalc.servicos.update(selecionado=False)
            for key in request.POST:
                if key.startswith("selecionado_insumo_"):
                    prefixo = request.POST[key]
                    for sev_form in fs_sev:
                        if sev_form.prefix == prefixo and not sev_form.cleaned_data.get("DELETE", False):
                            obj = sev_form.save(commit=False)
                            obj.selecionado = True
                            obj.save()

            fs_sev.save()

            try:
                resultado = disparar_emails_cotacao_servicos(request, precalc)
                # compatível com retorno int (0 = nada enviado)
                if isinstance(resultado, int):
                    print(f"[SERVICOS][EMAIL] enviados_por_insumo={resultado}")
                else:
                    enviados, ignorados, motivos = resultado
                    print(f"[SERVICOS][EMAIL] enviados={enviados} ignorados={ignorados} motivos={motivos}")
            except Exception as e:
                import traceback
                print("[SERVICOS][EMAIL][ERRO]", e)
                print(traceback.format_exc())


            salvo = True

    return salvo, form_precalculo, fs_sev
