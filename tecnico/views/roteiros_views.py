from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.contrib import messages
from comercial.models.centro_custo import CentroDeCusto
from tecnico.models.roteiro import RoteiroProducao, EtapaRoteiro
from tecnico.forms.roteiro_form import RoteiroProducaoForm
from tecnico.forms.roteiro_formsets import EtapaFormSet, InsumoFormSet, PropriedadesFormSet


from tecnico.models.roteiro import RoteiroProducao
from django.core.paginator import Paginator

from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import render
from tecnico.models import RoteiroProducao
from datetime import datetime
from qualidade_fornecimento.models import MateriaPrimaCatalogo

@login_required
@permission_required("tecnico.view_roteiroproducao", raise_exception=True)
def lista_roteiros(request):
    item_nome = request.GET.get("item", "")
    setor_id = request.GET.get("setor", "")
    
    qs = RoteiroProducao.objects.select_related("item").all()

    # Filtros
    if item_nome:
        qs = qs.filter(item__descricao__icontains=item_nome)
    if setor_id:
        qs = qs.filter(etapas__setor_id=setor_id)

    qs = qs.distinct().order_by("-criado_em")

    # Indicadores
    total_roteiros     = qs.count()
    mes_atual          = datetime.now().month
    atualizadas_mes    = qs.filter(atualizado_em__month=mes_atual).count()
    subtitle_atualizadas = f"Atualizadas em {datetime.now():%m/%Y}"

    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "roteiros/lista_roteiros.html", {
        "page_obj": page_obj,
        "total_roteiros": total_roteiros,
        "atualizadas_mes": atualizadas_mes,
        "subtitle_atualizadas": subtitle_atualizadas,
        "request": request,  # necessário para os filtros e permissões no template
    })



@login_required
@permission_required("tecnico.view_roteiroproducao", raise_exception=True)
def visualizar_roteiro(request, pk):
    roteiro = get_object_or_404(RoteiroProducao, pk=pk)
    return render(request, "tecnico/roteiros/visualizar.html", {
        "roteiro": roteiro
    })


@login_required
@permission_required("tecnico.delete_roteiroproducao", raise_exception=True)
def excluir_roteiro(request, pk):
    roteiro = get_object_or_404(RoteiroProducao, pk=pk)
    if request.method == "POST":
        roteiro.delete()
        messages.success(request, "Roteiro excluído com sucesso.")
        return redirect("tecnico:tecnico_roteiros")


from qualidade_fornecimento.models import MateriaPrimaCatalogo
from tecnico.models import Maquina
from django.db.models import F

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from tecnico.forms.roteiro_form import RoteiroProducaoForm
from tecnico.forms.roteiro_formsets import EtapaFormSet
from tecnico.models.roteiro import RoteiroProducao, PropriedadesEtapa, InsumoEtapa
from qualidade_fornecimento.models import MateriaPrimaCatalogo
from tecnico.models.maquina import Maquina
import json

@login_required
@permission_required("tecnico.add_roteiroproducao", raise_exception=True)
def cadastrar_roteiro(request):
    form = RoteiroProducaoForm(request.POST or None)

    # Dados para o JS
    insumos_data = list(
        MateriaPrimaCatalogo.objects.order_by("descricao")
        .values("id", "descricao")
    )
    maquinas_data = list(
    Maquina.objects
        .all()
        .order_by("nome")
        .values("id", "codigo", "nome")
)
    setores_data = list(
        CentroDeCusto.objects
            .select_related("departamento")
            .order_by("departamento__nome")
            .annotate(nome=F("departamento__nome"))
            .values("id", "nome")
    )

    if request.method == "POST":
        dados_json = request.POST.get("dados_json")
        if form.is_valid() and dados_json:
            roteiro = form.save()
            payload = json.loads(dados_json)

            for et in payload.get("etapas", []):
                etapa = EtapaRoteiro.objects.create(
                    roteiro=roteiro,
                    etapa=et["etapa"],
                    setor_id=et["setor"],
                    pph=et.get("pph") or None,
                    setup_minutos=et.get("setup_minutos") or None,
                )

                # Insumos
                for ins in et.get("insumos", []):
                    InsumoEtapa.objects.create(
                        etapa=etapa,
                        materia_prima_id=ins["materia_prima_id"],
                        quantidade=ins["quantidade"],
                        tipo_insumo=ins["tipo_insumo"],
                        obrigatorio=ins["obrigatorio"],
                    )

                # Propriedades
                props = et.get("propriedades") or {}
                if props.get("nome_acao"):
                    prop_obj = PropriedadesEtapa.objects.create(
                        etapa=etapa,
                        nome_acao=props.get("nome_acao", ""),
                        descricao_detalhada=props.get("descricao_detalhada", ""),
                    )
                    # AQUI: só passar a lista de IDs, não de dicts
                    ids = [m["id"] for m in props.get("maquinas", [])]
                    prop_obj.maquinas.set(ids)

            messages.success(request, "Roteiro cadastrado com sucesso.")
            return redirect("tecnico:tecnico_roteiros")

        messages.error(request, "Corrija os erros no formulário.")

    return render(request, "roteiros/form.roteiros.html", {
        "form": form,
        "edicao": False,
        "insumos_data": insumos_data,
        "maquinas_data": maquinas_data,
        "setores_data": setores_data,
    })


@login_required
@permission_required("tecnico.change_roteiroproducao", raise_exception=True)
def editar_roteiro(request, pk):
    roteiro = get_object_or_404(RoteiroProducao, pk=pk)
    form     = RoteiroProducaoForm(request.POST or None, instance=roteiro)

    # Dados para o JS
    insumos_data = list(
        MateriaPrimaCatalogo.objects.order_by("descricao")
        .values("id", "descricao")
    )
    maquinas_data = list(
    Maquina.objects
        .all()
        .order_by("nome")
        .values("id", "codigo", "nome")
)
    setores_data = list(
        CentroDeCusto.objects
            .select_related("departamento")
            .order_by("departamento__nome")
            .annotate(nome=F("departamento__nome"))
            .values("id", "nome")
    )

    # Monta o JSON inicial para pré-carregar o JS
    roteiro_data = {
        "item": roteiro.item_id,
        "etapas": []
    }
    for etapa in roteiro.etapas.all().order_by("etapa"):
        insumos_list = [
            {
                "materia_prima_id": i.materia_prima_id,
                "quantidade": float(i.quantidade),
                "tipo_insumo": i.tipo_insumo,
                "obrigatorio": i.obrigatorio,
            }
            for i in etapa.insumos.all()
        ]
        try:
            p = etapa.propriedades
            props = {
                "nome_acao": p.nome_acao,
                "descricao_detalhada": p.descricao_detalhada,
                "maquinas": [
                    {"id": m.id, "nome": m.nome}
                    for m in p.maquinas.all()
                ],
            }
        except PropriedadesEtapa.DoesNotExist:
            props = {}

        roteiro_data["etapas"].append({
            "etapa": etapa.etapa,
            "setor": etapa.setor_id,
            "pph": float(etapa.pph or 0),
            "setup_minutos": etapa.setup_minutos or 0,
            "insumos": insumos_list,
            "propriedades": props,
        })

    if request.method == "POST":
        dados_json = request.POST.get("dados_json", "")
        if form.is_valid() and dados_json:
            form.save()
            payload = json.loads(dados_json)

            # limpa tudo e recria
            roteiro.etapas.all().delete()

            for et in payload.get("etapas", []):
                etapa = EtapaRoteiro.objects.create(
                    roteiro=roteiro,
                    etapa=et["etapa"],
                    setor_id=et["setor"],
                    pph=et.get("pph") or None,
                    setup_minutos=et.get("setup_minutos") or None,
                )
                for ins in et.get("insumos", []):
                    InsumoEtapa.objects.create(
                        etapa=etapa,
                        materia_prima_id=ins["materia_prima_id"],
                        quantidade=ins["quantidade"],
                        tipo_insumo=ins["tipo_insumo"],
                        obrigatorio=ins["obrigatorio"],
                    )
                props = et.get("propriedades") or {}
                if props.get("nome_acao"):
                    prop_obj = PropriedadesEtapa.objects.create(
                        etapa=etapa,
                        nome_acao=props.get("nome_acao", ""),
                        descricao_detalhada=props.get("descricao_detalhada", ""),
                    )
                    # CORREÇÃO: apenas IDs
                    ids = [m["id"] for m in props.get("maquinas", [])]
                    prop_obj.maquinas.set(ids)

            messages.success(request, "Roteiro atualizado com sucesso.")
            return redirect("tecnico:tecnico_roteiros")

        messages.error(request, "Corrija os erros abaixo.")

    return render(request, "roteiros/form.roteiros.html", {
        "form": form,
        "edicao": True,
        "insumos_data": insumos_data,
        "maquinas_data": maquinas_data,
        "setores_data": setores_data,
        "roteiro_data": roteiro_data,
    })