from django.db import models
from django.utils import timezone


class Comunicado(models.Model):
    """
    Modelo que representa um comunicado interno, com assunto, descrição, tipo e
    departamento responsável.
    """

    TIPO_CHOICES = [
        ("Auditoria", "Auditoria"),
        ("Conscientizacao", "Conscientização"),
        ("Melhoria", "Melhoria"),
        ("Organizacao/Processos", "Organização / Processos"),
        ("Recursos Humanos", "Recursos Humanos"),
        ("Visita de Cliente", "Visita de Cliente"),
    ]

    data = models.DateField(
        default=timezone.now,
        verbose_name="Data do Comunicado"
    )
    assunto = models.CharField(
        max_length=100,
        verbose_name="Assunto"
    )
    descricao = models.TextField(
        verbose_name="Descrição"
    )
    tipo = models.CharField(
        max_length=50,
        choices=TIPO_CHOICES,
        verbose_name="Tipo do Comunicado"
    )
    departamento_responsavel = models.CharField(
        max_length=100,
        verbose_name="Departamento Responsável"
    )
    lista_assinaturas = models.FileField(
        upload_to="assinaturas/",
        null=True,
        blank=True,
        verbose_name="Lista de Assinaturas"
    )

    def __str__(self):
        return f"Comunicado {self.id} - {self.assunto}"

    class Meta:
        ordering = ['-data']
        verbose_name_plural = "Comunicados"
