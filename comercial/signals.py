from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import IntegrityError
from comercial.models import OrdemDesenvolvimento, Item
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=OrdemDesenvolvimento)
def atualizar_item_a_partir_da_od(sender, instance, **kwargs):
    """
    Quando a OD é salva:
    - Se existir um 'codigo_brasmol', atualiza o 'codigo' do Item
    - E muda o tipo_item de 'Cotacao' para 'Corrente'
    """
    item = instance.item
    novo_codigo = instance.codigo_brasmol

    if not novo_codigo:
        return

    if item.codigo == novo_codigo and item.tipo_item == "Corrente":
        return  # já atualizado, nada a fazer

    # Impede duplicação
    if Item.objects.exclude(pk=item.pk).filter(codigo=novo_codigo).exists():
        logger.warning(f"❌ Código '{novo_codigo}' já existe. Não foi possível atualizar o Item #{item.pk}")
        return

    try:
        item.codigo = novo_codigo
        item.tipo_item = "Corrente"  # <- mudança automática
        item.full_clean()
        item.save()
        logger.info(f"✅ Código e tipo do Item #{item.pk} atualizados com sucesso.")
    except IntegrityError as e:
        logger.error(f"Erro ao salvar Item #{item.pk}: {e}")
