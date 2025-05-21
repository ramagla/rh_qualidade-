from django.db import models
from Funcionario.models import Funcionario
from django.utils import timezone


class LigacaoPortaria(models.Model):
    nome = models.CharField("Quem ligou", max_length=100)
    numero = models.CharField("Número de telefone", max_length=20, blank=True)
    empresa = models.CharField("Empresa / Origem", max_length=100, blank=True)
    falar_com = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, verbose_name="Falar com")
    horario = models.TimeField("Horário da ligação")
    data = models.DateField("Data", default=timezone.now)
    recado_enviado = models.BooleanField("Recado enviado", default=False)
    recado = models.TextField("Recado")

    def __str__(self):
        return f"{self.nome} ({self.data} - {self.horario})"
