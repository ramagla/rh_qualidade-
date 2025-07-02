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
                ferramenta = form.save()

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
                ferramenta = form.save()

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

@login_required
@permission_required("comercial.view_ferramenta", raise_exception=True)
def enviar_cotacao_ferramenta(request, pk):
    ferramenta = get_object_or_404(Ferramenta, pk=pk)
    ferramenta.token_cotacao = uuid.uuid4()
    ferramenta.cotacao_enviada_em = timezone.now()
    ferramenta.save()

    link = request.build_absolute_uri(
        reverse("responder_cotacao", args=[ferramenta.token_cotacao])
    )

    servicos = ferramenta.servicos.all()

    corpo = f"""
🚀 Nova solicitação de cotação enviada:

🔧 Código: {ferramenta.codigo}
📝 Descrição: {ferramenta.descricao}
🏷️ Tipo: {ferramenta.get_tipo_display()}
👥 Cliente: {ferramenta.proprietario}
📎 Observações: {ferramenta.observacoes}

📄 Desenho: {'Sim' if ferramenta.desenho_pdf else 'Não'}
🔗 Link: {link}

📦 Materiais calculados:
"""
    if ferramenta.kg_matriz:
        corpo += f"- SAE D2 (Matriz): {ferramenta.kg_matriz:.2f} Kg\n"
    if ferramenta.kg_puncao:
        corpo += f"- SAE D2 (Punção): {ferramenta.kg_puncao:.2f} Kg\n"
    if ferramenta.kg_flange:
        corpo += f"- SAE P20 (Flange): {ferramenta.kg_flange:.2f} Kg\n"
    if ferramenta.kg_carros:
        corpo += f"- SAE 1020 (Carros): {ferramenta.kg_carros:.2f} Kg\n"
    if ferramenta.kg_formadores:
        corpo += f"- SAE D2 (Formadores): {ferramenta.kg_formadores:.2f} Kg\n"

    corpo += "\n🔧 Serviços:\n"
    for s in servicos:
        corpo += f"- {s.get_tipo_servico_display()} - Qtde: {s.quantidade}\n"

    send_mail(
        subject="📨 Cotação de Ferramenta - Comercial",
        message=corpo,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["rafael.almeida@brasmol.com.br"],
        fail_silently=False
    )

    messages.success(request, "Cotação enviada com sucesso!")
    return redirect("lista_ferramentas")



def formulario_cotacao(request, token):
    ferramenta = get_object_or_404(Ferramenta, token_cotacao=token)
    servicos = ferramenta.servicos.filter(valor_unitario__isnull=True)

    cotacao_finalizada = all(s.valor_unitario is not None for s in servicos)

    if cotacao_finalizada:
        return render(request, "cadastros/cotacao_finalizada.html", {"ferramenta": ferramenta})

    if request.method == "POST":
        sucesso = True
        for idx, s in enumerate(servicos):
            valor = request.POST.get(f"servico_{idx}_valor", "").replace(",", ".")
            try:
                if valor:
                    s.valor_unitario = Decimal(valor)
                    s.save()
            except (ValueError, InvalidOperation):
                sucesso = False
                messages.error(request, f"Erro no serviço {s.get_tipo_servico_display()}: valor inválido.")

        if sucesso:
            messages.success(request, "Valores atualizados com sucesso.")
        return redirect("responder_cotacao", token=token)

    return render(request, "cadastros/responder_cotacao.html", {
        "ferramenta": ferramenta,
        "servicos": servicos
    })


@login_required
@permission_required("comercial.view_ferramenta", raise_exception=True)
def visualizar_ferramenta(request, pk):
    ferramenta = get_object_or_404(Ferramenta, pk=pk)
    materiais = ferramenta.materiais.all()
    servicos = ferramenta.servicos.all()
    mao_de_obra = ferramenta.mao_obra.all()

    total_materiais = sum((m.valor_total for m in materiais if m.valor_unitario), 0)
    total_servicos = sum((s.valor_total for s in servicos if s.valor_unitario), 0)
    total_mo = sum((mo.valor_total for mo in mao_de_obra if mo.valor_hora), 0)
    total_geral = total_materiais + total_servicos + total_mo

    return render(request, "cadastros/visualizar_ferramenta.html", {
        "ferramenta": ferramenta,
        "materiais": materiais,
        "servicos": servicos,
        "mao_de_obra": mao_de_obra,
        "total_materiais": total_materiais,
        "total_servicos": total_servicos,
        "total_mo": total_mo,
        "total_geral": total_geral
    })


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

    blocos = BlocoFerramenta.objects.prefetch_related("itens").all()

    if numero:
        blocos = blocos.filter(numero__icontains=numero)

    # Paginação
    paginator = Paginator(blocos, 10)  # 10 blocos por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Cálculo dos totais
    total_blocos = blocos.count()
    total_itens = ItemBloco.objects.filter(bloco__in=blocos).count()
    peso_total_geral = sum(item.peso_total for item in ItemBloco.objects.filter(bloco__in=blocos))

    context = {
        "page_obj": page_obj,
        "total_blocos": total_blocos,
        "total_itens": total_itens,
        "peso_total_geral": peso_total_geral,
    }

    return render(request, "cadastros/lista_blocos.html", context)



@login_required
@permission_required("comercial.add_blocoferramenta", raise_exception=True)
def cadastrar_bloco(request):
    if request.method == "POST":
        form = BlocoForm(request.POST)
        formset = ItemBlocoFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                bloco = form.save()
                for item in formset.save(commit=False):
                    item.bloco = bloco
                    item.save()
                messages.success(request, "Bloco cadastrado com sucesso.")
                return redirect("lista_blocos")
    else:
        form = BlocoForm()
        formset = ItemBlocoFormSet()

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
        formset = ItemBlocoFormSet(request.POST, instance=bloco)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
                messages.success(request, "Bloco atualizado com sucesso.")
                return redirect("lista_blocos")
    else:
        form = BlocoForm(instance=bloco)
        formset = ItemBlocoFormSet(instance=bloco)

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
