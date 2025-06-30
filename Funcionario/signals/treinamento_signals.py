from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from Funcionario.models import Treinamento


@receiver(m2m_changed, sender=Treinamento.funcionarios.through)
def atualizar_escolaridade_funcionario(sender, instance, action, reverse, pk_set, **kwargs):
    """
    Atualiza a escolaridade dos funcionários associados ao treinamento quando
    há alterações na relação Many-to-Many.
    """
    if (
        action == "post_add"
        and instance.status == "concluido"
        and instance.categoria in ["tecnico", "graduacao", "pos-graduacao", "mestrado", "doutorado"]
    ):
        for funcionario_id in pk_set:
            funcionario = instance.funcionarios.get(pk=funcionario_id)
            funcionario.atualizar_escolaridade()
            funcionario.refresh_from_db()
