from django.db import models
from django_ckeditor_5.fields import CKEditor5Field

from .funcionario import Funcionario

import os
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.core.files.uploadedfile import UploadedFile
from django.utils.text import slugify

def renomear_anexo_lista_presenca(instance, filename):
    nome, ext = os.path.splitext(filename)
    assunto = slugify(instance.assunto or "lista-presenca")
    data = (instance.data_fim or instance.data_inicio).strftime("%Y%m%d")
    return os.path.join("listas_presenca", f"lista-{assunto}-{data}{ext}")

@deconstructible
class MaxFileSizeValidator:
    def __init__(self, max_mb=5):
        self.max_mb = max_mb
    def __call__(self, arquivo):
        if not arquivo:
            return
        if not isinstance(arquivo, UploadedFile):
            return
        if arquivo.size > self.max_mb * 1024 * 1024:
            raise ValidationError(f"Tamanho máximo permitido é {self.max_mb} MB.")
    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and self.max_mb == other.max_mb
    
class ListaPresenca(models.Model):
    """
    Representa uma lista de presença para treinamentos, cursos ou eventos internos,
    com descrição, horários e participantes vinculados.
    """

    TIPO_CHOICES = [
        ("Treinamento", "Treinamento"),
        ("Curso", "Curso"),
        ("Divulgacao", "Divulgação"),
        ("Conscientização", "Conscientização"),
    ]

    SITUACAO_CHOICES = [
        ("finalizado", "Finalizado"),
        ("em_andamento", "Em Andamento"),
    ]

    treinamento = models.CharField(
        max_length=255,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de Evento"
    )
    data_inicio = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Início"
    )
    data_fim = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Término"
    )
    horario_inicio = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Horário de Início"
    )
    horario_fim = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Horário de Término"
    )
    instrutor = models.CharField(
        max_length=255,
        verbose_name="Instrutor"
    )
    duracao = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Duração (horas)"
    )
    necessita_avaliacao = models.BooleanField(
        default=False,
        verbose_name="Necessita Avaliação?"
    )
    lista_presenca = models.FileField(
        upload_to=renomear_anexo_lista_presenca,
        blank=True,
        null=True,
        verbose_name="Arquivo da Lista de Presença",
        validators=[MaxFileSizeValidator(5)],
    )
    participantes = models.ManyToManyField(
        Funcionario,
        related_name="participantes",
        verbose_name="Participantes"
    )
    assunto = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Assunto"
    )
    descricao = CKEditor5Field(
        config_name="default",
        verbose_name="Descrição"
    )
    situacao = models.CharField(
        max_length=20,
        choices=SITUACAO_CHOICES,
        default="em_andamento",
        verbose_name="Situação"
    )
    planejado = models.CharField(
        max_length=3,
        choices=[("sim", "Sim"), ("nao", "Não")],
        default="nao",
        verbose_name="Planejado?"
    )

    def __str__(self):
        return f"Lista de Presença - {self.treinamento} ({self.data_inicio} - {self.data_fim})"

    def duracao_formatada(self):
        """
        Retorna a duração no formato "Xh Ym".
        """
        if self.duracao:
            total_minutes = int(self.duracao * 60)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours}h {minutes}m"
        return ""
    
    def delete(self, *args, **kwargs):
        if self.lista_presenca:
            self.lista_presenca.delete(save=False)
        super().delete(*args, **kwargs)

    class Meta:
        ordering = ["-data_inicio"]
        verbose_name_plural = "Listas de Presença"
