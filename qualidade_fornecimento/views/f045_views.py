import re
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from qualidade_fornecimento.forms.inline_rolo_formset import RoloFormSet
from qualidade_fornecimento.forms.relatorio_f045 import RelatorioF045Form
from qualidade_fornecimento.models.f045 import RelatorioF045
from qualidade_fornecimento.models.materiaPrima import RelacaoMateriaPrima
from qualidade_fornecimento.models.norma import (
    NormaComposicaoElemento,
    NormaTecnica,
    NormaTracao,
)
from qualidade_fornecimento.tasks import gerar_pdf_f045_background


@login_required
def f045_status(request, f045_id):
    """
    Retorna {"ready": true, "url": "<pdf_url>"} quando o PDF estiver gravado.
    """
    try:
        f045 = RelatorioF045.objects.get(pk=f045_id)
        if f045.pdf:  # ou checar se o arquivo existe
            return JsonResponse({"ready": True, "url": f045.pdf.url})
    except RelatorioF045.DoesNotExist:
        pass
    return JsonResponse({"ready": False})


def parse_decimal(value):
    try:
        return Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError, AttributeError):
        return None


@login_required
def gerar_f045(request, relacao_id):
    relacao = get_object_or_404(RelacaoMateriaPrima, pk=relacao_id)

    try:
        f045 = relacao.f045
        updated = False

        if f045.nro_relatorio != relacao.nro_relatorio:
            f045.nro_relatorio = relacao.nro_relatorio
            updated = True

        fornecedor_nome = getattr(relacao.fornecedor, "nome", str(relacao.fornecedor))
        if f045.fornecedor != fornecedor_nome:
            f045.fornecedor = fornecedor_nome
            updated = True

        if f045.numero_certificado != (relacao.numero_certificado or ""):
            f045.numero_certificado = relacao.numero_certificado or ""
            updated = True

        if f045.material != relacao.materia_prima.descricao:
            f045.material = relacao.materia_prima.descricao
            updated = True

        if f045.nota_fiscal != relacao.nota_fiscal:
            f045.nota_fiscal = relacao.nota_fiscal
            updated = True

        if f045.massa_liquida != relacao.peso_total:
            f045.massa_liquida = relacao.peso_total
            updated = True

        if updated:
            f045.save()

    except ObjectDoesNotExist:
        f045 = RelatorioF045.objects.create(
            relacao=relacao,
            nro_relatorio=relacao.nro_relatorio,
            fornecedor=getattr(relacao.fornecedor, "nome", str(relacao.fornecedor)),
            numero_certificado=relacao.numero_certificado or "",
            nota_fiscal=relacao.nota_fiscal or "",
            material=relacao.materia_prima.descricao,
            bitola=relacao.materia_prima.bitola or "",
            qtd_rolos=relacao.rolos.count(),
            massa_liquida=relacao.peso_total,
            usuario=request.user,
        )

    elementos = []
    dureza_norma = "N/A"
    res_min, res_max = None, None

    try:
        norma_obj = NormaTecnica.objects.get(nome_norma=relacao.materia_prima.norma)
        composicao = NormaComposicaoElemento.objects.filter(norma=norma_obj).first()

        if composicao:
            elementos = [
                {"sigla": "C", "min": composicao.c_min, "max": composicao.c_max},
                {"sigla": "Mn", "min": composicao.mn_min, "max": composicao.mn_max},
                {"sigla": "Si", "min": composicao.si_min, "max": composicao.si_max},
                {"sigla": "P", "min": composicao.p_min, "max": composicao.p_max},
                {"sigla": "S", "min": composicao.s_min, "max": composicao.s_max},
                {"sigla": "Cr", "min": composicao.cr_min, "max": composicao.cr_max},
                {"sigla": "Ni", "min": composicao.ni_min, "max": composicao.ni_max},
                {"sigla": "Cu", "min": composicao.cu_min, "max": composicao.cu_max},
                {"sigla": "Al", "min": composicao.al_min, "max": composicao.al_max},
            ]

        bitola = parse_decimal(relacao.materia_prima.bitola)
        tipo_abnt = relacao.materia_prima.tipo_abnt  # Novo: pega o tipo ABNT do cadastro

        if bitola and tipo_abnt:
            tracao = NormaTracao.objects.filter(
                norma=norma_obj,
                tipo_abnt__iexact=tipo_abnt,
                bitola_minima__lte=bitola,
                bitola_maxima__gte=bitola
            ).first()
        else:
            tracao = None

        if tracao:
            res_min = tracao.resistencia_min
            res_max = tracao.resistencia_max
            dureza_norma = tracao.dureza

            # Converte se a dureza vier como string do tipo "85 HRB"
            if isinstance(dureza_norma, str):
                match = re.search(r"(\d+(?:[.,]\d+)?)", dureza_norma)
                if match:
                    dureza_norma = match.group(1).replace(",", ".")
                else:
                    dureza_norma = ""
  


    except NormaTecnica.DoesNotExist:
        pass

    limites = {}
    for e in elementos:
        sigla = e["sigla"].lower()
        vmin = parse_decimal(e["min"])
        vmax = parse_decimal(e["max"])
        # só inclui se ambos forem Decimal válidos
        if vmin is not None and vmax is not None:
            limites[sigla] = (vmin, vmax)

    form = RelatorioF045Form(
        request.POST or None, instance=f045, limites_quimicos=limites
    )
    formset = RoloFormSet(request.POST or None, instance=relacao)
    rolos = relacao.rolos.all()
    tracoes_com_forms = list(zip(rolos, formset.forms))

    chemical_list = []
    for item in elementos:
        sigla = item["sigla"].lower()
        field = form[sigla + "_user"] if sigla + "_user" in form.fields else None
        chemical_list.append(
            {
                "sigla": item["sigla"],
                "min": item["min"],
                "max": item["max"],
                "field": field,
            }
        )

    bitola_raw = relacao.materia_prima.bitola or "0"
    largura_raw = relacao.materia_prima.largura or "0"

    bitola_nominal = float(parse_decimal(bitola_raw) or 0)
    largura_nominal = float(parse_decimal(largura_raw) or 0)



    if request.method == "POST":
        if form.is_valid() and formset.is_valid():
            updated_f045 = form.save(commit=False)
            switch_manual = request.POST.get("switchStatusManual") == "on"

            tolerancia = parse_decimal(relacao.materia_prima.tolerancia or "0")
            tolerancia_largura = parse_decimal(
                relacao.materia_prima.tolerancia_largura or "0"
            )
            dureza_limite = parse_decimal(dureza_norma)

            for form_rolo in formset.forms:
                rolo = form_rolo.instance
                rolo_id = str(rolo.pk)

                rolo.dureza = parse_decimal(request.POST.get(f"dureza_{rolo_id}"))
                rolo.tracao = parse_decimal(request.POST.get(f"tracao_{rolo_id}"))

                bitola_espessura = request.POST.get(f"bitola_espessura_{rolo_id}")
                bitola_largura = request.POST.get(f"bitola_largura_{rolo_id}")
                bitola_unica = request.POST.get(f"bitola_{rolo_id}")

                if bitola_espessura is not None or bitola_largura is not None:
                    rolo.bitola_espessura = (
                        parse_decimal(bitola_espessura) if bitola_espessura else None
                    )
                    rolo.bitola_largura = (
                        parse_decimal(bitola_largura) if bitola_largura else None
                    )
                elif bitola_unica is not None:
                    rolo.bitola_espessura = parse_decimal(bitola_unica)
                    rolo.bitola_largura = None

                if "switchMpa" in request.POST and rolo.tracao:
                    rolo.tracao *= Decimal("0.10197")

                rolo.save()
                rolo.aprova_rolo(
                    bitola_nominal,
                    largura_nominal,
                    tolerancia,
                    tolerancia_largura,
                    res_min,
                    res_max,
                    dureza_limite,
                )
                rolo.save()

            # >>>>> AQUI entra a avaliação dos químicos
            quimicos_aprovados = True
            for elemento in elementos:
                sigla = elemento["sigla"].lower()
                encontrado_raw = request.POST.get(f"encontrado_{sigla}", "").replace(
                    ",", "."
                )

                try:
                    encontrado = Decimal(encontrado_raw)
                except (InvalidOperation, ValueError):
                    encontrado = None

                minimo = elemento["min"]
                maximo = elemento["max"]

                if encontrado is not None:
                    if minimo in [None, 0] and maximo in [None, 0]:
                        aprovado = True
                    elif minimo is not None and maximo is not None:
                        aprovado = minimo <= encontrado <= maximo
                    else:
                        aprovado = False

                    if not aprovado:
                        quimicos_aprovados = False

            # Agora usa laudos + químicos para decidir o status
            # Agora usa laudos + químicos para decidir o status
            laudos = [rolo.laudo for rolo in relacao.rolos.all()]
            if all(l == "Aprovado" for l in laudos) and quimicos_aprovados:
                updated_f045.status_geral = "Aprovado"
            elif switch_manual:
                updated_f045.status_geral = "Aprovado Condicionalmente"
            else:
                updated_f045.status_geral = "Reprovado"

            # Salva o relatório com as avaliações
            updated_f045.save(limites_quimicos=limites, aprovado_manual=switch_manual)

            # Atualiza o status da relação com base no F045 salvo
            relacao.status = updated_f045.status_geral
            relacao.save(update_fields=["status"])

            # Só agora chama a task
            gerar_pdf_f045_background.delay(updated_f045.pk)




            request.session["f045_pending"] = updated_f045.pk
            return redirect("tb050_list")

    return render(
        request,
        "f045/f045_form.html",
        {
            "form": form,
            "formset": formset,
            "tracoes_com_forms": tracoes_com_forms,
            "chemical_list": chemical_list,
            "dureza_padrao_header": dureza_norma,
            "dureza_certificado": f045.dureza_certificado or "N/A",
            "relacao": relacao,
            "res_min": res_min,
            "res_max": res_max,
            "dureza_padrao": dureza_norma,
            "bitola_nominal": bitola_nominal,
            "largura_nominal": largura_nominal,
        },
    )


from django.http import JsonResponse
