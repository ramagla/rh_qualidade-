import os

from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ValidationError

@deconstructible
class MaxFileSizeValidator:
    def __init__(self, max_mb=5):
        self.max_mb = max_mb

    def __call__(self, arquivo):
        if arquivo and arquivo.size > self.max_mb * 1024 * 1024:
            raise ValidationError(f"Tamanho máximo permitido é {self.max_mb} MB.")

    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and self.max_mb == other.max_mb


def renomear_lista_assinaturas(instance, filename):
    nome, extensao = os.path.splitext(filename)
    tipo_slug = slugify(instance.tipo or "comunicado")
    return os.path.join(
        "comunicados",
        f"comunicado-{tipo_slug}-{instance.id or 'novo'}-{instance.data.strftime('%Y%m%d')}{extensao}"
    )

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
        upload_to=renomear_lista_assinaturas,
        blank=True,
        null=True,
        verbose_name="Lista de Assinaturas",
        validators=[MaxFileSizeValidator(5)],
    )

    def __str__(self):
        return f"Comunicado {self.id} - {self.assunto}"
    
    def delete(self, *args, **kwargs):
        if self.lista_assinaturas and os.path.isfile(self.lista_assinaturas.path):
            os.remove(self.lista_assinaturas.path)
        super().delete(*args, **kwargs)

    class Meta:
        ordering = ['-data']
        verbose_name_plural = "Comunicados"
