from datetime import timedelta

from django.db import models
from django.utils import timezone

from .funcionario import Funcionario
from .treinamento import Treinamento

import os
from django.utils.text import slugify
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

def renomear_anexo_avaliacao(instance, filename):
    nome, ext = os.path.splitext(filename)
    funcionario = slugify(instance.funcionario.nome if instance.funcionario else "funcionario")
    treinamento = slugify(instance.treinamento.nome_curso if instance.treinamento else "treinamento")
    data = instance.data_avaliacao.strftime("%Y%m%d") if instance.data_avaliacao else "semdata"
    return os.path.join("avaliacoes_treinamento", f"avaliacao-{funcionario}-{treinamento}-{data}{ext}")

@deconstructible
class MaxFileSizeValidator:
    def __init__(self, max_mb=5):
        self.max_mb = max_mb
    def __call__(self, arquivo):
        if arquivo and isinstance(arquivo, UploadedFile) and arquivo.size > self.max_mb * 1024 * 1024:
            raise ValidationError(f"Tamanho máximo permitido é {self.max_mb} MB.")
    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and self.max_mb == other.max_mb
    
class AvaliacaoTreinamento(models.Model):
    """
    Representa a avaliação de um treinamento realizada após determinado período,
    com base em critérios de conhecimento, aplicação e resultados.
    """

    OPCOES_CONHECIMENTO = [
        (1, "Não possui conhecimento mínimo da metodologia para sua aplicação."),
        (2, "Apresenta deficiências nos conceitos, o que compromete a aplicação."),
        (3, "Possui noções básicas, mas necessita de acompanhamento e suporte na aplicação."),
        (4, "Possui domínio necessário da metodologia e a utiliza adequadamente."),
        (5, "Possui completo domínio e utiliza a metodologia com excelência."),
    ]

    OPCOES_APLICACAO = [
        (1, "Está muito abaixo do esperado."),
        (2, "Aplicação está abaixo do esperado."),
        (3, "Aplicação é razoável, mas não dentro do esperado."),
        (4, "Aplicação está adequada e corresponde às expectativas."),
        (5, "Aplicação excede as expectativas."),
    ]

    OPCOES_RESULTADOS = [
        (1, "Nenhum resultado foi obtido efetivamente até o momento."),
        (2, "As melhorias obtidas estão muito abaixo do esperado."),
        (3, "As melhorias obtidas são consideráveis, mas não dentro do esperado."),
        (4, "As melhorias obtidas são boas e estão dentro do esperado."),
        (5, "As melhorias obtidas excederam as expectativas."),
    ]

    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.CASCADE,
        verbose_name="Funcionário"
    )
    treinamento = models.ForeignKey(
        Treinamento,
        on_delete=models.CASCADE,
        related_name="avaliacoes",
        verbose_name="Treinamento"
    )

    data_avaliacao = models.DateField(
        verbose_name="Data da Avaliação"
    )
    periodo_avaliacao = models.IntegerField(
        default=60,
        verbose_name="Período da Avaliação (dias)"
    )
    anexo = models.FileField(
        upload_to=renomear_anexo_avaliacao,
        null=True,
        blank=True,
        verbose_name="Comprovante/Anexo",
        validators=[MaxFileSizeValidator(5)]
    )
   
    responsavel_1 = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="avaliacoes_responsavel_1",
        verbose_name="Responsável 1"
    )
    responsavel_2 = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="avaliacoes_responsavel_2",
        verbose_name="Responsável 2"
    )
    responsavel_3 = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="avaliacoes_responsavel_3",
        verbose_name="Responsável 3"
    )

    pergunta_1 = models.IntegerField(
        choices=OPCOES_CONHECIMENTO,
        null=True,
        blank=True,
        verbose_name="Conhecimento da Metodologia"
    )
    pergunta_2 = models.IntegerField(
        choices=OPCOES_APLICACAO,
        null=True,
        blank=True,
        verbose_name="Aplicação na Prática"
    )
    pergunta_3 = models.IntegerField(
        choices=OPCOES_RESULTADOS,
        null=True,
        blank=True,
        verbose_name="Resultados Obtidos"
    )

    descricao_melhorias = models.TextField(
        default="Nenhuma melhoria descrita",
        blank=True,
        verbose_name="Descrição das Melhorias"
    )
    avaliacao_geral = models.IntegerField(
        choices=[
            (1, "Pouco eficaz"),
            (2, "Eficaz"),
            (3, "Razoável"),
            (4, "Bom"),
            (5, "Muito eficaz"),
        ],
        null=True,
        blank=True,
        verbose_name="Avaliação Geral"
    )

    def get_status_prazo(self):
        """
        Verifica se a avaliação foi realizada dentro do prazo, comparando com a data de avaliação.
        """
        if self.treinamento and self.treinamento.data_fim and self.data_avaliacao:
            data_limite = self.treinamento.data_fim + timedelta(days=self.periodo_avaliacao)
            return "Dentro do Prazo" if self.data_avaliacao <= data_limite else "Em Atraso"
        return "Data inválida"






    def __str__(self):
        return f"Avaliação de {self.funcionario.nome} - {self.treinamento.titulo}"

    class Meta:
        ordering = ['-data_avaliacao']
        verbose_name_plural = "Avaliações de Treinamento"

    @property
    def data_limite(self):
        if self.treinamento and self.treinamento.data_fim:
            return self.treinamento.data_fim + timedelta(days=self.periodo_avaliacao)
        return None
