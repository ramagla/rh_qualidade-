from decimal import Decimal

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
    PreCalculo,
    PreCalculoMaterial,
    PreCalculoServicoExterno,
)
from comercial.forms.precalculos_form import (
    PreCalculoForm,
    AnaliseComercialForm,
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





from decimal import Decimal

@login_required
@permission_required("comercial.view_precalculo", raise_exception=True)
def itens_precaculo(request, pk):
    cot = get_object_or_404(Cotacao, pk=pk)

    # Lista todos os pré-cálculos da cotação
    precalculos = PreCalculo.objects.filter(cotacao=cot).order_by("numero")

    # Enriquecimento para exibição no template
    for precalc in precalculos:
        precalc.tipo_precalculo = "Item de Cotação"
        precalc.total_materiais = precalc.materiais.count()
        precalc.total_servicos = precalc.servicos.count()
        precalc.total_geral = precalc.total_materiais + precalc.total_servicos
        precalc.analise_ok = hasattr(precalc, "analise_comercial_item")
        precalc.regras_ok = hasattr(precalc, "regras_calculo_item")
        precalc.avaliacao_ok = hasattr(precalc, "avaliacao_tecnica_item")
        precalc.desenvolvimento_ok = hasattr(precalc, "desenvolvimento_item")

        # ✅ Valor total das ferramentas
        precalc.valor_ferramental = sum(
            f.ferramenta.valor_total or 0
            for f in precalc.ferramentas_item.all()
        )

        # ✅ Total Geral (produto + ferramentas)
        preco_final = precalc.preco_selecionado or Decimal("0.00")
        precalc.total_geral = preco_final + Decimal(precalc.valor_ferramental)

        # ✅ Preço Escolhido com percentual (%)
        precalc.preco_margem_formatado = next(
            (
                f"{item['unitario']:.2f} ({item['percentual']}%)"
                for item in precalc.calcular_precos_com_impostos()
                if round(item['unitario'], 4) == round(preco_final, 4)
            ),
            f"{preco_final:.2f}" if preco_final else None
        )

    # Paginação
    paginator = Paginator(precalculos, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "cotacoes/precalculo_lista.html", {
        "cotacao": cot,
        "page_obj": page_obj,
        "total_materiais": sum(p.total_materiais for p in precalculos),
        "total_servicos": sum(p.total_servicos for p in precalculos),
        "total_itens": precalculos.count(),
    })



@login_required
@permission_required("comercial.change_precalculo", raise_exception=True)
def editar_precaculo(request, pk):
    precalc = get_object_or_404(PreCalculo, pk=pk)
    cot    = precalc.cotacao
    salvo  = False
    mensagem_precofinal = None 

    # identifica aba submetida
    aba = request.POST.get("aba")


    # form principal (observações gerais)
    form_precalculo = PreCalculoForm(
        request.POST if request.method == "POST" else None,
        instance=precalc
    )

    # inicializa variáveis de retorno
    form_analise = form_regras = form_avali = form_desenv = form_precofinal = form_roteiro = None

    fs_mat = fs_sev = fs_rot = fs_ferr = None
    servicos_respondidos = False  # ✅ sempre inicializar



    # POST: processa a aba correta via handler
    if request.method == "POST":
        if aba == "analise" and "form_analise_submitted" in request.POST:
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
            salvo, form_precalculo, fs_mat = processar_aba_materiais(
                request, precalc, materiais_respondidos
            )


        elif aba == "servicos" and (
            "form_servicos_submitted" in request.POST or
            any(k.startswith("sev-") for k in request.POST)
        ):
            faltam = precalc.servicos.filter(
                Q(preco_kg__isnull=True) | Q(preco_kg=0)
            ).exists()
            servicos_respondidos = not faltam
            salvo, form_precalculo, fs_sev = processar_aba_servicos(
                request, precalc, servicos_respondidos
            )


        elif aba == "roteiro" and "form_roteiro_submitted" in request.POST:
            form_precalculo = PreCalculoForm(request.POST, instance=precalc)  # garante os dados do POST
            salvo, fs_rot, form_precalculo = processar_aba_roteiro(request, precalc, form_precalculo=form_precalculo)
            form_roteiro = form_precalculo




        elif aba == "ferramentas" and "form_ferramentas_submitted" in request.POST:
            salvo, fs_ferr = processar_aba_ferramentas(request, precalc)

        # Mensagens
        print("🧪 DEBUG FINAL")
        print("salvo:", salvo)
        print("aba:", aba)
        print("mensagem_precofinal:", mensagem_precofinal)

        if salvo:
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
        _, form_analise = processar_aba_analise(request, precalc)
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



    if not fs_mat and (
        request.method == "GET" or
        any(k.startswith("mat-") for k in request.POST)
    ):
        materiais_respondidos = precalc.materiais.filter(preco_kg__isnull=False).exists()
        _, _, fs_mat = processar_aba_materiais(request, precalc, materiais_respondidos)

    if not fs_sev and (
        request.method == "GET" or
        any(k.startswith("sev-") for k in request.POST)
    ):
        faltam = precalc.servicos.filter(
            Q(preco_kg__isnull=True) | Q(preco_kg=0)
        ).exists()
        servicos_respondidos = not faltam
        _, _, fs_sev = processar_aba_servicos(request, precalc, servicos_respondidos)


    if not fs_rot:
        _, fs_rot, form_roteiro = processar_aba_roteiro(request, precalc)




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
    item_id = getattr(getattr(precalc, "analise_comercial_item", None), "item_id", None)

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
        "materiais_respondidos": precalc.materiais.filter(preco_kg__isnull=False).exists(),
        "servicos_respondidos": servicos_respondidos,
        "aba_ativa": aba,

    })

@login_required
@permission_required('comercial.add_precalculomaterial', raise_exception=True)
def criar_precaculo(request, pk):
    cot = get_object_or_404(Cotacao, pk=pk)

    aba = next((k.replace("form_", "").replace("_submitted", "") for k in request.POST if k.startswith("form_")), None)

    # Define formulários com POST apenas na aba ativa
    form_analise = AnaliseComercialForm(request.POST if aba == "analise" else None)
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

    form_avali = AvaliacaoTecnicaForm(request.POST if aba == "avali" else None)
    form_desenv = DesenvolvimentoForm(request.POST if aba == "desenv" else None)

    if request.method == "POST":
        if not aba:
            messages.error(request, "Nenhuma aba foi enviada.")
        else:
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

            if aba == "analise" and form_analise.is_valid():
                preencher_assinatura(form_analise.save(commit=False))
            elif aba == "regras" and form_regras.is_valid():
                preencher_assinatura(form_regras.save(commit=False))
            elif aba == "avali" and form_avali.is_valid():
                preencher_assinatura(form_avali.save(commit=False))
            elif aba == "desenv" and form_desenv.is_valid():
                preencher_assinatura(form_desenv.save(commit=False))
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
        "form_regras": form_regras,
        "form_avali": form_avali,
        "form_desenv": form_desenv,
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

    # Títulos amigáveis
    TITULOS_ANALISE = {
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
        "possui_projeto": "Possui projeto próprio?",
        "precisa_dispositivo": "Precisa de dispositivo?",
        "caracteristicas_criticas": "Características críticas?",
        "precisa_amostras": "Necessita amostras?",
        "restricao_dimensional": "Restrições dimensionais?",
        "acabamento_superficial": "Acabamento superficial?",
        "validacao_metrologica": "Validação metrológica?",
        "rastreabilidade": "Rastreabilidade técnica?",
        "metas_a": "Metas de qualidade?",
        "metas_b": "Metas de produtividade?",
        "metas_c": "Metas de desempenho?",
        "metas_d": "Metas de funcionamento?",
        "seguranca": "Item de segurança?",
        "requisito_especifico": "Requisito específico?",
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



    return render(request, "cotacoes/visualizar_f011.html", {
        "precalc": precalc,
        "numero_formulario": f"F011 - Pré-Cálculo N{precalc.numero:05d}",
        "campos_obs": campos_obs,
        "campos_obs_tecnica": campos_obs_tecnica,
        "titulos_analise": TITULOS_ANALISE,
        "titulos_avaliacao": TITULOS_AVALIACAO,
        "ferramentas_info": ferramentas_info,

    })
