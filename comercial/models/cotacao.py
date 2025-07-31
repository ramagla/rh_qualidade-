from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field

from .clientes import Cliente

User = get_user_model()


class AuditModel(models.Model):
    """Campos de auditoria / assinatura em todos os registros."""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="%(class)s_created", verbose_name="Criado por"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="%(class)s_updated", verbose_name="Atualizado por"
    )

    class Meta:
        abstract = True


class Cotacao(AuditModel):
    TIPO_CHOICES = [
        ("Atualização", "Atualização"),
        ("Novo", "Novo"),
    ]
    FRETE_CHOICES = [
        ("CIF", "CIF"),
        ("FOB", "FOB"),
    ]

    data_abertura = models.DateTimeField(
        default=timezone.now,
        verbose_name="Data de Abertura"
    )
    tipo = models.CharField(
        "Tipo de Cotação",
        max_length=12,
        choices=TIPO_CHOICES
    )
    
    responsavel = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name="cotacoes", verbose_name="Responsável"
    )
    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT,
        verbose_name="Cliente"
    )
    frete = models.CharField(
        "Frete",
        max_length=3,
        choices=FRETE_CHOICES
    )
    observacoes = CKEditor5Field(
        "Observações",
        config_name="default",
        blank=True,
        null=True
    )
    # Campos herdados do Cliente, mas editáveis aqui
    cond_pagamento = models.CharField(
        "Condição de Pagamento",
        max_length=100
    )
    icms = models.DecimalField(
        "ICMS (%)",
        max_digits=5,
        decimal_places=2
    )

    validade_proposta = models.PositiveIntegerField(
        "Validade da proposta (dias)",
        default=30,
        help_text="Número de dias de validade da proposta a partir da data de abertura."
    )

    data_envio_proposta = models.DateField(
            "Data de Envio da Proposta",
            null=True, blank=True,
            help_text="Data em que a proposta foi efetivamente gerada/enviada."
        )

    class Meta:
        verbose_name = "Cotação"
        verbose_name_plural = "Cotações"

    @property
    def numero(self):
        """
        Retorna o número da cotação, somando 5000 ao ID interno.
        Assim, a primeira cotação (id=1) terá numero=5001, etc.
        """
        return 5000 + (self.id or 0)

    def __str__(self):
        # exibe o número personalizado em vez de usar apenas o id
        return f"Cotação #{self.numero} – {self.cliente.razao_social}"


