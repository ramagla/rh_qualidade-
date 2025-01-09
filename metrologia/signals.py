from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Calibracao, TabelaTecnica, CalibracaoDispositivo, Dispositivo


import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Calibracao)
def atualizar_data_ultima_calibracao(sender, instance, **kwargs):
    logger.info(f"Sinal acionado para Calibracao ID {instance.id}")
    if instance.status == 'Aprovado' and instance.data_calibracao:
        tabela_tecnica = instance.codigo
        if not tabela_tecnica.data_ultima_calibracao or instance.data_calibracao > tabela_tecnica.data_ultima_calibracao:
            tabela_tecnica.data_ultima_calibracao = instance.data_calibracao
            tabela_tecnica.save()
            logger.info(f"Data de última calibração atualizada para: {tabela_tecnica.data_ultima_calibracao}")
        else:
            logger.info("A data da calibração não é mais recente.")
    else:
        logger.info("A calibração não foi aprovada ou não possui data.")

@receiver(post_save, sender=CalibracaoDispositivo)
def atualizar_data_ultima_calibracao_dispositivo(sender, instance, **kwargs):
    """
    Atualiza a data da última calibração no modelo Dispositivo
    quando uma instância de CalibracaoDispositivo é salva.
    """
    if instance.status == 'Aprovado' and instance.data_afericao:
        dispositivo = instance.codigo_dispositivo  # Referência ao dispositivo
        # Atualiza a data somente se for mais recente
        if not dispositivo.data_ultima_calibracao or instance.data_afericao > dispositivo.data_ultima_calibracao:
            dispositivo.data_ultima_calibracao = instance.data_afericao
            dispositivo.save()

