from django.db import models


class Departamentos(models.Model):
    """
    Representa um departamento organizacional da empresa, com nome, sigla e status de atividade.
    """

    nome = models.CharField("Nome do Departamento", max_length=100, unique=True)
    sigla = models.CharField("Sigla", max_length=30, unique=True)
    ativo = models.BooleanField("Ativo", default=True)

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ["nome"]

    def __str__(self):
        return self.nome
