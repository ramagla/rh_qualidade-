import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Calibracao, CalibracaoDispositivo, Dispositivo, TabelaTecnica

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Calibracao)
def atualizar_data_ultima_calibracao(sender, instance, **kwargs):
    logger.info(f"Sinal acionado para Calibracao ID {instance.id}")
    if instance.status == "Aprovado" and instance.data_calibracao:
        tabela_tecnica = instance.codigo
        if (
            not tabela_tecnica.data_ultima_calibracao
            or instance.data_calibracao > tabela_tecnica.data_ultima_calibracao
        ):
            tabela_tecnica.data_ultima_calibracao = instance.data_calibracao
            tabela_tecnica.save()
            logger.info(
                f"Data de última calibração atualizada para: {tabela_tecnica.data_ultima_calibracao}"
            )
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
    if instance.status == "Aprovado" and instance.data_afericao:
        dispositivo = instance.codigo_dispositivo  # Referência ao dispositivo
        # Atualiza a data somente se for mais recente
        if (
            not dispositivo.data_ultima_calibracao
            or instance.data_afericao > dispositivo.data_ultima_calibracao
        ):
            dispositivo.data_ultima_calibracao = instance.data_afericao
            dispositivo.save()



from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils.timezone import now

from metrologia.models.models_calibracao import Calibracao
from metrologia.models.models_calibracao_dispositivo import CalibracaoDispositivo
from metrologia.models.AnaliseCriticaMetrologia import AnaliseCriticaMetrologia

@receiver(post_save, sender=Calibracao)
def criar_analise_critica_instrumento(sender, instance, created, **kwargs):
    if instance.status == "Reprovado":
        equipamento = instance.codigo
        exatidao = equipamento.exatidao_requerida or 0

        if not AnaliseCriticaMetrologia.objects.filter(
            equipamento_instrumento=equipamento,
            tipo='instrumento',
            data_assinatura__isnull=True
        ).exists():
            AnaliseCriticaMetrologia.objects.create(
                equipamento_instrumento=equipamento,
                tipo='instrumento',
                descricao_equipamento=getattr(equipamento, "nome_equipamento", ""),
                modelo=getattr(equipamento, "modelo", ""),
                capacidade_medicao="",
                data_ultima_calibracao=instance.data_calibracao,
                nao_conformidade_detectada=(
                    "Equipamento reprovado na calibração.\n"
                    f"⛔ Valor encontrado (L): {instance.l:.3f}\n"
                    f"✅ Exatidão requerida: {exatidao:.3f}\n"
                    "O valor de L excede a exatidão permitida."
                ),
                usuario=User.objects.filter(is_superuser=True).first(),
            )



from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from metrologia.models import CalibracaoDispositivo, AnaliseCriticaMetrologia


@receiver(post_save, sender=CalibracaoDispositivo)
def criar_analise_critica_dispositivo(sender, instance, created, **kwargs):
    if instance.status == "Reprovado":
        dispositivo = instance.codigo_dispositivo

        if not AnaliseCriticaMetrologia.objects.filter(
            equipamento_dispositivo=dispositivo,
            tipo='dispositivo',
            data_assinatura__isnull=True
        ).exists():

            # 📌 Monta texto com cotas reprovadas
            cotas_reprovadas = []
            for afericao in instance.afericoes.select_related("cota").all():
                if afericao.status == "Reprovado":
                    cota = afericao.cota
                    cotas_reprovadas.append(
                        f"- Cota {cota.numero}: {afericao.valor} (esperado entre {cota.valor_minimo} ~ {cota.valor_maximo})"
                    )

            texto_nc = (
                "Dispositivo reprovado na aferição.\n"
                "⛔ Aferições fora da faixa esperada:\n"
                + "\n".join(cotas_reprovadas)
                if cotas_reprovadas else
                "Dispositivo reprovado na aferição. (Detalhes não disponíveis)"
            )

            AnaliseCriticaMetrologia.objects.create(
                equipamento_dispositivo=dispositivo,
                tipo='dispositivo',
                descricao_equipamento=getattr(dispositivo, "nome_dispositivo", ""),
                modelo=getattr(dispositivo, "modelo", ""),
                capacidade_medicao=getattr(dispositivo, "capacidade_medicao", ""),
                data_ultima_calibracao=instance.data_afericao,
                nao_conformidade_detectada=texto_nc,
                usuario=User.objects.filter(is_superuser=True).first(),
            )
