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

    paginator    = Paginator(qs, 20)
    page_obj     = paginator.get_page(request.GET.get("page"))
    # novos: roteiros ainda não aprovados, para popular o modal
    roteiros_pendentes = RoteiroProducao.objects.filter(aprovado=False).order_by("item__codigo")

    return render(request, "roteiros/lista_roteiros.html", {
        "page_obj": page_obj,
        "roteiros_pendentes": roteiros_pendentes,
        "total_roteiros": total_roteiros,
        "atualizadas_mes": atualizadas_mes,
        "subtitle_atualizadas": subtitle_atualizadas,
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
    embalagem = []
    etapa_exped = next(
        (e for e in etapas if e.setor.nome.lower() == "expedição"),
        None
    )
    if etapa_exped:
        for ins in etapa_exped.insumos.all():
            tipo = ins.materia_prima.descricao
            qtd_para_mil = ins.quantidade or 0
            try:
                pecas_por_emb = int(1000 / qtd_para_mil) if qtd_para_mil else None
            except Exception:
                pecas_por_emb = None

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

        messages.error(request, "Corrija os erros no formulário.")
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

 


@login_required
@permission_required("tecnico.change_roteiroproducao", raise_exception=True)
def editar_roteiro(request, pk):
    roteiro = get_object_or_404(RoteiroProducao, pk=pk)
    form = RoteiroProducaoForm(request.POST or None, instance=roteiro)

    # Dados para carregamento do template
    insumos_data = list(MateriaPrimaCatalogo.objects.order_by("descricao").values("id", "codigo", "descricao"))
    maquinas_data = list(Maquina.objects.order_by("nome").values("id", "codigo", "nome"))
    setores_data = list(CentroDeCusto.objects.order_by("nome").values("id", "nome"))
    ferramentas_data = list(Ferramenta.objects.order_by("codigo").values("id", "codigo", "descricao"))

    # Dados para preencher o formulário no template
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
            } for i in etapa.insumos.all()
        ]

        try:
            p = etapa.propriedades
            props = {
                    "nome_acao": p.nome_acao,
                    "nome_acao_id": str(p.nome_acao_id) if hasattr(p, "nome_acao_id") else "",  # para o select2 funcionar
                    "descricao_detalhada": p.descricao_detalhada,
                    "maquinas": [{"id": m.id, "nome": m.nome} for m in p.maquinas.all()],
                    "ferramenta": {
                        "id": p.ferramenta.id if p.ferramenta else "",
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
                "segurancas": segurancas,  # ✅ Aqui está certo!

        })

    if request.method == "POST":
        dados_json = request.POST.get("dados_json", "")
        if form.is_valid() and dados_json:
            roteiro.revisao = (roteiro.revisao or 1) + 1
            roteiro.save(update_fields=["revisao"])
            form.save()
            payload = json.loads(dados_json)

            print("DEBUG ▶️ Dados JSON recebidos:")
            from pprint import pprint
            pprint(payload)

            roteiro.etapas.all().delete()

            for index, et in enumerate(payload.get("etapas", [])):
                print(f"\n➡️ Etapa {index+1} - Criando Etapa Nº {et.get('etapa')}")

                etapa = EtapaRoteiro.objects.create(
                    roteiro=roteiro,
                    etapa=et["etapa"],
                    setor_id=et["setor"],
                    pph=et.get("pph") or None,
                    setup_minutos=et.get("setup_minutos") or None,
                )

                # Insumos
                for ins in et.get("insumos", []):
                    print(f"  ➕ Insumo: {ins}")
                    InsumoEtapa.objects.create(
                        etapa=etapa,
                        materia_prima_id=ins["materia_prima_id"],
                        quantidade=ins["quantidade"],
                        tipo_insumo=ins["tipo_insumo"],
                        obrigatorio=ins["obrigatorio"],
                    )

                # Propriedades
                props = et.get("propriedades") or {}

                print("  ⚙️ Propriedades recebidas:")
                pprint(props)

                ferramenta_raw = props.get("ferramenta", {}).get("id")
                print("  🔍 Ferramenta raw ID recebido:", ferramenta_raw)

                ferramenta_id = int(ferramenta_raw) if ferramenta_raw and str(ferramenta_raw).isdigit() else None
                print("  ✅ ID validado para ferramenta:", ferramenta_id)

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


            messages.success(request, "Roteiro atualizado com sucesso.")
            messages.success(request,
                f"Roteiro atualizado com sucesso. Nova revisão: {roteiro.revisao}"
            )
            return redirect("tecnico:tecnico_roteiros")

        messages.error(request, "Corrija os erros abaixo.")
    segurancas = [
        ("seguranca_mp", "MP"),
        ("seguranca_ts", "TS"),
        ("seguranca_m1", "M1"),
        ("seguranca_l1", "L1"),
        ("seguranca_l2", "L2"),
    ]

    return render(request, "roteiros/form.roteiros.html", {
        "form": form,
        "edicao": True,
        "insumos_data": insumos_data,
        "maquinas_data": maquinas_data,
        "setores_data": setores_data,
        "roteiro_data": roteiro_data,
        "ferramentas": ferramentas_data,
        "segurancas": segurancas, 
        "servicos": list(ServicoRealizado.objects.order_by("nome").values("id", "nome")),

    })

