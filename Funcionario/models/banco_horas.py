from django.db import models
from django.conf import settings
from django.utils import timezone
from portaria.models import AtrasoSaida

class BancoHoras(models.Model):
    funcionario = models.ForeignKey("Funcionario", on_delete=models.CASCADE, related_name="banco_horas")
    data = models.DateField(default=timezone.now)   
    horas_trabalhadas = models.DurationField(null=True, blank=True)
    observacao = models.TextField(blank=True)
    he_50 = models.BooleanField(default=False)
    he_100 = models.BooleanField(default=False)

    ocorrencia = models.ForeignKey(AtrasoSaida, null=True, blank=True, on_delete=models.SET_NULL, related_name="banco_relacionado")
    saldo_horas = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Saldo (h)",
        help_text="Horas positivas ou negativas do dia"
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.funcionario} - {self.data}"
