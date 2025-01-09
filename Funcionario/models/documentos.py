from django.db import models
from django.utils import timezone
from .cargo import Cargo


class Documento(models.Model):
    STATUS_CHOICES = [
        ('aprovado', 'Aprovado'),
        ('em_revisao', 'Em Revisão'),
        ('inativo', 'Inativo'),
    ]

    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=4)
    arquivo = models.FileField(upload_to='documentos/', blank=True, null=True)  # Nome mais claro
    responsavel_recuperacao = models.ForeignKey(Cargo, related_name='cargos', on_delete=models.CASCADE)
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='em_revisao',
    )

    def __str__(self):
        return self.nome

class RevisaoDoc(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
    ]
    documento = models.ForeignKey(Documento, related_name='revisoes', on_delete=models.CASCADE)
    numero_revisao = models.CharField(max_length=20)
    data_revisao = models.DateField(default=timezone.now)
    descricao_mudanca = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ativo',
    )

    def __str__(self):
        return f"Revisão {self.numero_revisao} - {self.documento.nome}"