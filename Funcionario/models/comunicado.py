from django.db import models
from django.utils import timezone


class Comunicado(models.Model):
    TIPO_CHOICES = [
        ("Auditoria", "Auditoria"),
        ("Conscientizacao", "Conscientização"),
        ("Melhoria", "Melhoria"),
        ("Organizacao/Processos", "Organização / Processos"),
        ("Recursos Humanos", "Recursos Humanos"),
        ("Visita de Cliente", "Visita de Cliente"),
    ]

    data = models.DateField(default=timezone.now)
    assunto = models.CharField(max_length=100)
    descricao = models.TextField()
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    departamento_responsavel = models.CharField(max_length=100)
    lista_assinaturas = models.FileField(
        upload_to="assinaturas/", null=True, blank=True
    )

    def __str__(self):
        return f"Comunicado {self.id} - {self.assunto}"
