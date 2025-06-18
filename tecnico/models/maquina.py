from django.db import models

class Maquina(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=100)
    servico_realizado = models.CharField(max_length=200)
    velocidade = models.DecimalField(max_digits=10, decimal_places=2, help_text="Unidade do produto por hora")
    valor_hora = models.DecimalField(max_digits=10, decimal_places=2)
    consumo_kwh = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    