from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from django.urls import reverse
from comercial.forms.ferramenta_form import FerramentaForm
from comercial.models import Ferramenta
from comercial.models.ferramenta import MaoDeObraFerramenta, MaterialFerramenta, ServicoFerramenta
from decimal import Decimal, InvalidOperation

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
    MaterialFerramentaFormSet,
    MaoDeObraFormSet,
    ServicoFormSet
)
from django.db.models.query import QuerySet  # no topo se necessário



@login_required
@permission_required("comercial.add_ferramenta", raise_exception=True)
def cadastrar_ferramenta(request):
    if request.method == "POST":
        form = FerramentaForm(request.POST, request.FILES)

        # Inicializa os formsets *sem* instance
        materiais_formset = MaterialFerramentaFormSet(request.POST, prefix="material")
        mo_formset = MaoDeObraFormSet(request.POST, prefix="mo")
        servico_formset = ServicoFormSet(request.POST, prefix="servico")

        if form.is_valid() and materiais_formset.is_valid() and mo_formset.is_valid() and servico_formset.is_valid():
            with transaction.atomic():
                ferramenta = form.save()

                for mform in materiais_formset.save(commit=False):
                    mform.ferramenta = ferramenta
                    mform.save()
                for d in materiais_formset.deleted_objects:
                    d.delete()

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
            ferramenta = None  # caso form seja inválido
    else:
        form = FerramentaForm()
        materiais_formset = MaterialFerramentaFormSet(queryset=MaterialFerramenta.objects.none(), prefix="material")
        mo_formset = MaoDeObraFormSet(queryset=MaoDeObraFerramenta.objects.none(), prefix="mo")
        servico_formset = ServicoFormSet(queryset=ServicoFerramenta.objects.none(), prefix="servico")
        ferramenta = None

    return render(request, "cadastros/form_ferramentas.html", {
        "form": form,
        "materiais_formset": materiais_formset,
        "mo_formset": mo_formset,
        "servico_formset": servico_formset,
        "formsets_agrupados": [materiais_formset, mo_formset, servico_formset],
        "ferramenta": ferramenta
    })


from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.db import transaction

from comercial.models import Ferramenta
from comercial.forms.ferramenta_form import (
    FerramentaForm,
    MaterialFerramentaFormSet,
    MaoDeObraFormSet,
    ServicoFormSet
)
from comercial.models.ferramenta import MaterialFerramenta, MaoDeObraFerramenta, ServicoFerramenta


@login_required
@permission_required("comercial.change_ferramenta", raise_exception=True)
def editar_ferramenta(request, pk):
    ferramenta = get_object_or_404(Ferramenta, pk=pk)

    if request.method == "POST":
        form = FerramentaForm(request.POST, request.FILES, instance=ferramenta)
        materiais_formset = MaterialFerramentaFormSet(request.POST, request.FILES, instance=ferramenta, prefix="material")
        mo_formset = MaoDeObraFormSet(request.POST, instance=ferramenta, prefix="mo")
        servico_formset = ServicoFormSet(request.POST, instance=ferramenta, prefix="servico")


        if form.is_valid() and materiais_formset.is_valid() and mo_formset.is_valid() and servico_formset.is_valid():
            with transaction.atomic():
                ferramenta = form.save()

                for mform in materiais_formset.save(commit=False):
                    mform.ferramenta = ferramenta
                    mform.save()
                for d in materiais_formset.deleted_objects:
                    d.delete()

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
        materiais_formset = MaterialFerramentaFormSet(instance=ferramenta, prefix="material")
        mo_formset = MaoDeObraFormSet(instance=ferramenta, prefix="mo")
        servico_formset = ServicoFormSet(instance=ferramenta, prefix="servico")


    return render(request, "cadastros/form_ferramentas.html", {
        "form": form,
        "materiais_formset": materiais_formset,
        "mo_formset": mo_formset,
        "servico_formset": servico_formset,
        "formsets_agrupados": [materiais_formset, mo_formset, servico_formset],
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

    materiais = ferramenta.materiais.all()
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

📦 Materiais:
"""
    for m in materiais:
        corpo += f"- {m.nome_material} ({m.unidade_medida}) - Qtde: {m.quantidade}\n"

    corpo += "\n🔧 Serviços:\n"
    for s in servicos:
        corpo += f"- {s.get_tipo_servico_display()} - Qtde: {s.quantidade}\n"

    send_mail(
        subject="📨 Cotação de Ferramenta - Comercial",
        message=corpo,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["rafael.almeida@brasmol.com.br"],  # ajuste
        fail_silently=False
    )

    messages.success(request, "Cotação enviada com sucesso!")
    return redirect("lista_ferramentas")


def formulario_cotacao(request, token):
    ferramenta = get_object_or_404(Ferramenta, token_cotacao=token)
    materiais = ferramenta.materiais.filter(valor_unitario__isnull=True)
    servicos = ferramenta.servicos.filter(valor_unitario__isnull=True)


    # Verifica se todos os valores já foram preenchidos
    cotacao_finalizada = all(m.valor_unitario is not None for m in materiais) and \
                         all(s.valor_unitario is not None for s in servicos)

    if cotacao_finalizada:
        return render(request, "cadastros/cotacao_finalizada.html", {"ferramenta": ferramenta})

    if request.method == "POST":
        sucesso = True

        for idx, m in enumerate(materiais):
            valor = request.POST.get(f"material_{idx}_valor", "").replace(",", ".")
            try:
                if valor:
                    m.valor_unitario = Decimal(valor)
                    m.save()
            except (ValueError, InvalidOperation):
                sucesso = False
                messages.error(request, f"Erro no material {m.nome_material}: valor inválido.")

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
        "materiais": materiais,
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
