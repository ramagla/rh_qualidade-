from django.db import models

from .cargo import Cargo
from .funcionario import Funcionario


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

    def __str__(self):
        return f"Avaliação de Job Rotation - {self.funcionario.nome}"

    class Meta:
        ordering = ["-data_inicio"]
        verbose_name_plural = "Avaliações de Job Rotation"
