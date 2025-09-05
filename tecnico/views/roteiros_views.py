from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Max, Count, Q 
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now
from django.http import JsonResponse

from comercial.models import Item, CentroDeCusto, Ferramenta
from qualidade_fornecimento.models import MateriaPrimaCatalogo
from tecnico.forms.roteiro_form import RoteiroProducaoForm
from tecnico.forms.roteiro_formsets import EtapaFormSet, InsumoFormSet, PropriedadesFormSet
from tecnico.models.maquina import Maquina, ServicoRealizado
from tecnico.models.roteiro import (
    RoteiroProducao,
    EtapaRoteiro,
    PropriedadesEtapa,
    InsumoEtapa,
    RoteiroRevisao,   # novo modelo de histórico de revisões
)

import re

# tecnico/views/roteiros_views.py
LIMITE_ABS_INTEIRO = Decimal("100000")  # exemplo de novo limite
DEC_PLACES = 10
QUANT_10 = Decimal("1").scaleb(-DEC_PLACES)  # 0.0000000001

def limpar_decimal(valor, padrao=None):
    """
    - Aceita '', None -> retorna padrao (None).
    - Suporta notação científica (ex.: 5e-9).
    - Converte vírgula para ponto (pt-BR -> en-US).
    - Normaliza para 10 casas decimais (alinha com o model).
    - Valida limite absoluto (< 100000 conforme sua constante).
    """
    if valor is None:
        return padrao

    # Se já vier como número, preserve notação científica com str()
    if isinstance(valor, (int, float, Decimal)):
        try:
            d = Decimal(str(valor))
        except (InvalidOperation, ValueError, TypeError):
            return padrao
    else:
        s = str(valor).strip()
        if s == "":
            return padrao

        # permite 'e'/'E' para notação científica
        s = re.sub(r"[^\deE,.\-+]", "", s)

        # normaliza separador decimal
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", ".")

        try:
            d = Decimal(s)  # aceita '5e-9'
        except (InvalidOperation, ValueError, TypeError):
            return padrao

    # normaliza para 10 casas decimais (igual ao DecimalField)
    d = d.quantize(QUANT_10, rounding=ROUND_HALF_UP)

    if abs(d) >= LIMITE_ABS_INTEIRO:
        raise ValueError(f"Valor {d} ultrapassa o limite permitido (< 100000).")

    return d

@login_required
@permission_required("tecnico.view_roteiroproducao", raise_exception=True)
def lista_roteiros(request):
    # 1) Captura filtros
    codigo_item    = request.GET.get("codigo_item", "")
    status_filtro  = request.GET.get("status")
    if not status_filtro:
        status_filtro = "ativo"
    criado_inicio  = request.GET.get("criado_inicio", "")
    criado_fim     = request.GET.get("criado_fim", "")
    setor_id       = request.GET.get("setor", "")

    # 2) Queryset base
    qs = RoteiroProducao.objects.select_related("item").all()

    # 3) Aplica filtros
    if codigo_item:
        qs = qs.filter(item__codigo__icontains=codigo_item)
    if status_filtro:
         qs = qs.filter(status=status_filtro)
    if criado_inicio:
        qs = qs.filter(criado_em__date__gte=criado_inicio)
    if criado_fim:
        qs = qs.filter(criado_em__date__lte=criado_fim)
    if setor_id:
        qs = qs.filter(etapas__setor_id=setor_id)

    qs = qs.distinct().order_by("-criado_em")

    # 4) Métricas e paginação (mantém como antes)
    total_roteiros      = qs.count()
    mes_atual           = datetime.now().month
    atualizadas_mes     = qs.filter(atualizado_em__month=mes_atual).count()
    subtitle_atualizadas = f"Atualizadas em {datetime.now():%m/%Y}"
    total_aprovados     = qs.filter(aprovado=True).count()
    total_revisao_acima_3 = qs.filter(revisao__gt=3).count()
    ultima_data         = qs.aggregate(max_data=Max("atualizado_em"))["max_data"]

    paginator    = Paginator(qs, 20)
    page_obj     = paginator.get_page(request.GET.get("page"))

    # 5) Dados para os filtros do template
    itens = Item.objects.order_by("codigo").values_list("codigo", "codigo")
    status_choices = RoteiroProducao.STATUS_CHOICES

    roteiros_pendentes = qs.filter(aprovado=False)[:50]  # ou conforme desejar
    roteiros_clonaveis = qs.order_by("item__codigo", "tipo_roteiro")[:100]

    return render(request, "roteiros/lista_roteiros.html", {
        "page_obj": page_obj,
        "total_roteiros": total_roteiros,
        "atualizadas_mes": atualizadas_mes,
        "subtitle_atualizadas": subtitle_atualizadas,
        "total_aprovados": total_aprovados,
        "total_revisao_acima_3": total_revisao_acima_3,
        "ultima_data": ultima_data,
        "itens": itens,
        "status_choices": status_choices,
        "roteiros_pendentes": roteiros_pendentes,
        "roteiros": roteiros_clonaveis,
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
@permission_required("tecnico.aprovar_roteiro", raise_exception=True)
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

        # monta um dict completo com todas as propriedades
        propriedades_info = {
            "nome_acao": props.nome_acao if props else "",
            "descricao_detalhada": props.descricao_detalhada if props else "",
            "maquinas": [m.nome for m in (props.maquinas.all() if props else [])],
            "ferramenta": (
                f"{props.ferramenta.codigo} – {props.ferramenta.descricao}"
                if props and props.ferramenta else ""
            ),
            "seguranca": {
                "MP": props.seguranca_mp if props else False,
                "TS": props.seguranca_ts if props else False,
                "M1": props.seguranca_m1 if props else False,
                "L1": props.seguranca_l1 if props else False,
                "L2": props.seguranca_l2 if props else False,
            },
        }

        etapas_detalhadas.append({
            "numero": etapa.etapa,
            "descricao": propriedades_info["nome_acao"],
            "equipamento_codigos": [
                m.codigo for m in (props.maquinas.all() if props else [])
            ],
            "ferramenta": propriedades_info["ferramenta"] or "-",
            "dispositivo": "-",
            "tempo_regulagem": (
                etapa.setup_minutos / 60
                if etapa.setup_minutos is not None else "-"
            ),
            "producao": etapa.pph,
            "alivio_tensao": propriedades_info["descricao_detalhada"] or "-",
            "propriedades": propriedades_info,
            "simbolos_seguranca": [
                roteiro.item.simbolo_mp.url   if props and props.seguranca_mp and roteiro.item.simbolo_mp else None,
                roteiro.item.simbolo_ts.url   if props and props.seguranca_ts and roteiro.item.simbolo_ts else None,
                roteiro.item.simbolo_m1.url   if props and props.seguranca_m1 and roteiro.item.simbolo_m1 else None,
                roteiro.item.simbolo_l1.url   if props and props.seguranca_l1 and roteiro.item.simbolo_l1 else None,
                roteiro.item.simbolo_l2.url   if props and props.seguranca_l2 and roteiro.item.simbolo_l2 else None,
            ],
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
    item_id = request.POST.get("item") or None
    initial_data = {"item": item_id} if item_id else {}

    if item_id and not request.POST.get("fontes_homologadas"):
        try:
            item = Item.objects.get(id=item_id)
            initial_data["fontes_homologadas"] = item.fontes_homologadas.all()
        except Item.DoesNotExist:
            pass

    form = RoteiroProducaoForm(request.POST or None, initial=initial_data)


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
                # Insumos
            for i, ins in enumerate(et.get("insumos", []), start=1):
                try:
                    InsumoEtapa.objects.create(
                        etapa=etapa,
                        materia_prima_id=ins["materia_prima_id"],
                        tipo_insumo=ins.get("tipo_insumo", "matéria_prima"),
                        obrigatorio=ins.get("obrigatorio", False),
                        desenvolvido=limpar_decimal(ins.get("desenvolvido")),
                        peso_liquido=limpar_decimal(ins.get("peso_liquido")),
                        peso_bruto=limpar_decimal(ins.get("peso_bruto")),
                    )
                except ValueError as e:
                    messages.error(
                        request,
                        f"Etapa {et.get('etapa')} — Insumo #{i}: {e}. "
                        "Use no máximo 7 casas decimais e valor absoluto < 1000."
                    )
                    raise



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
        "segurancas": segurancas,
        "servicos": list(ServicoRealizado.objects.order_by("nome").values("id", "nome")),
    })


from django.http import JsonResponse
from comercial.models import Item

from django.http import JsonResponse
from comercial.models.item import Item

# tecnico/views/ajax_views.py
from django.http import JsonResponse
from comercial.models import Item

def ajax_fontes_homologadas_por_item(request):
    item_id = request.GET.get("item_id")
    if not item_id:
        return JsonResponse({"error": "ID do item não fornecido"}, status=400)

    try:
        item = Item.objects.get(id=item_id)
        fontes = item.fontes_homologadas.all()
        data = [{"id": f.id, "text": str(f)} for f in fontes]
        return JsonResponse({"results": data})
    except Item.DoesNotExist:
        return JsonResponse({"results": []})




@login_required
@permission_required("tecnico.aprovar_roteiro", raise_exception=True)
def editar_roteiro(request, pk):
    """
    Edição de Roteiro com preservação de etapas existentes.
    A revisão do formulário vem SEMPRE da última revisão do histórico (por data/id).
    """
    roteiro = get_object_or_404(RoteiroProducao, pk=pk)

    # ➜ última revisão pela data (tie-break por id)
    # Apenas para exibir no helptext
    ultima_revisao_hist = roteiro.revisoes.order_by("-data_revisao", "-id").first()

    form = RoteiroProducaoForm(request.POST or None, instance=roteiro)
    # ❗ Não setamos mais initial aqui; o valor vem do model (sincronizado pelo signal)


    # Dados auxiliares para selects/autocomplete do template
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

    # Monta o JSON inicial para o template (inclui o id da etapa)
    roteiro_data = {"item": roteiro.item_id, "etapas": []}
    for etapa in roteiro.etapas.all().order_by("etapa"):
        insumos_list = [
            {
                "materia_prima_id": ins.materia_prima_id,
                "tipo_insumo": ins.tipo_insumo,
                "obrigatorio": ins.obrigatorio,
                "desenvolvido": float(ins.desenvolvido) if ins.desenvolvido is not None else 0,
                "peso_liquido": float(ins.peso_liquido) if ins.peso_liquido is not None else 0,
                "peso_bruto": float(ins.peso_bruto) if ins.peso_bruto is not None else 0,
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

        roteiro_data["etapas"].append({
            "id": etapa.id,
            "etapa": etapa.etapa,
            "setor": etapa.setor_id,
            "pph": float(etapa.pph or 0),
            "setup_minutos": etapa.setup_minutos or 0,
            "insumos": insumos_list,
            "propriedades": props,
            "segurancas": [
                ("seguranca_mp", "MP"),
                ("seguranca_ts", "TS"),
                ("seguranca_m1", "M1"),
                ("seguranca_l1", "L1"),
                ("seguranca_l2", "L2"),
            ],
        })

    if request.method == "POST":
        dados_json = request.POST.get("dados_json", "")

        if form.is_valid():
            with transaction.atomic():
                # ❗ Não alteramos 'revisao' automaticamente aqui.
                roteiro = form.save()

                # Carrega payload com segurança
                try:
                    payload = json.loads(dados_json or "{}")
                except Exception:
                    payload = {"etapas": []}

                manter_ids = []

                for et in payload.get("etapas", []):
                    etapa_id = et.get("id")
                    etapa_obj = None

                    if etapa_id:
                        etapa_obj = EtapaRoteiro.objects.filter(
                            pk=etapa_id, roteiro=roteiro
                        ).first()

                    # UPDATE ou CREATE
                    if etapa_obj:
                        etapa_obj.etapa = et["etapa"]
                        etapa_obj.setor_id = et["setor"]
                        etapa_obj.pph = et.get("pph") or None
                        etapa_obj.setup_minutos = et.get("setup_minutos") or None
                        etapa_obj.save()
                    else:
                        etapa_obj = EtapaRoteiro.objects.create(
                            roteiro=roteiro,
                            etapa=et["etapa"],
                            setor_id=et["setor"],
                            pph=et.get("pph") or None,
                            setup_minutos=et.get("setup_minutos") or None,
                        )

                    manter_ids.append(etapa_obj.id)

                    # INSUMOS: recria para garantir consistência
                    etapa_obj.insumos.all().delete()
                    for i, ins in enumerate(et.get("insumos", []), start=1):
                        try:
                            InsumoEtapa.objects.create(
                                etapa=etapa_obj,
                                materia_prima_id=ins["materia_prima_id"],
                                tipo_insumo=ins.get("tipo_insumo", "matéria_prima"),
                                obrigatorio=ins.get("obrigatorio", False),
                                desenvolvido=limpar_decimal(ins.get("desenvolvido")),
                                peso_liquido=limpar_decimal(ins.get("peso_liquido")),
                                peso_bruto=limpar_decimal(ins.get("peso_bruto")),
                            )
                        except ValueError as e:
                            messages.error(
                                request,
                                f"Etapa {et.get('etapa')} — Insumo #{i}: {e}. "
                                "Use no máximo 7 casas decimais e valor absoluto < 1000."
                            )
                            raise

                    # PROPRIEDADES: upsert OneToOne e set() em M2M
                    props = et.get("propriedades") or {}
                    if props.get("nome_acao"):
                        prop_obj, _ = PropriedadesEtapa.objects.get_or_create(etapa=etapa_obj)
                        prop_obj.nome_acao = props.get("nome_acao", "")
                        prop_obj.descricao_detalhada = props.get("descricao_detalhada", "")
                        prop_obj.ferramenta_id = (props.get("ferramenta") or {}).get("id") or None
                        prop_obj.seguranca_mp = props.get("seguranca_mp", False)
                        prop_obj.seguranca_ts = props.get("seguranca_ts", False)
                        prop_obj.seguranca_m1 = props.get("seguranca_m1", False)
                        prop_obj.seguranca_l1 = props.get("seguranca_l1", False)
                        prop_obj.seguranca_l2 = props.get("seguranca_l2", False)
                        prop_obj.save()

                        maquinas_ids = [m["id"] for m in props.get("maquinas", []) if m.get("id")]
                        prop_obj.maquinas.set(maquinas_ids)
                    else:
                        PropriedadesEtapa.objects.filter(etapa=etapa_obj).delete()

                # Remove apenas as etapas que sumiram do payload
                roteiro.etapas.exclude(id__in=manter_ids).delete()

            messages.success(request, "Roteiro atualizado com sucesso.")
            return redirect("tecnico:tecnico_roteiros")
        else:
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
        "ultima_revisao": ultima_revisao_hist,  # opcional para o template exibir helptext
    })










from tecnico.models.roteiro import RoteiroProducao, EtapaRoteiro, PropriedadesEtapa, InsumoEtapa
from django.db import transaction
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

@login_required
@permission_required("tecnico.clonar_roteiro", raise_exception=True)
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
                    tipo_insumo=insumo.tipo_insumo,
                    obrigatorio=insumo.obrigatorio,
                    desenvolvido=insumo.desenvolvido or Decimal("0.0"),
                    peso_liquido=insumo.peso_liquido or Decimal("0.0"),
                    peso_bruto=insumo.peso_bruto or Decimal("0.0"),
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


# tecnico/views/roteiros_views.py
import pandas as pd
from django.contrib import messages
from tecnico.models.roteiro import RoteiroProducao, EtapaRoteiro
from comercial.models import Item, CentroDeCusto

from tecnico.models.roteiro import RoteiroProducao, EtapaRoteiro, PropriedadesEtapa, InsumoEtapa
from qualidade_fornecimento.models import MateriaPrimaCatalogo
from tecnico.models import Maquina
from comercial.models import Item, CentroDeCusto, Ferramenta
import pandas as pd

# tecnico/views/roteiros_views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

import pandas as pd

# tecnico/views/roteiros_views.py

# tecnico/views/roteiros_views.py
import re
import pandas as pd
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import render, redirect

# 🔁 AJUSTE ESTES IMPORTS CONFORME SEU PROJETO
from comercial.models import Item, Ferramenta            # Item/Ferramenta normalmente no app comercial
from tecnico.models.roteiro import RoteiroProducao, EtapaRoteiro
from tecnico.models.maquina import Maquina               # ou o módulo correto onde Maquina está
from comercial.models import CentroDeCusto              # ou o app/módulo correto do CentroDeCusto


def _to_int(v):
    try:
        return int(str(v).strip())
    except Exception:
        return None


def _to_float(v):
    try:
        s = str(v).strip().replace(",", ".")
        return float(s) if s else None
    except Exception:
        return None


def _to_bool(v):
    return str(v).strip().lower() in {"sim", "true", "1", "yes"}


def _norm_item_code(c):
    """
    Normaliza o código do item: trim, caixa alta e remove sufixo final de etapa (ex.: A29.001A -> A29.001).
    """
    s = str(c).strip().upper()
    return re.sub(r"[A-Z]$", "", s)


@login_required
@permission_required("tecnico.importar_roteiro", raise_exception=True)
def importar_roteiros_excel(request):
    # Recupera resultado anterior (PRG) para mostrar no GET
    import_result = request.session.pop("import_result", None)

    # Falta de arquivo no POST
    if request.method == "POST" and not request.FILES.get("arquivo"):
        messages.error(request, "Selecione um arquivo Excel antes de importar.")
        return redirect("tecnico:importar_roteiros_excel")

    if request.method == "POST" and request.FILES.get("arquivo"):
        excel = request.FILES["arquivo"]

        try:
            df = pd.read_excel(excel).fillna("")

            obrigatorias = ["Código Item", "Tipo Roteiro", "Etapa Nº", "Setor", "PPH", "Setup (min)"]
            faltantes = [c for c in obrigatorias if c not in df.columns]
            if faltantes:
                messages.error(request, f"Coluna(s) obrigatória(s) ausente(s): {', '.join(faltantes)}.")
                return redirect("tecnico:importar_roteiros_excel")

            # Colunas opcionais
            has_nome_acao      = "Nome Ação" in df.columns
            has_desc_detalhada = "Descrição Detalhada" in df.columns
            has_ferramenta     = "Ferramenta" in df.columns
            has_maquinas       = "Máquinas" in df.columns
            has_mp_codigo      = "MP Código" in df.columns
            has_qtde           = "Qtde" in df.columns
            has_tipo_insumo    = "Tipo Insumo" in df.columns
            has_obrigatorio    = "Obrigatório" in df.columns

            # Campos existentes no modelo (evita passar chave inválida ao create)
            etapa_fields = {f.name for f in EtapaRoteiro._meta.get_fields()}

            # Agrupamento (item + tipo de roteiro)
            agrupado = df.groupby(["Código Item", "Tipo Roteiro"], dropna=False)

            total_roteiros_criados = 0
            total_etapas_criadas = 0

            erros_grupo_item = []         # grupos ignorados por Item inexistente
            avisos_grupo_existente = []   # grupos ignorados por roteiro já existente
            erros_linha_setor = []        # linhas ignoradas por Setor inexistente
            avisos_relacionados = []      # avisos de refs não encontradas (Ferramenta/Máquina)

            with transaction.atomic():
                for (raw_codigo_item, raw_tipo_roteiro), grupo in agrupado:
                    codigo_item = _norm_item_code(raw_codigo_item)
                    tipo_roteiro = str(raw_tipo_roteiro).strip().upper()

                    # Item inexistente -> ignora todo o grupo
                    try:
                        item = Item.objects.get(codigo=codigo_item)
                    except Item.DoesNotExist:
                        erros_grupo_item.append(
                            f"Item '{codigo_item}' não encontrado. Grupo (item/roteiro {tipo_roteiro}) ignorado."
                        )
                        continue

                    # ✅ Se já existir roteiro para (item, tipo), ignora grupo
                    if RoteiroProducao.objects.filter(item=item, tipo_roteiro=tipo_roteiro).exists():
                        avisos_grupo_existente.append(
                            f"Roteiro já existe para Item {codigo_item} / Tipo {tipo_roteiro}. Grupo ignorado."
                        )
                        continue

                    # Cria um novo roteiro
                    roteiro = RoteiroProducao.objects.create(
                        item=item, tipo_roteiro=tipo_roteiro, revisao=1
                    )
                    total_roteiros_criados += 1

                    # Cria etapas do grupo
                    for _, row in grupo.iterrows():
                        # Centro de Custo (Setor) obrigatório por linha
                        try:
                            setor = CentroDeCusto.objects.get(nome__iexact=str(row["Setor"]).strip())
                        except CentroDeCusto.DoesNotExist:
                            erros_linha_setor.append(
                                f"Setor '{row['Setor']}' não encontrado (Item {codigo_item}, Etapa {row['Etapa Nº']}). Linha ignorada."
                            )
                            continue

                        etapa_data = {
                            "roteiro": roteiro,
                            "etapa": _to_int(row["Etapa Nº"]) or 0,
                            "setor": setor,
                            "pph": _to_float(row["PPH"]),
                            "setup_minutos": _to_float(row["Setup (min)"]),
                        }

                        # Opcionais presentes no modelo
                        if has_nome_acao and "nome_acao" in etapa_fields:
                            etapa_data["nome_acao"] = str(row["Nome Ação"]).strip()
                        if has_desc_detalhada and "descricao_detalhada" in etapa_fields:
                            etapa_data["descricao_detalhada"] = str(row["Descrição Detalhada"]).strip()
                        if has_tipo_insumo and "tipo_insumo" in etapa_fields:
                            etapa_data["tipo_insumo"] = str(row["Tipo Insumo"]).strip()
                        if has_obrigatorio and "obrigatorio" in etapa_fields:
                            etapa_data["obrigatorio"] = _to_bool(row["Obrigatório"])
                        if has_mp_codigo and "mp_codigo" in etapa_fields:
                            etapa_data["mp_codigo"] = str(row["MP Código"]).strip()

                        if has_qtde and ("qtde" in etapa_fields or "quantidade" in etapa_fields or "quantidade_insumo" in etapa_fields):
                            valor_qtde = _to_float(row["Qtde"])
                            if "qtde" in etapa_fields:
                                etapa_data["qtde"] = valor_qtde
                            elif "quantidade" in etapa_fields:
                                etapa_data["quantidade"] = valor_qtde
                            elif "quantidade_insumo" in etapa_fields:
                                etapa_data["quantidade_insumo"] = valor_qtde

                        # Ferramenta (FK opcional)
                        if has_ferramenta and "ferramenta" in etapa_fields:
                            cod_ferr = str(row["Ferramenta"]).strip()
                            if cod_ferr:
                                try:
                                    etapa_data["ferramenta"] = Ferramenta.objects.get(codigo=cod_ferr)
                                except Ferramenta.DoesNotExist:
                                    avisos_relacionados.append(
                                        f"Ferramenta '{cod_ferr}' não encontrada (Item {codigo_item}, Etapa {row['Etapa Nº']})."
                                    )

                        # Cria a etapa
                        etapa = EtapaRoteiro.objects.create(**etapa_data)
                        total_etapas_criadas += 1

                        # Máquinas (M2M opcional)
                        if has_maquinas:
                            maquinas_raw = str(row["Máquinas"]).strip()
                            if maquinas_raw:
                                codigos = [c.strip() for c in maquinas_raw.split(",") if c.strip()]
                                for cod_maquina in codigos:
                                    try:
                                        maq = Maquina.objects.get(codigo=cod_maquina)
                                        if hasattr(etapa, "maquinas"):
                                            etapa.maquinas.add(maq)
                                        elif hasattr(etapa, "equipamentos"):
                                            etapa.equipamentos.add(maq)
                                    except Maquina.DoesNotExist:
                                        avisos_relacionados.append(
                                            f"Máquina '{cod_maquina}' não encontrada (Item {codigo_item}, Etapa {row['Etapa Nº']})."
                                        )

            # Monta o resumo e salva na sessão (PRG)
            resumo = {
                "total_roteiros_criados": total_roteiros_criados,
                "total_etapas_criadas": total_etapas_criadas,
                "erros_grupo_item": erros_grupo_item,               # itens inexistentes
                "erros_linha_setor": erros_linha_setor,             # setor inexistente por linha
                "avisos_relacionados": avisos_relacionados,         # ferramentas/máquinas não encontradas
                "avisos_grupo_existente": avisos_grupo_existente,   # ✅ grupos pulados por roteiro já existente
            }

            messages.success(
                request,
                f"Importação finalizada: {total_roteiros_criados} roteiro(s) e {total_etapas_criadas} etapa(s) criados."
            )
            request.session["import_result"] = resumo
            return redirect("tecnico:importar_roteiros_excel")

        except Exception as e:
            messages.error(request, f"Erro ao processar o Excel: {e}")
            return redirect("tecnico:importar_roteiros_excel")

    # GET: renderiza tela e relatório (se houver)
    context = {"import_result": import_result}
    return render(request, "roteiros/importar_roteiros.html", context)



# tecnico/views/roteiros_views.py
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from tecnico.models.roteiro import RoteiroProducao, RoteiroRevisao
from tecnico.forms.roteiro_revisao_form import RoteiroRevisaoForm

@login_required
@permission_required("tecnico.view_roteiroproducao", raise_exception=True)
def historico_revisoes_roteiro(request, pk):
    roteiro = get_object_or_404(RoteiroProducao, pk=pk)
    revisoes = roteiro.revisoes.all()  # mais recente primeiro (ordering no model)
    return render(request, "roteiros/historico_revisoes_roteiro.html", {
        "roteiro": roteiro,
        "revisoes": revisoes,
    })

@login_required
@permission_required("tecnico.change_roteiroproducao", raise_exception=True)
def adicionar_revisao_roteiro(request, pk):
    roteiro = get_object_or_404(RoteiroProducao, pk=pk)
    if request.method == "POST":
        form = RoteiroRevisaoForm(request.POST)
        if form.is_valid():
            revisao = form.save(commit=False)
            revisao.roteiro = roteiro
            revisao.criado_por = request.user
            revisao.save()
            messages.success(request, "Revisão adicionada com sucesso.")
            return redirect("tecnico:historico_revisoes_roteiro", pk=roteiro.pk)
    else:
        form = RoteiroRevisaoForm()

    return render(request, "roteiros/adicionar_revisao_roteiro.html", {
        "roteiro": roteiro,
        "form": form,
    })

@login_required
@permission_required("tecnico.delete_roteiroproducao", raise_exception=True)
def inativar_revisao_roteiro(request, revisao_id):
    revisao = get_object_or_404(RoteiroRevisao, pk=revisao_id)
    roteiro_id = revisao.roteiro_id
    if request.method == "POST":
        revisao.status = "inativo"
        revisao.save(update_fields=["status"])
        messages.success(request, "Revisão inativada com sucesso.")
        return redirect("tecnico:historico_revisoes_roteiro", pk=roteiro_id)
    return render(request, "roteiros/confirmar_inativacao_revisao.html", {"revisao": revisao})
