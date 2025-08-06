from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import IntegrityError
from comercial.models import OrdemDesenvolvimento, Item
from comercial.models.precalculo import AnaliseComercial
from comercial.models.ordem_desenvolvimento import OrdemDesenvolvimento
from django.db import transaction
from django.utils.timezone import now
import logging

from django.db import models

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



@receiver(post_save, sender=AnaliseComercial)
def criar_ordem_desenvolvimento_ao_aprovar(sender, instance, created, **kwargs):
    try:
        if instance.status != "aprovado":
            return

        precalc = instance.precalculo

        # Já possui OD?
        if OrdemDesenvolvimento.objects.filter(precalculo=precalc).exists():
            return

        item = instance.item
        cliente = item.cliente

        # Garante atomicidade
        with transaction.atomic():
            ultimo_numero = OrdemDesenvolvimento.objects.aggregate(
                models.Max("numero")
            )["numero__max"] or 99

            od = OrdemDesenvolvimento.objects.create(
                numero=ultimo_numero + 1,
                precalculo=precalc,
                item=item,
                cliente=cliente,
                razao="novo",  # Valor padrão, pode ser ajustado
                metodologia_aprovacao=instance.metodologia,
                qtde_amostra=None,
                automotivo_oem=item.automotivo_oem,
                comprador=cliente.comprador if hasattr(cliente, "comprador") else "",
                requisito_especifico=item.requisito_especifico,
                item_seguranca=item.item_seguranca,
                codigo_desenho=item.codigo_desenho,
                revisao=item.revisao,
                data_revisao=item.data_revisao,
                assinatura_comercial_nome=instance.assinatura_nome,
                assinatura_comercial_email=instance.assinatura_cn,
                assinatura_comercial_data=instance.data_assinatura or now(),
            )

            logger.info(f"✅ OD #{od.numero} criada automaticamente para o Pré-Cálculo #{precalc.pk}")
    except Exception as e:
        logger.error(f"❌ Erro ao criar OD automática: {e}")

from datetime import datetime


@receiver(post_save, sender=AnaliseComercial)
def criar_ordem_amostra_ao_solicitar(sender, instance, created, **kwargs):
    try:
        if instance.status != "amostras":
            return

        precalc = instance.precalculo
        if not precalc or OrdemDesenvolvimento.objects.filter(precalculo=precalc).exists():
            return

        item = instance.item
        cliente = item.cliente

        with transaction.atomic():
            hoje_str = datetime.now().strftime("%Y%m%d")

            # Gera código da amostra
            sufixo_amostra = 1
            codigo_amostra = f"{hoje_str}-{sufixo_amostra:02d}"
            while OrdemDesenvolvimento.objects.filter(codigo_amostra=codigo_amostra).exists():
                sufixo_amostra += 1
                codigo_amostra = f"{hoje_str}-{sufixo_amostra:02d}"

            ultimo_numero = OrdemDesenvolvimento.objects.aggregate(
                models.Max("numero")
            )["numero__max"] or 99

            OrdemDesenvolvimento.objects.create(
                numero=ultimo_numero + 1,
                precalculo=precalc,
                item=item,
                cliente=cliente,
                razao="amostras",
                amostra="sim",
                codigo_amostra=codigo_amostra,  # ✅ Apenas este campo gerado
                metodologia_aprovacao=instance.metodologia,
                qtde_amostra=300,
                automotivo_oem=item.automotivo_oem,
                comprador=getattr(cliente, "comprador", ""),
                requisito_especifico=item.requisito_especifico,
                item_seguranca=item.item_seguranca,
                codigo_desenho=item.codigo_desenho,
                revisao=item.revisao,
                data_revisao=item.data_revisao,
                assinatura_comercial_nome=instance.assinatura_nome,
                assinatura_comercial_email=instance.assinatura_cn,
                assinatura_comercial_data=instance.data_assinatura or now(),
            )
    except Exception as e:
        logger.error(f"❌ Erro ao criar OD para amostras: {e}")





from comercial.models.viabilidade import ViabilidadeAnaliseRisco  # já que está fora do arquivo do modelo
from comercial.models.precalculo import AnaliseComercial
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
import logging

@receiver(post_save, sender=AnaliseComercial)
def criar_viabilidade_automatica(sender, instance, created, **kwargs):
    try:
        if instance.status != "aprovado":
            return

        precalc = instance.precalculo
        item = instance.item

        if not item.automotivo_oem:
            return

        if ViabilidadeAnaliseRisco.objects.filter(precalculo=precalc).exists():
            return  # já existe viabilidade

        with transaction.atomic():
            ultima_viabilidade = ViabilidadeAnaliseRisco.objects.aggregate(
                models.Max("numero")
            )["numero__max"] or 99

            viabilidade = ViabilidadeAnaliseRisco.objects.create(
                numero=ultima_viabilidade + 1,
                precalculo=precalc,
                cliente=item.cliente,
                requisito_especifico=item.requisito_especifico,
                automotivo_oem=item.automotivo_oem,
                item_seguranca=item.item_seguranca,
                codigo_desenho=item.codigo_desenho,
                revisao=item.revisao,
                data_desenho=item.data_revisao,
                codigo_brasmol=item.codigo,

                # Valores padrão (ou ajuste caso adicione depois)
                produto_definido=False,
                risco_comercial=False,

                assinatura_comercial_nome=instance.assinatura_nome,
                assinatura_comercial_departamento="COMERCIAL",
                assinatura_comercial_data=instance.data_assinatura,
                conclusao_comercial=instance.conclusao,
                consideracoes_comercial=instance.consideracoes,
                criado_por=instance.usuario
            )


            logger.info(f"✅ Viabilidade #{viabilidade.numero} criada automaticamente para o Pré-Cálculo #{precalc.pk}")
    except Exception as e:
        logger.error(f"❌ Erro ao criar Viabilidade automática: {e}")


from django.db.models.signals import post_save
from django.dispatch import receiver
from comercial.models import OrdemDesenvolvimento, Item
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=OrdemDesenvolvimento)
def atualizar_item_com_codigos_da_od(sender, instance, **kwargs):
    try:
        item = instance.item
        atualizado = False

        # Atualiza o código (código interno) do item com base no código Bras-Mol
        if instance.codigo_brasmol and item.codigo != instance.codigo_brasmol:
            if not Item.objects.exclude(pk=item.pk).filter(codigo=instance.codigo_brasmol).exists():
                item.codigo = instance.codigo_brasmol
                atualizado = True
            else:
                logger.warning(f"❌ Código Bras-Mol '{instance.codigo_brasmol}' já está em uso por outro item.")

        # Atualiza o campo codigo_amostra no item
        if instance.codigo_amostra and item.codigo_amostra != instance.codigo_amostra:
            if not Item.objects.exclude(pk=item.pk).filter(codigo_amostra=instance.codigo_amostra).exists():
                item.codigo_amostra = instance.codigo_amostra
                atualizado = True
            else:
                logger.warning(f"❌ Código de amostra '{instance.codigo_amostra}' já está em uso por outro item.")

        if atualizado:
            item.full_clean()
            item.save()
            logger.info(f"✅ Item #{item.pk} atualizado com sucesso com base na OD #{instance.pk}")
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar o item via OD #{instance.pk}: {e}")



