# comercial/views/cotacao_views.py

import uuid
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from comercial.forms.precalculos_form import PrecoFinalForm

from comercial.models import Cotacao

from itertools import chain
from django.core.paginator import Paginator
from comercial.models.precalculo import PreCalculo, RegrasCalculo

from comercial.models.precalculo import PreCalculoMaterial, PreCalculoServicoExterno, RoteiroCotacao, CotacaoFerramenta
from qualidade_fornecimento.models.fornecedor import FornecedorQualificado
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo
from tecnico.models.roteiro import InsumoEtapa

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


#from django.forms import inlineformset_factory
from django.contrib import messages
# comercial/views/cotacao_views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.forms import inlineformset_factory
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone

from comercial.models import Cotacao

# ← aponte para o seu arquivo precalculos_form.py
from comercial.forms.precalculos_form import (
    PreCalculoMaterialForm,
    PreCalculoServicoExternoForm,
    RegrasCalculoForm,
    RoteiroCotacaoForm,
    CotacaoFerramentaForm,
    AvaliacaoTecnicaForm,
    AnaliseComercialForm,
    DesenvolvimentoForm,
)

# comercial/views/precalc_views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.forms import inlineformset_factory


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.forms import inlineformset_factory
from django.utils import timezone
from django.contrib import messages

from comercial.models import PreCalculo, Cotacao
from comercial.forms.precalculos_form import (
    PreCalculoMaterialForm,
    PreCalculoServicoExternoForm,
    RoteiroCotacaoForm,
    CotacaoFerramentaForm,
    RegrasCalculoForm,
    AvaliacaoTecnicaForm,
    AnaliseComercialForm,
    DesenvolvimentoForm,
)
from decimal import Decimal
from comercial.forms.precalculos_form import PreCalculoForm

@login_required
@permission_required('comercial.change_precalculo', raise_exception=True)
def editar_precaculo(request, pk):
    precalc = get_object_or_404(PreCalculo, pk=pk)
    materiais_respondidos = precalc.materiais.filter(preco_kg__isnull=False).exists()

    cot = precalc.cotacao

    aba = next((k.replace("form_", "").replace("_submitted", "") for k in request.POST if k.startswith("form_")), None)

    # Cria regras_calculo caso não exista
    if not hasattr(precalc, "regras_calculo_item"):
        RegrasCalculo.objects.create(
            precalculo=precalc,
            icms=cot.icms,
            pis=Decimal("0.65"),
            confins=Decimal("3.00"),
            ir=Decimal("1.20"),
            csll=Decimal("1.08"),
            df=Decimal("2.50"),
            dv=Decimal("5.00"),
            usuario=request.user,
            assinatura_nome=request.user.get_full_name() or request.user.username,
            assinatura_cn=request.user.email,
            data_assinatura=timezone.now(),
        )

    if not precalc.materiais.exists():
        for _ in range(3):
            PreCalculoMaterial.objects.create(
                precalculo=precalc,
                codigo="",
                desenvolvido_mm=0,
                peso_liquido=0,
                peso_bruto=0,
            )

    # Criar serviços externos com base em roteiro ou adicionar 3 linhas vazias
    # Criar serviços externos com base em roteiro ou adicionar 3 linhas no total
    if precalc.servicos.count() < 3:
        servicos_criados = precalc.servicos.count()

        if hasattr(precalc, "analise_comercial_item"):
            item = precalc.analise_comercial_item.item
            try:
                roteiro = item.roteiro
                tratamentos = InsumoEtapa.objects.filter(
                    etapa__roteiro=roteiro,
                    etapa__setor__nome__icontains="Tratamento Externo"
                )
                for insumo in tratamentos:
                    # Evita criar insumo duplicado
                    if not precalc.servicos.filter(insumo=insumo).exists():
                        PreCalculoServicoExterno.objects.create(
                            precalculo=precalc,
                            insumo=insumo,
                            desenvolvido_mm=0,
                            peso_liquido=0,
                            peso_bruto=0,
                        )
                        servicos_criados += 1
            except Exception as e:
                print(f"⚠️ Erro ao carregar serviços externos: {e}")

        # Garante ao menos 3 linhas
        while servicos_criados < 3:
        # Só cria se houver insumo disponível para preencher
            try:
                insumo_vazio = InsumoEtapa.objects.filter(etapa__setor__nome__icontains="Tratamento Externo").first()
                if insumo_vazio:
                    PreCalculoServicoExterno.objects.create(
                        precalculo=precalc,
                        insumo=insumo_vazio,
                        desenvolvido_mm=0,
                        peso_liquido=0,
                        peso_bruto=0,
                    )
                    servicos_criados += 1
                else:
                    break  # não cria linhas inválidas
            except Exception as e:
                print("Erro ao criar linha de serviço:", e)
                break


  

    if not precalc.roteiro_item.exists() and hasattr(precalc, "analise_comercial_item"):
        item = precalc.analise_comercial_item.item

        if hasattr(item, "roteiro"):
            roteiro = item.roteiro
            qtde = precalc.analise_comercial_item.qtde_estimada or 1

            for etapa in roteiro.etapas.select_related("setor"):
                pph = etapa.pph or 1
                setup = etapa.setup_minutos or 0
                custo_hora = etapa.setor.custo_atual or 0

                try:
                    tempo_pecas_horas = Decimal(qtde) / Decimal(pph)
                except ZeroDivisionError:
                    tempo_pecas_horas = Decimal(0)

                tempo_setup_horas = Decimal(setup) / Decimal(60)
                valor_total = (tempo_pecas_horas + tempo_setup_horas) * Decimal(custo_hora)

                nome_acao = getattr(getattr(etapa, "propriedades", None), "nome_acao", "Sem Nome")

                RoteiroCotacao.objects.create(
                    precalculo=precalc,
                    etapa=etapa.etapa,
                    setor=etapa.setor,
                    nome_acao=nome_acao,
                    pph=pph,
                    setup_minutos=setup,
                    custo_hora=custo_hora,
                    custo_total=round(valor_total, 2),
                    usuario=request.user,
                    assinatura_nome=request.user.get_full_name() or request.user.username,
                    assinatura_cn=request.user.email,
                    data_assinatura=timezone.now(),
                )

    # Formsets
    MatSet = inlineformset_factory(PreCalculo, PreCalculoMaterial, form=PreCalculoMaterialForm, extra=0, can_delete=True)
    SevSet = inlineformset_factory(PreCalculo, PreCalculoServicoExterno, form=PreCalculoServicoExternoForm, extra=0, can_delete=True)
    RotSet = inlineformset_factory(PreCalculo, RoteiroCotacao, form=RoteiroCotacaoForm, extra=0, can_delete=False)
    FerrSet = inlineformset_factory(PreCalculo, CotacaoFerramenta, form=CotacaoFerramentaForm, extra=0, can_delete=True)

    # Form principal para observacoes_materiais
    form_precalculo = PreCalculoForm(request.POST if request.method == "POST" else None, instance=precalc)

    # Formularios das abas
    form_analise = AnaliseComercialForm(request.POST if aba == "analise" else None, instance=getattr(precalc, 'analise_comercial_item', None))
    form_regras = RegrasCalculoForm(request.POST if aba == "regras" else None, instance=precalc.regras_calculo_item)
    form_avali = AvaliacaoTecnicaForm(request.POST if aba == "avali" else None, instance=getattr(precalc, 'avaliacao_tecnica_item', None))
    form_desenv = DesenvolvimentoForm(request.POST if aba == "desenv" else None, instance=getattr(precalc, 'desenvolvimento_item', None))
# 🛠️ Corrige vírgula no preco_selecionado antes de criar o form
    if request.method == "POST" and "preco_selecionado" in request.POST:
        preco_raw = request.POST.get("preco_selecionado")
        if preco_raw:
            preco_corrigido = preco_raw.replace(",", ".")
            request.POST._mutable = True
            request.POST["preco_selecionado"] = preco_corrigido
            request.POST._mutable = False

    # Criar o form após corrigir preco_selecionado
    form_precofinal = PrecoFinalForm(request.POST if aba == "precofinal" else None, instance=precalc)

    # Formsets das abas
    fs_mat = MatSet(request.POST if aba == "materiais" else None, instance=precalc, prefix='mat')
    fs_sev = SevSet(request.POST if aba == "servicos" else None, instance=precalc, prefix='sev')
    fs_rot = RotSet(request.POST if aba == "roteiro" else None, instance=precalc, prefix='rot')
    fs_ferr = FerrSet(request.POST if aba == "ferramentas" else None, instance=precalc, prefix='ferr')

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

    if request.method == 'POST':
        salvo = False

    # 🛠️ Salvar formulário de Preço Final (aba específica)
    if 'form_precofinal_submitted' in request.POST and form_precofinal.is_valid():
        preco_raw = request.POST.get("preco_selecionado")
        if preco_raw:
            try:
                preco_limpo = preco_raw.replace(",", ".")
                form_precofinal.instance.preco_selecionado = Decimal(preco_limpo)
            except Exception as e:
                messages.error(request, f"Erro ao processar o preço selecionado: {e}")
        form_precofinal.save()
        salvo = True

    # 🛠️ Salvar outras abas independentemente
    if 'form_analise_submitted' in request.POST and form_analise.is_valid():
        obj = form_analise.save(commit=False)
        obj.precalculo = precalc
        obj.usuario = request.user
        obj.assinatura_nome = request.user.get_full_name() or request.user.username
        obj.assinatura_cn = request.user.email
        obj.data_assinatura = timezone.now()
        obj.save()
        salvo = True

    if 'form_regras_submitted' in request.POST and form_regras.is_valid():
        obj = form_regras.save(commit=False)
        obj.precalculo = precalc
        obj.usuario = request.user
        obj.assinatura_nome = request.user.get_full_name() or request.user.username
        obj.assinatura_cn = request.user.email
        obj.data_assinatura = timezone.now()
        obj.save()
        salvo = True

    if 'form_avali_submitted' in request.POST and form_avali.is_valid():
        obj = form_avali.save(commit=False)
        obj.precalculo = precalc
        obj.usuario = request.user
        obj.assinatura_nome = request.user.get_full_name() or request.user.username
        obj.assinatura_cn = request.user.email
        obj.data_assinatura = timezone.now()
        obj.save()
        salvo = True

    if 'form_desenv_submitted' in request.POST and form_desenv.is_valid():
        obj = form_desenv.save(commit=False)
        obj.precalculo = precalc
        obj.usuario = request.user
        obj.assinatura_nome = request.user.get_full_name() or request.user.username
        obj.assinatura_cn = request.user.email
        obj.data_assinatura = timezone.now()
        obj.save()
        salvo = True


        # Aba Materiais: salvar form principal (observações) e formset materiais
    if aba == "materiais":
        print("📥 fs_mat.is_valid():", fs_mat.is_valid())

        if form_precalculo.is_valid() and fs_mat.is_valid():
            form_precalculo.save()
            algo_salvo = False

            # 📌 NOVO: identificar o selecionado (prefix ex: mat-1)
            selecionado = request.POST.get("material_selecionado")
            codigos_disparados = set()
            algo_salvo = False

            for mat_form in fs_mat:
                if mat_form.cleaned_data and not mat_form.cleaned_data.get("DELETE", False):
                    mat = mat_form.save(commit=False)

                    # ✅ Marcar apenas o selecionado
                    mat.selecionado = (mat_form.prefix == selecionado)
                    mat.save()

                    # ✅ Disparar e-mail apenas uma vez por código (e se ainda não respondeu)
                    if (
                        not materiais_respondidos
                        and mat.codigo
                        and not mat.preco_kg
                        and mat.codigo not in codigos_disparados
                    ):
                        disparar_email_cotacao_material(request, mat)
                        codigos_disparados.add(mat.codigo)

                    algo_salvo = True

            # Aplica deletes do formset
            fs_mat.save(commit=False)

            # Marca como salvo se algo mudou
            salvo = algo_salvo



        else:
            for i, form in enumerate(fs_mat.forms):
                print(f"❌ Form {i} ERROS:", form.errors)
            print("⚠️ Non-form errors:", fs_mat.non_form_errors())

        # Aba Serviços Externos: salvar observações e formset
    if aba == "servicos":
        print("📥 fs_sev.is_valid():", fs_sev.is_valid())

        if form_precalculo.is_valid() and fs_sev.is_valid():
            form_precalculo.save()
            selecionado = request.POST.get("servico_selecionado")
            codigos_disparados = set()
            servicos_respondidos = precalc.servicos.filter(preco_kg__isnull=False).exists()
            algo_salvo = False

            for sev_form in fs_sev:
                if sev_form.cleaned_data and not sev_form.cleaned_data.get("DELETE", False):
                    sev = sev_form.save(commit=False)
                    sev.selecionado = (sev_form.prefix == selecionado)
                    sev.save()

                    if (
                        not servicos_respondidos
                        and sev.insumo.materia_prima.codigo
                        and not sev.preco_kg
                        and sev.insumo.materia_prima.codigo not in codigos_disparados
                    ):
                        disparar_email_cotacao_servico(request, sev)
                        codigos_disparados.add(sev.insumo.materia_prima.codigo)

                    algo_salvo = True

            fs_sev.save(commit=False)
            salvo = algo_salvo
        else:
            for i, form in enumerate(fs_sev.forms):
                print(f"❌ Form {i} ERROS:", form.errors)
            print("⚠️ Non-form errors:", fs_sev.non_form_errors())


        # Salvar outros formsets com cálculo de custo_total para fs_rot
        qtde = getattr(precalc.analise_comercial_item, 'qtde_estimada', 1) or 1

        for fs in [fs_sev, fs_rot, fs_ferr]:
            if fs.is_valid():
                for form in fs:
                    if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                        if fs.prefix == "rot":
                            # Roteiro: recalcular custo_total
                            pph = Decimal(form.cleaned_data.get("pph") or 1)
                            setup = Decimal(form.cleaned_data.get("setup_minutos") or 0)
                            custo_hora = Decimal(form.cleaned_data.get("custo_hora") or 0)

                            tempo_pecas = Decimal(qtde) / pph if pph else 0
                            tempo_setup = setup / Decimal(60)
                            total = (tempo_pecas + tempo_setup) * custo_hora

                            form.instance.custo_total = round(total, 2)

                fs.save()
                salvo = True

        if salvo:
            messages.success(request, "Pré-cálculo atualizado com sucesso.")
            return redirect("itens_precaculo", pk=precalc.cotacao.pk)
        else:
            messages.error(request, "Nenhuma alteração válida foi identificada para salvar.")

    item_id = None
    if hasattr(precalc, "analise_comercial_item") and precalc.analise_comercial_item.item_id:
        item_id = precalc.analise_comercial_item.item_id

    precos_sem_impostos = precalc.calcular_precos_sem_impostos()
    precos_com_impostos = precalc.calcular_precos_com_impostos()

    return render(request, "cotacoes/form_precalculo.html", {
        "cotacao": cot,
        "precalc": precalc,
        "form_precalculo": form_precalculo,  # Para exibir e salvar observacoes_materiais
        "form_analise": form_analise,
        "form_regras": form_regras,
        "form_avali": form_avali,
        "form_desenv": form_desenv,
        "fs_mat": fs_mat,
        "fs_sev": fs_sev,
        "fs_rot": fs_rot,
        "fs_ferr": fs_ferr,
        "campos_obs": campos_obs,
        "campos_obs_tecnica": campos_obs_tecnica,
        "item_id": item_id,
        "edicao": True,
        "aba_ativa": aba,
        "form_precofinal": form_precofinal,
        "precos_sem_impostos": precos_sem_impostos,
        "precos_com_impostos": precos_com_impostos,
        "materiais_respondidos": materiais_respondidos,


    })


from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from comercial.models import Cotacao, PreCalculo
from comercial.forms.precalculos_form import (
    AnaliseComercialForm,
    RegrasCalculoForm,
    AvaliacaoTecnicaForm,
    DesenvolvimentoForm,
)

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

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal

from comercial.models.precalculo import PreCalculoMaterial


@login_required
@permission_required("comercial.delete_precalculo", raise_exception=True)
def excluir_precalculo(request, pk):
    item = get_object_or_404(PreCalculo, pk=pk)
    cotacao_id = item.cotacao.id  # guarda antes de deletar
    item.delete()
    messages.success(request, "Item de Pré-Cálculo excluído com sucesso.")
    return redirect("itens_precaculo", pk=cotacao_id)



def disparar_email_cotacao_material(request, material):
    """
    Dispara o e-mail de cotação de matéria-prima para o setor de compras,
    incluindo apenas código e descrição, sem os dados preenchidos pelo usuário.
    """
    link = request.build_absolute_uri(
        reverse("responder_cotacao_materia_prima", args=[material.pk])
    )

    # Busca a descrição com base no código
    try:
        mp = MateriaPrimaCatalogo.objects.get(codigo=material.codigo)
        descricao = mp.descricao
    except MateriaPrimaCatalogo.DoesNotExist:
        descricao = "---"

    # Corpo do e-mail simplificado
    corpo = f"""
🧪 Solicitação de Cotação - Matéria-Prima

📦 Código: {material.codigo}
📝 Descrição: {descricao}

🔗 Responder: {link}
    """

    # Disparo do e-mail
    send_mail(
        subject="📨 Cotação de Matéria-Prima",
        message=corpo,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["rafael.almeida@brasmol.com.br"],
        fail_silently=False,
    )



from django.contrib import messages
from django.shortcuts import redirect

from decimal import Decimal, InvalidOperation

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


def disparar_email_cotacao_servico(request, servico):
    """
    Dispara o e-mail de cotação de serviço externo para o setor de compras.
    """
    from django.urls import reverse
    from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo

    link = request.build_absolute_uri(
        reverse("responder_cotacao_servico_lote", args=[servico.pk])
    )

    try:
        mp = servico.insumo.materia_prima
        descricao = mp.descricao
        codigo = mp.codigo
    except:
        descricao = "---"
        codigo = "sem código"

    corpo = f"""
🔧 Cotação de Serviço Externo – Tratamento

📦 Código: {codigo}
📝 Descrição: {descricao}

🔗 Link para resposta: {link}
    """

    send_mail(
        subject="📨 Cotação de Serviço Externo",
        message=corpo,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["rafael.almeida@brasmol.com.br"],
        fail_silently=False,
    )


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