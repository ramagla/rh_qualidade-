import os
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils.timezone import localtime, now
from weasyprint import HTML

from qualidade_fornecimento.models.norma import (
    NormaComposicaoElemento,
    NormaTecnica,
    NormaTracao,
)


def gerar_pdf_e_salvar(f045):
    relacao = f045.relacao
    rolos = relacao.rolos.all()

    logo_path = os.path.join(settings.STATIC_ROOT, "img", "logo.png")
    seguranca_path = os.path.join(settings.STATIC_ROOT, "img", "seguranca.png")

    logo_url = f"file://{logo_path}"
    seguranca_url = f"file://{seguranca_path}"

    # Recuperar norma, composicao e faixa de tracao (igual a VIEW)
    try:
        norma = NormaTecnica.objects.get(nome_norma=relacao.materia_prima.norma)
        composicao = NormaComposicaoElemento.objects.filter(
            norma=norma,
            tipo_abnt = f045.tipo_abnt
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

    # Composição Química — gerar sempre (igual à VIEW)
    encontrados = []
    elementos = [
        ("C", composicao.c_min if composicao else None, composicao.c_max if composicao else None, getattr(f045, "c_user", None)),
        ("Mn", composicao.mn_min if composicao else None, composicao.mn_max if composicao else None, getattr(f045, "mn_user", None)),
        ("Si", composicao.si_min if composicao else None, composicao.si_max if composicao else None, getattr(f045, "si_user", None)),
        ("P", composicao.p_min if composicao else None, composicao.p_max if composicao else None, getattr(f045, "p_user", None)),
        ("S", composicao.s_min if composicao else None, composicao.s_max if composicao else None, getattr(f045, "s_user", None)),
        ("Cr", composicao.cr_min if composicao else None, composicao.cr_max if composicao else None, getattr(f045, "cr_user", None)),
        ("Ni", composicao.ni_min if composicao else None, composicao.ni_max if composicao else None, getattr(f045, "ni_user", None)),
        ("Cu", composicao.cu_min if composicao else None, composicao.cu_max if composicao else None, getattr(f045, "cu_user", None)),
        ("Al", composicao.al_min if composicao else None, composicao.al_max if composicao else None, getattr(f045, "al_user", None)),
    ]
    for sigla, vmin, vmax, valor in elementos:
        try:
            val = Decimal(str(valor).replace(",", ".")) if valor is not None else None
            ok = (
                vmin <= val <= vmax
                if val is not None and vmin is not None and vmax is not None
                else False
            )
        except:
            val = valor
            ok = False
        encontrados.append({
            "sigla": sigla,
            "min": vmin,
            "max": vmax,
            "valor": val,
            "ok": ok,
        })

    # Assinatura (igual a VIEW)
    assinatura_nome = f045.usuario.get_full_name() or f045.usuario.username
    assinatura_email = f045.usuario.email
    assinatura_data = localtime(now()).strftime("%d/%m/%Y %H:%M:%S")

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
    html = HTML(string=html_string, base_url=f"file://{settings.STATIC_ROOT}")
    pdf_bytes = html.write_pdf()

    # Caminho e nome do arquivo
    filename = f"F045_Relatorio_{f045.nro_relatorio}.pdf"
    caminho_pasta = os.path.join(settings.MEDIA_ROOT, "f045")
    os.makedirs(caminho_pasta, exist_ok=True)
    caminho_pdf = os.path.join(caminho_pasta, filename)

    # Remove PDF antigo se existir
    if f045.pdf and os.path.exists(f045.pdf.path):
        os.remove(f045.pdf.path)

    # Salva no FileField
    f045.pdf.save(filename, ContentFile(pdf_bytes), save=True)

    return os.path.basename(f045.pdf.name)
