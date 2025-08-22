# tecnico/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models.roteiro import RoteiroProducao, RoteiroRevisao

def _sync_revisao_do_roteiro(roteiro: RoteiroProducao) -> None:
    """
    Define roteiro.revisao = numero_revisao da última revisão 'ativa'
    (ordenada por data_revisao desc, id desc). Se não houver revisão ativa,
    zera para string vazia (ou '0', se preferir).
    """
    ultima = (
        roteiro.revisoes
        .filter(status="ativo")
        .order_by("-data_revisao", "-id")
        .first()
    )
    novo_valor = ultima.numero_revisao if ultima else ""

    # Evita save desnecessário
    if (roteiro.revisao or "") != (novo_valor or ""):
        RoteiroProducao.objects.filter(pk=roteiro.pk).update(revisao=novo_valor)

@receiver(post_save, sender=RoteiroRevisao)
def sincronizar_revisao_apos_salvar(sender, instance: RoteiroRevisao, **kwargs):
    _sync_revisao_do_roteiro(instance.roteiro)

@receiver(post_delete, sender=RoteiroRevisao)
def sincronizar_revisao_apos_excluir(sender, instance: RoteiroRevisao, **kwargs):
    _sync_revisao_do_roteiro(instance.roteiro)
