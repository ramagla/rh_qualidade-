# qualidade_fornecimento/tasks.py
import os
from celery import shared_task
from qualidade_fornecimento.services.gerar_pdf_f045 import gerar_pdf_e_salvar
from qualidade_fornecimento.models.f045 import RelatorioF045

from django.core.files import File

from rh_qualidade import settings

@shared_task
def gerar_pdf_f045_background(f045_id: int):
    f045 = RelatorioF045.objects.get(pk=f045_id)

    # 1) Gera bytes e salva no disco
    caminho = gerar_pdf_e_salvar(f045)  
    #    — modificar gerar_pdf_e_salvar para retornar o caminho absoluto ou relativo

    # 2) Agora abra e salve no field 'pdf'
    full_path = os.path.join(settings.MEDIA_ROOT, caminho.lstrip("/"))
    with open(full_path, "rb") as fp:
        f045.pdf.save(os.path.basename(full_path), File(fp), save=True)


from qualidade_fornecimento.services.pdf_inspecao_servico_externo import gerar_pdf_inspecao_servico_externo
from qualidade_fornecimento.models.controle_servico_externo import ControleServicoExterno

@shared_task
def gerar_pdf_inspecao_servico_background(servico_id: int):
    """
    Gera e salva o PDF da inspeção de serviço externo em segundo plano.
    """
    servico = ControleServicoExterno.objects.get(pk=servico_id)

    # 1) Gera e salva via service
    caminho = gerar_pdf_inspecao_servico_externo(servico)  # Precisa que o service retorne o caminho do arquivo

    if caminho:
        # 2) Agora reabre para salvar no campo .pdf
        full_path = os.path.join(settings.MEDIA_ROOT, caminho.lstrip("/"))

        if os.path.exists(full_path):
            with open(full_path, "rb") as fp:
                servico.inspecao.pdf.save(os.path.basename(full_path), File(fp), save=True)