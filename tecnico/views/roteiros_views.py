from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.contrib import messages
from comercial.models import Item
from comercial.models.centro_custo import CentroDeCusto
from tecnico.models.roteiro import RoteiroProducao, EtapaRoteiro
from tecnico.forms.roteiro_form import RoteiroProducaoForm
from tecnico.forms.roteiro_formsets import EtapaFormSet, InsumoFormSet, PropriedadesFormSet
from comercial.models.ferramenta import Ferramenta
from tecnico.models.maquina import ServicoRealizado
from django.db import transaction

from tecnico.models.roteiro import RoteiroProducao
from django.core.paginator import Paginator

from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import render
from tecnico.models import RoteiroProducao
from datetime import datetime
from qualidade_fornecimento.models import MateriaPrimaCatalogo

from django.utils.timezone import now
from django.contrib import messages
from django.shortcuts import redirect

from django.db.models import Max, Count, Q

@login_required
@permission_required("tecnico.view_roteiroproducao", raise_exception=True)
def lista_roteiros(request):
    item_nome = request.GET.get("item", "")
    setor_id  = request.GET.get("setor", "")
    qs = RoteiroProducao.objects.select_related("item").all()
    if item_nome:
        qs = qs.filter(item__descricao__icontains=item_nome)
    if setor_id:
        qs = qs.filter(etapas__setor_id=setor_id)
    qs = qs.distinct().order_by("-criado_em")

    total_roteiros      = qs.count()
    mes_atual           = datetime.now().month
    atualizadas_mes     = qs.filter(atualizado_em__month=mes_atual).count()
    subtitle_atualizadas = f"Atualizadas em {datetime.now():%m/%Y}"

    total_aprovados = qs.filter(aprovado=True).count()
    total_revisao_acima_3 = qs.filter(revisao__gt=3).count()
    ultima_data = qs.aggregate(max_data=Max("atualizado_em"))["max_data"]

    paginator    = Paginator(qs, 20)
    page_obj     = paginator.get_page(request.GET.get("page"))
    roteiros = RoteiroProducao.objects.select_related("item").all().order_by("item__codigo")
    roteiros_pendentes = RoteiroProducao.objects.select_related("item").filter(aprovado=False).order_by("item__codigo")

    return render(request, "roteiros/lista_roteiros.html", {
        "page_obj": page_obj,
        "roteiros": roteiros,
        "roteiros_pendentes": roteiros_pendentes,
        "total_roteiros": total_roteiros,
        "atualizadas_mes": atualizadas_mes,
        "subtitle_atualizadas": subtitle_atualizadas,
        "total_aprovados": total_aprovados,
        "total_revisao_acima_3": total_revisao_acima_3,
        "ultima_data": ultima_data,
        "request": request,
    })

from django.utils.timezone import now

@login_required
@permission_required("tecnico.change_roteiroproducao", raise_exception=True)
def aprovar_roteiros_lote(request):
    if request.method == "POST":
        pk = request.POST.get("roteiros_aprovados")
        roteiro = get_object_or_404(RoteiroProducao, pk=pk)
        roteiro.aprovado     = True
        roteiro.aprovado_por = request.user
        roteiro.aprovado_em  = now()
        roteiro.save()
        messages.success(
            request,
            f"Roteiro {roteiro.item.codigo} aprovado com sucesso."
        )
    return redirect("tecnico:tecnico_roteiros")


@login_required
@permission_required("tecnico.change_roteiroproducao", raise_exception=True)
def aprovar_roteiro(request, pk):
    roteiro = get_object_or_404(RoteiroProducao, pk=pk)
    if request.method == "POST":
        roteiro.aprovado     = True
        roteiro.aprovado_por = request.user
        roteiro.aprovado_em  = now()
        roteiro.save()
        messages.success(
            request,
            f"Roteiro {roteiro.item.codigo} aprovado com sucesso por "
            f"{request.user.get_full_name() or request.user.username}."
        )
    return redirect("tecnico:visualizar_roteiro", pk=pk)


@login_required
@permission_required("tecnico.view_roteiroproducao", raise_exception=True)
def visualizar_roteiro(request, pk):
    # 1) Busca o roteiro e carrega relações necessárias
    roteiro = get_object_or_404(
        RoteiroProducao.objects.select_related("item"),
        pk=pk
    )
    item = roteiro.item  # ✅ agora item é o objeto correto

    etapas = roteiro.etapas \
        .select_related("setor") \
        .prefetch_related("insumos", "propriedades__maquinas")

    # 2) Monta lista de dicts que o template vai entender (etapas detalhadas)
    etapas_detalhadas = []
    for etapa in etapas:
        props = getattr(etapa, "propriedades", None)
        etapas_detalhadas.append({
            "numero": etapa.etapa,
            "descricao": props.nome_acao if props else "",
            "equipamento_codigos": [
                m.codigo for m in (props.maquinas.all() if props else [])
            ],
            "ferramenta": (
                f"{props.ferramenta.codigo} – {props.ferramenta.descricao}"
                if props and props.ferramenta else "-"
            ),
            "dispositivo": "-",  
            "tempo_regulagem": (
                etapa.setup_minutos / 60
                if etapa.setup_minutos is not None else "-"
            ),
            "producao": etapa.pph,
            "alivio_tensao": (
                props.descricao_detalhada
                if props and props.descricao_detalhada else "-"
            ),

            # Flags de segurança (opcional, se ainda precisar usar)
            "seguranca_mp": props.seguranca_mp if props else False,
            "seguranca_ts": props.seguranca_ts if props else False,
            "seguranca_m1": props.seguranca_m1 if props else False,
            "seguranca_l1": props.seguranca_l1 if props else False,
            "seguranca_l2": props.seguranca_l2 if props else False,

            # Lista de imagens de simbologia conforme switches marcados
            "simbolos_seguranca": [
                roteiro.item.simbolo_mp.url if props and props.seguranca_mp and roteiro.item.simbolo_mp else None,
                roteiro.item.simbolo_ts.url if props and props.seguranca_ts and roteiro.item.simbolo_ts else None,
                roteiro.item.simbolo_m1.url if props and props.seguranca_m1 and roteiro.item.simbolo_m1 else None,
                roteiro.item.simbolo_l1.url if props and props.seguranca_l1 and roteiro.item.simbolo_l1 else None,
                roteiro.item.simbolo_l2.url if props and props.seguranca_l2 and roteiro.item.simbolo_l2 else None,
            ]


        })



    # 3) Pega a primeira matéria-prima (para o cabeçalho)
    materia_prima = None
    for etapa in etapas:
        ins = etapa.insumos.first()
        if ins:
            materia_prima = ins.materia_prima
            break

    # 4) Monta dados de embalagem da etapa de "Expedição"
    # 4) Monta dados de embalagem da etapa de "Expedição"
    embalagem = []
    etapa_exped = next(
        (e for e in etapas if e.setor.nome.lower() == "expedição"),
        None
    )
    if etapa_exped:
        for ins in etapa_exped.insumos.all():
            tipo = ins.materia_prima.descricao
            pecas_por_emb = int(ins.quantidade) if ins.quantidade else None

            embalagem.append({
                "tipo": tipo,
                "pecas_por_embalagem": pecas_por_emb,
            })

    # 5) Define quem elaborou (e a data) para assinatura
    elaborado_por = request.user
    data_elaborado = roteiro.criado_em

    # 6) Renderiza passando tudo para o template
    return render(request, "roteiros/visualizar_item_ip.html", {
        "item": roteiro.item,
        "roteiro": roteiro,
        "etapas": etapas_detalhadas,
        "materia_prima": materia_prima,
        "embalagem": embalagem,
        "elaborado_por": elaborado_por,
        "data_elaborado": data_elaborado,
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
    MateriaPrimaCatalogo.objects.order_by("descricao").values("id", "codigo", "descricao")
)

    maquinas_data = list(
    Maquina.objects
        .all()
        .order_by("nome")
        .values("id", "codigo", "nome")
)
    setores_data = list(
        CentroDeCusto.objects.order_by("nome").values("id", "nome")
    )


    ferramentas_data = list(
        Ferramenta.objects
            .order_by("codigo")
            .values("id", "codigo", "descricao")
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

                # Validação segura da ferramenta
                ferramenta_raw = props.get("ferramenta", {}).get("id")
                ferramenta_id = int(ferramenta_raw) if ferramenta_raw and str(ferramenta_raw).isdigit() else None

                if props.get("nome_acao"):
                    prop_obj = PropriedadesEtapa.objects.create(
                        etapa=etapa,
                        nome_acao=props.get("nome_acao", ""),
                        descricao_detalhada=props.get("descricao_detalhada", ""),
                        ferramenta_id=props.get("ferramenta", {}).get("id") or None,
                        seguranca_mp=props.get("seguranca_mp", False),
                        seguranca_ts=props.get("seguranca_ts", False),
                        seguranca_m1=props.get("seguranca_m1", False),
                        seguranca_l1=props.get("seguranca_l1", False),
                        seguranca_l2=props.get("seguranca_l2", False),
                    )

                    ids = [m["id"] for m in props.get("maquinas", [])]
                    prop_obj.maquinas.set(ids)



            messages.success(request, "Roteiro cadastrado com sucesso.")
            return redirect("tecnico:tecnico_roteiros")

    segurancas = [
        ("seguranca_mp", "MP"),
        ("seguranca_ts", "TS"),
        ("seguranca_m1", "M1"),
        ("seguranca_l1", "L1"),
        ("seguranca_l2", "L2"),
    ]

    return render(request, "roteiros/form.roteiros.html", {
        "form": form,
        "edicao": False,
        "insumos_data": insumos_data,
        "maquinas_data": maquinas_data,
        "setores_data": setores_data,
        "ferramentas": ferramentas_data,
        "segurancas": segurancas,  # ✅ Adicione aqui
        "servicos": list(ServicoRealizado.objects.order_by("nome").values("id", "nome")),

    })

 
from pprint import pprint


@login_required
@permission_required("tecnico.change_roteiroproducao", raise_exception=True)
def editar_roteiro(request, pk):
    roteiro = get_object_or_404(RoteiroProducao, pk=pk)
    form = RoteiroProducaoForm(request.POST or None, instance=roteiro)

    # Dados para o template
    insumos_data = list(
        MateriaPrimaCatalogo.objects.order_by("descricao")
        .values("id", "codigo", "descricao")
    )
    maquinas_data = list(
        Maquina.objects.order_by("nome")
        .values("id", "codigo", "nome")
    )
    setores_data = list(
        CentroDeCusto.objects.order_by("nome")
        .values("id", "nome")
    )
    ferramentas_data = list(
        Ferramenta.objects.order_by("codigo")
        .values("id", "codigo", "descricao")
    )

    # Monta o JSON inicial para o template
    roteiro_data = {"item": roteiro.item_id, "etapas": []}
    for etapa in roteiro.etapas.all().order_by("etapa"):
        insumos_list = [
            {
                "materia_prima_id": ins.materia_prima_id,
                "quantidade": float(ins.quantidade),
                "tipo_insumo": ins.tipo_insumo,
                "obrigatorio": ins.obrigatorio,
            }
            for ins in etapa.insumos.all()
        ]

        try:
            p = etapa.propriedades
            props = {
                "nome_acao": p.nome_acao,
                "descricao_detalhada": p.descricao_detalhada,
                "maquinas": [{"id": m.id, "nome": m.nome} for m in p.maquinas.all()],
                "ferramenta": {
                    "id": p.ferramenta.id if p.ferramenta else None,
                    "texto": f"{p.ferramenta.codigo} – {p.ferramenta.descricao}" if p.ferramenta else ""
                },
                "seguranca_mp": p.seguranca_mp,
                "seguranca_ts": p.seguranca_ts,
                "seguranca_m1": p.seguranca_m1,
                "seguranca_l1": p.seguranca_l1,
                "seguranca_l2": p.seguranca_l2,
            }
        except PropriedadesEtapa.DoesNotExist:
            props = {}

        segurancas = [
            ("seguranca_mp", "MP"),
            ("seguranca_ts", "TS"),
            ("seguranca_m1", "M1"),
            ("seguranca_l1", "L1"),
            ("seguranca_l2", "L2"),
        ]

        roteiro_data["etapas"].append({
            "etapa": etapa.etapa,
            "setor": etapa.setor_id,
            "pph": float(etapa.pph or 0),
            "setup_minutos": etapa.setup_minutos or 0,
            "insumos": insumos_list,
            "propriedades": props,
            "segurancas": segurancas,
        })

    if request.method == "POST":
        dados_json = request.POST.get("dados_json", "")
        print("🚨 RECEBEU POST em editar_roteiro")
        print("   request.POST keys:", list(request.POST.keys()))
        print("   dados_json raw:", dados_json)
        print("   form.errors antes de is_valid():", form.errors)

        if form.is_valid():
            print("✅ form.is_valid() == True")
            with transaction.atomic():
                roteiro = form.save()
                print(f"   • form.save() → roteiro.id = {roteiro.id}")
                roteiro.revisao = (roteiro.revisao or 1) + 1
                roteiro.save(update_fields=["revisao"])
                print(f"   • revisao agora = {roteiro.revisao}")
                roteiro.etapas.all().delete()
                print("   • etapas antigas excluídas")

                try:
                    payload = json.loads(dados_json)
                    print("   • JSON carregado:")
                    pprint(payload)
                except Exception as e:
                    print("   ❌ erro ao json.loads:", e)
                    payload = {"etapas": []}

                for idx, et in enumerate(payload.get("etapas", []), start=1):
                    print(f"\n   ➡️ Etapa {idx}: {et}")
                    etapa_obj = EtapaRoteiro.objects.create(
                        roteiro=roteiro,
                        etapa=et["etapa"],
                        setor_id=et["setor"],
                        pph=et.get("pph") or None,
                        setup_minutos=et.get("setup_minutos") or None,
                    )
                    print(f"      • EtapaRoteiro criado id={etapa_obj.id}")

                    for ins in et.get("insumos", []):
                        print(f"      • criando InsumoEtapa: {ins}")
                        InsumoEtapa.objects.create(
                            etapa=etapa_obj,
                            materia_prima_id=ins["materia_prima_id"],
                            quantidade=ins["quantidade"],
                            tipo_insumo=ins["tipo_insumo"],
                            obrigatorio=ins["obrigatorio"],
                        )

                    props = et.get("propriedades") or {}
                    print("      • propriedades recebidas:", props)

                    if props.get("nome_acao"):
                        prop_obj = PropriedadesEtapa.objects.create(
                            etapa=etapa_obj,
                            nome_acao=props.get("nome_acao", ""),
                            descricao_detalhada=props.get("descricao_detalhada", ""),
                            ferramenta_id=props.get("ferramenta", {}).get("id") or None,
                            seguranca_mp=props.get("seguranca_mp", False),
                            seguranca_ts=props.get("seguranca_ts", False),
                            seguranca_m1=props.get("seguranca_m1", False),
                            seguranca_l1=props.get("seguranca_l1", False),
                            seguranca_l2=props.get("seguranca_l2", False),
                        )
                        print(f"      • PropriedadesEtapa criado id={prop_obj.id}")
                        maquinas_ids = [m["id"] for m in props.get("maquinas", [])]
                        prop_obj.maquinas.set(maquinas_ids)
                        print(f"      • máquinas vinculadas: {maquinas_ids}")

            messages.success(request, "Roteiro atualizado com sucesso.")
            return redirect("tecnico:tecnico_roteiros")

        else:
            print("❌ form.is_valid() == False")
            print("   form.errors após is_valid():", form.errors)
            messages.error(request, "Corrija os erros abaixo.")

    return render(request, "roteiros/form.roteiros.html", {
        "form": form,
        "edicao": True,
        "insumos_data": insumos_data,
        "maquinas_data": maquinas_data,
        "setores_data": setores_data,
        "roteiro_data": roteiro_data,
        "ferramentas": ferramentas_data,
        "segurancas": [
            ("seguranca_mp", "MP"),
            ("seguranca_ts", "TS"),
            ("seguranca_m1", "M1"),
            ("seguranca_l1", "L1"),
            ("seguranca_l2", "L2"),
        ],
        "servicos": list(ServicoRealizado.objects.order_by("nome").values("id", "nome")),
    })








from tecnico.models.roteiro import RoteiroProducao, EtapaRoteiro, PropriedadesEtapa, InsumoEtapa
from django.db import transaction
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

@login_required
@permission_required("tecnico.add_roteiroproducao", raise_exception=True)
def clonar_roteiro(request, pk):
    original = get_object_or_404(RoteiroProducao, pk=pk)

    # Letras disponíveis: A–Z
    letras = [chr(i) for i in range(ord("A"), ord("Z") + 1)]

    # Letras já utilizadas para o mesmo item
    tipos_existentes = RoteiroProducao.objects.filter(item=original.item).values_list("tipo_roteiro", flat=True)
    proximo_tipo = next((l for l in letras if l not in tipos_existentes), None)

    if not proximo_tipo:
        messages.error(request, "Não foi possível clonar. Todos os tipos de roteiro (A–Z) já foram usados para este item.")
        return redirect("tecnico:tecnico_roteiros")

    with transaction.atomic():
        clone = RoteiroProducao.objects.create(
            item=original.item,
            tipo_roteiro=proximo_tipo,
            revisao=1,
            peso_unitario_gramas=original.peso_unitario_gramas,
            observacoes_gerais=original.observacoes_gerais,
            aprovado=False,
        )

        for etapa in original.etapas.all():
            nova_etapa = EtapaRoteiro.objects.create(
                roteiro=clone,
                etapa=etapa.etapa,
                setor=etapa.setor,
                pph=etapa.pph,
                setup_minutos=etapa.setup_minutos,
            )

            for insumo in etapa.insumos.all():
                InsumoEtapa.objects.create(
                    etapa=nova_etapa,
                    materia_prima=insumo.materia_prima,
                    quantidade=insumo.quantidade,
                    tipo_insumo=insumo.tipo_insumo,
                    obrigatorio=insumo.obrigatorio,
                )

            if hasattr(etapa, "propriedades"):
                prop = etapa.propriedades
                nova_prop = PropriedadesEtapa.objects.create(
                    etapa=nova_etapa,
                    nome_acao=prop.nome_acao,
                    descricao_detalhada=prop.descricao_detalhada,
                    ferramenta=prop.ferramenta,
                    seguranca_mp=prop.seguranca_mp,
                    seguranca_ts=prop.seguranca_ts,
                    seguranca_m1=prop.seguranca_m1,
                    seguranca_l1=prop.seguranca_l1,
                    seguranca_l2=prop.seguranca_l2,
                )
                nova_prop.maquinas.set(prop.maquinas.all())

    messages.success(request, f"Roteiro clonado com sucesso como tipo {proximo_tipo}.")
    return redirect("tecnico:tecnico_roteiros")
