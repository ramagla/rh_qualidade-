import re
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.utils.timezone import localtime as tz_localtime, now

from assinatura_eletronica.models import AssinaturaEletronica
from assinatura_eletronica.utils import gerar_assinatura, gerar_qrcode_base64
from qualidade_fornecimento.forms.inline_rolo_formset import RoloFormSet
from qualidade_fornecimento.forms.relatorio_f045 import RelatorioF045Form
from qualidade_fornecimento.models.f045 import RelatorioF045
from qualidade_fornecimento.models.materiaPrima import RelacaoMateriaPrima
from qualidade_fornecimento.models.norma import (
    NormaComposicaoElemento,
    NormaTecnica,
    NormaTracao,
)
from qualidade_fornecimento.templatetags.custom_filters import parse_decimal_seguro


@login_required
@permission_required('qualidade_fornecimento.view_relatoriof045', raise_exception=True)
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
@permission_required('qualidade_fornecimento.view_relatoriof045', raise_exception=True)
def visualizar_f045_pdf(request, relacao_id):
    relacao = get_object_or_404(RelacaoMateriaPrima, pk=relacao_id)
    f045 = relacao.f045
    rolos = relacao.rolos.all()

    # Norma e composição
    try:
        norma_obj = relacao.materia_prima.norma
        tipo_abnt = relacao.materia_prima.tipo_abnt
        composicao = NormaComposicaoElemento.objects.filter(
            norma=norma_obj, tipo_abnt__iexact=tipo_abnt
        ).first()
        try:
            bitola_decimal = (
                Decimal(str(relacao.materia_prima.bitola).replace(",", "."))
                if relacao.materia_prima.bitola not in (None, "")
                else None
            )
        except (InvalidOperation, TypeError, ValueError):
            bitola_decimal = None

        norma_tracao = (
            NormaTracao.objects.filter(
                norma=norma_obj,
                tipo_abnt__iexact=tipo_abnt,
                bitola_minima__lte=bitola_decimal,
                bitola_maxima__gte=bitola_decimal,
            ).first()
            if (bitola_decimal is not None and tipo_abnt)
            else None
        )
    except (NormaTecnica.DoesNotExist, NormaComposicaoElemento.DoesNotExist, ValueError):
        composicao = None
        norma_tracao = None

    # Verificação química
    encontrados = []
    if composicao:
        elementos = [
            ("C", composicao.c_min, composicao.c_max, getattr(f045, "c_user", None)),
            ("Mn", composicao.mn_min, composicao.mn_max, getattr(f045, "mn_user", None)),
            ("Si", composicao.si_min, composicao.si_max, getattr(f045, "si_user", None)),
            ("P", composicao.p_min, composicao.p_max, getattr(f045, "p_user", None)),
            ("S", composicao.s_min, composicao.s_max, getattr(f045, "s_user", None)),
            ("Cr", composicao.cr_min, composicao.cr_max, getattr(f045, "cr_user", None)),
            ("Ni", composicao.ni_min, composicao.ni_max, getattr(f045, "ni_user", None)),
            ("Cu", composicao.cu_min, composicao.cu_max, getattr(f045, "cu_user", None)),
            ("Al", composicao.al_min, composicao.al_max, getattr(f045, "al_user", None)),
        ]
        for sigla, vmin, vmax, valor in elementos:
            try:
                val = Decimal(str(valor).replace(",", ".")) if valor is not None else None
                if vmin in [None, 0] and vmax in [None, 0]:
                    ok = True
                elif val is not None and vmin is not None and vmax is not None:
                    ok = vmin <= val <= vmax
                else:
                    ok = False
            except Exception:
                val = valor
                ok = False
            encontrados.append({
                "sigla": sigla, "min": vmin, "max": vmax,
                "valor": val, "ok": ok,
                "nome_elemento": "",
            })

    # ===== Laudo do Certificado (Tração/Dureza vs Norma) para o PDF =====
    def _parse_decimal_str(valor):
        if valor is None:
            return None
        s = str(valor).strip()
        for tok in ("kgf/mm2", "kgf/mm²", "MPa", "HRB", "HRC", "—", "N/A"):
            s = s.replace(tok, "")
        s = s.replace(",", ".")
        try:
            return Decimal(s)
        except Exception:
            return None

    res_min = res_max = dureza_limite = None
    if norma_tracao:
        if getattr(norma_tracao, "resistencia_min", None) is not None:
            res_min = Decimal(str(norma_tracao.resistencia_min).replace(",", "."))
        if getattr(norma_tracao, "resistencia_max", None) is not None:
            res_max = Decimal(str(norma_tracao.resistencia_max).replace(",", "."))
        if getattr(norma_tracao, "dureza", None):
            dureza_limite = Decimal(str(norma_tracao.dureza).replace(",", "."))

    tracao_cert = _parse_decimal_str(getattr(f045, "resistencia_tracao", None))
    dureza_cert = _parse_decimal_str(getattr(f045, "dureza_certificado", None))

    if tracao_cert is None and dureza_cert is None:
        laudo_certificado_pdf = None
    else:
        tracao_ok = True
        dureza_ok = True
        if tracao_cert is not None and res_min is not None and res_max is not None:
            tracao_ok = (res_min <= tracao_cert <= res_max)
        if dureza_limite is not None and dureza_cert is not None:
            dureza_ok = (dureza_cert <= dureza_limite)
        laudo_certificado_pdf = "Ap" if (tracao_ok and dureza_ok) else "Re"
    # ===== FIM Laudo do Certificado =====

    # Assinatura padrão (fallback)
    assinatura_nome = f045.usuario.get_full_name() or f045.usuario.username
    assinatura_email = f045.usuario.email
    assinatura_data = tz_localtime(f045.data_assinatura) if f045.data_assinatura else None
    assinatura_hash = None
    assinatura_departamento = "Não informado"
    qr_base64 = None
    url_validacao = None

    assinatura_eletronica = AssinaturaEletronica.objects.filter(
        origem_model="RelatorioF045",
        origem_id=f045.id
    ).first()

    if assinatura_eletronica:
        assinatura_hash = assinatura_eletronica.hash
        url_validacao = request.build_absolute_uri(f"/assinatura/validar/{assinatura_hash}/")
        qr_base64 = gerar_qrcode_base64(url_validacao)

        usuario_assinatura = assinatura_eletronica.usuario
        assinatura_nome = usuario_assinatura.get_full_name() or usuario_assinatura.username
        assinatura_email = usuario_assinatura.email

        funcionario = getattr(usuario_assinatura, 'funcionario', None)
        if funcionario and funcionario.local_trabalho:
            assinatura_departamento = funcionario.local_trabalho.nome

    context = {
        "obj": f045,
        "rolos": rolos,
        "relacao": relacao,
        "encontrados": encontrados,
        "norma_tracao": norma_tracao,
        "logo_url": static('logo.png'),
        "seguranca_url": static('seguranca.png'),

        # Assinatura digital
        "assinatura_nome": assinatura_nome,
        "assinatura_email": assinatura_email,
        "assinatura_data": assinatura_data,
        "assinatura_hash": assinatura_hash,
        "assinatura_departamento": assinatura_departamento,
        "qr_base64": qr_base64,
        "url_validacao": url_validacao,

        # Título
        "titulo": f"F045 – Relatório {f045.nro_relatorio}",

        # Novo: laudo calculado para impressão na tabela “Outras características”
        "laudo_certificado_pdf": laudo_certificado_pdf,
    }

    return render(request, "f045/f045_visualizacao.html", context)



@login_required
@permission_required('qualidade_fornecimento.change_relatoriof045', raise_exception=True)
def gerar_f045(request, relacao_id):
    relacao = get_object_or_404(RelacaoMateriaPrima, pk=relacao_id)

    print("====== DEBUG ROLAGEM ======")
    print(f"Relação ID: {relacao.id} — Nº Relatório: {relacao.nro_relatorio}")
    print(f"Total de rolos encontrados: {relacao.rolos.count()}")
    for r in relacao.rolos.all():
        print(
            f"Rolo nº: {r.nro_rolo} | Enrolamento: {r.enrolamento} | Dobramento: {r.dobramento} | "
            f"Torção: {r.torcao_residual} | Visual: {r.aspecto_visual} | Alongamento: {r.alongamento} | "
            f"Flechamento: {r.flechamento}"
        )


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
        norma_obj = relacao.materia_prima.norma
        tipo_abnt = relacao.materia_prima.tipo_abnt
        composicao = NormaComposicaoElemento.objects.filter(
            norma=norma_obj,
            tipo_abnt__iexact=tipo_abnt
        ).first()


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

        bitola = parse_decimal_seguro(relacao.materia_prima.bitola)
        tipo_abnt = relacao.materia_prima.tipo_abnt

        tracao = (
            NormaTracao.objects.filter(
                norma=norma_obj,
                tipo_abnt__iexact=tipo_abnt,
                bitola_minima__lte=bitola,
                bitola_maxima__gte=bitola,
            ).first()
            if (bitola is not None and tipo_abnt)
            else None
        )


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
        # INCLUI SEMPRE — mesmo que vmin ou vmax sejam None
        limites[sigla] = (vmin, vmax)


    form = RelatorioF045Form(
        request.POST or None, instance=f045, limites_quimicos=limites
    )
    if request.method == "POST":
        formset = RoloFormSet(request.POST, instance=relacao, prefix="rolos")
    else:
        formset = RoloFormSet(instance=relacao, prefix="rolos")


        print(f"DEBUG FORMSET — TOTAL FORMS: {formset.total_form_count()}")
        for i, f in enumerate(formset.forms):
            print(f"Form {i}: instance.pk={f.instance.pk}, tb050_id={f.instance.tb050_id}, nro_rolo={f.instance.nro_rolo}")

        

    rolos = relacao.rolos.all()
    tracoes_com_forms = list(zip(rolos, formset.forms))
    print(f"==== TESTE 2 — TRACOES_COM_FORMS ====")
    print(f"Total pares: {len(tracoes_com_forms)}")
    for i, (rolo, rolo_form) in enumerate(tracoes_com_forms):
        print(
            f"Pair {i}: rolo.nro_rolo={rolo.nro_rolo}, "
            f"form.instance.pk={rolo_form.instance.pk}, form.tb050_id={rolo_form.instance.tb050_id}"
        )



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

    bitola_nominal = parse_decimal_seguro(bitola_raw) or Decimal("0")
    largura_nominal = parse_decimal_seguro(largura_raw) or Decimal("0")

    if request.method == "POST":
        if form.is_valid() and formset.is_valid():
            updated_f045 = form.save(commit=False)
            switch_manual = request.POST.get("switchStatusManual") == "on"

            tolerancia = parse_decimal_seguro(relacao.materia_prima.tolerancia or "0")
            tolerancia_largura = parse_decimal_seguro(relacao.materia_prima.tolerancia_largura or "0")

            dureza_limite = parse_decimal(dureza_norma)  # mantém, retorna Decimal ou None

            for form_rolo in formset:
                if not form_rolo.has_changed():
                    continue  # pular rolos que não mudaram

                rolo = form_rolo.save(commit=False)

                # 🔥 ESSENCIAL — garante que o formset não quebre
                rolo.tb050 = relacao

                # atribuições manuais:
                rolo_id = rolo.nro_rolo

                rolo.dureza = parse_decimal_seguro(request.POST.get(f"dureza_{rolo_id}"))
                rolo.tracao = parse_decimal_seguro(request.POST.get(f"tracao_{rolo_id}"))

                bitola_espessura = request.POST.get(f"bitola_espessura_{rolo_id}")
                bitola_largura = request.POST.get(f"bitola_largura_{rolo_id}")
                bitola_unica = request.POST.get(f"bitola_{rolo_id}")

                if bitola_espessura or bitola_largura:
                    rolo.bitola_espessura = parse_decimal_seguro(bitola_espessura) if bitola_espessura else None
                    rolo.bitola_largura = parse_decimal(bitola_largura) if bitola_largura else None
                elif bitola_unica:
                    rolo.bitola_espessura = parse_decimal(bitola_unica)
                    rolo.bitola_largura = None

                if "switchMpa" in request.POST and rolo.tracao:
                    rolo.tracao *= Decimal("0.10197")

                # Salva só uma vez!
                rolo.save()

                # Atualiza laudo
                rolo.aprova_rolo(
                    bitola_nominal,           # Decimal
                    largura_nominal,          # Decimal
                    tolerancia,               # Decimal
                    tolerancia_largura,       # Decimal
                    res_min,                  # Decimal ou None
                    res_max,                  # Decimal ou None
                    dureza_limite,            # Decimal ou None
                )
                rolo.save()

                # ✅ Salva os campos do formset (enrolamento, dobramento, etc.)
                form_rolo.instance = rolo  # (opcional, mas garante que o formset fique sincronizado)
                form_rolo.save()



            # >>>>> AQUI entra a avaliação dos químicos
            quimicos_aprovados = True
            for elemento in elementos:
                sigla = elemento["sigla"].lower()
                encontrado_raw = request.POST.get(f"encontrado_{sigla}", "").replace(
                    ",", "."
                )

                try:
                    encontrado = parse_decimal_seguro(encontrado_raw)
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

           # Grava data da assinatura
            # Grava nome e e-mail do usuário que assinou
            updated_f045.assinatura_nome = request.user.get_full_name() or request.user.username
            updated_f045.assinatura_cn = request.user.email
            updated_f045.data_assinatura = now()
            updated_f045.save(update_fields=["assinatura_nome", "assinatura_cn", "data_assinatura"])

            # Cria ou atualiza a assinatura eletrônica associada
            conteudo_hash = f"{updated_f045.nro_relatorio}|{updated_f045.material}|{updated_f045.numero_certificado}|{updated_f045.status_geral}"
            assinatura_hash = gerar_assinatura(updated_f045, request.user)

            AssinaturaEletronica.objects.update_or_create(
                origem_model="RelatorioF045",
                origem_id=updated_f045.id,
                defaults={
                    "hash": assinatura_hash,
                    "conteudo": conteudo_hash,
                    "usuario": request.user,
                    "data_assinatura": updated_f045.data_assinatura,
                }
            )

            messages.success(request, "Relatório F045 salvo com sucesso.")
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
            "bitola_nominal": f"{bitola_nominal}".replace(".", ","),
            "largura_nominal": f"{largura_nominal}".replace(".", ","),

        },
    )
