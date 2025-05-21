from django.db import models
from ..models.veiculo import VeiculoPortaria

class PessoaPortaria(models.Model):
    TIPOS = [
        ("visitante", "Visitante"),
        ("entregador", "Entregador"),
    ]

    tipo = models.CharField(max_length=20, choices=TIPOS)
    nome = models.CharField(max_length=100)
    documento = models.CharField("RG", max_length=20, blank=True, null=True)
    empresa = models.CharField("Empresa/Origem", max_length=100, blank=True, null=True)
    foto = models.ImageField(upload_to="fotos_portaria/", blank=True, null=True)
    veiculos_vinculados = models.ManyToManyField(
        "VeiculoPortaria", blank=True, related_name="pessoas_vinculadas"
    )

    def __str__(self):
        return self.nome
