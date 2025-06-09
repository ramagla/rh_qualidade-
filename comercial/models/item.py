from django.db import models

class Item(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    descricao = models.CharField(max_length=255)
    unidade = models.CharField(max_length=10)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"
