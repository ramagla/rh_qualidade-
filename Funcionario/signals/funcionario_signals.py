from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.timezone import now

from Funcionario.models import Funcionario, HistoricoCargo, JobRotationEvaluation


@receiver(post_save, sender=JobRotationEvaluation)
def atualizar_cargo_funcionario(sender, instance, **kwargs):
    """
    Atualiza o cargo do funcionário caso a avaliação do RH seja 'Apto'.
    """
    if instance.avaliacao_rh == "Apto" and instance.nova_funcao:
        funcionario = instance.funcionario
        funcionario.cargo_atual = instance.nova_funcao
        funcionario.save()


@receiver(pre_save, sender=Funcionario)
def criar_historico_cargo(sender, instance, **kwargs):
    """
    Cria um histórico de cargo sempre que o cargo do funcionário for alterado.
    """
    if instance.pk:
        funcionario_antigo = Funcionario.objects.get(pk=instance.pk)
        if funcionario_antigo.cargo_atual != instance.cargo_atual:
            HistoricoCargo.objects.create(
                funcionario=instance,
                cargo=instance.cargo_atual,
                data_atualizacao=now(),
            )
