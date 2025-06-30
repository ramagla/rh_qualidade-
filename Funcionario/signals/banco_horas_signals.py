from django.db.models.signals import post_save
from django.dispatch import receiver

from Funcionario.models.banco_horas import BancoHoras
from portaria.models import AtrasoSaida


@receiver(post_save, sender=BancoHoras)
def atualizar_observacao_ocorrencia(sender, instance, **kwargs):
    """
    Atualiza a observação da ocorrência vinculada (de AtrasoSaida)
    com base na observação do BancoHoras.
    """
    ocorrencia_id = getattr(instance, "_ocorrencia_vinculada_id", None)

    if ocorrencia_id and instance.observacao:
        try:
            ocorrencia = AtrasoSaida.objects.get(id=ocorrencia_id)
            ocorrencia.observacao = instance.observacao
            ocorrencia.save()
        except AtrasoSaida.DoesNotExist:
            pass
