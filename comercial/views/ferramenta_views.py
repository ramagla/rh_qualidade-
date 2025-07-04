from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from django.urls import reverse
from comercial.forms.ferramenta_form import FerramentaForm
from comercial.models import Ferramenta
from comercial.models.ferramenta import BlocoFerramenta, ItemBloco, MaoDeObraFerramenta,  ServicoFerramenta
from decimal import Decimal, InvalidOperation
from comercial.forms.ferramenta_form import BlocoForm, ItemBlocoFormSet
from django.db.models import Sum, Avg


@login_required
@permission_required("comercial.view_ferramenta", raise_exception=True)
def lista_ferramentas(request):
    ferramentas = Ferramenta.objects.all()

    # 🔍 Filtros
    codigo = request.GET.get("codigo")
    tipo = request.GET.get("tipo")

    if codigo:
        ferramentas = ferramentas.filter(codigo__icontains=codigo)

    if tipo:
        ferramentas = ferramentas.filter(tipo=tipo)

    # 📊 Indicadores
    total_ferramentas = ferramentas.count()
    total_novas = ferramentas.filter(tipo="Nova").count()
    total_adaptacoes = ferramentas.filter(tipo="Adpt").count()
    total_outros = ferramentas.exclude(tipo__in=["Nova", "Adpt"]).count()

    # 📄 Paginação
    paginator = Paginator(ferramentas.order_by("codigo"), 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "total_ferramentas": total_ferramentas,
        "total_novas": total_novas,
        "total_adaptacoes": total_adaptacoes,
        "total_outros": total_outros,
    }

    return render(request, "cadastros/lista_ferramentas.html", context)


from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction

from comercial.models import Ferramenta
from comercial.forms.ferramenta_form import (
    FerramentaForm,
    MaoDeObraFormSet,
    ServicoFormSet
)
from django.db.models.query import QuerySet  # no topo se necessário



@login_required
@permission_required("comercial.add_ferramenta", raise_exception=True)
def cadastrar_ferramenta(request):
    if request.method == "POST":
        form = FerramentaForm(request.POST, request.FILES)
        mo_formset = MaoDeObraFormSet(request.POST, prefix="mo")
        servico_formset = ServicoFormSet(request.POST, prefix="servico")

        if form.is_valid() and mo_formset.is_valid() and servico_formset.is_valid():
            with transaction.atomic():
                ferramenta = form.save(commit=False)

                # ⬇️ Calcula os pesos do bloco, se houver
                if ferramenta.bloco:
                    itens = ferramenta.bloco.itens.all()
                    ferramenta.peso_sae_kg = sum(Decimal(i.peso_total or 0) for i in itens if i.material == "SAE 1020")
                    ferramenta.peso_vnd_kg = sum(Decimal(i.peso_total or 0) for i in itens if i.material == "VND")


                ferramenta.save()

                for moform in mo_formset.save(commit=False):
                    moform.ferramenta = ferramenta
                    moform.save()
                for d in mo_formset.deleted_objects:
                    d.delete()

                for sform in servico_formset.save(commit=False):
                    sform.ferramenta = ferramenta
                    sform.save()
                for d in servico_formset.deleted_objects:
                    d.delete()

                messages.success(request, "Ferramenta cadastrada com sucesso!")
                return redirect("lista_ferramentas")
        else:
            ferramenta = None
    else:
        form = FerramentaForm()
        mo_formset = MaoDeObraFormSet(queryset=MaoDeObraFerramenta.objects.none(), prefix="mo")
        servico_formset = ServicoFormSet(queryset=ServicoFerramenta.objects.none(), prefix="servico")
        ferramenta = None

    return render(request, "cadastros/form_ferramentas.html", {
        "form": form,
        "mo_formset": mo_formset,
        "servico_formset": servico_formset,
        "formsets_agrupados": [mo_formset, servico_formset],
        "ferramenta": ferramenta
    })



from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.db import transaction

from comercial.models import Ferramenta
from comercial.forms.ferramenta_form import (
    FerramentaForm,
    MaoDeObraFormSet,
    ServicoFormSet
)
from comercial.models.ferramenta import  MaoDeObraFerramenta, ServicoFerramenta


@login_required
@permission_required("comercial.change_ferramenta", raise_exception=True)
def editar_ferramenta(request, pk):
    ferramenta = get_object_or_404(Ferramenta, pk=pk)

    if request.method == "POST":
        form = FerramentaForm(request.POST, request.FILES, instance=ferramenta)
        mo_formset = MaoDeObraFormSet(request.POST, instance=ferramenta, prefix="mo")
        servico_formset = ServicoFormSet(request.POST, instance=ferramenta, prefix="servico")

        if form.is_valid() and mo_formset.is_valid() and servico_formset.is_valid():
            with transaction.atomic():
                ferramenta = form.save(commit=False)

                # ⬇️ Atualiza os pesos conforme o bloco selecionado
                if ferramenta.bloco:
                    itens = ferramenta.bloco.itens.all()
                    ferramenta.peso_sae_kg = sum(Decimal(i.peso_total or 0) for i in itens if i.material == "SAE 1020")
                    ferramenta.peso_vnd_kg = sum(Decimal(i.peso_total or 0) for i in itens if i.material == "VND")


                ferramenta.save()


                for moform in mo_formset.save(commit=False):
                    moform.ferramenta = ferramenta
                    moform.save()
                for d in mo_formset.deleted_objects:
                    d.delete()

                for sform in servico_formset.save(commit=False):
                    sform.ferramenta = ferramenta
                    sform.save()
                for d in servico_formset.deleted_objects:
                    d.delete()

                messages.success(request, "Ferramenta atualizada com sucesso!")
                return redirect("lista_ferramentas")
        else:
            messages.error(request, "Corrija os erros abaixo para continuar.")
    else:
        form = FerramentaForm(instance=ferramenta)
        mo_formset = MaoDeObraFormSet(instance=ferramenta, prefix="mo")
        servico_formset = ServicoFormSet(instance=ferramenta, prefix="servico")

    return render(request, "cadastros/form_ferramentas.html", {
        "form": form,
        "mo_formset": mo_formset,
        "servico_formset": servico_formset,
        "formsets_agrupados": [mo_formset, servico_formset],
        "ferramenta": ferramenta
    })




@login_required
@permission_required("comercial.delete_ferramenta", raise_exception=True)
def excluir_ferramenta(request, pk):
    ferramenta = get_object_or_404(Ferramenta, pk=pk)
    ferramenta.delete()
    messages.success(request, "Ferramenta excluída com sucesso.")
    return redirect("lista_ferramentas")




import uuid
from django.core.mail import send_mail
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings
from django.utils.html import strip_tags

@login_required
@permission_required("comercial.view_ferramenta", raise_exception=True)
def enviar_cotacao_ferramenta(request, pk):
    ferramenta = get_object_or_404(Ferramenta, pk=pk)

    # Gera token e data de envio
    ferramenta.token_cotacao = uuid.uuid4()
    ferramenta.cotacao_enviada_em = timezone.now()
    ferramenta.save()

    # Gera link público para resposta
    link = request.build_absolute_uri(
        reverse("responder_cotacao", args=[ferramenta.token_cotacao])
    )

    # Corpo simplificado do e-mail
    corpo = f"""
🚀 Nova solicitação de cotação enviada:

🔧 Código: {ferramenta.codigo}
📝 Descrição: {ferramenta.descricao}
🏷️ Tipo: {ferramenta.get_tipo_display()}
👥 Cliente: {ferramenta.proprietario}
📎 Observações: {strip_tags(ferramenta.observacoes)}

📄 Desenho: {'Sim' if ferramenta.desenho_pdf else 'Não'}
🔗 Link: {link}
"""

    # Envio do e-mail
    send_mail(
        subject="📨 Cotação de Ferramenta - Comercial",
        message=corpo,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["rafael.almeida@brasmol.com.br"],
        fail_silently=False,
    )

    messages.success(request, "Cotação enviada com sucesso!")
    return redirect("lista_ferramentas")





from decimal import Decimal, InvalidOperation
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from comercial.models import Ferramenta


def formulario_cotacao(request, token):
    ferramenta = get_object_or_404(Ferramenta, token_cotacao=token)
    servicos = ferramenta.servicos.filter(valor_unitario__isnull=True)

    # ✅ Verifica se falta preencher os valores dos materiais agrupados
    falta_material = (
        ferramenta.valor_unitario_sae is None or
        ferramenta.valor_unitario_carros is None or
        ferramenta.valor_unitario_vnd is None or
        ferramenta.valor_unitario_matriz is None or
        ferramenta.valor_unitario_puncao is None or
        ferramenta.valor_unitario_formadores is None or
        ferramenta.valor_unitario_flange is None
    )

    # ✅ Verifica se há algum serviço com valor unitário em branco
    falta_servicos = any(s.valor_unitario is None for s in ferramenta.servicos.all())

    # ✅ Se tudo estiver preenchido, redireciona para tela final
    if not falta_material and not falta_servicos:
        return render(request, "cadastros/cotacao_finalizada.html", {"ferramenta": ferramenta})

    if request.method == "POST":
        sucesso = True

        # 🛠️ Atualiza os serviços
        for idx, s in enumerate(servicos):
            valor = request.POST.get(f"servico_{idx}_valor", "").replace(",", ".")
            try:
                if valor:
                    s.valor_unitario = Decimal(valor)
                    s.save()
            except (ValueError, InvalidOperation):
                sucesso = False
                messages.error(request, f"Erro no serviço {s.get_tipo_servico_display()}: valor inválido.")

        # 🧱 Atualiza os valores dos materiais agrupados
        try:
            # SAE 1020 (agrupa bloco + carros)
            sae_valor = request.POST.get("valor_unitario_sae-1020", "").replace(",", ".")
            if sae_valor:
                valor = Decimal(sae_valor)
                ferramenta.valor_unitario_sae = valor
                ferramenta.valor_unitario_carros = valor

            # VND
            vnd_valor = request.POST.get("valor_unitario_vnd", "").replace(",", ".")
            if vnd_valor:
                ferramenta.valor_unitario_vnd = Decimal(vnd_valor)

            # SAE D2 (matriz + puncao + formadores)
            sae_d2_valor = request.POST.get("valor_unitario_sae-d2", "").replace(",", ".")
            if sae_d2_valor:
                valor = Decimal(sae_d2_valor)
                ferramenta.valor_unitario_matriz = valor
                ferramenta.valor_unitario_puncao = valor
                ferramenta.valor_unitario_formadores = valor

            # SAE P20 (flange)
            sae_p20_valor = request.POST.get("valor_unitario_sae-p20", "").replace(",", ".")
            if sae_p20_valor:
                ferramenta.valor_unitario_flange = Decimal(sae_p20_valor)

            ferramenta.save()

        except (ValueError, InvalidOperation):
            sucesso = False
            messages.error(request, "Erro nos valores dos materiais. Preencha corretamente.")

        if sucesso:
            messages.success(request, "Valores atualizados com sucesso.")
        return redirect("responder_cotacao", token=token)

    # 📦 Prepara dados agrupados de materiais
    materiais_agrupados = {
        "SAE 1020": (ferramenta.peso_sae_kg or 0) + (ferramenta.kg_carros or 0),
        "VND": ferramenta.peso_vnd_kg or 0,
        "SAE D2": (ferramenta.kg_matriz or 0) + (ferramenta.kg_puncao or 0) + (ferramenta.kg_formadores or 0),
        "SAE P20": ferramenta.kg_flange or 0,
    }

    return render(request, "cadastros/responder_cotacao.html", {
        "ferramenta": ferramenta,
        "servicos": servicos,
        "materiais_agrupados": materiais_agrupados
    })




from decimal import Decimal
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404
from comercial.models import Ferramenta


from decimal import Decimal
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404
from comercial.models import Ferramenta


@login_required
@permission_required("comercial.view_ferramenta", raise_exception=True)
def visualizar_ferramenta(request, pk):
    ferramenta = get_object_or_404(Ferramenta, pk=pk)

    mao_de_obra = ferramenta.mao_obra.all()
    servicos = ferramenta.servicos.all()
    materiais = []

    def add_material(nome, peso, valor_unitario):
        try:
            peso = Decimal(peso or 0)
            valor_unitario = Decimal(valor_unitario or 0)
            materiais.append({
                "nome": nome,
                "peso": peso,
                "valor_unitario": valor_unitario,
                "total": peso * valor_unitario
            })
        except Exception as e:
            print(f"Erro em add_material({nome}): {e}")

    # 🧱 Bloco
    if ferramenta.bloco:
        nome_bloco = f"(Bloco {ferramenta.bloco.numero})"
        add_material(f"SAE 1020 {nome_bloco}", ferramenta.peso_sae_kg, ferramenta.valor_unitario_sae)
        add_material(f"VND {nome_bloco}", ferramenta.peso_vnd_kg, ferramenta.valor_unitario_vnd)
    else:
        add_material("SAE 1020", ferramenta.peso_sae_kg, ferramenta.valor_unitario_sae)
        add_material("VND", ferramenta.peso_vnd_kg, ferramenta.valor_unitario_vnd)

    # 🧮 Fórmulas com material na frente
    add_material("SAE D2 (Matriz)", ferramenta.kg_matriz, ferramenta.valor_unitario_matriz)
    add_material("SAE D2 (Punção)", ferramenta.kg_puncao, ferramenta.valor_unitario_puncao)
    add_material("SAE P20 (Flange)", ferramenta.kg_flange, ferramenta.valor_unitario_flange)
    add_material("SAE 1020 (Carros)", ferramenta.kg_carros, ferramenta.valor_unitario_carros)
    add_material("SAE D2 (Formadores)", ferramenta.kg_formadores, ferramenta.valor_unitario_formadores)

    # Totais
    total_materiais = sum((m["total"] for m in materiais), Decimal("0.00"))
    total_servicos = sum((s.valor_total for s in servicos if s.valor_unitario), Decimal("0.00"))
    total_mo = sum((mo.valor_total for mo in mao_de_obra if mo.valor_hora), Decimal("0.00"))
    total_geral = total_materiais + total_servicos + total_mo

    context = {
        "ferramenta": ferramenta,
        "materiais": materiais,
        "servicos": servicos,
        "mao_de_obra": mao_de_obra,
        "total_materiais": total_materiais,
        "total_servicos": total_servicos,
        "total_mo": total_mo,
        "total_geral": total_geral,
    }

    return render(request, "cadastros/visualizar_ferramenta.html", context)




from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.timezone import now
from comercial.models import CentroDeCusto

@login_required
def ajax_valor_hora_centro_custo(request):
    tipo = request.GET.get("tipo")
    nome_departamento = "Ferramentaria" if tipo == "Ferramentaria" else "Projeto" if tipo == "Projeto" else None

    if not nome_departamento:
        return JsonResponse({"sucesso": False, "erro": "Tipo inválido"})

    centro = (
        CentroDeCusto.objects
        .select_related("departamento")
        .filter(departamento__nome__icontains=nome_departamento, vigencia__lte=now().date())
        .order_by("-vigencia")
        .first()
    )

    if centro:
        return JsonResponse({"sucesso": True, "valor": float(centro.custo_atual)})
    else:
        return JsonResponse({"sucesso": False, "erro": "Nenhum custo vigente encontrado"})


@login_required
@permission_required("comercial.view_blocoferramenta", raise_exception=True)
def lista_blocos(request):
    numero = request.GET.get("numero")
    material = request.GET.get("material")

    blocos = BlocoFerramenta.objects.prefetch_related("itens").all()

    # Filtros
    if numero:
        blocos = blocos.filter(numero__icontains=numero)

    if material:
        blocos = blocos.filter(itens__material=material).distinct()

    # Lista de blocos distintos para o filtro (select2)
    blocos_distintos = BlocoFerramenta.objects.order_by("numero").values_list("numero", flat=True).distinct()

    # Paginação
    paginator = Paginator(blocos, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Cálculo dos totais
    total_blocos = blocos.count()
    total_itens = ItemBloco.objects.filter(bloco__in=blocos).count()
    peso_total_geral = sum(item.peso_total for item in ItemBloco.objects.filter(bloco__in=blocos))

    # Novos indicadores
    total_sae = ItemBloco.objects.filter(material="SAE 1020", bloco__in=blocos).aggregate(Sum("peso_total"))["peso_total__sum"] or 0
    total_vnd = ItemBloco.objects.filter(material="VND", bloco__in=blocos).aggregate(Sum("peso_total"))["peso_total__sum"] or 0
    peso_medio = blocos.annotate(total=Sum("itens__peso_total")).aggregate(Avg("total"))["total__avg"] or 0

    context = {
        "page_obj": page_obj,
        "total_blocos": total_blocos,
        "total_itens": total_itens,
        "peso_total_geral": peso_total_geral,
        "total_sae": total_sae,
        "total_vnd": total_vnd,
        "peso_medio": peso_medio,
        "blocos_distintos": blocos_distintos,
    }

    return render(request, "cadastros/lista_blocos.html", context)




@login_required
@permission_required("comercial.add_blocoferramenta", raise_exception=True)
def cadastrar_bloco(request):
    if request.method == "POST":
        form = BlocoForm(request.POST)
        formset = ItemBlocoFormSet(request.POST, prefix='itens')

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                bloco = form.save()
                formset.instance = bloco
                formset.save()
                messages.success(request, "Bloco cadastrado com sucesso.")
                return redirect("lista_blocos")
        else:
            print("⛔ Formulário inválido:")
            print("Form:", form.errors)
            print("Formset:", formset.errors)
            print("Formset non_form_errors:", formset.non_form_errors())
    else:
        form = BlocoForm()
        formset = ItemBlocoFormSet(prefix='itens')

    return render(request, "cadastros/form_blocos.html", {
        "form": form,
        "formset": formset,
        "titulo": "Cadastrar Bloco"
    })




@login_required
@permission_required("comercial.change_blocoferramenta", raise_exception=True)
def editar_bloco(request, pk):
    bloco = get_object_or_404(BlocoFerramenta, pk=pk)

    if request.method == "POST":
        form = BlocoForm(request.POST, instance=bloco)
        formset = ItemBlocoFormSet(request.POST, instance=bloco, prefix='itens')

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                bloco = form.save()
                formset.save()
                messages.success(request, "Bloco atualizado com sucesso.")
                return redirect("lista_blocos")
        else:
            print("⛔ Erro ao atualizar:")
            print("Form:", form.errors)
            print("Formset:", formset.errors)
            print("Formset non_form_errors:", formset.non_form_errors())
    else:
        form = BlocoForm(instance=bloco)
        formset = ItemBlocoFormSet(instance=bloco, prefix='itens')

    return render(request, "cadastros/form_blocos.html", {
        "form": form,
        "formset": formset,
        "titulo": f"Editar Bloco {bloco.numero}"
    })






@login_required
@permission_required("comercial.delete_blocoferramenta", raise_exception=True)
def excluir_bloco(request, pk):
    bloco = get_object_or_404(BlocoFerramenta, pk=pk)
    if request.method == "POST":
        bloco.delete()
        messages.success(request, "Bloco excluído com sucesso.")
        return redirect("lista_blocos")
    return redirect("lista_blocos")  # A exclusão será confirmada via modal, então redireciona


from django.http import JsonResponse
from comercial.models.ferramenta import ItemBloco, BlocoFerramenta

from django.http import JsonResponse
from comercial.models.ferramenta import BlocoFerramenta

@login_required
def ajax_materiais_do_bloco(request, bloco_id):
    try:
        bloco = BlocoFerramenta.objects.prefetch_related("itens").get(pk=bloco_id)
        sae_total = sum((item.peso_total or 0) for item in bloco.itens.filter(material="SAE 1020"))
        vnd_total = sum((item.peso_total or 0) for item in bloco.itens.filter(material="VND"))
        return JsonResponse({
            "sucesso": True,
            "sae_kg": float(sae_total),
            "vnd_kg": float(vnd_total)
        })
    except Exception as e:
        return JsonResponse({"sucesso": False, "erro": str(e)})
