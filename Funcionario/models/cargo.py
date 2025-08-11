from django.db import models
from django.utils import timezone
from Funcionario.models.departamentos import Departamentos
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
import os

@deconstructible
class MaxFileSizeValidator:
    def __init__(self, max_mb=5):
        self.max_mb = max_mb
    def __call__(self, arquivo):
        if arquivo and arquivo.size > self.max_mb * 1024 * 1024:
            raise ValidationError(f"Tamanho máximo permitido é {self.max_mb} MB.")
    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and self.max_mb == other.max_mb

def renomear_descricao_cargo(instance, filename):
    nome, ext = os.path.splitext(filename)
    return os.path.join(
        "cargos",
        f"descricao-cargo-{slugify(instance.nome)}-dc-{instance.numero_dc}{ext}"
    )

NIVEIS_HIERARQUIA = [
    (1, "Alta Direção / Conselho"),
    (2, "Diretoria"),
    (3, "Gerência Sênior"),
    (4, "Gerência Média"),
    (5, "Coordenação"),
    (6, "Supervisão"),
    (7, "Liderança Técnica"),
    (8, "Analista / Técnico"),
    (9, "Assistente / Auxiliar"),
    (10, "Operacional"),
]


class Cargo(models.Model):
    """
    Modelo que representa a descrição de um cargo com suas responsabilidades,
    requisitos e vinculação hierárquica.
    """

    nome = models.CharField(
        max_length=100,
        verbose_name="Nome do Cargo"
    )
    numero_dc = models.CharField(
        max_length=4,
        verbose_name="Número DC"
    )
    descricao_arquivo = models.FileField(
        upload_to=renomear_descricao_cargo,
        blank=True,
        null=True,
        verbose_name="Arquivo Descritivo",
        validators=[MaxFileSizeValidator(5)],
    )
    departamento = models.ForeignKey(
        Departamentos,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cargos",
        verbose_name="Departamento"
    )
    nivel = models.PositiveSmallIntegerField(
        choices=NIVEIS_HIERARQUIA,
        verbose_name="Nível Hierárquico",
        help_text="1 = Mais alto (Direção), 10 = Mais baixo (Operacional)",
        default=10
    )

    responsabilidade_atividade_primaria = models.TextField(
        verbose_name="Responsabilidade e Autoridade: (Atividade Primária)",
        blank=True,
        null=True
    )
    responsabilidade_atividade_secundaria = models.TextField(
        verbose_name="Responsabilidade e Autoridade: (Atividade Secundária)",
        blank=True,
        null=True
    )
    educacao_minima = models.TextField(
        verbose_name="Educação mínima",
        blank=True,
        null=True
    )
    treinamento_externo = models.TextField(
        verbose_name="Treinamento / Curso (Externo)",
        blank=True,
        null=True
    )
    treinamento_interno_minimo = models.TextField(
        verbose_name="Treinamento mínimo (interno)",
        blank=True,
        null=True
    )
    experiencia_minima = models.TextField(
        verbose_name="Experiência mínima",
        blank=True,
        null=True
    )
    elaborador = models.ForeignKey(
        "Funcionario.Funcionario",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="cargos_elaborados",
        verbose_name="Elaborador"
    )
    elaborador_data = models.DateField(
        default=timezone.now,
        verbose_name="Data de Elaboração"
    )
    aprovador = models.ForeignKey(
        "Funcionario.Funcionario",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="cargos_aprovados",
        verbose_name="Aprovador"
    )
    aprovador_data = models.DateField(
        default=timezone.now,
        verbose_name="Data de Aprovação"
    )

    def __str__(self):
        return f"{self.nome} - DC N° {self.numero_dc.zfill(2)}"

    class Meta:
        ordering = ["nivel", "nome"]
        verbose_name_plural = "Cargos"


class Revisao(models.Model):
    """
    Histórico de revisões de um cargo, contendo descrição das alterações e data.
    """

    cargo = models.ForeignKey(
        Cargo,
        related_name="revisoes",
        on_delete=models.CASCADE,
        verbose_name="Cargo"
    )
    numero_revisao = models.CharField(
        max_length=20,
        verbose_name="Número da Revisão"
    )
    data_revisao = models.DateField(
        default=timezone.now,
        verbose_name="Data da Revisão"
    )
    descricao_mudanca = models.TextField(
        verbose_name="Descrição da Mudança"
    )

    def __str__(self):
        return f"Revisão {self.numero_revisao} - {self.cargo.nome}"

    class Meta:
        ordering = ["-data_revisao"]
        verbose_name_plural = "Revisões de Cargo"
