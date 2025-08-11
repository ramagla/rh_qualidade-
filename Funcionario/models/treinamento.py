import calendar
import os
from calendar import monthrange

from django.db import models
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field

from .funcionario import Funcionario
import os
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.text import slugify
from django.core.files.uploadedfile import UploadedFile

def renomear_anexo_treinamento(instance, filename):
    nome, ext = os.path.splitext(filename)
    curso = slugify(instance.nome_curso or "curso")
    data = (instance.data_fim or instance.data_inicio).strftime("%Y%m%d")
    return os.path.join("certificados", f"treinamento-{curso}-{data}{ext}")

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

anexo = models.FileField(
    upload_to=renomear_anexo_treinamento,
    blank=True,
    null=True,
    verbose_name="Anexo",
    validators=[MaxFileSizeValidator(5)],
)


class Treinamento(models.Model):
    """
    Representa um treinamento ou curso realizado pelos funcionários,
    contendo informações detalhadas sobre o tipo, categoria, período,
    instituição e anexos relacionados.
    """

    TIPO_TREINAMENTO_CHOICES = [
        ("interno", "Interno"),
        ("externo", "Externo"),
    ]

    CATEGORIA_CHOICES = [
        ("capacitacao", "Capacitação"),
        ("tecnico", "Técnico"),
        ("graduacao", "Graduação"),
        ("pos-graduacao", "Pos-graduação"),
        ("treinamento", "Treinamento"),
        ("divulgacao", "Divulgação"),
    ]

    STATUS_CHOICES = [
        ("planejado", "Planejado"), 
        ("concluido", "Concluído"),
        ("trancado", "Trancado"),
        ("cursando", "Cursando"),
        ("requerido", "Requerido"),
    ]

    SITUACAO_CHOICES = [
        ("aprovado", "Aprovado"),
        ("reprovado", "Reprovado"),
    ]

    PLANEJADO_CHOICES = [
        ("sim", "Sim"),
        ("nao", "Não"),
    ]

    funcionarios = models.ManyToManyField(
        Funcionario,
        related_name="treinamentos",
        verbose_name="Funcionários"
    )
    tipo = models.CharField(
        max_length=50,
        choices=TIPO_TREINAMENTO_CHOICES,
        verbose_name="Tipo de Treinamento"
    )
    categoria = models.CharField(
        max_length=100,
        choices=CATEGORIA_CHOICES,
        verbose_name="Categoria"
    )
    nome_curso = models.CharField(
        max_length=100,
        verbose_name="Nome do Curso"
    )
    instituicao_ensino = models.CharField(
        max_length=255,
        default="Bras-Mol",
        verbose_name="Instituição de Ensino"
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="cursando",
        verbose_name="Status"
    )
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_fim = models.DateField(verbose_name="Data de Término")
    carga_horaria = models.CharField(max_length=50, verbose_name="Carga Horária")
    anexo = models.FileField(
        upload_to=renomear_anexo_treinamento,
        blank=True,
        null=True,
        verbose_name="Anexo",
        validators=[MaxFileSizeValidator(5)],
    )
    descricao = CKEditor5Field(
        config_name="default",
        blank=True,
        null=True,
        verbose_name="Descrição"
    )
    situacao = models.CharField(
        max_length=50,
        choices=SITUACAO_CHOICES,
        blank=True,
        null=True,
        help_text="Campo exibido apenas para treinamentos requeridos.",
        verbose_name="Situação"
    )
    planejado = models.CharField(
        max_length=3,
        choices=PLANEJADO_CHOICES,
        default="nao",
        verbose_name="Planejado"
    )
    necessita_avaliacao = models.BooleanField(
        default=False,
        verbose_name="Necessita Avaliação"
    )

    class Meta:
        verbose_name = "Treinamento"
        verbose_name_plural = "Treinamentos"
        ordering = ["-data_inicio"]

    def __str__(self):
        return self.nome_curso

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para garantir regras específicas:
        - Remove situação caso status não seja 'requerido'.
        - Atualiza escolaridade dos funcionários associados ao concluir treinamento específico.
        """
        if self.status != "requerido":
            self.situacao = None

        super().save(*args, **kwargs)

        if self.status == "concluido" and self.categoria in [
            "tecnico", "graduacao", "pos-graduacao", "mestrado", "doutorado"
        ]:
            for funcionario in self.funcionarios.all():
                funcionario.atualizar_escolaridade()

    def delete(self, *args, **kwargs):
        if self.anexo:
            self.anexo.delete(save=False)
        super().delete(*args, **kwargs)


    @property
    def meses_agendados(self):
        """
        Retorna uma lista formatada dos meses abrangidos pelo treinamento.
        Exemplo: ['Jan/24', 'Fev/24']
        """
        meses = []
        ano_inicio, mes_inicio = self.data_inicio.year, self.data_inicio.month
        ano_fim, mes_fim = self.data_fim.year, self.data_fim.month

        for ano in range(ano_inicio, ano_fim + 1):
            mes_inicial = mes_inicio if ano == ano_inicio else 1
            mes_final = mes_fim if ano == ano_fim else 12
            for mes in range(mes_inicial, mes_final + 1):
                meses.append(f"{calendar.month_abbr[mes].capitalize()}/{str(ano)[-2:]}")
        return meses
