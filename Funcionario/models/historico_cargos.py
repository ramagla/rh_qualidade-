from django.db import models
from .funcionario import Funcionario
from .cargo import Cargo

class HistoricoCargo(models.Model):
    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.CASCADE,
        related_name="historico_cargos"
    )
    cargo = models.ForeignKey(
        Cargo,
        on_delete=models.CASCADE,
        related_name="historico_cargos"
    )
    data_atualizacao = models.DateTimeField()  # Permite definir manualmente ou automaticamente

    def __str__(self):
        return f"{self.funcionario.nome} - {self.cargo.nome} ({self.data_atualizacao})"
