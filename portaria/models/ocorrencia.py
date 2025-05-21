# portaria/models/ocorrencia.py
from django.db import models
from django.contrib.auth.models import User
from Funcionario.models import Funcionario

class OcorrenciaPortaria(models.Model):
    TIPO_CHOICES = [
        ("alarme", "Alarme"),
        ("acesso_indevido", "Acesso Indevido"),
        ("confusao", "Confusão"),
        ("reclamacao", "Reclamação"),
        ("outros", "Outros"),
    ]

    STATUS_CHOICES = [
        ("aberta", "Aberta"),
        ("analise", "Em Análise"),
        ("encerrada", "Encerrada"),
    ]

    tipo_ocorrencia = models.CharField(max_length=30, choices=TIPO_CHOICES)
    local = models.CharField(max_length=100)
    data_inicio = models.DateField()
    hora_inicio = models.TimeField()
    data_fim = models.DateField(blank=True, null=True)
    hora_fim = models.TimeField(blank=True, null=True)
    descricao = models.TextField()
    pessoas_envolvidas = models.ManyToManyField(Funcionario, blank=True, related_name="ocorrencias")
    foi_registrado_boletim = models.BooleanField(default=False)
    arquivo_anexo = models.FileField(upload_to="ocorrencias/", blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="aberta")
    responsavel_registro = models.ForeignKey(User, on_delete=models.PROTECT)
    data_registro = models.DateTimeField(auto_now_add=True)
    numero_boletim = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.get_tipo_ocorrencia_display()} - {self.local} ({self.data_inicio})"
