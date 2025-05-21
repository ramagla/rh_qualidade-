from django.db import models
from django.utils.timezone import now
from .pessoas import PessoaPortaria
from .veiculo import VeiculoPortaria


# portaria/models/entrada_visitante.py
class EntradaVisitante(models.Model):
    pessoa = models.ForeignKey(PessoaPortaria, on_delete=models.CASCADE)
    veiculo = models.ForeignKey(VeiculoPortaria, on_delete=models.SET_NULL, blank=True, null=True)
    data = models.DateField(default=now)
    hora_entrada = models.TimeField(default=now)
    hora_saida = models.TimeField(blank=True, null=True)
    falar_com = models.CharField(max_length=100)
    motivo = models.CharField(
        max_length=50,
        choices=[
            ("coleta", "Coleta de Mercadorias"),
            ("entrega", "Entrega de Mercadorias"),
            ("servico", "Prestador de Serviço"),
            ("entrevista", "Entrevista"),
            ("reuniao", "Reunião"),
            ("outro", "Outro"),
        ]
    )
    outro_motivo = models.CharField(max_length=100, blank=True, null=True)
