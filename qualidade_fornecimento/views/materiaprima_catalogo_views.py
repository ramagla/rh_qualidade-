import pandas as pd
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from qualidade_fornecimento.forms import MateriaPrimaCatalogoForm
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo
from qualidade_fornecimento.utils import extrair_bitola, extrair_norma, inferir_classe


def cadastrar_materia_prima_catalogo(request):
    if request.method == "POST":
        form = MateriaPrimaCatalogoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Matéria-prima cadastrada com sucesso!")
            return redirect("materiaprima_catalogo_list")
    else:
        form = MateriaPrimaCatalogoForm()

    return render(
        request, "cadastro_materia_prima/form_materia_prima.html", {"form": form}
    )


from django.core.paginator import Paginator
from django.shortcuts import render

from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo


def listar_materia_prima_catalogo(request):
    # Filtros via GET
    codigo = request.GET.get("codigo", "").strip()
    descricao = request.GET.get("descricao", "").strip()
    norma = request.GET.get("norma", "").strip()
    classe = request.GET.get("classe", "").strip()
    tipo = request.GET.get("tipo", "").strip()

    # Base queryset
    queryset = MateriaPrimaCatalogo.objects.all().order_by("-atualizado_em")

    # Aplicar filtros
    if codigo:
        queryset = queryset.filter(codigo__icontains=codigo)
    if descricao:
        queryset = queryset.filter(descricao__icontains=descricao)
    if norma:
        queryset = queryset.filter(norma__icontains=norma)
    if classe:
        queryset = queryset.filter(classe__iexact=classe)
    if tipo:
        queryset = queryset.filter(tipo=tipo)

    # Indicadores
    total_registros = queryset.count()
    total_carbono = queryset.filter(classe="Carbono").count()
    total_inox = queryset.filter(classe="Inox").count()
    total_outros = queryset.exclude(classe__in=["Carbono", "Inox"]).count()

    # Paginação
    paginator = Paginator(queryset, 15)
    page_number = request.GET.get("page")
    lista_materias = paginator.get_page(page_number)

    # Dados únicos para os filtros (Select2)
    codigos_disponiveis = (
        MateriaPrimaCatalogo.objects.values_list("codigo", flat=True)
        .distinct()
        .order_by("codigo")
    )
    descricoes_disponiveis = (
        MateriaPrimaCatalogo.objects.values_list("descricao", flat=True)
        .distinct()
        .order_by("descricao")
    )
    normas_disponiveis = (
        MateriaPrimaCatalogo.objects.exclude(norma__isnull=True)
        .exclude(norma__exact="")
        .values_list("norma", flat=True)
        .distinct()
        .order_by("norma")
    )
    classes_disponiveis = (
        MateriaPrimaCatalogo.objects.values_list("classe", flat=True)
        .distinct()
        .order_by("classe")
    )

    # Contexto
    context = {
        "lista_materias": lista_materias,
        "total_registros": total_registros,
        "total_carbono": total_carbono,
        "total_inox": total_inox,
        "total_outros": total_outros,
        "codigos_disponiveis": codigos_disponiveis,
        "descricoes_disponiveis": descricoes_disponiveis,
        "normas_disponiveis": normas_disponiveis,
        "classes_disponiveis": classes_disponiveis,
        "request": request,
    }

    return render(request, "cadastro_materia_prima/listar_materiaprima.html", context)


def importar_materia_prima_excel(request):
    if request.method == "POST" and request.FILES.get("excel_file"):
        excel_file = request.FILES["excel_file"]
        try:
            df = pd.read_excel(excel_file)

            colunas_obrigatorias = ["codigo", "descricao"]
            for col in colunas_obrigatorias:
                if col not in df.columns:
                    messages.error(
                        request, f"A coluna obrigatória '{col}' não está presente."
                    )
                    return redirect("materiaprima_importar")

            importados = 0
            atualizados = 0

            for _, row in df.iterrows():
                codigo = str(row.get("codigo")).strip()
                descricao = str(row.get("descricao", "")).strip()
                localizacao = str(row.get("localizacao", "")).strip()
                tipo = str(row.get("tipo", "Materia-Prima")).strip()  # Valor padrão

                if not codigo or not descricao:
                    continue

                norma = extrair_norma(descricao)
                bitola = extrair_bitola(descricao)
                classe = inferir_classe(descricao)

                obj, created = MateriaPrimaCatalogo.objects.update_or_create(
                    codigo=codigo,
                    defaults={
                        "descricao": descricao,
                        "localizacao": localizacao,
                        "norma": norma,
                        "bitola": bitola,
                        "classe": classe,
                        "tipo": tipo,
                    },
                )

                if created:
                    importados += 1
                else:
                    atualizados += 1

            messages.success(
                request,
                f"Importação concluída com sucesso: {importados} novos e {atualizados} atualizados.",
            )
        except Exception as e:
            messages.error(request, f"Erro ao importar: {e}")
    else:
        messages.warning(request, "Nenhum arquivo foi enviado.")

    return render(
        request, "cadastro_materia_primatb050/importar_excel_materia_prima.html"
    )


def editar_materia_prima(request, pk):
    materia_prima = get_object_or_404(MateriaPrimaCatalogo, pk=pk)
    if request.method == "POST":
        form = MateriaPrimaCatalogoForm(request.POST, instance=materia_prima)
        if form.is_valid():
            form.save()
            messages.success(request, "Matéria-prima atualizada com sucesso!")

            if "salvar_proximo" in request.POST:
                # Tenta buscar o próximo ID
                proxima = (
                    MateriaPrimaCatalogo.objects.filter(id__gt=materia_prima.id)
                    .order_by("id")
                    .first()
                )
                if proxima:
                    return redirect("materiaprima_editar", pk=proxima.id)
                else:
                    messages.info(request, "Esse era o último registro.")
                    return redirect("materiaprima_catalogo_list")

            return redirect("materiaprima_catalogo_list")
    else:
        form = MateriaPrimaCatalogoForm(instance=materia_prima)

    return render(
        request,
        "cadastro_materia_prima/form_materia_prima.html",
        {"form": form, "editar": True},
    )


from django.db.models import ProtectedError


def deletar_materia_prima(request, pk):
    materia_prima = get_object_or_404(MateriaPrimaCatalogo, pk=pk)

    if request.method == "POST":
        try:
            materia_prima.delete()
            messages.success(request, "Matéria-prima deletada com sucesso!")
        except ProtectedError as e:
            messages.error(
                request,
                "❌ Não é possível excluir esta matéria-prima pois ela está vinculada a registros em uso.",
            )
        return redirect("materiaprima_catalogo_list")

    return render(
        request,
        "cadastro_materia_prima/deletar_materia_prima.html",
        {"materia_prima": materia_prima},
    )


from django.utils.timezone import now


def visualizar_materia_prima(request, pk):
    materia = get_object_or_404(MateriaPrimaCatalogo, pk=pk)
    context = {
        "materia": materia,
        "now": now(),
    }
    return render(
        request, "cadastro_materia_prima/visualizar_materiaprima.html", context
    )
