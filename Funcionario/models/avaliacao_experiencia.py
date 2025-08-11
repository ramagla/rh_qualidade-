from datetime import timedelta

from django.db import models
from django.utils import timezone

from .funcionario import Funcionario
import os
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.core.files.uploadedfile import UploadedFile

def renomear_anexo_avaliacao_experiencia(instance, filename):
    nome, ext = os.path.splitext(filename)
    funcionario = slugify(getattr(instance.funcionario, "nome", "") or "funcionario")
    data = instance.data_avaliacao.strftime("%Y%m%d") if instance.data_avaliacao else "semdata"
    return os.path.join("avaliacoes", "experiencia", f"avaliacao-experiencia-{funcionario}-{data}{ext}")

@deconstructible
class MaxFileSizeValidator:
    def __init__(self, max_mb=5):
        self.max_mb = max_mb
    def __call__(self, arquivo):
        if not arquivo or not isinstance(arquivo, UploadedFile):
            return
        if arquivo.size > self.max_mb * 1024 * 1024:
            raise ValidationError(f"Tamanho máximo permitido é {self.max_mb} MB.")
    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and self.max_mb == other.max_mb

class AvaliacaoExperiencia(models.Model):
    """
    Representa a avaliação de experiência de um funcionário recém-contratado,
    contendo critérios como adaptação, interesse e orientação final.
    """

    data_avaliacao = models.DateField(
        verbose_name="Data da Avaliação"
    )
    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.CASCADE,
        verbose_name="Funcionário"
    )
    gerencia = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Gerência"
    )

    adaptacao_trabalho = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Adaptação ao Trabalho"
    )
    interesse = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Interesse"
    )
    relacionamento_social = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Relacionamento Social"
    )
    capacidade_aprendizagem = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Capacidade de Aprendizagem"
    )
    anexo = models.FileField(
        upload_to=renomear_anexo_avaliacao_experiencia,
        blank=True,
        null=True,
        verbose_name="Anexo",
        validators=[MaxFileSizeValidator(5)],
    )


    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações"
    )
    orientacao = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Orientação"
    )

    @property
    def get_status_avaliacao(self):
        """
        Retorna o status da avaliação com emoji com base na orientação final.
        """
        if self.orientacao == "Efetivar":
            return "😃 Efetivar"
        elif self.orientacao == "Encaminhar p/ Treinamento":
            return "😊 Treinamento"
        elif self.orientacao == "Desligar":
            return "😕 Desligar"
        return "Indeterminado"

    def get_status_prazo(self):
        """
        Verifica se a avaliação está dentro do prazo de 30 dias.
        """
        hoje = timezone.now().date()
        data_limite = self.data_avaliacao + timedelta(days=30)
        return "Dentro do Prazo" if data_limite >= hoje else "Em Atraso"

    def __str__(self):
        return f"Avaliação de Experiência de {self.funcionario} em {self.data_avaliacao.strftime('%d/%m/%Y')}"
    
    def delete(self, *args, **kwargs):
        if self.anexo:
            self.anexo.delete(save=False)
        super().delete(*args, **kwargs)

    class Meta:
        ordering = ['-data_avaliacao']
        verbose_name_plural = "Avaliações de Experiência"
