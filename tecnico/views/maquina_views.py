from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from tecnico.models.maquina import Maquina
from tecnico.forms.maquina_form import ImportarExcelForm, MaquinaForm

from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Avg, Q
from django.shortcuts import render
from tecnico.models.maquina import Maquina

@login_required
@permission_required("tecnico.view_maquina", raise_exception=True)
def lista_maquinas(request):
    # 🔎 Filtros
    codigo = request.GET.get("codigo", "").strip()
    grupo = request.GET.get("grupo", "").strip()

    qs = Maquina.objects.all()

    if codigo:
        qs = qs.filter(codigo__icontains=codigo)

    if grupo:
        qs = qs.filter(grupo_de_maquinas=grupo)

    # 📊 Indicadores
    total_maquinas = qs.count()
    velocidade_media = qs.aggregate(Avg("velocidade"))["velocidade__avg"] or 0
    valor_hora_medio = qs.aggregate(Avg("valor_hora"))["valor_hora__avg"] or 0

    # 📄 Códigos únicos para filtro
    codigos_disponiveis = (
        Maquina.objects.exclude(codigo__isnull=True)
        .exclude(codigo="")
        .order_by("codigo")
        .values_list("codigo", flat=True)
        .distinct()
    )

    # 📄 Grupos disponíveis
    grupos_disponiveis = dict(Maquina.FAMILIA_PRODUTO_LABELS)

    # 📄 Paginação
    paginator = Paginator(qs.order_by("nome"), 20)  # 20 por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "total_maquinas": total_maquinas,
        "velocidade_media": f"{velocidade_media:.2f}",
        "valor_hora_medio": f"{valor_hora_medio:.2f}",
        "codigos_disponiveis": codigos_disponiveis,
        "grupos_disponiveis": grupos_disponiveis,
    }

    return render(request, "maquinas/lista_maquinas.html", context)
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from tecnico.models.maquina import Maquina
from tecnico.forms.maquina_form import MaquinaForm



@login_required
@permission_required("tecnico.add_maquina", raise_exception=True)
def cadastrar_maquina(request):
    form = MaquinaForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Máquina cadastrada com sucesso.")
        return redirect("tecnico:tecnico_maquinas")
    context = {
        "form": form,
        "edicao": False,
    }
    return render(request, "maquinas/form_maquinas.html", context)


@login_required
@permission_required("tecnico.change_maquina", raise_exception=True)
def editar_maquina(request, pk):
    maquina = get_object_or_404(Maquina, pk=pk)
    form = MaquinaForm(request.POST or None, instance=maquina)
    if form.is_valid():
        form.save()
        messages.success(request, "Máquina atualizada com sucesso.")
        return redirect("tecnico:tecnico_maquinas")
    context = {
        "form": form,
        "edicao": True,
    }
    return render(request, "maquinas/form_maquinas.html", context)


@login_required
@permission_required("tecnico.delete_maquina", raise_exception=True)
def excluir_maquina(request, pk):
    maquina = get_object_or_404(Maquina, pk=pk)
    if request.method == "POST":
        maquina.delete()
        messages.success(request, "Máquina excluída com sucesso.")
        return redirect("tecnico:tecnico_maquinas")
    return render(request, "maquinas/confirmar_exclusao.html", {"maquina": maquina})


# views.py
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from tecnico.models.maquina import ServicoRealizado
from django.template.loader import render_to_string
import json

@login_required
def ajax_listar_servicos(request):
    servicos = ServicoRealizado.objects.all().order_by("nome")
    html = render_to_string("maquinas/_lista_servicos.html", {"servicos": servicos})

    return HttpResponse(html)

@csrf_exempt
@login_required
def ajax_adicionar_servico(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            nome = data.get("nome", "").strip()

            if not nome:
                return JsonResponse({"error": "Nome não pode ser vazio."}, status=400)

            servico, _ = ServicoRealizado.objects.get_or_create(nome=nome)

            return JsonResponse({
                "id": servico.id,
                "nome": servico.nome
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método não permitido"}, status=405)

@csrf_exempt
@login_required
def ajax_editar_servico(request, pk):
    if request.method == "POST":
        data = json.loads(request.body)
        ServicoRealizado.objects.filter(pk=pk).update(nome=data.get("nome"))
        return JsonResponse({"success": True})

@csrf_exempt
@login_required
def ajax_excluir_servico(request, pk):
    if request.method == "POST":
        ServicoRealizado.objects.filter(pk=pk).delete()
        return JsonResponse({"success": True})

import pandas as pd
from tecnico.models.maquina import Maquina, ServicoRealizado
from django.contrib import messages

@login_required
@permission_required("tecnico.add_maquina", raise_exception=True)
def importar_maquinas_view(request):
    if request.method == "POST":
        form = ImportarExcelForm(request.POST, request.FILES)
        if form.is_valid():
            arquivo = form.cleaned_data["arquivo"]
            df = pd.read_excel(arquivo)

            # 🔧 Normaliza os nomes das colunas
            df.columns = (
                df.columns
                .str.strip()
                .str.lower()
                .str.normalize("NFKD")
                .str.encode("ascii", errors="ignore")
                .str.decode("utf-8")
                .str.replace(" ", "_")
            )

            print("🔎 Colunas normalizadas:", df.columns.tolist())
            print("📄 Preview da planilha:")
            print(df.head())

            total_criadas = 0
            total_atualizadas = 0
            erros = []

            for i, row in df.iterrows():
                try:
                    print(f"\n➡️ Processando linha {i + 2}...")
                    print(row)

                    codigo = str(row.get("codigo")).strip()
                    print(f"🔧 Código extraído: '{codigo}' (tipo: {type(codigo)})")

                    if not codigo or codigo.lower() == "nan":
                        raise ValueError("Campo 'codigo' está vazio ou ausente.")

                    maquina, created = Maquina.objects.update_or_create(
                        codigo=codigo,
                        defaults={
                            "nome": row.get("nome"),
                            "grupo_de_maquinas": row.get("grupo_de_maquinas"),
                            "velocidade": row.get("velocidade") or 0,
                            "valor_hora": row.get("valor_hora") or 0,
                            "consumo_kwh": row.get("consumo_kwh") or 0,
                        }
                    )

                    if created:
                        total_criadas += 1
                    else:
                        total_atualizadas += 1

                    # ⛓️ Relaciona os serviços
                    servicos_str = str(row.get("servicos") or "").strip()
                    if servicos_str:
                        nomes_servicos = [s.strip() for s in servicos_str.split(";") if s.strip()]
                        servicos_objs = []
                        for nome in nomes_servicos:
                            servico, _ = ServicoRealizado.objects.get_or_create(nome=nome)
                            servicos_objs.append(servico)
                        maquina.servicos_realizados.set(servicos_objs)

                except Exception as e:
                    print(f"❌ Erro na linha {i + 2}: {e}")
                    erros.append(f"Linha {i + 2}: {e}")

            if total_criadas or total_atualizadas:
                messages.success(
                    request,
                    f"{total_criadas} máquinas criadas, {total_atualizadas} atualizadas com sucesso."
                )
            if erros:
                messages.error(request, "Ocorreram erros:\n" + "\n".join(erros))

            return redirect("tecnico:tecnico_maquinas")

    else:
        form = ImportarExcelForm()

    return render(request, "maquinas/importar_maquinas.html", {"form": form})