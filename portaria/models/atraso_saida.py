from django.db import models
from Funcionario.models import Funcionario

class AtrasoSaida(models.Model):
    TIPO_CHOICES = [
        ("atraso", "Atraso"),
        ("saida", "Saída Antecipada"),
        ("hora_extra", "Hora Extra"),  # ✅ Novo

    ]

    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name="ocorrencias_portaria")
    data = models.DateField()
    horario = models.TimeField(null=True, blank=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    observacao = models.TextField(blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Atraso ou Saída Antecipada"
        verbose_name_plural = "Atrasos e Saídas Antecipadas"
        ordering = ["-data", "-horario"]

    def __str__(self):
        return f"{self.funcionario.nome} - {self.get_tipo_display()} em {self.data}"
