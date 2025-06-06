import os
import tempfile
from datetime import date
from decimal import Decimal
from io import BytesIO

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import get_template, render_to_string
from django.templatetags.static import static
from django.utils.timezone import localtime, now
from weasyprint import HTML

from qualidade_fornecimento.models.f045 import RelatorioF045
from qualidade_fornecimento.models.materiaPrima import RelacaoMateriaPrima
from qualidade_fornecimento.models.norma import (
    NormaComposicaoElemento,
    NormaTecnica,
    NormaTracao,
)


# ==========================
# GERAR PDF FINAL SALVO
# ==========================
@login_required
def gerar_pdf_f045(request, relacao_id):
    return _renderizar_pdf_f045(request, relacao_id, salvar_pdf=True)


# ==========================
# VISUALIZAR TEMPORÁRIO
# ==========================
@login_required
def visualizar_f045_pdf(request, relacao_id):
    return _renderizar_pdf_f045(request, relacao_id, salvar_pdf=False)


# ==========================
# FUNÇÃO COMPARTILHADA
# ==========================
def _renderizar_pdf_f045(request, relacao_id, salvar_pdf=False):
    relacao = get_object_or_404(RelacaoMateriaPrima, pk=relacao_id)
    f045 = relacao.f045
    rolos = relacao.rolos.all()

    logo_path = os.path.join(settings.STATIC_ROOT, "img", "logo.png")
    seguranca_path = os.path.join(settings.STATIC_ROOT, "img", "seguranca.png")

    logo_url = f"file://{logo_path}"
    seguranca_url = f"file://{seguranca_path}"

    # Recuperar norma, composição e faixa de tração
    try:
        norma = NormaTecnica.objects.get(nome_norma=relacao.materia_prima.norma)
        composicao = NormaComposicaoElemento.objects.filter(
            norma=norma,
            tipo_abnt=relacao.materia_prima.tipo_abnt
        ).first()

        bitola = (
            relacao.materia_prima.bitola.replace(",", ".")
            if relacao.materia_prima.bitola
            else None
        )
        bitola_float = float(bitola) if bitola else None

        norma_tracao = (
        NormaTracao.objects.filter(
            norma=norma,
            tipo_abnt=relacao.materia_prima.tipo_abnt,
            bitola_minima__lte=bitola_float,
            bitola_maxima__gte=bitola_float,
        ).first()
        if bitola_float
        else None
    )

    except (
        NormaTecnica.DoesNotExist,
        NormaComposicaoElemento.DoesNotExist,
        ValueError,
    ):
        composicao = None
        norma_tracao = None

    # Composição Química
    encontrados = []
    if composicao:
        elementos = [
            ("C", composicao.c_min, composicao.c_max, getattr(f045, "c_user", None)),
            (
                "Mn",
                composicao.mn_min,
                composicao.mn_max,
                getattr(f045, "mn_user", None),
            ),
            (
                "Si",
                composicao.si_min,
                composicao.si_max,
                getattr(f045, "si_user", None),
            ),
            ("P", composicao.p_min, composicao.p_max, getattr(f045, "p_user", None)),
            ("S", composicao.s_min, composicao.s_max, getattr(f045, "s_user", None)),
            (
                "Cr",
                composicao.cr_min,
                composicao.cr_max,
                getattr(f045, "cr_user", None),
            ),
            (
                "Ni",
                composicao.ni_min,
                composicao.ni_max,
                getattr(f045, "ni_user", None),
            ),
            (
                "Cu",
                composicao.cu_min,
                composicao.cu_max,
                getattr(f045, "cu_user", None),
            ),
            (
                "Al",
                composicao.al_min,
                composicao.al_max,
                getattr(f045, "al_user", None),
            ),
        ]
        for sigla, vmin, vmax, valor in elementos:
            try:
                val = (
                    Decimal(str(valor).replace(",", ".")) if valor is not None else None
                )
                ok = (
                    vmin <= val <= vmax
                    if val is not None and vmin is not None and vmax is not None
                    else False
                )
            except:
                val = valor
                ok = False
            encontrados.append(
                {"sigla": sigla, "min": vmin, "max": vmax, "valor": val, "ok": ok}
            )

   # Assinatura
    usuario = request.user
    assinatura_nome = usuario.get_full_name() or usuario.username
    assinatura_email = usuario.email
    assinatura_data = localtime(now()).strftime("%d/%m/%Y %H:%M:%S")

    # Se for salvar, atualiza campos no banco
    if salvar_pdf:
        f045.assinatura_nome = assinatura_nome
        f045.assinatura_cn = assinatura_email
        f045.data_assinatura = localtime(now())
        f045.save(update_fields=["assinatura_nome", "assinatura_cn", "data_assinatura"])   

    context = {
        "obj": f045,
        "rolos": rolos,
        "relacao": relacao,
        "encontrados": encontrados,
        "norma_tracao": norma_tracao,
        "logo_url": logo_url,
        "seguranca_url": seguranca_url,
        "data_atual": date.today().strftime("%d/%m/%Y"),
        "assinatura_nome": assinatura_nome,
        "assinatura_email": assinatura_email,
        "assinatura_data": assinatura_data,
    }

    html_string = render_to_string("f045/f045_pdf.html", context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri("/"))
    pdf_bytes = html.write_pdf()

    if salvar_pdf:
        filename = f"F045_Relatorio_{f045.nro_relatorio}.pdf"
        f045.pdf.save(filename, ContentFile(pdf_bytes))
        return filename  # ⚠️ Retorna o nome do arquivo!

    else:
        return HttpResponse(pdf_bytes, content_type="application/pdf")