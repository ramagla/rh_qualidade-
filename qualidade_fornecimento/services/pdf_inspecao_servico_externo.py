from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils.timezone import now, localtime
from weasyprint import HTML
from datetime import date


def gerar_pdf_inspecao_servico_externo(servico):
    """
    Gera o PDF da inspeção de serviço externo com dados do serviço + inspeção
    e salva no campo `pdf` (sem salvar fisicamente em disco).
    """

    dominio = "http://127.0.0.1:8000"  # Em produção, usar request.build_absolute_uri
    logo_url = dominio + static("logo.png")

    if not hasattr(servico, 'inspecao'):
        return None  # Não gera se não existir inspeção vinculada

    inspecao = servico.inspecao

    # 🔐 Busca o usuário associado (via middleware ou contexto, ou manualmente atribuído)
    usuario = getattr(servico, "_usuario", None)
    if not usuario:
        from django.contrib.auth.models import User
        usuario = User.objects.first()

    assinatura_nome = usuario.get_full_name() or usuario.username
    assinatura_email = usuario.email
    assinatura_data = localtime(now()).strftime("%d/%m/%Y %H:%M:%S")

    context = {
        "servico": servico,
        "inspecao": inspecao,
        "logo_url": logo_url,
        "data_atual": date.today().strftime("%d/%m/%Y"),
        "assinatura_nome": assinatura_nome,
        "assinatura_email": assinatura_email,
        "assinatura_data": assinatura_data,
    }

    # 🧾 Renderiza o HTML e converte em PDF
    html_string = render_to_string("inspecao_servico_externo/inspecao_servico_externo_pdf.html", context)
    pdf_io = BytesIO()
    HTML(string=html_string, base_url=dominio).write_pdf(target=pdf_io)
    pdf_io.seek(0)

    # 📎 Define o nome do arquivo
    filename = f"INSPECAO_SERVICO_{servico.pedido}.pdf"

    # 💾 Salva no campo FileField, sem gravar fisicamente no disco
    servico.inspecao.pdf.save(
        filename,
        InMemoryUploadedFile(pdf_io, None, filename, 'application/pdf', pdf_io.getbuffer().nbytes, None),
        save=True
    )

    return servico.inspecao.pdf.url
