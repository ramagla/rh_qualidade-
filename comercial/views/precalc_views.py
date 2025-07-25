from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from comercial.models import Cotacao
from comercial.models.precalculo import (
    AnaliseComercial,
    PreCalculo,
    PreCalculoMaterial,
    PreCalculoServicoExterno,
)
from comercial.forms.precalculos_form import (
    AnaliseComercialForm,
    PreCalculoForm,
    RegrasCalculoForm,
    AvaliacaoTecnicaForm,
    DesenvolvimentoForm,
)
from qualidade_fornecimento.models.fornecedor import FornecedorQualificado
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo
from django.db.models import Q

# Handlers das abas do formulário de pré-cálculo
from comercial.views.handlers.analise_handler import processar_aba_analise
from comercial.views.handlers.avaliacao_handler import processar_aba_avaliacao
from comercial.views.handlers.desenvolvimento_handler import processar_aba_desenvolvimento
from comercial.views.handlers.ferramentas_handler import processar_aba_ferramentas
from comercial.views.handlers.materiais_handler import processar_aba_materiais
from comercial.views.handlers.precofinal_handler import processar_aba_precofinal
from comercial.views.handlers.regras_handler import processar_aba_regras
from comercial.views.handlers.roteiro_handler import processar_aba_roteiro
from comercial.views.handlers.servicos_handler import processar_aba_servicos

from collections import Counter




from decimal import Decimal, ROUND_HALF_UP

from tecnico.models.roteiro import RoteiroProducao

@login_required
@permission_required("comercial.view_precalculo", raise_exception=True)
def itens_precaculo(request, pk):
    cot = get_object_or_404(Cotacao, pk=pk)
    precalculos = PreCalculo.objects.filter(cotacao=cot).order_by("numero")

    # Enriquecimento de cada pré-cálculo
    for precalc in precalculos:
        precalc.tipo_precalculo = "Item de Cotação"
        precalc.total_materiais = precalc.materiais.count()
        precalc.total_servicos = precalc.servicos.count()
        precalc.analise_ok = hasattr(precalc, "analise_comercial_item")
        precalc.regras_ok = hasattr(precalc, "regras_calculo_item")
        precalc.avaliacao_ok = hasattr(precalc, "avaliacao_tecnica_item")
        precalc.desenvolvimento_ok = hasattr(precalc, "desenvolvimento_item")

        # Valor Ferramental
        precalc.valor_ferramental = sum(
            f.ferramenta.valor_total or Decimal("0.00")
            for f in precalc.ferramentas_item.all()
        )

        # Preço efetivo (override manual ou selecionado)
        preco_final = (
            precalc.preco_manual
            if precalc.preco_manual and precalc.preco_manual > Decimal("0.00")
            else (precalc.preco_selecionado or Decimal("0.00"))
        )

        # Valor Total = Preço Escolhido × Qtde Estimada
        qtde = getattr(precalc.analise_comercial_item, "qtde_estimada", 0) or 0
        precalc.valor_total = preco_final * Decimal(qtde)

        # Total Geral = Valor Total + Ferramental
        precalc.total_geral = precalc.valor_total + precalc.valor_ferramental

        # Preço Escolhido com percentual (%)
        if precalc.preco_manual and precalc.preco_manual > Decimal("0.00"):
            custo_unitario = precalc.calcular_precos_com_impostos()[0]["unitario"]
            percentual_manual = (
                (preco_final - custo_unitario)
                / custo_unitario
                * Decimal("100")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            precalc.preco_margem_formatado = f"{preco_final:.2f} ({percentual_manual}%)"
        else:
            precalc.preco_margem_formatado = next(
                (
                    f"{item['unitario']:.2f} ({item['percentual']}%)"
                    for item in precalc.calcular_precos_com_impostos()
                    if round(item["unitario"], 4) == round(preco_final, 4)
                ),
                f"{preco_final:.2f}" if preco_final else None
            )

    # Paginação
    paginator = Paginator(precalculos, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Contagem de itens por status de análise
    lista_status = []
    for p in precalculos:
        if hasattr(p, "analise_comercial_item"):
            lista_status.append(p.analise_comercial_item.status)
        else:
            lista_status.append("andamento")
    contagem = Counter(lista_status)

    return render(request, "cotacoes/precalculo_lista.html", {
        "cotacao": cot,
        "precalculos": precalculos,
        "page_obj": page_obj,
        "status_aprovado": contagem.get("aprovado", 0),
        "status_reprovado": contagem.get("reprovado", 0),
        "status_amostras": contagem.get("amostras", 0),
        "status_andamento": contagem.get("andamento", 0),
    })



@login_required
@permission_required("comercial.change_precalculo", raise_exception=True)
def editar_precaculo(request, pk):
    tipoRoteiro = request.GET.get("tipoRoteiro", "")
    precalc = get_object_or_404(PreCalculo, pk=pk)
    cot    = precalc.cotacao
    salvo  = False
    mensagem_precofinal = None   



    # identifica aba submetida
    if request.method == "GET":
        aba = request.GET.get("aba", "analise")
    else:
        aba = request.POST.get("aba")
    salvo = False

    materiais_respondidos = False
    servicos_respondidos = False
    
    # form principal (observações gerais)
    # form principal (observações gerais) — inicializa com POST para abas que usam observações
    if request.method == "POST" and aba in ["materiais", "servicos", "roteiro"]:
        data = request.POST.copy()

        # Corrige vírgulas decimais de campos de peso para evitar crash
        for k in data:
            if "peso_bruto_total" in k:
                data[k] = data[k].replace(".", "").replace(",", ".")

        form_precalculo = PreCalculoForm(data, instance=precalc)
    else:
        form_precalculo = PreCalculoForm(instance=precalc)



    # inicializa variáveis de retorno
    form_analise = form_regras = form_avali = form_desenv = form_precofinal = form_roteiro = None

    fs_mat = fs_sev = fs_rot = fs_ferr = None
    servicos_respondidos = False  # ✅ sempre inicializar



    # POST: processa a aba correta via handler
    if request.method == "POST":
        if aba == "analise" and "form_analise_submitted" in request.POST:
            form_analise = AnaliseComercialForm(
                request.POST,
                instance=getattr(precalc, "analise_comercial_item", None),
                cotacao=precalc.cotacao
            )
            salvo, form_analise = processar_aba_analise(request, precalc)

        elif aba == "regras" and "form_regras_submitted" in request.POST:
            salvo, form_regras = processar_aba_regras(request, precalc)

        elif aba == "avali" and "form_avaliacao_submitted" in request.POST:
            salvo, form_avali = processar_aba_avaliacao(request, precalc)

        elif aba == "desenv" and "form_desenvolvimento_submitted" in request.POST:
            salvo, form_desenv = processar_aba_desenvolvimento(request, precalc)

        elif aba == "precofinal" and "form_precofinal_submitted" in request.POST:
            salvo, form_precofinal, precos_sem_impostos, precos_com_impostos, mensagem_precofinal = processar_aba_precofinal(request, precalc)

        elif aba == "materiais" and (
            "form_materiais_submitted" in request.POST or
            any(k.startswith("mat-") for k in request.POST)
        ):
            materiais_respondidos = precalc.materiais.filter(preco_kg__isnull=False).exists()
            salvo, _, fs_mat = processar_aba_materiais(request, precalc, materiais_respondidos, form_precalculo)


        elif aba == "servicos" and (
            "form_servicos_submitted" in request.POST or
            any(k.startswith("sev-") for k in request.POST)
        ):
            faltam = precalc.servicos.filter(
                Q(preco_kg__isnull=True) | Q(preco_kg=0)
            ).exists()
            servicos_respondidos = not faltam
            salvo, _, fs_sev = processar_aba_servicos(
                request,
                precalc,
                servicos_respondidos=servicos_respondidos,
                form_precalculo=form_precalculo,
            )



        elif aba == "roteiro" and "form_roteiro_submitted" in request.POST:
            salvo, fs_rot = processar_aba_roteiro(request, precalc, form_precalculo)




        elif aba == "ferramentas" and "form_ferramentas_submitted" in request.POST:
            salvo, fs_ferr = processar_aba_ferramentas(request, precalc)

        # salvamento seguro do campo de observação
        if form_precalculo and form_precalculo.is_valid():
            campo_obs = {
                'materiais': 'observacoes_materiais',
                'servicos' : 'observacoes_servicos',
                'roteiro'  : 'observacoes_roteiro',
            }.get(aba)


            # ⚠️ Recarrega os valores anteriores das outras observações para evitar sobrescrita
            campos_obs = ["observacoes_materiais", "observacoes_servicos", "observacoes_roteiro"]
            for campo in campos_obs:
                if campo != campo_obs:  # preserva os campos não submetidos agora
                    setattr(precalc, campo, getattr(precalc, campo))

            if campo_obs and campo_obs in form_precalculo.cleaned_data:
                valor = form_precalculo.cleaned_data[campo_obs]
                setattr(precalc, campo_obs, valor)
                precalc.save(update_fields=[campo_obs])
                salvo = True  # força mensagem e redirect mesmo sem mudanças no formset






        
        # Mensagens
        print("🧪 DEBUG FINAL")
        print("salvo:", salvo)
        print("aba:", aba)
        print("mensagem_precofinal:", mensagem_precofinal)

        if salvo and aba != "atualizar_materiais":
            print("✅ ENVIANDO MENSAGEM DE SUCESSO")
            messages.success(request, "Pré-cálculo atualizado com sucesso.")
            return redirect("itens_precaculo", pk=precalc.cotacao.pk)


        elif aba == "precofinal":
            print("⚠️ ENVIANDO MENSAGEM DE AVISO")
            messages.warning(request, mensagem_precofinal or "Nenhuma alteração válida foi identificada para salvar.")

        else:
            print("❌ ENVIANDO MENSAGEM DE ERRO")
            messages.error(request, "Nenhuma alteração válida foi identificada para salvar.")




    # GET ou fallback: carrega todas as abas para navegação
    if not form_analise:
        form_analise = AnaliseComercialForm(
            instance=getattr(precalc, "analise_comercial_item", None),
            cotacao=precalc.cotacao
        )


    if not form_regras:
        _, form_regras = processar_aba_regras(request, precalc)
    if not form_avali:
        _, form_avali = processar_aba_avaliacao(request, precalc)
    if not form_desenv:
        _, form_desenv = processar_aba_desenvolvimento(request, precalc)

    # ⚠️ NUNCA chame o processar_aba_precofinal de novo se aba for "precofinal"
    if not form_precofinal:
        if aba == "precofinal":
            # Usa os valores que já foram retornados no POST
            pass
        else:
            _, form_precofinal, precos_sem_impostos, precos_com_impostos, _ = processar_aba_precofinal(request, precalc)

    # Segurança: se precos ainda não estiverem definidos
    if "precos_sem_impostos" not in locals():
        precos_sem_impostos = precalc.calcular_precos_sem_impostos()
    if "precos_com_impostos" not in locals():
        precos_com_impostos = precalc.calcular_precos_com_impostos()



    # Carrega apenas se for GET puro e formset ainda não tiver sido processado
    if not fs_mat and (
        request.method == "GET" or
        any(k.startswith("mat-") for k in request.POST)
    ):
        materiais_respondidos = precalc.materiais.filter(preco_kg__isnull=False).exists()
        _, form_precalculo, fs_mat = processar_aba_materiais(
            request, precalc, materiais_respondidos, form_precalculo=form_precalculo
    )


    if not fs_sev and (
        request.method == "GET" or
        any(k.startswith("sev-") for k in request.POST)
    ):
        faltam = precalc.servicos.filter(
            Q(preco_kg__isnull=True) | Q(preco_kg=0)
        ).exists()
        servicos_respondidos = not faltam
        _, form_precalculo, fs_sev = processar_aba_servicos(
            request,
            precalc,
            servicos_respondidos=servicos_respondidos,
            form_precalculo=form_precalculo,
        )



    if not fs_rot:
        _, fs_rot = processar_aba_roteiro(request, precalc)
        form_roteiro = None  # ou use fs_rot se quiser alimentar o form principal de roteiro








    if not fs_ferr:
        _, fs_ferr = processar_aba_ferramentas(request, precalc)

    # campos de observações para o template
        campos_obs = [
        ("material_fornecido", "material_fornecido_obs"),
        ("requisitos_entrega", "requisitos_entrega_obs"),
        ("requisitos_pos_entrega", "requisitos_pos_entrega_obs"),
        ("requisitos_comunicacao", "requisitos_comunicacao_obs"),
        ("requisitos_notificacao", "requisitos_notificacao_obs"),
        ("especificacao_embalagem", "especificacao_embalagem_obs"),
        ("especificacao_identificacao", "especificacao_identificacao_obs"),
        ("tipo_embalagem", "tipo_embalagem_obs"),
    ]

    campos_obs_tecnica = [
        ("possui_projeto", "projeto_obs"),
        ("precisa_dispositivo", "dispositivo_obs"),
        ("caracteristicas_criticas", "criticas_obs"),
        ("precisa_amostras", "amostras_obs"),
        ("restricao_dimensional", "restricao_obs"),
        ("acabamento_superficial", "acabamento_obs"),
        ("validacao_metrologica", "metrologia_obs"),
        ("rastreabilidade", "rastreabilidade_obs"),
        ("metas_a", "metas_a_obs"),
        ("metas_b", "metas_b_obs"),
        ("metas_c", "metas_c_obs"),
        ("metas_d", "metas_d_obs"),
        ("seguranca", "seguranca_obs"),
        ("requisito_especifico", "requisito_especifico_obs"),
    ]


    perguntas_avaliacao_tecnica = [
        {"campo": "caracteristicas_criticas", "label": "1. Existe característica especial além das relacionadas nas especificações?", "obs": "criticas_obs"},
        {"campo": "item_aparencia", "label": "2. A peça é item de aparência?", "obs": "item_aparencia_obs"},
        {"campo": "fmea", "label": "3. O cliente forneceu FMEA de produto?", "obs": "fmea_obs"},
        {"campo": "teste_solicitado", "label": "4. O cliente solicitou algum teste além dos relacionados nas especificações?", "obs": "teste_solicitado_obs"},
        {"campo": "lista_fornecedores", "label": "5. O cliente forneceu lista de fornecedores/materiais aprovados?", "obs": "lista_fornecedores_obs"},
        {"campo": "normas_disponiveis", "label": "6. As normas/especificações/requisitos estão disponíveis?", "obs": "normas_disponiveis_obs"},
        {"campo": "requisitos_regulamentares", "label": "7. São aplicáveis requisitos estatutários/regulamentares?", "obs": "requisitos_regulamentares_obs"},
        {"campo": "requisitos_adicionais", "label": "8. Existem requisitos adicionais e/ou não declarados pelo cliente?", "obs": "requisitos_adicionais_obs"},
        {"campo": "metas_a", "label": "9a. Metas de qualidade (exemplo: PPM)?", "obs": "metas_a_obs"},
        {"campo": "metas_b", "label": "9b. Metas de produtividade?", "obs": "metas_b_obs"},
        {"campo": "metas_c", "label": "9c. Metas de desempenho (exemplo: Cp, Cpk, etc.)?", "obs": "metas_c_obs"},
        {"campo": "metas_confiabilidade", "label": "9d. Metas de confiabilidade (exemplo: vida útil)?", "obs": "metas_confiabilidade_obs"},
        {"campo": "metas_d", "label": "9e. Metas de funcionamento?", "obs": "metas_d_obs"},
        {"campo": "seguranca", "label": "10. Os requisitos sobre o item de segurança foram considerados?", "obs": "seguranca_obs"},
        {"campo": "requisito_especifico", "label": "11. O cliente forneceu o requisito específico?", "obs": "requisito_especifico_obs"},
    ]

    item_id = getattr(getattr(precalc, "analise_comercial_item", None), "item_id", None)
    tipo_item = request.GET.get("tipo_roteiro") or getattr(
        getattr(precalc.analise_comercial_item, "item", None), "tipo_item", "A"
    )
    tipo_roteiro_choices = RoteiroProducao._meta.get_field("tipo_roteiro").choices


    return render(request, "cotacoes/form_precalculo.html", {
    "cotacao": cot,
    "precalc": precalc,
    "form_precalculo": form_precalculo,
    "form_analise": form_analise,
    "form_regras": form_regras,
    "form_avali": form_avali,
    "form_desenv": form_desenv,
    "form_precofinal": form_precofinal,
    "form_roteiro": form_roteiro,
    "fs_mat": fs_mat,
    "fs_sev": fs_sev,
    "fs_rot": fs_rot,
    "fs_ferr": fs_ferr,
    "campos_obs": campos_obs,
    "campos_obs_tecnica": campos_obs_tecnica,
    "item_id": item_id,
    "edicao": True,
    "aba_ativa": aba,
    "precos_sem_impostos": precos_sem_impostos,
    "precos_com_impostos": precos_com_impostos,
    "analise": precalc.analise_comercial_item,
    "materiais_respondidos": materiais_respondidos,
    "servicos_respondidos": servicos_respondidos,
    "perguntas_avaliacao_tecnica": perguntas_avaliacao_tecnica,
     "tipo_item": tipo_item,
        "tipo_roteiro_choices": tipo_roteiro_choices,    # lista de (value,label)
})


from comercial.models.item import Item  # certifique-se de importar
# ...


from datetime import datetime

@login_required
@permission_required('comercial.add_precalculomaterial', raise_exception=True)
def criar_precaculo(request, pk):
    cot = get_object_or_404(Cotacao, pk=pk)

    aba = next((k.replace("form_", "").replace("_submitted", "") for k in request.POST if k.startswith("form_")), None)
    novo_item_instancia = None


    data_str = request.POST.get("novo_data_revisao")
    data_formatada = None
    if data_str:
        try:
            data_formatada = datetime.strptime(data_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    codigo_desenho = request.POST.get("novo_codigo_desenho") or ""

    # Intercepta criação de novo item antes de instanciar o formulário
    if request.method == "POST" and aba == "analise" and request.POST.get("item") == "__novo__":
        novo_item_instancia = Item.objects.create(
            cliente=cot.cliente,
            tipo_item="Cotacao",
            codigo=codigo_desenho,            
            descricao=request.POST.get("novo_descricao") or "",
            ncm=request.POST.get("novo_ncm") or "",
            lote_minimo=request.POST.get("novo_lote_minimo") or 1,
            revisao=request.POST.get("novo_revisao") or "",
            data_revisao=data_formatada,
            codigo_desenho=request.POST.get("novo_codigo_desenho") or "",
            ipi=request.POST.get("novo_ipi") or None,
            automotivo_oem=bool(request.POST.get("novo_automotivo_oem")),
            requisito_especifico=bool(request.POST.get("novo_requisito_especifico")),
            item_seguranca=bool(request.POST.get("novo_item_seguranca")),
            status="Ativo",
        )
        mutable = request.POST._mutable
        request.POST._mutable = True
        request.POST["item"] = str(novo_item_instancia.pk)
        request.POST._mutable = mutable

    item_id = request.POST.get("item")
    item_instancia = None
    if aba == "analise":
        if item_id == "__novo__" and novo_item_instancia:
            item_instancia = novo_item_instancia
        elif item_id and item_id != "__novo__":
            try:
                item_instancia = Item.objects.get(pk=item_id)
            except Item.DoesNotExist:
                messages.error(request, "O item selecionado não foi encontrado.")
                return redirect(request.path)

        form_analise = AnaliseComercialForm(
            request.POST,
            cotacao=cot,
            edicao=False,
            instance=AnaliseComercial(item=item_instancia) if item_instancia else None
        )
    else:
        form_analise = AnaliseComercialForm(None, cotacao=cot, edicao=False)
    form_analise.data = form_analise.data.copy()
    if aba == "regras":
        form_regras = RegrasCalculoForm(
            request.POST or None,
            initial={
                "icms": cot.icms,
                "pis": Decimal("0.65"),
                "confins": Decimal("3.00"),
                "ir": Decimal("1.20"),
                "csll": Decimal("1.08"),
                "df": Decimal("2.50"),
                "dv": Decimal("5.00"),
            } if not request.POST else None
        )
    else:
        form_regras = RegrasCalculoForm()

    if request.method == "POST":
        if not aba:
            messages.error(request, "Nenhuma aba foi enviada.")
            return redirect(request.path)

        print("🛠 Erros do form_analise:", form_analise.errors)

        if aba == "analise" and form_analise.is_valid():
            # Só aqui criamos o pré-cálculo
            ultimo = PreCalculo.objects.filter(cotacao=cot).order_by("-numero").first()
            proximo_numero = (ultimo.numero + 1) if ultimo else 1
            novo = PreCalculo.objects.create(cotacao=cot, numero=proximo_numero, criado_por=request.user)

            def preencher_assinatura(obj):
                obj.precalculo = novo
                obj.usuario = request.user
                obj.assinatura_nome = request.user.get_full_name() or request.user.username
                obj.assinatura_cn = request.user.email
                obj.data_assinatura = timezone.now()
                obj.save()

            analise = form_analise.save(commit=False)
            analise.item = item_instancia
            preencher_assinatura(analise)

        elif aba == "regras" and form_regras.is_valid():
            # Também só criamos o pré-cálculo aqui
            ultimo = PreCalculo.objects.filter(cotacao=cot).order_by("-numero").first()
            proximo_numero = (ultimo.numero + 1) if ultimo else 1
            novo = PreCalculo.objects.create(cotacao=cot, numero=proximo_numero, criado_por=request.user)

            def preencher_assinatura(obj):
                obj.precalculo = novo
                obj.usuario = request.user
                obj.assinatura_nome = request.user.get_full_name() or request.user.username
                obj.assinatura_cn = request.user.email
                obj.data_assinatura = timezone.now()
                obj.save()

            preencher_assinatura(form_regras.save(commit=False))

        else:
            messages.error(request, "Erro ao validar o formulário da aba.")
            return redirect(request.path)

        messages.success(request, "Pré-cálculo salvo com sucesso.")
        return redirect("itens_precaculo", pk=cot.pk)



    campos_obs = [
        ("material_fornecido", "material_fornecido_obs"),
        ("requisitos_entrega", "requisitos_entrega_obs"),
        ("requisitos_pos_entrega", "requisitos_pos_entrega_obs"),
        ("requisitos_comunicacao", "requisitos_comunicacao_obs"),
        ("requisitos_notificacao", "requisitos_notificacao_obs"),
        ("especificacao_embalagem", "especificacao_embalagem_obs"),
        ("especificacao_identificacao", "especificacao_identificacao_obs"),
        ("tipo_embalagem", "tipo_embalagem_obs"),
    ]

    campos_obs_tecnica = [
        ("possui_projeto", "projeto_obs"),
        ("precisa_dispositivo", "dispositivo_obs"),
        ("caracteristicas_criticas", "criticas_obs"),
        ("precisa_amostras", "amostras_obs"),
        ("restricao_dimensional", "restricao_obs"),
        ("acabamento_superficial", "acabamento_obs"),
        ("validacao_metrologica", "metrologia_obs"),
        ("rastreabilidade", "rastreabilidade_obs"),
        ("metas_a", "metas_a_obs"),
        ("metas_b", "metas_b_obs"),
        ("metas_c", "metas_c_obs"),
        ("metas_d", "metas_d_obs"),
        ("seguranca", "seguranca_obs"),
        ("requisito_especifico", "requisito_especifico_obs"),
    ]

    return render(request, "cotacoes/form_precalculo.html", {
        "cotacao": cot,
        "form_analise": form_analise,
        "form": form_analise,
        "form_regras": form_regras,
        "campos_obs": campos_obs,
        "edicao": False,
        "campos_obs_tecnica": campos_obs_tecnica,
        
    })






@login_required
@permission_required("comercial.delete_precalculo", raise_exception=True)
def excluir_precalculo(request, pk):
    item = get_object_or_404(PreCalculo, pk=pk)
    cotacao_id = item.cotacao.id  # guarda antes de deletar
    item.delete()
    messages.success(request, "Item de Pré-Cálculo excluído com sucesso.")
    return redirect("itens_precaculo", pk=cotacao_id)






def responder_cotacao_materia_prima(request, pk):
    material = get_object_or_404(PreCalculoMaterial, pk=pk)
    codigo = material.codigo

    # Busca todas as cotações com o mesmo código
    materiais = PreCalculoMaterial.objects.filter(codigo=codigo).order_by("pk")
    fornecedores = FornecedorQualificado.objects.filter(
        produto_servico__in=[
            "Fita de Aço/Inox", "Arame de Aço", "Arame de inox"
        ],
        ativo="Ativo"
    ).order_by("nome")


    try:
        materia_prima = MateriaPrimaCatalogo.objects.get(codigo=codigo)
    except MateriaPrimaCatalogo.DoesNotExist:
        materia_prima = None

    cotacao_numero = material.precalculo.cotacao.numero if material.precalculo and material.precalculo.cotacao else None
    precalculo_numero = material.precalculo.numero if material.precalculo else None
    observacoes_gerais = material.precalculo.observacoes_materiais if material.precalculo else ""

    if request.method == "POST":
        for i, mat in enumerate(materiais):
            # Evita alterações em materiais com status finalizado
            if mat.status == "ok":
                continue

            mat.fornecedor_id = request.POST.get(f"fornecedor_{i}") or None
            mat.icms = request.POST.get(f"icms_{i}") or None
            mat.lote_minimo = request.POST.get(f"lote_minimo_{i}") or None
            mat.entrega_dias = request.POST.get(f"entrega_dias_{i}") or None
            mat.preco_kg = request.POST.get(f"preco_kg_{i}") or None
            mat.save()

        messages.success(request, "Cotações salvas com sucesso.")
        return redirect(request.path)  # Ou redirecione para a lista

    return render(request, "cotacoes/responder_cotacao_material.html", {
        "materiais": materiais,
        "fornecedores": fornecedores,
        "cotacao_numero": cotacao_numero,
        "precalculo_numero": precalculo_numero,
        "materia_prima": materia_prima,
        "observacoes_gerais": observacoes_gerais,
        "codigo": codigo,
    })





def responder_cotacao_servico_lote(request, pk):
    servico = get_object_or_404(PreCalculoServicoExterno, pk=pk)
    codigo = servico.insumo.materia_prima.codigo
    servicos = PreCalculoServicoExterno.objects.filter(insumo__materia_prima__codigo=codigo).order_by("pk")

    fornecedores = FornecedorQualificado.objects.filter(
        produto_servico__icontains="Trat",  # Padrão usado para tratamento
        status__in=["Qualificado", "Qualificado Condicional"]
    ).order_by("nome")

    try:
        materia_prima = servico.insumo.materia_prima
    except:
        materia_prima = None

    cotacao_numero = servico.precalculo.cotacao.numero if servico.precalculo and servico.precalculo.cotacao else None
    precalculo_numero = servico.precalculo.numero if servico.precalculo else None
    observacoes_gerais = servico.precalculo.observacoes_materiais if servico.precalculo else ""

    if request.method == "POST":
        for i, sev in enumerate(servicos):
            sev.fornecedor_id = request.POST.get(f"fornecedor_{i}") or None
            sev.lote_minimo = request.POST.get(f"lote_minimo_{i}") or None
            sev.entrega_dias = request.POST.get(f"entrega_dias_{i}") or None
            preco_raw = request.POST.get(f"preco_kg_{i}") or None
            if preco_raw:
                preco_raw = preco_raw.replace(",", ".")
            sev.preco_kg = preco_raw
            sev.save()

        messages.success(request, "Cotações salvas com sucesso.")
        return redirect(request.path)
    
    
    return render(request, "cotacoes/responder_cotacao_servico_lote.html", {
        "servicos": servicos,
        "fornecedores": fornecedores,
        "cotacao_numero": cotacao_numero,
        "precalculo_numero": precalculo_numero,
        "materia_prima": materia_prima,
        "observacoes_gerais": observacoes_gerais,
        "codigo": codigo,

    })


from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render
from comercial.models.precalculo import PreCalculo

from django.db.models import Sum

@login_required
@permission_required("comercial.view_precalculo", raise_exception=True)
def visualizar_precalculo(request, pk):
    precalc = get_object_or_404(PreCalculo, pk=pk)

    # Campos booleanos da análise comercial + observações
    campos_obs = [
        ("metodologia", ""),
        ("material_fornecido", "material_fornecido_obs"),
        ("requisitos_entrega", "requisitos_entrega_obs"),
        ("requisitos_pos_entrega", "requisitos_pos_entrega_obs"),
        ("requisitos_comunicacao", "requisitos_comunicacao_obs"),
        ("requisitos_notificacao", "requisitos_notificacao_obs"),
        ("especificacao_embalagem", "especificacao_embalagem_obs"),
        ("especificacao_identificacao", "especificacao_identificacao_obs"),
        ("tipo_embalagem", "tipo_embalagem_obs"),
    ]

    # Campos booleanos da avaliação técnica + observações
    # Campos booleanos da avaliação técnica + observações
    campos_obs_tecnica = [
        ("caracteristicas_criticas", "criticas_obs"),
        ("item_aparencia", "item_aparencia_obs"),
        ("fmea", "fmea_obs"),
        ("teste_solicitado", "teste_solicitado_obs"),
        ("lista_fornecedores", "lista_fornecedores_obs"),
        ("normas_disponiveis", "normas_disponiveis_obs"),
        ("requisitos_regulamentares", "requisitos_regulamentares_obs"),
        ("requisitos_adicionais", "requisitos_adicionais_obs"),
        
        # inserção lógica no template para linha do título 9
        ("metas_a", "metas_a_obs"),
        ("metas_b", "metas_b_obs"),
        ("metas_c", "metas_c_obs"),
        ("metas_confiabilidade", "metas_confiabilidade_obs"),
        ("metas_d", "metas_d_obs"),

        ("seguranca", "seguranca_obs"),
        ("requisito_especifico", "requisito_especifico_obs"),
    ]



    # Títulos amigáveis
    TITULOS_ANALISE = {
        "metodologia": "Metodologia de aprovação de produto",

        "material_fornecido": "Material fornecido pelo cliente?",
        "requisitos_entrega": "Requisitos de entrega?",
        "requisitos_pos_entrega": "Requisitos pós-entrega?",
        "requisitos_comunicacao": "Comunicação eletrônica?",
        "requisitos_notificacao": "Notificação de embarque?",
        "especificacao_embalagem": "Especificação de embalagem?",
        "especificacao_identificacao": "Especificação de identificação?",
        "tipo_embalagem": "Tipo de embalagem?",
    }

    TITULOS_AVALIACAO = {
    "caracteristicas_criticas": "1. Existem características críticas definidas?",
    "item_aparencia": "2. A peça é item de aparência?",
    "fmea": "3. O cliente forneceu FMEA de produto?",
    "teste_solicitado": "4. O cliente solicitou testes adicionais?",
    "lista_fornecedores": "5. Lista de fornecedores/materiais aprovados?",
    "normas_disponiveis": "6. Normas/especificações estão disponíveis?",
    "requisitos_regulamentares": "7. Existem requisitos estatutários/regulamentares?",
    "requisitos_adicionais": "8. Requisitos adicionais ou não declarados?",
    
    # Título visual para o bloco 9 (será usado como linha especial no template)
    "titulo_9": "9. O cliente especificou requisitos para:",

    "metas_a": "9a. Metas de qualidade?",
    "metas_b": "9b. Metas de produtividade?",
    "metas_c": "9c. Metas de desempenho?",
    "metas_confiabilidade": "9d. Metas de confiabilidade?",
    "metas_d": "9e. Metas de funcionamento?",
    
    "seguranca": "10. Item de segurança?",
    "requisito_especifico": "11. Requisito específico do cliente?",
}



    # ▶️ Enriquecimento: adiciona horas agrupadas por tipo na ferramenta
    ferramentas_info = []

    for cot_ferr in precalc.ferramentas_item.all():
        ferramenta = cot_ferr.ferramenta

        horas_projeto = ferramenta.mao_obra.filter(tipo="Projeto").aggregate(
            total=Sum("horas")
        ).get("total") or 0

        horas_ferramentaria = ferramenta.mao_obra.filter(tipo="Ferramentaria").aggregate(
            total=Sum("horas")
        ).get("total") or 0

        ferramentas_info.append({
            "obj": cot_ferr,
            "tipo": ferramenta.tipo,
            "horas_projeto": horas_projeto,
            "horas_ferramentaria": horas_ferramentaria,
            "observacoes": cot_ferr.observacoes,
            "assinatura_nome": cot_ferr.assinatura_nome,
            "assinatura_cn": cot_ferr.assinatura_cn,
        })

    tem_servicos_selecionados = precalc.servicos.filter(selecionado=True).exists()

    return render(request, "cotacoes/visualizar_f011.html", {
        "precalc": precalc,
        "numero_formulario": f"F011 - Pré-Cálculo N{precalc.numero:05d}",
        "campos_obs": campos_obs,
        "campos_obs_tecnica": campos_obs_tecnica,
        "titulos_analise": TITULOS_ANALISE,
        "titulos_avaliacao": TITULOS_AVALIACAO,
        "ferramentas_info": ferramentas_info,
        "tem_servicos_selecionados": tem_servicos_selecionados,  # ✅ adicionada aqui


    })


from decimal import Decimal, InvalidOperation, DivisionByZero
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from comercial.models.precalculo import PreCalculo
from decimal import Decimal, ROUND_HALF_UP

@login_required
@permission_required("comercial.view_precalculo", raise_exception=True)
def precificacao_produto(request, pk):
    precalc = get_object_or_404(PreCalculo, pk=pk)
    material = precalc.materiais.filter(selecionado=True).first()
    servico = precalc.servicos.filter(selecionado=True).first()

    preco_total = preco_total_sem_icms = preco_total_lote_minimo = None
    preco_total_servico = preco_total_servico_lote = preco_total_servico_sem_icms = None

    # 🟢 Cálculo do Material
    if material:
        try:
            preco_kg = Decimal(material.preco_kg or 0)
            icms = Decimal(material.icms or 0)
            peso_total = Decimal(material.peso_bruto_total or 0)
            lote_minimo = Decimal(material.lote_minimo or 0)

            preco_sem_icms = preco_kg * (Decimal("1") - icms / 100)
            preco_total = preco_kg * peso_total
            preco_total_sem_icms = preco_sem_icms * peso_total
            preco_total_lote_minimo = preco_sem_icms * lote_minimo
        except (InvalidOperation, TypeError):
            pass

    # 🟢 Cálculo do Serviço
    if servico:
        try:
            preco_kg = Decimal(servico.preco_kg or 0)
            icms = Decimal(servico.icms or 0)
            peso_total = Decimal(servico.peso_bruto_total or 0)
            lote_minimo = Decimal(servico.lote_minimo or 0)

            preco_sem_icms = preco_kg * (Decimal("1") - icms / 100)
            preco_total_servico = preco_kg * peso_total
            preco_total_servico_sem_icms = preco_sem_icms * peso_total
            preco_total_servico_lote = preco_sem_icms * lote_minimo
        except (InvalidOperation, TypeError):
            pass

    # 🟣 Cálculo do Roteiro de Produção
    roteiro_calculado = []
    lote = Decimal(precalc.analise_comercial_item.qtde_estimada or 1)

    for etapa in precalc.roteiro_item.all():
        try:
            setup = Decimal(etapa.setup_minutos or 0)
            custo_hora = Decimal(etapa.custo_hora or 0)
            producao_hr = Decimal(etapa.pph or 1)

            tempo_por_lote = setup / lote
            tempo_por_peca = Decimal("60") / producao_hr
            tempo_real = tempo_por_lote + tempo_por_peca
            taxa_cc = custo_hora / Decimal("60")
            custo_total = tempo_real * taxa_cc

            roteiro_calculado.append({
                "etapa": etapa,
                "tempo_por_lote": tempo_por_lote,
                "tempo_por_peca": tempo_por_peca,
                "tempo_real": tempo_real,
                "taxa_cc": taxa_cc,
                "custo_total": custo_total,
            })
        except (InvalidOperation, TypeError, AttributeError):
            continue

     # 🟠 Cálculo dos Impostos
    impostos = precalc.regras_calculo_item if hasattr(precalc, "regras_calculo_item") else None
    total_impostos = None

    if impostos:
        try:
            total_impostos = sum([
                Decimal(precalc.cotacao.icms or 0),
                Decimal(impostos.pis or 0),
                Decimal(impostos.confins or 0),
                Decimal(impostos.ir or 0),
                Decimal(impostos.csll or 0),
                Decimal(impostos.df or 0),
                Decimal(impostos.dv or 0),
            ])
        except (InvalidOperation, TypeError):
            total_impostos = None          


   # 🟡 Cálculo do Custo Final - para gráfico e resumo
    qtde = Decimal(getattr(precalc.analise_comercial_item, "qtde_estimada", 1) or 1)

    # ——— Materiais
    mat = precalc.materiais.filter(selecionado=True).first()
    total_materia = Decimal((mat.peso_bruto_total or 0)) * Decimal((mat.preco_kg or 0)) if mat else Decimal(0)
    unit_materia = total_materia / qtde if qtde else Decimal(0)

    # ——— Serviços
    total_servico = sum(
        Decimal((s.peso_bruto_total or 0)) * Decimal((s.preco_kg or 0))
        for s in precalc.servicos.all()
    )
    unit_servico = total_servico / qtde if qtde else Decimal(0)

    # ——— Roteiro
    total_roteiro = sum(
        Decimal(rot.custo_total or 0) for rot in precalc.roteiro_item.all()
    )
    unit_roteiro = total_roteiro / qtde if qtde else Decimal(0)

    # ——— Total Geral
    total_geral = total_materia + total_servico + total_roteiro

    # ——— Função auxiliar para percentual
    def pct(val):
        return (val / total_geral * 100).quantize(Decimal("0.01")) if total_geral > 0 else Decimal("0.00")

    # ——— Resultado formatado
    custo_materia = {
        "total": total_materia.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "unitario": unit_materia.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
        "percentual": pct(total_materia),
    }

    custo_servico = {
        "total": total_servico.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "unitario": unit_servico.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
        "percentual": pct(total_servico),
    }

    custo_roteiro = {
        "total": total_roteiro.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "unitario": unit_roteiro.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
        "percentual": pct(total_roteiro),
    }

    # ——— Ferramental
    valor_ferramental = Decimal("0.00")
    for f in precalc.ferramentas_item.all():
        try:
            valor_ferramental += Decimal(f.ferramenta.valor_total or 0)
        except AttributeError:
            continue

    analise = precalc.analise_comercial_item
    item = analise.item if analise else None



    return render(request, "cotacoes/precificacao_produto.html", {
        "precalc": precalc,
        "cotacao": precalc.cotacao,
        "material": material,
        "servico": servico,
        "preco_total_material": preco_total,
        "preco_total_material_sem_icms": preco_total_sem_icms,
        "preco_total_lote_minimo": preco_total_lote_minimo,
        "preco_total_servico": preco_total_servico,
        "preco_total_servico_sem_icms": preco_total_servico_sem_icms,
        "preco_total_servico_lote": preco_total_servico_lote,
        "roteiro_calculado": roteiro_calculado,
        "impostos": impostos,
        "total_impostos": total_impostos,
        "custo_materia": custo_materia,
        "custo_servico": custo_servico,
        "custo_roteiro": custo_roteiro,
        "valor_ferramental": valor_ferramental,
        "total_geral": total_geral,
        "precos_sem_impostos": precalc.calcular_precos_sem_impostos(),
        "precos_com_impostos": precalc.calcular_precos_com_impostos(),
        "analise": analise,
"item": item,
    })




from django.db.models import Prefetch

def gerar_proposta_view(request, cotacao_id):
    cotacao = get_object_or_404(Cotacao, id=cotacao_id)

    if request.method == "POST":
        ids = request.POST.getlist("precalculos_selecionados")

        precalculos = (
            PreCalculo.objects
            .filter(id__in=ids)
            .select_related("analise_comercial_item__item")
            .prefetch_related(
                "materiais",          # ✅ só prefetch direto
                "servicos",
                "ferramentas_item__ferramenta"
            )
        )

        # Cálculo do valor total do ferramental
        for precalc in precalculos:
            precalc.valor_ferramental = sum(
                (f.ferramenta.valor_total or 0)
                for f in precalc.ferramentas_item.all()
            )

        return render(request, "cotacoes/proposta_preview.html", {
            "cotacao": cotacao,
            "precalculos": precalculos
        })


@login_required
@permission_required("comercial.add_precalculo", raise_exception=True)
def duplicar_precaculo(request, pk):
    original = get_object_or_404(PreCalculo, pk=pk)
    cotacao = original.cotacao

    # Novo número sequencial
    ultimo = PreCalculo.objects.filter(cotacao=cotacao).order_by("-numero").first()
    proximo_numero = (ultimo.numero + 1) if ultimo else 1

    clone = PreCalculo.objects.create(
        cotacao=cotacao,
        numero=proximo_numero,
        criado_por=request.user,
        observacoes_materiais=original.observacoes_materiais,
        observacoes_servicos=original.observacoes_servicos,
        observacoes_roteiro=original.observacoes_roteiro,
    )

    # Clona os relacionamentos (analise, regras, etc.)
    for relacao in ['analise_comercial_item', 'avaliacao_tecnica_item', 'regras_calculo_item', 'desenvolvimento_item']:
        item = getattr(original, relacao, None)
        if item:
            item.pk = None  # força cópia
            item.precalculo = clone
            item.usuario = request.user
            item.assinatura_nome = request.user.get_full_name() or request.user.username
            item.assinatura_cn = request.user.email
            item.data_assinatura = timezone.now()
            item.save()

    # Clonar materiais
    for mat in original.materiais.all():
        mat.pk = None
        mat.precalculo = clone
        mat.save()

    # Clonar serviços
    for sev in original.servicos.all():
        sev.pk = None
        sev.precalculo = clone
        sev.save()

    # Clonar etapas do roteiro
    for rot in original.roteiro_item.all():
        rot.pk = None
        rot.precalculo = clone
        rot.save()

    # Clonar ferramentas
    for ferr in original.ferramentas_item.all():
        ferr.pk = None
        ferr.precalculo = clone
        ferr.save()

    messages.success(request, "Pré-cálculo duplicado com sucesso.")
    return redirect("itens_precaculo", pk=cotacao.pk)
