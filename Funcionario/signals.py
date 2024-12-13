from django.db.models.signals import m2m_changed,post_save
from django.dispatch import receiver
from .models import Treinamento, JobRotationEvaluation, Funcionario

@receiver(m2m_changed, sender=Treinamento.funcionarios.through)
def atualizar_escolaridade_funcionario(sender, instance, action, reverse, pk_set, **kwargs):
    """
    Atualiza a escolaridade dos funcionários associados ao treinamento quando
    há alterações na relação Many-to-Many.
    """
    if action == "post_add" and instance.status == 'concluido' and instance.categoria in ['tecnico', 'graduacao', 'pos-graduacao', 'mestrado', 'doutorado']:
        for funcionario_id in pk_set:
            funcionario = instance.funcionarios.get(pk=funcionario_id)
            funcionario.atualizar_escolaridade()
            funcionario.refresh_from_db()  # Recarrega o objeto do banco após salvar

@receiver(post_save, sender=JobRotationEvaluation)
def atualizar_cargo_funcionario(sender, instance, **kwargs):
    """
    Atualiza o cargo do funcionário caso a avaliação do RH seja 'Apto'.
    """
    if instance.avaliacao_rh == "Apto" and instance.nova_funcao:
        funcionario = instance.funcionario
        funcionario.cargo_atual = instance.nova_funcao  # Atualiza o cargo atual
        funcionario.save()  # Salva as alterações no banco
