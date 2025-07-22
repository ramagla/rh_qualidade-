from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from tecnico.models.maquina import Maquina
from tecnico.forms.maquina_form import MaquinaForm

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
    nome   = request.GET.get("nome", "").strip()

    qs = Maquina.objects.all()

    if codigo:
        qs = qs.filter(codigo__icontains=codigo)

    if nome:
        qs = qs.filter(nome__icontains=nome)

    # 📊 Indicadores
    total_maquinas     = qs.count()
    velocidade_media   = qs.aggregate(Avg("velocidade"))["velocidade__avg"] or 0
    valor_hora_medio   = qs.aggregate(Avg("valor_hora"))["valor_hora__avg"] or 0

    # 📄 Paginação
    paginator = Paginator(qs.order_by("nome"), 20)  # 20 por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "total_maquinas": total_maquinas,
        "velocidade_media": f"{velocidade_media:.2f}",
        "valor_hora_medio": f"{valor_hora_medio:.2f}",
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
        data = json.loads(request.body)
        ServicoRealizado.objects.get_or_create(nome=data.get("nome"))
        return JsonResponse({"success": True})

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
