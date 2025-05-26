from django.db import models
from django.utils.timezone import now
from .pessoas import PessoaPortaria
from .veiculo import VeiculoPortaria
from rh_qualidade.utils import title_case  # Importa a função de formatação


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

    def save(self, *args, **kwargs):
            # Aplicar capitalização inteligente
            if self.pessoa and self.pessoa.nome:
                self.pessoa.nome = title_case(self.pessoa.nome)
                self.pessoa.save(update_fields=['nome'])

            if self.pessoa and self.pessoa.empresa:
                self.pessoa.empresa = title_case(self.pessoa.empresa)
                self.pessoa.save(update_fields=['empresa'])

            if self.falar_com:
                self.falar_com = title_case(self.falar_com)

            super().save(*args, **kwargs)