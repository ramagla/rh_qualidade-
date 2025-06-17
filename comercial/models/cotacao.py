from django.db import models

class Cotacao(models.Model):
    titulo = models.CharField(max_length=255)
    data_criacao = models.DateTimeField(auto_now_add=True)
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.titulo
