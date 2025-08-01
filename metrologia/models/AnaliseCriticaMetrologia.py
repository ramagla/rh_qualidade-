from django.db import models
from django.contrib.auth.models import User
from django_ckeditor_5.fields import CKEditor5Field

from metrologia.models.models_tabelatecnica import TabelaTecnica
from metrologia.models.models_dispositivos import Dispositivo

class AnaliseCriticaMetrologia(models.Model):
    TIPO_CHOICES = [
        ('instrumento', 'Instrumento'),
        ('dispositivo', 'Dispositivo'),
   ]
    equipamento_instrumento = models.ForeignKey(
        TabelaTecnica, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Equipamento (Instrumento)"
    )
    equipamento_dispositivo = models.ForeignKey(
        Dispositivo, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Equipamento (Dispositivo)"
    )
    descricao_equipamento = models.CharField("Descrição do Equipamento", max_length=255, blank=True)
    tipo = models.CharField(
        max_length=12,
        choices=TIPO_CHOICES,
        verbose_name='Tipo',
        default='instrumento'  # valor da chave (não a descrição)
    )
    modelo = models.CharField("Modelo", max_length=100, blank=True)
    capacidade_medicao = models.CharField("Capacidade de Medição / Resolução", max_length=255, blank=True)
    data_ultima_calibracao = models.DateField("Data da Última Calibração", null=True, blank=True)

    nao_conformidade_detectada = CKEditor5Field("Não Conformidade Detectada")

    compromete_qualidade = models.BooleanField("A não conformidade compromete a qualidade dos produtos?", default=False)
    observacoes_qualidade = CKEditor5Field("Observações (Qualidade)", blank=True, null=True)

    verificar_pecas_processo = models.BooleanField("Há necessidade de verificar as peças em processo e estoque?", default=False)
    observacoes_pecas = CKEditor5Field("Observações (Peças/Estoque)", blank=True, null=True)

    comunicar_cliente = models.BooleanField("Há necessidade de comunicar o cliente?", default=False)
    observacoes_cliente = CKEditor5Field("Observações (Cliente)", blank=True, null=True)

    # Assinatura
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, editable=False)
    assinado_em = models.DateTimeField(auto_now_add=True)
    data_assinatura = models.DateTimeField("Data da assinatura", null=True, blank=True)
    assinatura_nome = models.CharField("Nome da assinatura", max_length=150, null=True, blank=True)
    assinatura_cn = models.CharField("CN da assinatura (email)", max_length=150, null=True, blank=True)

    class Meta:
        verbose_name = "Análise Crítica da Metrologia"
        verbose_name_plural = "Análises Críticas da Metrologia"

    def __str__(self):
        return f"Análise Crítica - {self.pk}"
