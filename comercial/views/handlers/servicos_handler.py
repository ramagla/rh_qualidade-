from django.forms import inlineformset_factory
from django.forms.models import BaseInlineFormSet
from decimal import Decimal
from comercial.forms.precalculos_form import PreCalculoServicoExternoForm
from comercial.models.precalculo import PreCalculo, PreCalculoServicoExterno
from comercial.utils.email_cotacao_utils import disparar_emails_cotacao_servicos
from tecnico.models.roteiro import InsumoEtapa

class ServicoInlineFormSet(BaseInlineFormSet):
    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)
        for fld in ("lote_minimo", "entrega_dias", "fornecedor", "icms", "preco_kg"):
            if fld in form.fields:
                form.fields[fld].required = False
        return form


def processar_aba_servicos(request, precalc, submitted=False, servicos_respondidos=False, form_precalculo=None):
    salvo = False

    # 🔍 GET: Carrega os insumos do tipo 'insumos' do roteiro técnico
    if request.method == "GET" and hasattr(precalc, "analise_comercial_item") and not precalc.servicos.exists():
        roteiro = getattr(precalc.analise_comercial_item, "roteiro_selecionado", None)
        if roteiro:
            etapas = roteiro.etapas.prefetch_related("insumos").all()
            insumos_filtrados = []

            for etapa in etapas:
                for insumo in etapa.insumos.filter(tipo_insumo="insumos"):
                    insumos_filtrados.append(insumo)

            # Remove os serviços anteriores
            PreCalculoServicoExterno.objects.filter(precalculo=precalc).delete()

            # Cria 3 cópias para cada insumo
            for insumo in insumos_filtrados:
                for _ in range(3):
                    PreCalculoServicoExterno.objects.create(
                        precalculo=precalc,
                        insumo=insumo,
                        desenvolvido_mm=insumo.desenvolvido or 0,
                        peso_liquido=insumo.peso_liquido or 0,
                        peso_bruto=insumo.peso_bruto or 0,
                        preco_kg=None,
                        icms=None,
                        nome_insumo=getattr(insumo.materia_prima, "codigo", ""),
                        codigo_materia_prima=getattr(insumo.materia_prima, "codigo", ""),
                        descricao_materia_prima=getattr(insumo.materia_prima, "descricao", ""),
                        unidade=getattr(insumo.materia_prima, "unidade", ""),
                    )

            precalc.refresh_from_db()

    # 🧾 POST: Processa os dados do formulário
    data = None
    if request.method == "POST":
        data = request.POST.copy()
        total = int(data.get("sev-TOTAL_FORMS", 0))

        # Normaliza os decimais
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

    print("\n[DEBUG] Formset (Pré-Renderização) - Serviços Externos")
    for i, form in enumerate(fs_sev.forms):
        inst = form.instance
        print(
            f"Form {i} | pk={inst.pk} | insumo_id={inst.insumo_id} | "
            f"desenvolvido_mm={inst.desenvolvido_mm} | "
            f"peso_liquido={inst.peso_liquido} | peso_bruto={inst.peso_bruto}"
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

            # Salva observações, se houver
            if form_precalculo and form_precalculo.is_valid():
                campo_obs = "observacoes_servicos"
                valor = form_precalculo.cleaned_data.get(campo_obs)
                setattr(precalc, campo_obs, valor)
                precalc.save(update_fields=[campo_obs])

            # Define todos como não selecionados
            precalc.servicos.update(selecionado=False)

            # Define como selecionado com base nos radios
            for key in request.POST:
                if key.startswith("selecionado_insumo_"):
                    prefixo = request.POST[key]
                    for sev_form in fs_sev:
                        if sev_form.prefix == prefixo and not sev_form.cleaned_data.get("DELETE", False):
                            sev = sev_form.save(commit=False)
                            sev.selecionado = True
                            sev.save()

            fs_sev.save()

            # Dispara e-mails caso necessário
            if not servicos_respondidos:
                disparar_emails_cotacao_servicos(request, precalc)

            salvo = True

    return salvo, form_precalculo, fs_sev