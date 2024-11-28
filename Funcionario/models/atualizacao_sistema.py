from django.db import models

class AtualizacaoSistema(models.Model):
    STATUS_CHOICES = [
        ('concluido', 'Concluído'),
        ('em_andamento', 'Em andamento'),
        ('cancelado', 'Cancelado'),
    ]

    titulo = models.CharField(max_length=100)
    descricao = models.TextField()
    previsao = models.DateField()
    versao = models.CharField(max_length=20)
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='em_andamento',
    )

    def __str__(self):
        return f"{self.versao} - {self.titulo}"
