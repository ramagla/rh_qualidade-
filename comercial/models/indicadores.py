from django.db import models

class IndicadorComercialRegistroMensal(models.Model):
    INDICADORES_CHOICES = [
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
