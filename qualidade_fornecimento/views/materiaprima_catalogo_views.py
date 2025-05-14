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


from django.core.paginator import Paginator
from django.shortcuts import render
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from qualidade_fornecimento.models import NormaTecnica  # Import necessário

def listar_materia_prima_catalogo(request):
    # Filtros via GET
    codigo = request.GET.get("codigo", "").strip()
    descricao = request.GET.get("descricao", "").strip()
    norma = request.GET.get("norma", "").strip()
    classe = request.GET.get("classe", "").strip()
    tipo = request.GET.get("tipo", "").strip()
    tipo_material = request.GET.get("tipo_material", "").strip()
    tipo_abnt = request.GET.get("tipo_abnt", "").strip()

    # Base queryset
    queryset = MateriaPrimaCatalogo.objects.all().order_by("-atualizado_em")

    # Aplicar filtros
    if codigo:
        queryset = queryset.filter(codigo__icontains=codigo)
    if descricao:
        queryset = queryset.filter(descricao__icontains=descricao)
    if norma:
        queryset = queryset.filter(norma_id=norma)
    if classe:
        queryset = queryset.filter(classe__iexact=classe)
    if tipo:
        queryset = queryset.filter(tipo=tipo)
    if tipo_material:
        queryset = queryset.filter(tipo_material__icontains=tipo_material)
    if tipo_abnt:
        queryset = queryset.filter(tipo_abnt__icontains=tipo_abnt)

    # Indicadores
    total_registros = queryset.count()
    total_carbono = queryset.filter(tipo_material__icontains="carbono").count()
    total_inox = queryset.filter(tipo_material__icontains="inox").count()
    total_outros = queryset.exclude(tipo_material__icontains="carbono").exclude(tipo_material__icontains="inox").count()

    # Paginação
    paginator = Paginator(queryset, 15)
    page_number = request.GET.get("page")
    lista_materias = paginator.get_page(page_number)

    # Dados únicos para os filtros (Select2)
    codigos_disponiveis = MateriaPrimaCatalogo.objects.values_list("codigo", flat=True).distinct().order_by("codigo")
    descricoes_disponiveis = MateriaPrimaCatalogo.objects.values_list("descricao", flat=True).distinct().order_by("descricao")

    normas_ids = (
        MateriaPrimaCatalogo.objects
        .filter(norma__isnull=False)
        .values_list("norma", flat=True)
        .distinct()
    )
    normas_disponiveis = NormaTecnica.objects.filter(id__in=normas_ids).order_by("nome_norma")

    classes_disponiveis = MateriaPrimaCatalogo.objects.values_list("classe", flat=True).distinct().order_by("classe")
    tipos_materiais_disponiveis = (
        MateriaPrimaCatalogo.objects
        .filter(tipo_material__isnull=False)
        .values_list("tipo_material", flat=True)
        .distinct()
        .order_by("tipo_material")
    )
    tipos_abnt_disponiveis = (
        MateriaPrimaCatalogo.objects
        .filter(tipo_abnt__isnull=False)
        .values_list("tipo_abnt", flat=True)
        .distinct()
        .order_by("tipo_abnt")
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
        "tipos_materiais_disponiveis": tipos_materiais_disponiveis,
        "tipos_abnt_disponiveis": tipos_abnt_disponiveis,
        "request": request,
    }

    return render(request, "cadastro_materia_prima/listar_materiaprima.html", context)



from django.contrib import messages
from django.shortcuts import render, redirect
import openpyxl
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo
from django.contrib.auth.decorators import login_required
import logging

logger = logging.getLogger(__name__)

import pandas as pd
from django.contrib import messages
from django.shortcuts import render, redirect
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo

from django.shortcuts import render, redirect
from django.contrib import messages
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo
from qualidade_fornecimento.models.norma import NormaTecnica
import pandas as pd


from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages
import pandas as pd
from qualidade_fornecimento.models import NormaTecnica, MateriaPrimaCatalogo


@login_required
def importar_materia_prima_excel(request):
    if request.method == "POST":
        print("✅ View de importação chamada com sucesso")  # DEBUG

        excel_file = request.FILES.get("excel_file")
        print("📁 Arquivo recebido:", excel_file)  # DEBUG

        if not excel_file:
            messages.error(request, "Nenhum arquivo selecionado para importação.")
            return redirect("materiaprima_importar")

        try:
            df = pd.read_excel(
                excel_file,
                na_values=["NA", "na", "n/a", "N/A", "-", "—", ""]
            )
            df = df.where(pd.notnull(df), None)
            df.columns = [col.strip().lower() for col in df.columns]
            print("📄 Colunas do Excel:", df.columns.tolist())  # DEBUG
            print("🔍 Primeiras linhas:", df.head(3).to_dict(orient="records"))  # DEBUG

            colunas_obrigatorias = [
                    "código", "descrição", "localização", "tipo", "tipo material",
                    "bitolo ø (mm)", "largura (mm)", "tolerância (mm)",
                    "tolerância largura (mm)", "norma", "tipo abnt/classe"
                ]


            for col in colunas_obrigatorias:
                if col not in df.columns:
                    print(f"❌ Coluna obrigatória ausente: {col}")  # DEBUG
                    messages.error(request, f"Coluna obrigatória '{col}' não encontrada no arquivo.")
                    return redirect("materiaprima_importar")

            importados = 0
            atualizados = 0
            erros = []

            for index, row in df.iterrows():
                try:
                    print(f"\n📌 Processando linha {index + 2}: {row.to_dict()}")  # DEBUG

                    codigo = str(row.get("código", "")).strip()
                    descricao = str(row.get("descrição", "")).strip()

                    if not codigo or not descricao:
                        print(f"⚠️ Linha {index + 2} ignorada por falta de código ou descrição")  # DEBUG
                        continue

                    localizacao = str(row.get("localização") or "").strip()
                    tipo = str(row.get("tipo") or "").strip()
                    tipo_material = str(row.get("tipo de material") or "").strip()
                    bitola = str(row.get("bitolo ø (mm)") or "").replace(",", ".").strip()
                    largura = str(row.get("largura (mm)") or "").replace(",", ".").strip()
                    tolerancia = str(row.get("tolerância (mm)") or "").replace(",", ".").strip()
                    tolerancia_largura = str(row.get("tolerância largura (mm)") or "").replace(",", ".").strip()
                    norma_nome = str(row.get("norma") or "").strip()
                    tipo_abnt = str(row.get("tipo abnt/classe") or "").strip()

                    norma_obj = None
                    if norma_nome:
                        norma_obj = NormaTecnica.objects.filter(nome_norma__iexact=norma_nome).first()
                        if not norma_obj:
                            norma_obj = NormaTecnica.objects.create(nome_norma=norma_nome)

                    if tipo.lower() == "tratamento":
                        localizacao = ""
                        tipo_material = ""
                        bitola = ""
                        largura = ""
                        tolerancia = ""
                        tolerancia_largura = ""
                        norma_obj = None
                        tipo_abnt = ""

                    obj, created = MateriaPrimaCatalogo.objects.update_or_create(
                        codigo=codigo,
                        defaults={
                            "descricao": descricao,
                            "localizacao": localizacao,
                            "tipo": tipo,
                            "tipo_material": tipo_material,
                            "bitola": bitola,
                            "largura": largura,
                            "tolerancia": tolerancia,
                            "tolerancia_largura": tolerancia_largura,
                            "norma": norma_obj,
                            "tipo_abnt": tipo_abnt,
                        },
                    )

                    print(f"✅ {'Criado' if created else 'Atualizado'}: {codigo}")  # DEBUG

                    if created:
                        importados += 1
                    else:
                        atualizados += 1

                except Exception as erro_linha:
                    print(f"❌ Erro na linha {index + 2}: {erro_linha}")  # DEBUG
                    erros.append(f"Linha {index + 2}: erro ao importar - {str(erro_linha)}")

            if erros:
                messages.warning(request, "Algumas linhas apresentaram erros.")
                for erro in erros:
                    messages.warning(request, erro)
            elif importados == 0 and atualizados == 0:
                messages.info(request, "Nenhum registro foi importado. Verifique os dados.")
            else:
                messages.success(
                    request,
                    f"Importação concluída: {importados} novos registros, {atualizados} atualizados."
                )

        except Exception as e:
            print("❌ ERRO GERAL NA IMPORTAÇÃO:", e)  # DEBUG
            messages.error(request, f"Erro ao processar o arquivo Excel: {str(e)}")

        return redirect("materiaprima_importar")

    print("🔁 Método GET carregado (render de template)")  # DEBUG
    return render(request, "cadastro_materia_prima/importar_excel_materia_prima.html")










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
