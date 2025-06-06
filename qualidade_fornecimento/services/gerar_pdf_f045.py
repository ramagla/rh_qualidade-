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

    logo_path = os.path.join(settings.STATIC_ROOT, "img", "logo.png")
    seguranca_path = os.path.join(settings.STATIC_ROOT, "img", "seguranca.png")

    logo_url = f"file://{logo_path}"
    seguranca_url = f"file://{seguranca_path}"


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

    campos_quimicos = [
    ("C", "Carbono"),
    ("Mn", "Manganês"),
    ("Si", "Silício"),
    ("P", "Fósforo"),
    ("S", "Enxofre"),
    ("Cr", "Cromo"),
    ("Ni", "Níquel"),
    ("Cu", "Cobre"),
    ("Al", "Alumínio"),
]

    encontrados = []

    for sigla, nome in campos_quimicos:
        # Se composicao existir, pega min e max — senão, None
        vmin = getattr(composicao, f"{sigla.lower()}_min", None) if composicao else None
        vmax = getattr(composicao, f"{sigla.lower()}_max", None) if composicao else None
        valor = getattr(f045, f"{sigla.lower()}_user", None)

        try:
            val = Decimal(str(valor).replace(",", ".")) if valor is not None else None
            ok = (vmin == 0 and vmax == 0) or (val is not None and vmin is not None and vmax is not None and vmin <= val <= vmax)
            if vmin is None or vmax is None:
                ok = True  # Se não tem limites, considera aprovado
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

    return os.path.basename(f045.pdf.name)  # só o nome do arquivo