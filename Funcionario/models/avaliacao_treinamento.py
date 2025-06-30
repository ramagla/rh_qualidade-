from datetime import timedelta

from django.db import models
from django.utils import timezone

from .funcionario import Funcionario
from .treinamento import Treinamento


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
        upload_to="avaliacoes_treinamento/",
        null=True,
        blank=True,
        verbose_name="Comprovante/Anexo"
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
        Retorna o status de prazo da avaliação com base na data e período.
        """
        data_limite = self.data_avaliacao + timedelta(days=self.periodo_avaliacao)
        return "Dentro do Prazo" if timezone.now().date() <= data_limite else "Em Atraso"

    def __str__(self):
        return f"Avaliação de {self.funcionario.nome} - {self.treinamento.titulo}"

    class Meta:
        ordering = ['-data_avaliacao']
        verbose_name_plural = "Avaliações de Treinamento"
