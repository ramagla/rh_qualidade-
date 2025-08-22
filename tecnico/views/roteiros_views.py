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

LIMITE_ABS_INTEIRO = Decimal("1000")   # 10^3 para max_digits=10, decimal_places=7
DEC_PLACES = 7
QUANT_7 = Decimal("1").scaleb(-DEC_PLACES)  # = Decimal('0.0000001')

def limpar_decimal(valor, padrao=None):
    """
    - Aceita '', None -> retorna None (evita gravar 0 indevido).
    - Remove separador de milhar.
    - Converte vírgula para ponto (pt-BR -> en-US).
    - Normaliza para 7 casas decimais.
    - Valida limite absoluto (< 1000).
    """
    if valor is None:
        return padrao
    s = str(valor).strip()
    if s == "":
        return padrao

    # remove qualquer coisa que não seja dígito, vírgula, ponto ou sinal
    s = re.sub(r"[^\d,.\-+]", "", s)

    # "1.234,56" -> "1234.56"; "1234,56" -> "1234.56"
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")

    try:
        d = Decimal(s)
    except (InvalidOperation, ValueError, TypeError):
        return padrao

    # normaliza para 7 casas decimais
    d = d.quantize(QUANT_7, rounding=ROUND_HALF_UP)

    # valida limite absoluto do Decimal(10,7): |x| < 1000
    if abs(d) >= LIMITE_ABS_INTEIRO:
        raise ValueError(f"Valor {d} ultrapassa o limite permitido (< 1000).")

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

@login_required
@permission_required("tecnico.importar_roteiro", raise_exception=True)
def importar_roteiros_excel(request):
    if request.method == "POST" and request.FILES.get("arquivo"):
        excel = request.FILES["arquivo"]
        try:
            df = pd.read_excel(excel).fillna("")

            obrigatorias = ["Código Item", "Tipo Roteiro", "Etapa Nº", "Setor", "PPH", "Setup (min)"]
            for col in obrigatorias:
                if col not in df.columns:
                    messages.error(request, f"Coluna obrigatória ausente: {col}")
                    return redirect("importar_roteiros_excel")

            agrupado = df.groupby(["Código Item", "Tipo Roteiro"])
            criados = 0

            with transaction.atomic():
                for (codigo_item, tipo_roteiro), grupo in agrupado:
                    try:
                        item = Item.objects.get(codigo=str(codigo_item).strip())
                        roteiro, _ = RoteiroProducao.objects.get_or_create(
                            item=item,
                            tipo_roteiro=tipo_roteiro.strip().upper(),
                            defaults={"revisao": 1}
                        )

                        for _, row in grupo.iterrows():
                            setor = CentroDeCusto.objects.get(nome__iexact=row["Setor"].strip())
                            etapa = EtapaRoteiro.objects.create(
                                roteiro=roteiro,
                                etapa=int(row["Etapa Nº"]),
                                setor=setor,
                                pph=float(row["PPH"]) or None,
                                setup_minutos=float(row["Setup (min)"]) or None,
                            )

                            # Insumo
                            if row["MP Código"]:
                                try:
                                    mp = MateriaPrimaCatalogo.objects.get(codigo=row["MP Código"].strip())
                                    InsumoEtapa.objects.create(
                                        etapa=etapa,
                                        materia_prima=mp,
                                        quantidade=float(row["Qtde"]),
                                        tipo_insumo=row["Tipo Insumo"],
                                        obrigatorio=(str(row["Obrigatório"]).strip().lower() == "sim"),
                                    )
                                except MateriaPrimaCatalogo.DoesNotExist:
                                    messages.warning(request, f"MP {row['MP Código']} não encontrada (etapa {etapa}).")

                            # Propriedades
                            if row["Nome Ação"]:
                                ferramenta = None
                                if row["Ferramenta"]:
                                    ferramenta = Ferramenta.objects.filter(codigo__iexact=row["Ferramenta"].strip()).first()

                                prop = PropriedadesEtapa.objects.create(
                                    etapa=etapa,
                                    nome_acao=row["Nome Ação"],
                                    descricao_detalhada=row["Descrição Detalhada"],
                                    ferramenta=ferramenta
                                )

                                # Máquinas (lista separada por vírgula)
                                codigos_maquinas = [m.strip() for m in str(row["Máquinas"]).split(",") if m.strip()]
                                maquinas = Maquina.objects.filter(codigo__in=codigos_maquinas)
                                prop.maquinas.set(maquinas)

                        criados += 1
                    except Exception as e:
                        messages.error(request, f"Erro ao processar {codigo_item} tipo {tipo_roteiro}: {e}")
                        return redirect("importar_roteiros_excel")

            messages.success(request, f"Importação finalizada: {criados} roteiro(s) criados.")
            return redirect("tecnico:tecnico_roteiros")

        except Exception as e:
            messages.error(request, f"Erro ao processar o Excel: {e}")
            return redirect("importar_roteiros_excel")

    return render(request, "roteiros/importar_roteiros.html")


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
