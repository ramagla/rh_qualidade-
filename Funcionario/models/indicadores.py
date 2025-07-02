# Funcionario/models/indicadores.py

from django.db import models

class FechamentoIndicadorTreinamento(models.Model):
    ano = models.IntegerField()
    trimestre = models.IntegerField()  # esse campo é obrigatório
    valor_t1 = models.FloatField(null=True, blank=True)
    valor_t2 = models.FloatField(null=True, blank=True)
    valor_t3 = models.FloatField(null=True, blank=True)
    valor_t4 = models.FloatField(null=True, blank=True)
    media = models.FloatField(null=True, blank=True)
    data_fechamento = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("ano", "trimestre")
