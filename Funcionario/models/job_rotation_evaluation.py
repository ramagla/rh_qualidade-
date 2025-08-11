from django.db import models

from .cargo import Cargo
from .funcionario import Funcionario
# job_rotation_evaluation.py
import os
from django.utils.text import slugify
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

def renomear_anexo_jobrotation(instance, filename):
    nome, ext = os.path.splitext(filename)
    funcionario = slugify(getattr(instance.funcionario, "nome", "") or "funcionario")
    data = instance.data_inicio.strftime("%Y%m%d") if instance.data_inicio else "semdata"
    return os.path.join("job_rotation", "evaluations", f"jobrotation-{funcionario}-{data}{ext}")

@deconstructible
class MaxFileSizeValidator:
    def __init__(self, max_mb=5):
        self.max_mb = max_mb
    def __call__(self, arquivo):
        if arquivo and isinstance(arquivo, UploadedFile) and arquivo.size > self.max_mb * 1024 * 1024:
            raise ValidationError(f"Tamanho máximo permitido é {self.max_mb} MB.")
    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and self.max_mb == other.max_mb
    
class JobRotationEvaluation(models.Model):
    """
    Representa uma avaliação de job rotation realizada para movimentação de função,
    com acompanhamento do gestor, RH e do próprio funcionário.
    """

    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.CASCADE,
        related_name="job_rotation_evaluations",
        verbose_name="Funcionário"
    )
    local_trabalho = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Local de Trabalho"
    )
    cargo_atual = models.ForeignKey(
        Cargo,
        related_name="job_rotation_evaluations_cargo",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Cargo Atual"
    )
    competencias = models.TextField(
        null=True,
        blank=True,
        verbose_name="Competências"
    )
    data_ultima_avaliacao = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data da Última Avaliação"
    )
    status_ultima_avaliacao = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Status da Última Avaliação"
    )
    cursos_realizados = models.JSONField(
        default=list,
        null=True,
        blank=True,
        verbose_name="Cursos Realizados"
    )
    escolaridade = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Escolaridade"
    )
    area = models.CharField(
        max_length=100,
        verbose_name="Área"
    )
    nova_funcao = models.ForeignKey(
        Cargo,
        related_name="nova_funcao",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Nova Função"
    )
    data_inicio = models.DateField(
        verbose_name="Data de Início"
    )
    termino_previsto = models.DateField(
        editable=False,
        null=True,
        blank=True,
        verbose_name="Término Previsto"
    )
    gestor_responsavel = models.ForeignKey(
        Funcionario,
        related_name="gestor_responsavel",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Gestor Responsável"
    )
    descricao_cargo = models.TextField(
        null=True,
        blank=True,
        verbose_name="Descrição do Cargo"
    )
    treinamentos_requeridos = models.TextField(
        blank=True,
        verbose_name="Treinamentos Requeridos"
    )
    treinamentos_propostos = models.TextField(
        blank=True,
        verbose_name="Treinamentos Propostos"
    )
    avaliacao_gestor = models.TextField(
        blank=True,
        verbose_name="Avaliação do Gestor"
    )
    avaliacao_funcionario = models.TextField(
        blank=True,
        verbose_name="Avaliação do Funcionário"
    )
    avaliacao_rh = models.CharField(
        max_length=20,
        choices=[
            ("Apto", "Apto"),
            ("Inapto", "Inapto"),
            ("Prorrogar TN", "Prorrogar TN"),
            ("EmProgresso", "Em Progresso"),
        ],
        verbose_name="Avaliação RH"
    )
    disponibilidade_vaga = models.BooleanField(
        default=False,
        verbose_name="Disponibilidade de Vaga"
    )
    anexo = models.FileField(
        upload_to=renomear_anexo_jobrotation,
        null=True,
        blank=True,
        verbose_name="Anexo (arquivo)",
        validators=[MaxFileSizeValidator(5)]
    )


    def __str__(self):
        return f"Avaliação de Job Rotation - {self.funcionario.nome}"
    
    def delete(self, *args, **kwargs):
        if self.anexo:
            self.anexo.delete(save=False)
        super().delete(*args, **kwargs)

    class Meta:
        ordering = ["-data_inicio"]
        verbose_name_plural = "Avaliações de Job Rotation"
