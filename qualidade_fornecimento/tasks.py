# qualidade_fornecimento/tasks.py
import os

from celery import shared_task
from django.core.files import File
from django.conf import settings

from qualidade_fornecimento.models.f045 import RelatorioF045
from qualidade_fornecimento.services.gerar_pdf_f045 import gerar_pdf_e_salvar

@shared_task
def gerar_pdf_f045_background(f045_id: int):
    try:
        f045 = RelatorioF045.objects.get(pk=f045_id)
    except RelatorioF045.DoesNotExist:
        print(f"⚠️ Relatório com ID {f045_id} não encontrado. Task abortada.")
        return

    # 1️⃣ Gera o PDF e recebe o nome do arquivo
    nome_arquivo = gerar_pdf_e_salvar(f045)

    # 2️⃣ Monta o path real no disco
    full_path = os.path.join(settings.MEDIA_ROOT, "f045", nome_arquivo)

    # 3️⃣ Salva no campo pdf
    if os.path.exists(full_path):
        with open(full_path, "rb") as fp:
            f045.pdf.save(nome_arquivo, File(fp), save=True)
        print(f"✅ PDF salvo com sucesso: {full_path}")
    else:
        print(f"❌ ERRO: Arquivo PDF não encontrado: {full_path}")



# -----------------------------------------------
# PDF de INSPEÇÃO DE SERVIÇO EXTERNO (F001)
# -----------------------------------------------
from qualidade_fornecimento.models.controle_servico_externo import ControleServicoExterno
from qualidade_fornecimento.services.pdf_inspecao_servico_externo import gerar_pdf_inspecao_servico_externo

@shared_task
def gerar_pdf_inspecao_servico_background(servico_id: int):
    """
    Gera e salva o PDF da inspeção de serviço externo (F001) em segundo plano.
    """
    servico = ControleServicoExterno.objects.get(pk=servico_id)

    # 1) Gera e salva via service — deve retornar o caminho absoluto do PDF
    caminho_absoluto = gerar_pdf_inspecao_servico_externo(servico)

    # 2) Reabre o arquivo e salva no campo FileField (.pdf)
    if caminho_absoluto and os.path.exists(caminho_absoluto):
        with open(caminho_absoluto, "rb") as fp:
            servico.inspecao.pdf.save(os.path.basename(caminho_absoluto), File(fp), save=True)
