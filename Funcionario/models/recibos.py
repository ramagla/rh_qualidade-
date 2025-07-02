from django.db import models
from django.contrib.auth.models import User
from Funcionario.models import Funcionario


class ReciboPagamento(models.Model):
    """
    Representa um recibo de pagamento de um funcionário em determinado mês, contendo
    valores totais, descontos e líquidos, além do arquivo PDF anexado.
    """

    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.CASCADE,
        related_name='recibos_pagamento',
        verbose_name="Funcionário"
    )
    nome_colaborador = models.CharField(
        max_length=150,
        verbose_name="Nome do Colaborador"
    )  # redundância para facilitar filtros e relatórios
    mes_referencia = models.DateField(
        verbose_name="Mês de Referência"
    )
    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor Total"
    )
    valor_descontos = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor dos Descontos"
    )
    valor_liquido = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor Líquido"
    )
    arquivo_pdf = models.FileField(
        upload_to="recibos_pagamento/",
        verbose_name="Arquivo PDF"
    )
    data_importacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Importação"
    )

    class Meta:
        verbose_name = "Recibo de Pagamento"
        verbose_name_plural = "Recibos de Pagamento"
        ordering = ["-mes_referencia", "nome_colaborador"]

    def __str__(self):
        return f"{self.nome_colaborador} - {self.mes_referencia.strftime('%m/%Y')}"
