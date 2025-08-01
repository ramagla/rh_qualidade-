from django.forms import inlineformset_factory
from django.forms.models import BaseInlineFormSet
from decimal import Decimal
from django.db.models import Q
from comercial.forms.precalculos_form import PreCalculoForm, PreCalculoServicoExternoForm
from comercial.models.precalculo import PreCalculo, PreCalculoServicoExterno
from comercial.utils.email_cotacao_utils import disparar_emails_cotacao_servicos
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

    # Na tela de GET, busca no roteiro todos os insumos de setores de tratamento
    if request.method == "GET" and hasattr(precalc, "analise_comercial_item"):
        try:
            roteiro = getattr(precalc.analise_comercial_item, "roteiro_selecionado", None)

            if roteiro:
                etapas = roteiro.etapas.select_related("setor").all()
                for etapa in etapas:
                    def normalizar(texto):
                        return unicodedata.normalize("NFKD", texto) \
                                      .encode("ASCII", "ignore") \
                                      .decode("ASCII") \
                                      .lower()

                    setor_nome = normalizar(etapa.setor.nome or "")
                    palavras_chave = ["externo", "oleo", "oleamento", "tratamento"]
                    if any(p in setor_nome for p in palavras_chave):
                        for insumo in etapa.insumos.select_related("materia_prima").all():
                            if insumo.materia_prima_id:
                                tratamentos.append(insumo)

                # Remove serviços antigos não mais válidos
                servicos_invalidos = PreCalculoServicoExterno.objects.filter(
                    precalculo=precalc
                ).exclude(insumo__in=tratamentos)
                if servicos_invalidos.exists():
                    servicos_invalidos.delete()

                # Cria novos registros (3 cópias de cada insumo)
                novos_insumos = [
                    i for i in tratamentos
                    if not precalc.servicos.filter(insumo=i).exists()
                ]
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
                            # ** CORREÇÃO **: usa o campo unidade de InsumoEtapa, não de MateriaPrimaCatalogo
                            unidade=getattr(insumo, "unidade", ""),
                        )
                precalc.refresh_from_db()

        except Exception:
            pass

    data = None
    if request.method == "POST":
        data = request.POST.copy()
        total = int(data.get("sev-TOTAL_FORMS", 0))

        # Normaliza decimais no POST
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

    # Monta o formset
    SevSet = inlineformset_factory(
        PreCalculo,
        PreCalculoServicoExterno,
        form=PreCalculoServicoExternoForm,
        formset=ServicoInlineFormSet,
        extra=0,
        can_delete=True,
    )
    fs_sev = SevSet(data if request.method == "POST" else None, instance=precalc, prefix="sev")

    # POST: salva e dispara e-mails de cotação se for o caso
    if request.method == "POST" and "form_servicos_submitted" in request.POST:
        if fs_sev.is_valid():
            fs_sev.save()
            if form_precalculo and form_precalculo.is_valid():
                campo_obs = "observacoes_servicos"
                valor = form_precalculo.cleaned_data.get(campo_obs)
                setattr(precalc, campo_obs, valor)
                precalc.save(update_fields=[campo_obs])

            # Dentro do bloco POST do handler
            for sev in precalc.servicos.all():
                sev.selecionado = False
                sev.save(update_fields=["selecionado"])

            # Seleciona o correto com base nos radios enviados no POST
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
                disparar_emails_cotacao_servicos(request, precalc)




            salvo = True

    return salvo, form_precalculo, fs_sev
