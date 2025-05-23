from django.db import models
from django.utils.timezone import now

class RegistroConsumoAgua(models.Model):
    data = models.DateField(default=now, verbose_name="Data")
    leitura_inicial = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Leitura Inicial (m³)")
    leitura_final = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Leitura Final (m³)")
    observacao = models.TextField(blank=True, null=True, verbose_name="Observação")

    class Meta:
        verbose_name = "Registro de Consumo de Água"
        verbose_name_plural = "Registros de Consumo de Água"
        ordering = ["-data"]

    def consumo(self):
        return round(self.leitura_final - self.leitura_inicial, 2)

    def __str__(self):
        return f"{self.data} - {self.consumo()} m³"
