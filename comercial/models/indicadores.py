from django.db import models
from django.db import models
from decimal import Decimal

class IndicadorComercialRegistroMensal(models.Model):
    INDICADORES_CHOICES = [
        ("1.1", "Faturamento"),
        ("4.1", "Atendimento do Prazo de Cotação"),
        ("4.2", "Número de Itens Novos Vendidos"),
        ("4.3", "Número de Cotações por Funcionário"),
        ("4.4", "Taxa de Orçamentos Aprovados"),
    ]

    indicador = models.CharField(max_length=10, choices=INDICADORES_CHOICES)
    ano = models.IntegerField()
    mes = models.IntegerField(null=True, blank=True)
    trimestre = models.IntegerField(null=True, blank=True)

    valor = models.FloatField()
    media = models.FloatField()
    meta = models.FloatField()
    total_realizados = models.IntegerField(default=0)
    total_aprovados = models.IntegerField(default=0)
    comentario = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("indicador", "ano", "mes", "trimestre")
        verbose_name = "Registro de Indicador Comercial"
        verbose_name_plural = "Registros de Indicadores Comerciais"

    def __str__(self):
        tag = f"M{self.mes}" if self.mes else f"T{self.trimestre}"
        return f"{self.indicador} - {self.ano}/{tag}"


class MetaFaturamento(models.Model):
    ANO_MINIMO = 2000
    ANO_MAXIMO = 2100

    ano = models.PositiveIntegerField()
    mes = models.PositiveSmallIntegerField(choices=[
        (1, "Jan"), (2, "Fev"), (3, "Mar"), (4, "Abr"),
        (5, "Mai"), (6, "Jun"), (7, "Jul"), (8, "Ago"),
        (9, "Set"), (10, "Out"), (11, "Nov"), (12, "Dez"),
    ])
    valor = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        unique_together = (("ano", "mes"),)
        ordering = ["-ano", "mes"]
        verbose_name = "Meta de Faturamento"
        verbose_name_plural = "Metas de Faturamento"

    def __str__(self):
        return f"{self.get_mes_display()}/{self.ano} - R$ {self.valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")