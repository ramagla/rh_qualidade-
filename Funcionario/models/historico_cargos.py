from django.db import models

from .cargo import Cargo
from .funcionario import Funcionario


class HistoricoCargo(models.Model):
    """
    Armazena o histórico de cargos ocupados por um funcionário ao longo do tempo.
    """

    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.CASCADE,
        related_name="historico_cargos",
        verbose_name="Funcionário"
    )
    cargo = models.ForeignKey(
        Cargo,
        on_delete=models.CASCADE,
        related_name="historico_cargos",
        verbose_name="Cargo"
    )
    data_atualizacao = models.DateTimeField(
        verbose_name="Data de Atualização"
    )

    def __str__(self):
        return f"{self.funcionario.nome} - {self.cargo.nome} ({self.data_atualizacao.strftime('%d/%m/%Y %H:%M')})"

    class Meta:
        ordering = ['-data_atualizacao']
        verbose_name_plural = "Histórico de Cargos"
