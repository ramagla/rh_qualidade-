# VIEWS CORRIGIDA E ATUALIZADA

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


@login_required
@login_required
def lista_normas(request):
    nome_norma = request.GET.get("nome_norma")

    qs = NormaTecnica.objects.all().order_by("-id")

    if nome_norma:
        qs = qs.filter(nome_norma=nome_norma)

    total_normas = NormaTecnica.objects.count()
    normas_com_arquivo = NormaTecnica.objects.exclude(arquivo_norma="").count()
    normas_sem_vinculo = NormaTecnica.objects.filter(vinculo_norma__isnull=True).count()

    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page")
    normas = paginator.get_page(page_number)

    context = {
        "normas": normas,
        "total_normas": total_normas,
        "normas_com_arquivo": normas_com_arquivo,
        "normas_sem_vinculo": normas_sem_vinculo,
        "nome_norma": nome_norma,
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
        # Força a lista de escolhas com base no banco ANTES de bindar os dados
        normas_catalogo = list(NormaTecnicaForm.base_fields["nome_norma"].choices) + [
            (norma.nome_norma, norma.nome_norma)
        ]
        vinculos_catalogo = list(
            NormaTecnicaForm.base_fields["vinculo_norma"].choices
        ) + [(norma.vinculo_norma, norma.vinculo_norma)]

        form = NormaTecnicaForm(request.POST, request.FILES, instance=norma)
        form.fields["nome_norma"].choices = list(set(normas_catalogo))
        form.fields["vinculo_norma"].choices = list(set(vinculos_catalogo))

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

        # Debug - veja se tem erros
        if not (
            form.is_valid() and fset_elementos.is_valid() and fset_tracao.is_valid()
        ):
            print("Erros no formulário principal:", form.errors)
            print("Erros no formset de elementos:", fset_elementos.errors)
            print("Erros no formset de tração:", fset_tracao.errors)
            messages.error(request, "Erro ao salvar. Verifique os campos em destaque.")

        else:
            with transaction.atomic():
                norma_atualizada = form.save()

                # Composição
                for elem in fset_elementos.save(commit=False):
                    elem.norma = norma_atualizada
                    elem.save()
                for obj in fset_elementos.deleted_objects:
                    obj.delete()

                # Tração
                for trac in fset_tracao.save(commit=False):
                    trac.norma = norma_atualizada
                    trac.save()
                for obj in fset_tracao.deleted_objects:
                    obj.delete()

            messages.success(request, "Norma atualizada com sucesso!")
            return redirect("lista_normas")

    else:
        form = NormaTecnicaForm(instance=norma)
        fset_elementos = ComposicaoFormSet(
            prefix="elem", queryset=NormaComposicaoElemento.objects.filter(norma=norma)
        )
        fset_tracao = TracaoFormSet(
            prefix="trac", queryset=NormaTracao.objects.filter(norma=norma)
        )

    context = {
        "form": form,
        "elementos_formset": fset_elementos,
        "tracao_formset": fset_tracao,
        "campos_comp": [
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


def get_tipos_abnt(request):
    nome_norma = request.GET.get("nome_norma")
    tipos = (
        MateriaPrimaCatalogo.objects.filter(norma=nome_norma)
        .values_list("tipo_abnt", flat=True)
        .distinct()
    )
    return JsonResponse({"tipos": list(tipos)})
