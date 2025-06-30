from django.db import models
from django.utils import timezone
from portaria.models import AtrasoSaida


class BancoHoras(models.Model):
    """
    Registra o controle de banco de horas de um funcionário em um determinado dia,
    incluindo horas extras, saldo e ocorrências relacionadas.
    """

    funcionario = models.ForeignKey(
        "Funcionario",
        on_delete=models.CASCADE,
        related_name="banco_horas",
        verbose_name="Funcionário"
    )
    data = models.DateField(
        default=timezone.now,
        verbose_name="Data"
    )
    horas_trabalhadas = models.DurationField(
        null=True,
        blank=True,
        verbose_name="Horas Trabalhadas"
    )
    observacao = models.TextField(
        blank=True,
        verbose_name="Observação"
    )
    he_50 = models.BooleanField(
        default=False,
        verbose_name="Hora Extra 50%"
    )
    he_100 = models.BooleanField(
        default=False,
        verbose_name="Hora Extra 100%"
    )

    ocorrencia = models.ForeignKey(
        AtrasoSaida,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="banco_relacionado",
        verbose_name="Ocorrência (Atraso/Saída)"
    )
    saldo_horas = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Saldo (h)",
        help_text="Horas positivas ou negativas do dia"
    )

    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )

    def __str__(self):
        return f"{self.funcionario} - {self.data.strftime('%d/%m/%Y')}"

    class Meta:
        ordering = ['-data']
        verbose_name_plural = "Banco de Horas"
