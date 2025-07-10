from django.forms import inlineformset_factory
from django.forms.models import BaseInlineFormSet
from decimal import Decimal
from django.db.models import Q
from comercial.forms.precalculos_form import PreCalculoServicoExternoForm, PreCalculoForm
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

def processar_aba_servicos(request, precalc, submitted=False, servicos_respondidos=False):
    print("🔧 [SERVIÇOS] Iniciando processar_aba_servicos()")
    print(f"📄 Método: {request.method}")
    print(f"📍 Serviços já existentes: {precalc.servicos.count()}")
    print(f"✅ Possui análise comercial? {'Sim' if hasattr(precalc, 'analise_comercial_item') else 'Não'}")

    submitted = request.method == "POST"
    print(f"📅 Submitted: {submitted}")

    tratamentos = []

    if not submitted and hasattr(precalc, "analise_comercial_item"):
        try:
            item = precalc.analise_comercial_item.item
            print(f"🧹 Item do pré-cálculo: {item} – ID: {getattr(item, 'id', 'sem id')}")

            if not hasattr(item, "roteiro") or not item.roteiro:
                print("⚠️ Item não possui roteiro associado. Encerrando processamento de serviços.")
            else:
                roteiro = item.roteiro
                etapas = roteiro.etapas.select_related("setor").all()
                print(f"🎯 Etapas encontradas: {etapas.count()}")
                for etapa in etapas:
                    print(f"    Etapa #{etapa.etapa} | Setor = '{etapa.setor.nome}'")
                    def normalizar(texto):
                        return unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII").lower()

                    setor_nome = normalizar(etapa.setor.nome or "")
                    palavras_chave = ["externo", "oleo", "oleamento", "tratamento"]
                    if any(palavra in setor_nome for palavra in palavras_chave):
                        for insumo in etapa.insumos.select_related("materia_prima").all():
                            print(f"      ➕ Insumo detectado: {insumo} (MP: {insumo.materia_prima})")
                            if insumo.materia_prima_id:
                                tratamentos.append(insumo)
                            else:
                                print(f"⚠️ Ignorado: insumo sem matéria-prima em etapa {etapa.etapa}")

                print(f"🔍 Insumos de tratamento encontrados: {len(tratamentos)}")

                servicos_invalidos = PreCalculoServicoExterno.objects.filter(precalculo=precalc).exclude(insumo__in=tratamentos)
                if servicos_invalidos.exists():
                    print(f"🚹 Excluindo {servicos_invalidos.count()} serviços externos inválidos")
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
                        print(f"➕ Serviço criado (fixo) para insumo: {insumo}")
                precalc.refresh_from_db()

        except Exception as e:
            print(f"🛑 Erro ao processar etapas ou insumos: {e}")
    else:
        if not hasattr(precalc, "analise_comercial_item"):
            print("⚠️ análise_comercial_item ausente. Ignorando criação de serviços.")
        else:
            print("⚠️ Requisição POST — ignorando criação automática de insumos.")

    data = None
    if submitted:
        print("📎 Convertendo valores do POST...")
        data = request.POST.copy()
        total = int(data.get("sev-TOTAL_FORMS", 0))
        print(f"📊 TOTAL_FORMS: {total}")

        status_field = PreCalculoServicoExterno._meta.get_field("status")
        default_status = status_field.get_default() or status_field.choices[0][0]

        for i in range(total):
            for fld in ("desenvolvido_mm", "peso_liquido", "peso_bruto", "preco_kg", "icms"):
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
                        print(f"⚠️ Erro ao converter {key} = '{val}': {e}")
                        data[key] = s
            sk = f"sev-{i}-status"
            if not data.get(sk):
                data[sk] = default_status

    form_precalculo = PreCalculoForm(request.POST if submitted else None, instance=precalc)

    SevSet = inlineformset_factory(
        PreCalculo,
        PreCalculoServicoExterno,
        form=PreCalculoServicoExternoForm,
        formset=ServicoInlineFormSet,
        extra=0,
        can_delete=True,
    )
    fs_sev = SevSet(data if submitted else None, instance=precalc, prefix="sev")

    print(f"📝 form_precalculo válido? {form_precalculo.is_valid()}")
    print(f"📋 fs_sev válido? {fs_sev.is_valid()}")
    if not fs_sev.is_valid():
        print("❌ Erros do fs_sev:")
        print(fs_sev.errors)
        print(fs_sev.non_form_errors())

    salvo = False
    if submitted and form_precalculo.is_valid() and fs_sev.is_valid():
        print("✅ Salvando dados de serviços...")
        form_precalculo.save()
        selecionado = request.POST.get("servico_selecionado")
        print(f"🏷️ Serviço selecionado (prefix): {selecionado}")

        for sev_form in fs_sev:
            if sev_form.cleaned_data and not sev_form.cleaned_data.get("DELETE", False):
                sev = sev_form.save(commit=False)
                sev.selecionado = (sev_form.prefix == selecionado)
                sev.save()
                print(f"💾 Serviço salvo: {sev}")

        fs_sev.save()

        if not servicos_respondidos:
            print("📤 Disparando e-mails de cotação...")
            enviados = set()
            for sev in precalc.servicos.all():
                codigo = getattr(sev.insumo.materia_prima, "codigo", None)
                if codigo and not sev.preco_kg and codigo not in enviados:
                    print(f"✉️ Enviando para código: {codigo}")
                    disparar_email_cotacao_servico(request, sev)
                    enviados.add(codigo)

        salvo = True

    print(f"🔚 Retornando: salvo={salvo}, form_precalculo, fs_sev")
    return salvo, form_precalculo, fs_sev
