from django.db import models
from .fornecedor import FornecedorQualificado

class AnaliseRiscoPreliminar(models.Model):
    fornecedor = models.ForeignKey(FornecedorQualificado, on_delete=models.CASCADE)
    tipo_fornecedor = models.CharField(max_length=100, blank=True)

    criterio_a = models.PositiveIntegerField("Critério A")
    criterio_b = models.PositiveIntegerField("Critério B")
    criterio_c = models.PositiveIntegerField("Critério C")
    criterio_d = models.PositiveIntegerField("Critério D")
    criterio_e = models.PositiveIntegerField("Critério E")
    criterio_f = models.PositiveIntegerField("Critério F")

    media_risco = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    classificacao_risco = models.CharField(max_length=50, blank=True)

    auditoria_segunda_parte = models.BooleanField(default=False)
    eficaz = models.CharField(max_length=100, blank=True, help_text="Resultado da análise ou ação corretiva")
    data_realizada = models.DateField("Data da última análise", blank=True, null=True)
    data_planejada = models.DateField("Data da próxima análise", blank=True, null=True)

    def calcular_risco(self):
        soma = sum([
            self.criterio_a,
            self.criterio_b,
            self.criterio_c,
            self.criterio_d,
            self.criterio_e,
            self.criterio_f
        ])
        self.media_risco = round(soma / 6, 2)

        if self.media_risco >= 4:
            self.classificacao_risco = "Alto"
        elif self.media_risco >= 2.5:
            self.classificacao_risco = "Médio"
        else:
            self.classificacao_risco = "Baixo"

    def save(self, *args, **kwargs):
        self.calcular_risco()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Risco {self.fornecedor.razao_social} - {self.classificacao_risco}"
