from django.forms import inlineformset_factory
from django.forms.models import BaseInlineFormSet
from decimal import Decimal
from django.db.models import Q
from comercial.forms.precalculos_form import PreCalculoForm, PreCalculoServicoExternoForm
from comercial.models.precalculo import PreCalculo, PreCalculoServicoExterno
from comercial.utils.email_cotacao_utils import disparar_email_cotacao_servico
from tecnico.models.roteiro import InsumoEtapa
import unicodedata

class ServicoInlineFormSet(BaseInlineFormSet):
    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)
        for fld in ("lote_minimo", "entrega_dias", "fornecedor", "icms", "preco_kg"):
            if fld in form.fields:
                form.fields[fld].required = False
        return form

def processar_aba_servicos(request, precalc, submitted=False, servicos_respondidos=False, form_precalculo=None):
    salvo = False
    tratamentos = []

    if request.method == "GET" and hasattr(precalc, "analise_comercial_item"):
        try:
            item = precalc.analise_comercial_item.item
            roteiro = getattr(item, "roteiro", None)
            if roteiro:
                etapas = roteiro.etapas.select_related("setor").all()
                for etapa in etapas:
                    def normalizar(texto):
                        return unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII").lower()

                    setor_nome = normalizar(etapa.setor.nome or "")
                    palavras_chave = ["externo", "oleo", "oleamento", "tratamento"]
                    if any(palavra in setor_nome for palavra in palavras_chave):
                        for insumo in etapa.insumos.select_related("materia_prima").all():
                            if insumo.materia_prima_id:
                                tratamentos.append(insumo)

                servicos_invalidos = PreCalculoServicoExterno.objects.filter(precalculo=precalc).exclude(insumo__in=tratamentos)
                if servicos_invalidos.exists():
                    servicos_invalidos.delete()

                novos_insumos = [i for i in tratamentos if not precalc.servicos.filter(insumo=i).exists()]
                for insumo in novos_insumos:
                    for _ in range(3):
                        PreCalculoServicoExterno.objects.create(
                            precalculo=precalc,
                            insumo=insumo,
                            desenvolvido_mm=0,
                            peso_liquido=0,
                            peso_bruto=0,
                            preco_kg=None,
                            icms=None,
                            nome_insumo=getattr(insumo.materia_prima, "codigo", ""),
                            codigo_materia_prima=getattr(insumo.materia_prima, "codigo", ""),
                            descricao_materia_prima=getattr(insumo.materia_prima, "descricao", ""),
                            unidade=getattr(insumo.materia_prima, "unidade", ""),
                        )
                precalc.refresh_from_db()

        except Exception:
            pass

    data = None
    if request.method == "POST":
        data = request.POST.copy()
        total = int(data.get("sev-TOTAL_FORMS", 0))

        status_field = PreCalculoServicoExterno._meta.get_field("status")
        default_status = status_field.get_default() or status_field.choices[0][0]

        for i in range(total):
            for fld in ("desenvolvido_mm", "peso_liquido", "peso_bruto", "preco_kg", "icms", "peso_bruto_total"):
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

    SevSet = inlineformset_factory(
        PreCalculo,
        PreCalculoServicoExterno,
        form=PreCalculoServicoExternoForm,
        formset=ServicoInlineFormSet,
        extra=0,
        can_delete=True,
    )
    fs_sev = SevSet(data if request.method == "POST" else None, instance=precalc, prefix="sev")

    if request.method == "POST" and "form_servicos_submitted" in request.POST:
        if fs_sev.is_valid():
            fs_sev.save()

            if form_precalculo and form_precalculo.is_valid():
                form_precalculo.instance = precalc
                form_precalculo.save()

            # Reseta todos como não selecionados inicialmente
            for sev in precalc.servicos.all():
                sev.selecionado = False
                sev.save(update_fields=["selecionado"])

            # Verifica os campos 'selecionado_insumo_<id>' do POST
            for key in request.POST:
                if key.startswith("selecionado_insumo_"):
                    prefixo = request.POST[key]
                    for sev_form in fs_sev:
                        if sev_form.prefix == prefixo and not sev_form.cleaned_data.get("DELETE", False):
                            sev = sev_form.save(commit=False)
                            sev.selecionado = True
                            sev.save()

            fs_sev.save()

            if not servicos_respondidos:
                enviados = set()
                for sev in precalc.servicos.all():
                    codigo = getattr(sev.insumo.materia_prima, "codigo", None)
                    if codigo and not sev.preco_kg and codigo not in enviados:
                        disparar_email_cotacao_servico(request, sev)
                        enviados.add(codigo)

            salvo = True

    return salvo, form_precalculo, fs_sev
