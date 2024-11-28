from django.db import models
from django.utils import timezone


class Cargo(models.Model):
    nome = models.CharField(max_length=100)
    numero_dc = models.CharField(max_length=4)
    descricao_arquivo = models.FileField(upload_to='cargos/', blank=True, null=True)
    departamento = models.CharField(max_length=100, verbose_name='Departamento')

    def __str__(self):
        return self.nome

class Revisao(models.Model):
    cargo = models.ForeignKey(Cargo, related_name='revisoes', on_delete=models.CASCADE)
    numero_revisao = models.CharField(max_length=20)
    data_revisao = models.DateField(default=timezone.now)
    descricao_mudanca = models.TextField()

    def __str__(self):
        return f"Revisão {self.numero_revisao} - {self.cargo.nome}"