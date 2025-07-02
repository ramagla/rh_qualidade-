from django.contrib.auth.models import User
from django.db import models
from Funcionario.models.documentos import RevisaoDoc


class RevisaoDocLeitura(models.Model):
    """
    Registra a leitura de uma revisão de documento por um usuário específico,
    incluindo a data da leitura realizada automaticamente.
    """

    revisao = models.ForeignKey(
        RevisaoDoc,
        related_name="leituras",
        on_delete=models.CASCADE,
        verbose_name="Revisão do Documento"
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Usuário"
    )
    data_leitura = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data da Leitura"
    )

    class Meta:
        verbose_name = "Leitura de Revisão de Documento"
        verbose_name_plural = "Leituras de Revisões de Documentos"
        unique_together = ("revisao", "usuario")
        ordering = ["-data_leitura"]

    def __str__(self):
        return f"{self.usuario} leu {self.revisao}"
