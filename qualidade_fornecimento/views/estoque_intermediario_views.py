from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from qualidade_fornecimento.models.estoque_intermediario import EstoqueIntermediario
from qualidade_fornecimento.forms.estoque_intermediario_forms import (
    EstoqueIntermediarioForm, 
    ApontarRetornoForm,  # ✅ novo form combinado
)

from datetime import timedelta

from django.db.models import Q                          # ✅ faltava
from qualidade_fornecimento.models.rolo import RoloMateriaPrima 

# ======== Listagens ========
@login_required
@permission_required("qualidade_fornecimento.view_estoqueintermediario", raise_exception=True)
def ei_list_em_fabrica(request):
    qs = (EstoqueIntermediario.objects
          .select_related("materia_prima", "lote")
          .filter(status="EM_FABRICA")
          .order_by("-data_envio", "-id"))
    now = timezone.now()
    kpis = {
        "total": qs.count(),
        "media_dias": round((sum(x.dias_em_fabrica for x in qs) / qs.count()), 1) if qs.exists() else 0,
        "acima_20dias": qs.filter(data_envio__lt=now - timedelta(days=20)).count(),
    }
    return render(request, "estoque_intermediario/list_em_fabrica.html", {"itens": qs, "kpis": kpis})

@login_required
@permission_required("qualidade_fornecimento.view_estoqueintermediario", raise_exception=True)
def ei_list_historico(request):
    qs = EstoqueIntermediario.objects.select_related("materia_prima", "lote", "tb050", "maquina").filter(status="RETORNADO")
    op = request.GET.get("op"); mp = request.GET.get("mp"); dt = request.GET.get("de"); at = request.GET.get("ate")
    if op: qs = qs.filter(op__icontains=op)
    if mp: qs = qs.filter(materia_prima_id=mp)
    if dt: qs = qs.filter(data_retorno__date__gte=dt)
    if at: qs = qs.filter(data_retorno__date__lte=at)
    return render(request, "estoque_intermediario/list_historico.html", {"itens": qs})

# ======== CRUD / Ações ========
@login_required
@permission_required("qualidade_fornecimento.add_estoqueintermediario", raise_exception=True)
def ei_create(request):
    if request.method == "POST":
        form = EstoqueIntermediarioForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.responsavel_envio = request.user
            obj.status = "EM_FABRICA"
            if not obj.data_envio:
                obj.data_envio = timezone.now()
            if not obj.tb050 and getattr(obj.lote, "tb050_id", None):
                obj.tb050_id = obj.lote.tb050_id
            obj.save()
            messages.success(request, "Envio registrado com sucesso.")
            return redirect("ei_list_em_fabrica")
    else:
        form = EstoqueIntermediarioForm(initial={"data_envio": timezone.now()})
    return render(request, "estoque_intermediario/form_create.html", {"form": form})

from django.core.exceptions import ValidationError


@login_required
@permission_required("qualidade_fornecimento.change_estoqueintermediario", raise_exception=True)
def ei_apontar_retorno(request, pk):
    obj = get_object_or_404(EstoqueIntermediario, pk=pk)
    if obj.status != "EM_FABRICA":
        messages.warning(request, "Este item não está 'Em Fábrica'.")
        return redirect("ei_list_em_fabrica")

    if request.method == "POST":
        form = ApontarRetornoForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.updated_by = request.user
            if not obj.tb050 and getattr(obj.lote, "tb050_id", None):
                obj.tb050_id = obj.lote.tb050_id
            obj.status = "RETORNADO"
            obj.responsavel_retorno = request.user
            obj.data_retorno = form.cleaned_data.get("data_retorno") or timezone.now()
            try:
                obj.full_clean()
                obj.save()
            except ValidationError as e:
                form.add_error(None, e)
                return render(request, "estoque_intermediario/form_apontar_retorno.html", {"form": form, "obj": obj})
            messages.success(request, "Item fechado e enviado ao Histórico.")
            return redirect("ei_list_historico")
    else:
        form = ApontarRetornoForm(instance=obj, initial={"data_retorno": timezone.now()})

    return render(request, "estoque_intermediario/form_apontar_retorno.html", {"form": form, "obj": obj})


@login_required
@permission_required("qualidade_fornecimento.change_estoqueintermediario", raise_exception=True)
def ei_estornar_para_em_fabrica(request, pk):
    obj = get_object_or_404(EstoqueIntermediario, pk=pk)
    if request.method == "POST":
        obj.status = "EM_FABRICA"
        obj.data_retorno = None
        obj.aprovado_por = None
        obj.updated_by = request.user
        obj.save()
        messages.info(request, "Item estornado para 'Em Fábrica'.")
        return redirect("ei_list_em_fabrica")
    return render(request, "estoque_intermediario/confirm_estornar.html", {"obj": obj})

# ======== API dependente ========
@login_required
@require_GET
def api_rolos_por_mp(request):
    mp_id = request.GET.get("mp")
    termo = (request.GET.get("q") or "").strip()

    if not mp_id:
        return JsonResponse({"results": []})  # ✅ evita 400 quando ainda não escolheu MP

    qs = (RoloMateriaPrima.objects
          .select_related("tb050")
          .filter(tb050__materia_prima_id=mp_id))

    if termo:
        qs = qs.filter(Q(nro_rolo__icontains=termo))

    qs = qs.order_by("-nro_rolo")[:500]

    data = []
    for r in qs:
      nro = str(r.nro_rolo)
      peso_txt = f" — {r.peso} kg" if getattr(r, "peso", None) is not None else ""
      tb_txt  = ""
      if getattr(r, "tb050", None):
          nr = getattr(r.tb050, "nro_relatorio", None)
          tb_txt = f" (TB050 #{nr})" if nr else f" (TB050 {r.tb050_id})"

      data.append({
        "id": nro,
        "texto": f"{nro}{peso_txt}{tb_txt}",
        "tb050_id": r.tb050_id,
        "tb050_label": f"TB050 #{getattr(r.tb050, 'nro_relatorio', r.tb050_id)}",
      })
    return JsonResponse({"results": data})