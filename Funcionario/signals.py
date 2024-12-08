from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Treinamento

@receiver(post_save, sender=Treinamento)
def atualizar_escolaridade_funcionario(sender, instance, **kwargs):
    for funcionario in instance.funcionarios.all():
        funcionario.atualizar_escolaridade()
