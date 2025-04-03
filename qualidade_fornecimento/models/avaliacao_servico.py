from django.db import models
from .fornecedor import FornecedorQualificado  # ou use 'from qualidade_fornecimento.models import Fornecedor'

class AvaliacaoFornecedorServico(models.Model):
    CLASSIFICACAO_CHOICES = [
        ("A - Qualificado", "A - Qualificado"),
        ("B - Qualificado Condicionalmente", "B - Qualificado Condicionalmente"),
        ("C - Não Qualificado", "C - Não Qualificado"),
    ]

    fornecedor = models.ForeignKey(FornecedorQualificado, on_delete=models.CASCADE)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    pontuacao = models.DecimalField("Pontuação (score)", max_digits=4, decimal_places=2)
    iqs = models.DecimalField("IQS", max_digits=4, decimal_places=2, blank=True, null=True)
    ip = models.DecimalField("Pontualidade - IP", max_digits=4, decimal_places=2)
    iqf = models.DecimalField("Qualidade - IQF", max_digits=4, decimal_places=2)
    iqg = models.DecimalField("IQG - Índice Global", max_digits=4, decimal_places=2, blank=True, null=True)
    classificacao = models.CharField(max_length=50, choices=CLASSIFICACAO_CHOICES, blank=True)
    mes_referencia = models.CharField(max_length=10)
    ano_referencia = models.CharField(max_length=4)

    def calcular_iqg(self):
        self.iqs = round(0.2 * self.pontuacao, 2)
        self.iqg = round(self.ip + self.iqf + self.iqs, 2)

    def classificar(self):
        if self.iqg <= 0.49:
            self.classificacao = "C - Não Qualificado"
        elif self.iqg >= 0.75:
            self.classificacao = "A - Qualificado"
        else:
            self.classificacao = "B - Qualificado Condicionalmente"

    def save(self, *args, **kwargs):
        self.calcular_iqg()
        self.classificar()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.fornecedor.razao_social} (Serviço Externo) - {self.mes_referencia}/{self.ano_referencia}"
