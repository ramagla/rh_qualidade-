from django.db import models
from .choices_departamento import DEPARTAMENTOS_EMPRESA

class Departamento(models.Model):
    codigo = models.CharField(max_length=30, choices=DEPARTAMENTOS_EMPRESA, unique=True)

    def __str__(self):
        return dict(DEPARTAMENTOS_EMPRESA).get(self.codigo, self.codigo)
