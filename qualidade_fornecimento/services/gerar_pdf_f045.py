import os
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.templatetags.static import static
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

    dominio = "http://127.0.0.1:8000"
    logo_url = dominio + static("logo.png")
    seguranca_url = dominio + static("seguranca.png")

    try:
        norma = NormaTecnica.objects.get(nome_norma=relacao.materia_prima.norma)
        composicao = NormaComposicaoElemento.objects.get(
            norma=norma, tipo_abnt=relacao.materia_prima.tipo_abnt
        )
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

    encontrados = []
    if composicao:
        elementos = [
            ("C", "Carbono", composicao.c_min, composicao.c_max, getattr(f045, "c_user", None)),
            ("Mn", "Manganês", composicao.mn_min, composicao.mn_max, getattr(f045, "mn_user", None)),
            ("Si", "Silício", composicao.si_min, composicao.si_max, getattr(f045, "si_user", None)),
            ("P", "Fósforo", composicao.p_min, composicao.p_max, getattr(f045, "p_user", None)),
            ("S", "Enxofre", composicao.s_min, composicao.s_max, getattr(f045, "s_user", None)),
            ("Cr", "Cromo", composicao.cr_min, composicao.cr_max, getattr(f045, "cr_user", None)),
            ("Ni", "Níquel", composicao.ni_min, composicao.ni_max, getattr(f045, "ni_user", None)),
            ("Cu", "Cobre", composicao.cu_min, composicao.cu_max, getattr(f045, "cu_user", None)),
            ("Al", "Alumínio", composicao.al_min, composicao.al_max, getattr(f045, "al_user", None)),
        ]
        for sigla, nome, vmin, vmax, valor in elementos:
            try:
                val = Decimal(str(valor).replace(",", ".")) if valor is not None else None
                ok = (vmin == 0 and vmax == 0) or (val is not None and vmin is not None and vmax is not None and vmin <= val <= vmax)
            except Exception:
                val = valor
                ok = False

            encontrados.append({
                "sigla": sigla,
                "nome_elemento": nome,
                "min": vmin,
                "max": vmax,
                "valor": val,
                "ok": ok,
            })

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
    html = HTML(string=html_string, base_url=dominio)
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

    return f045.pdf.url
