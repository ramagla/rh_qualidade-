from django.db import models

from .cargo import Cargo
from .funcionario import Funcionario


class HistoricoCargo(models.Model):
    funcionario = models.ForeignKey(
        Funcionario, on_delete=models.CASCADE, related_name="historico_cargos"
    )
    cargo = models.ForeignKey(
        Cargo, on_delete=models.CASCADE, related_name="historico_cargos"
    )
    # Permite definir manualmente ou automaticamente
    data_atualizacao = models.DateTimeField()

    def __str__(self):
        return f"{self.funcionario.nome} - {self.cargo.nome} ({self.data_atualizacao})"
