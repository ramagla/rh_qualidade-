# comercial/views/cotacao_views.py

import uuid
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator

from comercial.models import Cotacao

from itertools import chain
from django.core.paginator import Paginator
from comercial.models.precalculo import PreCalculo, RegrasCalculo

from comercial.models.precalculo import PreCalculoMaterial, PreCalculoServicoExterno, RoteiroCotacao, CotacaoFerramenta
from qualidade_fornecimento.models.fornecedor import FornecedorQualificado
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo

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
        PreCalculoMaterial.objects.create(
            precalculo=precalc,
            codigo="",
            desenvolvido_mm=0,
            peso_liquido=0,
            peso_bruto=0,
        )

    # Formsets
    MatSet = inlineformset_factory(PreCalculo, PreCalculoMaterial, form=PreCalculoMaterialForm, extra=0, can_delete=True)
    SevSet = inlineformset_factory(PreCalculo, PreCalculoServicoExterno, form=PreCalculoServicoExternoForm, extra=1, can_delete=True)
    RotSet = inlineformset_factory(PreCalculo, RoteiroCotacao, form=RoteiroCotacaoForm, extra=1, can_delete=True)
    FerrSet = inlineformset_factory(PreCalculo, CotacaoFerramenta, form=CotacaoFerramentaForm, extra=1, can_delete=True)

    # Form principal para observacoes_materiais
    form_precalculo = PreCalculoForm(request.POST if request.method == "POST" else None, instance=precalc)

    # Formularios das abas
    form_analise = AnaliseComercialForm(request.POST if aba == "analise" else None, instance=getattr(precalc, 'analise_comercial_item', None))
    form_regras = RegrasCalculoForm(request.POST if aba == "regras" else None, instance=precalc.regras_calculo_item)
    form_avali = AvaliacaoTecnicaForm(request.POST if aba == "avali" else None, instance=getattr(precalc, 'avaliacao_tecnica_item', None))
    form_desenv = DesenvolvimentoForm(request.POST if aba == "desenv" else None, instance=getattr(precalc, 'desenvolvimento_item', None))

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

        # Salvar formulários das abas
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
            if not fs_mat.is_valid():
                for i, form in enumerate(fs_mat.forms):
                    print(f"❌ Form {i} ERROS:", form.errors)
                print("⚠️ Non-form errors:", fs_mat.non_form_errors())

            if form_precalculo.is_valid() and fs_mat.is_valid():
                form_precalculo.save()
                fs_mat.save()
                salvo = True

                # Disparar e-mails para cada material salvo
                for mat_form in fs_mat:
                    if mat_form.cleaned_data and not mat_form.cleaned_data.get('DELETE', False):
                        mat = mat_form.save(commit=False)
                        disparar_email_cotacao_material(request, mat)

        # Salvar outros formsets
        for fs in [fs_sev, fs_rot, fs_ferr]:
            if fs.is_valid():
                for form in fs:
                    if form.has_changed() or form.cleaned_data.get("id") is None:
                        fs.save()
                        salvo = True
                        break

        if salvo:
            messages.success(request, "Pré-cálculo atualizado com sucesso.")
            return redirect("itens_precaculo", pk=precalc.cotacao.pk)
        else:
            messages.error(request, "Nenhuma alteração válida foi identificada para salvar.")

    item_id = None
    if hasattr(precalc, "analise_comercial_item") and precalc.analise_comercial_item.item_id:
        item_id = precalc.analise_comercial_item.item_id

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
    Dispara o e-mail de cotação de matéria-prima para o setor de compras.
    """
    link = request.build_absolute_uri(
        reverse("responder_cotacao_materia_prima", args=[material.pk])
    )

    corpo = f"""
🧪 Solicitação de Cotação - Matéria-Prima

📦 Código: {material.codigo}
🏷️ Fornecedor: {material.fornecedor or '---'}
📦 Lote Mínimo: {material.lote_minimo or '---'}
📦 Entrega (dias): {material.entrega_dias or '---'}
💰 ICMS (%): {material.icms or '0.00'}
💲 Preço/kg: {material.preco_kg or '---'}
⚖️ Peso Bruto: {material.peso_bruto or '---'} kg

🔗 Responder: {link}
    """

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
    fornecedores = FornecedorQualificado.objects.all()

    try:
        materia_prima = MateriaPrimaCatalogo.objects.get(codigo=material.codigo)
    except MateriaPrimaCatalogo.DoesNotExist:
        materia_prima = None

    cotacao_numero = material.precalculo.cotacao.numero if material.precalculo and material.precalculo.cotacao else None
    precalculo_numero = material.precalculo.numero if material.precalculo else None
    observacoes_gerais = material.precalculo.observacoes_materiais if material.precalculo else ""

    # Bloqueio de edição se status for 'ok'
    if request.method == "POST":
    # Evita salvar caso esteja finalizado
        if material.status == 'ok':
            messages.error(request, "Cotação finalizada. Alterações não são permitidas.")
            return redirect(request.path)

        material.fornecedor_id = request.POST.get("fornecedor") or None

        # Tratar campos decimais para evitar erro vazio -> decimal
        icms = request.POST.get("icms")
        material.icms = icms if icms else None

        lote_minimo = request.POST.get("lote_minimo")
        material.lote_minimo = lote_minimo if lote_minimo else None

        entrega_dias = request.POST.get("entrega_dias")
        material.entrega_dias = entrega_dias if entrega_dias else None

        preco_kg = request.POST.get("preco_kg")
        material.preco_kg = preco_kg if preco_kg else None

        material.save()
        material.refresh_from_db()  # Atualiza os dados do objeto na memória
        messages.success(request, "Cotação atualizada com sucesso.")


    return render(request, "cotacoes/responder_cotacao_material.html", {
        "material": material,
        "fornecedores": fornecedores,
        "cotacao_numero": cotacao_numero,
        "precalculo_numero": precalculo_numero,
        "materia_prima": materia_prima,
        "observacoes_gerais": observacoes_gerais,
    })