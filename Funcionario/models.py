from django.db import models
from django.utils import timezone

class Funcionario(models.Model):
    nome = models.CharField(max_length=100)
    data_admissao = models.DateField()
    cargo_inicial = models.CharField(max_length=100)
    cargo_atual = models.CharField(max_length=100)
    numero_registro = models.CharField(max_length=20, unique=True)
    local_trabalho = models.CharField(max_length=100)
    data_integracao = models.DateField()
    responsavel = models.CharField(max_length=100)
    cargo_responsavel = models.CharField(max_length=100)
    escolaridade = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Cargo(models.Model):
    nome = models.CharField(max_length=100)
    cbo = models.CharField(max_length=20)
    descricao_arquivo = models.FileField(upload_to='descriptions/', null=True, blank=True)
    numero_revisao = models.CharField(max_length=10, null=True, blank=True)
    data_ultima_atualizacao = models.DateField(default=timezone.now, null=True, blank=True)

    def __str__(self):
        return self.nome

class Revisao(models.Model):
    cargo = models.ForeignKey(Cargo, related_name='revisoes', on_delete=models.CASCADE)
    numero_revisao = models.CharField(max_length=10)
    data_revisao = models.DateField(default=timezone.now)
    descricao_mudanca = models.TextField()

    def __str__(self):
        return f"Revisão {self.numero_revisao} - {self.cargo.nome}"