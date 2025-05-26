# VIEWS CORRIGIDA E ATUALIZADA

from venv import logger
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from qualidade_fornecimento.forms.norma_forms import (
    ComposicaoFormSet,
    NormaTecnicaForm,
    TracaoFormSet,
)
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo
from qualidade_fornecimento.models.norma import (
    NormaComposicaoElemento,
    NormaTecnica,
    NormaTracao,
)



from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from qualidade_fornecimento.models.norma import NormaTecnica

@login_required
def lista_normas(request):
    nome_norma = request.GET.get("nome_norma")
    tem_tracao = request.GET.get("tem_tracao")
    tem_composicao = request.GET.get("tem_composicao")

    qs = NormaTecnica.objects.all().order_by("-id")

    # Filtro por nome da norma
    if nome_norma:
        qs = qs.filter(nome_norma=nome_norma)

    # Filtro por faixa de tração existente
    if tem_tracao == "sim":
        qs = qs.filter(tracoes__isnull=False).distinct()
    elif tem_tracao == "nao":
        qs = qs.filter(tracoes__isnull=True)

    # Filtro por composição química existente
    if tem_composicao == "sim":
        qs = qs.filter(elementos__isnull=False).distinct()
    elif tem_composicao == "nao":
        qs = qs.filter(elementos__isnull=True)

    total_normas = NormaTecnica.objects.count()
    normas_com_arquivo = NormaTecnica.objects.exclude(arquivo_norma="").count()
    normas_sem_vinculo = NormaTecnica.objects.filter(vinculo_norma__isnull=True).count()

    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page")
    normas = paginator.get_page(page_number)

    # Lista de normas ainda não aprovadas (para o modal de aprovação)
    normas_pendentes = NormaTecnica.objects.filter(aprovada=False)

    context = {
        "normas": normas,
        "normas_pendentes": normas_pendentes,
        "total_normas": total_normas,
        "normas_com_arquivo": normas_com_arquivo,
        "normas_sem_vinculo": normas_sem_vinculo,
        "nome_norma": nome_norma,
        "tem_tracao": tem_tracao,
        "tem_composicao": tem_composicao,
        "lista_normas": NormaTecnica.objects.values_list(
            "nome_norma", flat=True
        ).distinct(),
    }
    return render(request, "normas/lista_normas.html", context)



# lista fixa dos 18 campos numéricos da composição
CAMPOS_COMP = [
    "c_min",
    "c_max",
    "mn_min",
    "mn_max",
    "si_min",
    "si_max",
    "p_min",
    "p_max",
    "s_min",
    "s_max",
    "cr_min",
    "cr_max",
    "ni_min",
    "ni_max",
    "cu_min",
    "cu_max",
    "al_min",
    "al_max",
]


@login_required
def cadastrar_norma(request):
    """Cria uma nova norma técnica, suas composições químicas e faixas de tração."""
    if request.method == "POST":
        header_form = NormaTecnicaForm(request.POST, request.FILES)
        fset_elementos = ComposicaoFormSet(request.POST, prefix="elem")
        fset_tracao = TracaoFormSet(request.POST, prefix="trac")

        # permite linhas vazias
        for f in fset_elementos.forms + fset_tracao.forms:
            f.empty_permitted = True

        if (
            header_form.is_valid()
            and fset_elementos.is_valid()
            and fset_tracao.is_valid()
        ):
            with transaction.atomic():
                norma = header_form.save()

                # composição química
                for elem in fset_elementos.save(commit=False):
                    elem.norma = norma
                    elem.save()
                for obj in fset_elementos.deleted_objects:
                    obj.delete()

                # tração
                for trac in fset_tracao.save(commit=False):
                    trac.norma = norma

                    # Conversão de MPa para Kgf/mm² antes de salvar
                    usar_mpa = request.POST.get("usar_mpa") == "true"
                    if usar_mpa:
                        from decimal import Decimal
                        fator = Decimal('0.10197162129779')
                        if trac.resistencia_min:
                            trac.resistencia_min = round(trac.resistencia_min * fator, 2)
                        if trac.resistencia_max:
                            trac.resistencia_max = round(trac.resistencia_max * fator, 2)


                    trac.save()

                for obj in fset_tracao.deleted_objects:
                    obj.delete()

            return redirect("lista_normas")

    else:
        header_form = NormaTecnicaForm()
        fset_elementos = ComposicaoFormSet(
            queryset=NormaComposicaoElemento.objects.none(), prefix="elem"
        )
        fset_tracao = TracaoFormSet(queryset=NormaTracao.objects.none(), prefix="trac")

    ctx = {
        "form": header_form,
        "elementos_formset": fset_elementos,
        "tracao_formset": fset_tracao,
        "campos_comp": CAMPOS_COMP,  #  <<<  passa a lista p/ o template
        "editar": False,  #  sinaliza modo cadastro
    }
    return render(request, "normas/cadastrar_norma.html", ctx)


@login_required
def editar_norma(request, id):
    norma = get_object_or_404(NormaTecnica, id=id)

    if request.method == "POST":
        form = NormaTecnicaForm(request.POST, request.FILES, instance=norma)

        fset_elementos = ComposicaoFormSet(
            request.POST,
            prefix="elem",
            queryset=NormaComposicaoElemento.objects.filter(norma=norma),
        )
        fset_tracao = TracaoFormSet(
            request.POST,
            prefix="trac",
            queryset=NormaTracao.objects.filter(norma=norma),
        )

        if form.is_valid() and fset_elementos.is_valid() and fset_tracao.is_valid():
            with transaction.atomic():
                form.save()

                # Atualiza Composição Química
                elementos = fset_elementos.save(commit=False)
                for elem in elementos:
                    elem.norma = norma
                    elem.save()
                for obj in fset_elementos.deleted_objects:
                    obj.delete()

                # Atualiza Tração
                tracoes = fset_tracao.save(commit=False)
                for trac in tracoes:
                    trac.norma = norma

                    # Conversão de MPa para Kgf/mm² antes de salvar
                    usar_mpa = request.POST.get("usar_mpa") == "true"
                    if usar_mpa:
                        from decimal import Decimal
                        fator = Decimal('0.10197162129779')
                        if trac.resistencia_min:
                            trac.resistencia_min = round(trac.resistencia_min * fator, 2)
                        if trac.resistencia_max:
                            trac.resistencia_max = round(trac.resistencia_max * fator, 2)



                    trac.save()

                for obj in fset_tracao.deleted_objects:
                    obj.delete()

            messages.success(request, "Norma atualizada com sucesso!")
            return redirect("lista_normas")
        else:
            messages.error(request, "Erro ao salvar. Verifique os campos em destaque.")

    else:
        form = NormaTecnicaForm(instance=norma)
        fset_elementos = ComposicaoFormSet(
            prefix="elem",
            queryset=NormaComposicaoElemento.objects.filter(norma=norma),
        )
        fset_tracao = TracaoFormSet(
            prefix="trac",
            queryset=NormaTracao.objects.filter(norma=norma),
        )

    context = {
        "form": form,
        "elementos_formset": fset_elementos,
        "tracao_formset": fset_tracao,
        "campos_comp": [
            "c_min", "c_max",
            "mn_min", "mn_max",
            "si_min", "si_max",
            "p_min", "p_max",
            "s_min", "s_max",
            "cr_min", "cr_max",
            "ni_min", "ni_max",
            "cu_min", "cu_max",
            "al_min", "al_max",
        ],
        "editar": True,
    }
    return render(request, "normas/cadastrar_norma.html", context)



@login_required
def excluir_norma(request, id):
    norma = get_object_or_404(NormaTecnica, id=id)
    if request.method == "POST":
        norma.delete()
        return redirect("lista_normas")
    return render(request, "normas/excluir_norma.html", {"norma": norma})


def visualizar_norma(request, id):
    norma = get_object_or_404(NormaTecnica, id=id)
    return render(request, "normas/visualizar_norma.html", {"norma": norma})


# qualidade_fornecimento/views/norma_views.py
from django.http import JsonResponse
from qualidade_fornecimento.models.norma import NormaTecnica

def get_tipos_abnt(request):
    norma_id = request.GET.get("norma_id")
    logger.debug(f">>> Norma ID recebido na view: {norma_id}")

    if not norma_id:
        return JsonResponse({"tipos": []})

    tipos = (
        NormaComposicaoElemento.objects
        .filter(norma_id=norma_id)
        .exclude(tipo_abnt__isnull=True)
        .exclude(tipo_abnt='')
        .values_list('tipo_abnt', flat=True)
        .distinct()
    )

    return JsonResponse({"tipos": list(tipos)})


def is_tecnico(user):
    return user.groups.filter(name="tecnico").exists()
from django.utils.timezone import now

@login_required
def aprovar_normas(request):
    if request.method == "POST":
        id_norma = request.POST.get("normas_aprovadas")
        if id_norma:
            norma = NormaTecnica.objects.filter(id=id_norma).first()
            if norma:
                norma.aprovada = True
                norma.aprovado_por = request.user
                norma.aprovado_em = now()
                norma.save()
                messages.success(request, f"Norma '{norma.nome_norma}' aprovada com sucesso por {request.user.get_full_name() or request.user.username}.")
        else:
            messages.warning(request, "Nenhuma norma foi selecionada.")

    return redirect("lista_normas")
