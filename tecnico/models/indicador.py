# tecnico/models/indicadores.py
from django.db import models

class IndicadorTecnicoRegistroMensal(models.Model):
    INDICADORES_CHOICES = [
        ("5.1", "Cumprimento de Prazo de Desenvolvimento"),
        # Futuramente: ("5.2", "Outro Indicador Técnico"),
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
        verbose_name = "Registro de Indicador Técnico"
        verbose_name_plural = "Registros de Indicadores Técnicos"

    def __str__(self):
        tag = f"M{self.mes}" if self.mes else f"T{self.trimestre}"
        return f"{self.indicador} - {self.ano}/{tag}"
